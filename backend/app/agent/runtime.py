"""
Runtime execution context for the LangGraph agent.
Safely encapsulates live database sessions, user identity, and authenticated ToolContext.
Never serialized into graph state or exposed to the LLM.
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.llm.client import OllamaClient
from app.models.user import User
from app.tools.base import ToolContext


class AgentRuntimeContext:
    """
    Encapsulates backend runtime resources for agent execution.
    Injected via LangGraph RunnableConfig to keep graph state purely serializable.
    The LLM cannot forge, override, or alter these references.
    """

    def __init__(
        self,
        db: Session,
        user: User,
        client: Optional[OllamaClient] = None,
    ):
        self.db = db
        self.user = user
        self.tool_context = ToolContext(db=db, user=user)
        self.client = client or OllamaClient()

    @property
    def user_id(self) -> int:
        return self.user.id
