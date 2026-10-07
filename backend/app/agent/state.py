"""
Agent state schema for LangGraph nutrition agent.
Defines explicit, typed orchestrator state without sensitive credentials or direct DB references.
"""

from typing import Any, Dict, List, Optional, TypedDict


class AgentState(TypedDict):
    """
    Serializable state schema for LangGraph orchestration.
    Contains strictly conversational turns, pending tool calls, outputs, and iteration tracking.
    Database sessions and user authentication tokens are strictly excluded.
    """
    user_message: str
    authenticated_user_id: int
    messages: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    final_response: Optional[str]
    iteration_count: int
    tools_used: List[str]
