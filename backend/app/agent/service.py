"""
Agent coordinator service for managing execution lifecycle, logging, and metrics.
"""

import logging
import time
from app.agent.graph import agent_graph
from app.agent.runtime import AgentRuntimeContext
from app.agent.schemas import AgentChatResponse
from app.agent.state import AgentState

logger = logging.getLogger(__name__)


class AgentService:
    """
    High-level coordinator service for invoking the LangGraph agent.
    """

    async def chat(
        self,
        message: str,
        runtime_context: AgentRuntimeContext,
    ) -> AgentChatResponse:
        """
        Executes the agent graph on a user request with authenticated runtime context.
        """
        cleaned_message = message.strip()
        if not cleaned_message:
            raise ValueError("User message cannot be empty.")

        user_id = runtime_context.user_id
        start_time = time.perf_counter()

        logger.info(
            "Agent request started for authenticated user %d (msg_len: %d chars)",
            user_id,
            len(cleaned_message),
        )

        initial_state: AgentState = {
            "user_message": cleaned_message,
            "authenticated_user_id": user_id,
            "messages": [{"role": "user", "content": cleaned_message}],
            "tool_calls": [],
            "tool_results": [],
            "final_response": None,
            "iteration_count": 0,
            "tools_used": [],
        }

        config = {
            "configurable": {
                "runtime_context": runtime_context,
            }
        }

        result = await agent_graph.ainvoke(initial_state, config=config)

        total_duration = time.perf_counter() - start_time
        final_answer = result.get("final_response") or "I processed your request, but have no additional details to share."
        tools_used = result.get("tools_used", [])

        logger.info(
            "Agent request completed in %.2fs for user %d (tools_used: %s, steps: %d)",
            total_duration,
            user_id,
            tools_used,
            result.get("iteration_count", 0),
        )

        return AgentChatResponse(
            response=final_answer,
            tools_used=tools_used,
        )


agent_service = AgentService()
