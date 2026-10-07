"""
Tool registry for managing, discovering, and dispatching controlled agent tools.
Enables future LangGraph agents to introspect available tools, retrieve input schemas,
and execute actions safely within an authenticated context.
"""

from typing import Any, Dict, List, Optional
from app.exceptions.base import ResourceNotFoundException, ValidationException
from app.tools.base import BaseTool, ToolContext
from app.tools.food_tools import GetFoodTool, SearchFoodTool
from app.tools.goal_tools import GetActiveGoalTool
from app.tools.meal_tools import (
    CreateMealTool,
    DeleteMealTool,
    GetMealTool,
    GetTodayMealsTool,
)
from app.tools.nutrition_tools import (
    GetNutritionHistoryTool,
    GetNutritionTool,
    GetTodayNutritionTool,
)
from app.tools.profile_tools import GetUserProfileTool
from app.tools.recommend_tools import RecommendMealTool


class ToolRegistry:
    """
    Registry for managing controlled backend tools.
    Provides registration, schema discovery, and execution dispatcher.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance. Names must be unique."""
        if tool.name in self._tools:
            raise ValidationException(f"Tool with name '{tool.name}' is already registered.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Retrieve a tool by name if present."""
        return self._tools.get(name)

    def get_or_raise(self, name: str) -> BaseTool:
        """Retrieve a tool by name or raise ResourceNotFoundException."""
        tool = self.get(name)
        if tool is None:
            raise ResourceNotFoundException("Tool", name)
        return tool

    def list_tools(self) -> List[str]:
        """Return a list of all registered tool names."""
        return sorted(list(self._tools.keys()))

    def get_tool_metadata(self) -> List[Dict[str, Any]]:
        """
        Return metadata list for all registered tools, including their JSON schemas.
        Suitable for LLM tool declaration / function-calling bindings.
        """
        return [tool.get_metadata() for tool in self._tools.values()]

    def get_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Return a mapping of tool name to its parameter schema dictionary."""
        return {name: tool.get_metadata() for name, tool in self._tools.items()}

    def execute(self, name: str, arguments: Dict[str, Any], context: ToolContext) -> Any:
        """
        Execute a registered tool by name with provided arguments and context.
        Enforces argument validation and authorization rules.
        """
        tool = self.get_or_raise(name)
        return tool.run(arguments, context)


def create_default_registry() -> ToolRegistry:
    """
    Initializes and populates a ToolRegistry with all 11 controlled application tools.
    """
    registry = ToolRegistry()

    # 1. Food Tools
    registry.register(SearchFoodTool())
    registry.register(GetFoodTool())

    # 2. User Context Tools
    registry.register(GetUserProfileTool())
    registry.register(GetActiveGoalTool())

    # 3. Meal Tools
    registry.register(CreateMealTool())
    registry.register(GetTodayMealsTool())
    registry.register(GetMealTool())
    registry.register(DeleteMealTool())

    # 4. Nutrition Tools
    registry.register(GetTodayNutritionTool())
    registry.register(GetNutritionTool())
    registry.register(GetNutritionHistoryTool())

    # 5. Recommendation Tools (Phase 9)
    registry.register(RecommendMealTool())

    return registry


# Global registry singleton
tool_registry: ToolRegistry = create_default_registry()
