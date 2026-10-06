"""
Base interfaces and context definitions for controlled agent tools.
Every tool operates with typed Pydantic inputs and outputs, and enforces
authenticated user context where applicable.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, Type, TypeVar
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.exceptions.base import AuthorizationException
from app.models.user import User

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class EmptyInput(BaseModel):
    """Empty input schema for parameterless tools."""
    pass


class ToolContext:
    """
    Context passed to tools during execution.
    Contains the active database session and the authenticated User entity.
    """

    def __init__(self, db: Session, user: Optional[User] = None):
        self.db = db
        self.user = user

    def get_authenticated_user(self) -> User:
        """
        Ensures an authenticated user is present in the context.
        Raises AuthorizationException if context is unauthenticated.
        """
        if self.user is None or not self.user.is_active:
            raise AuthorizationException("Authenticated active user context is required to execute this tool.")
        return self.user

    @property
    def user_id(self) -> int:
        """Helper to get authenticated user id safely."""
        return self.get_authenticated_user().id


class ToolResult(BaseModel, Generic[OutputT]):
    """
    Standardized wrapper for tool execution output.
    """
    success: bool = True
    tool_name: str
    data: Optional[OutputT] = None
    error: Optional[str] = None


class BaseTool(ABC, Generic[InputT, OutputT]):
    """
    Abstract base class for all controlled agent tools.
    """

    name: str
    description: str
    input_schema: Type[InputT]
    output_schema: Type[OutputT]
    requires_auth: bool = True

    @abstractmethod
    def execute(self, params: InputT, context: ToolContext) -> OutputT:
        """
        Executes the tool with validated Pydantic parameters and context.
        Must call existing application services and NOT perform direct DB mutations or calculations.
        """
        pass

    def run(self, params_dict: Dict[str, Any], context: ToolContext) -> OutputT:
        """
        Validates parameters dictionary against input_schema and executes the tool.
        """
        if self.requires_auth and context.user is None:
            raise AuthorizationException(f"Tool '{self.name}' requires an authenticated user.")

        validated_params = self.input_schema.model_validate(params_dict or {})
        return self.execute(validated_params, context)

    def get_metadata(self) -> Dict[str, Any]:
        """
        Returns tool metadata with JSON schema for input parameters,
        compatible with LLM function-calling and agent orchestration frameworks.
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema.model_json_schema(),
            "requires_auth": self.requires_auth,
        }
