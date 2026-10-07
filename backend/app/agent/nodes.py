"""
Graph execution nodes for LangGraph nutrition agent.
Orchestrates model reasoning and controlled tool invocation.
"""

import json
import logging
import re
import time
from typing import Any, Dict, List
from langchain_core.runnables import RunnableConfig
from pydantic import ValidationError

from app.agent.prompts import (
    AGENT_SYSTEM_PROMPT,
    AgentFinalResponseAction,
    AgentToolAction,
)
from app.agent.runtime import AgentRuntimeContext
from app.agent.state import AgentState
from app.exceptions.base import AppException
from app.tools.registry import tool_registry

logger = logging.getLogger(__name__)

MAX_AGENT_ITERATIONS = 6


def _clean_json_output(raw_output: str) -> str:
    """Strip markdown code fence blocks if returned by the LLM."""
    content = raw_output.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.MULTILINE)
        content = re.sub(r"\s*```$", "", content, flags=re.MULTILINE)
        content = content.strip()
    return content


async def agent_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Agent decision node. Evaluates user request and tool results,
    then decides whether to call a tool or produce the final response.
    """
    runtime_context: AgentRuntimeContext = config["configurable"]["runtime_context"]
    user_id = state["authenticated_user_id"]
    current_iter = state.get("iteration_count", 0)

    # Enforce maximum iteration safety limit
    if current_iter >= MAX_AGENT_ITERATIONS:
        logger.warning(
            "Agent reached maximum reasoning iterations (%d) for user %d",
            MAX_AGENT_ITERATIONS,
            user_id,
        )
        return {
            "final_response": (
                "I reached the maximum reasoning steps for this request. "
                "Please clarify or simplify your question."
            ),
            "tool_calls": [],
        }

    # Construct conversation history
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT}
    ]
    for msg in state["messages"]:
        messages.append({
            "role": msg["role"],
            "content": str(msg["content"]),
        })

    logger.info(
        "Agent decision step %d for user %d (history len: %d)",
        current_iter + 1,
        user_id,
        len(messages),
    )

    t0 = time.perf_counter()
    raw_output = await runtime_context.client.chat(messages, format="json", temperature=0.0)
    duration = time.perf_counter() - t0
    logger.info("LLM reasoning step completed in %.2fs", duration)

    cleaned = _clean_json_output(raw_output)

    # Attempt to parse structured action
    parsed_json: Dict[str, Any] = {}
    try:
        parsed_json = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("LLM output is not valid JSON. Treating as direct final response: %s", cleaned[:80])
        return {
            "final_response": cleaned,
            "tool_calls": [],
            "messages": state["messages"] + [{"role": "assistant", "content": cleaned}],
        }

    action_type = parsed_json.get("action")

    if action_type == "call_tool":
        try:
            tool_action = AgentToolAction.model_validate(parsed_json)
            logger.info("Agent selected tool: '%s'", tool_action.tool)
            return {
                "tool_calls": [{"tool": tool_action.tool, "arguments": tool_action.arguments}],
                "iteration_count": current_iter + 1,
                "messages": state["messages"] + [{"role": "assistant", "content": json.dumps(parsed_json)}],
            }
        except ValidationError as exc:
            logger.warning("Tool call schema validation failed: %s", exc)
            return {
                "final_response": "I encountered an internal formatting issue selecting the tool. Please try again.",
                "tool_calls": [],
                "messages": state["messages"] + [{"role": "assistant", "content": str(exc)}],
            }

    elif action_type == "final_response":
        try:
            final_action = AgentFinalResponseAction.model_validate(parsed_json)
            logger.info("Agent produced final response (%d chars)", len(final_action.content))
            return {
                "final_response": final_action.content,
                "tool_calls": [],
                "messages": state["messages"] + [{"role": "assistant", "content": json.dumps(parsed_json)}],
            }
        except ValidationError:
            # Fallback to direct content string if present
            content_str = str(parsed_json.get("content", cleaned))
            return {
                "final_response": content_str,
                "tool_calls": [],
                "messages": state["messages"] + [{"role": "assistant", "content": content_str}],
            }

    # Fallback if unknown action
    fallback_content = str(parsed_json.get("content") or parsed_json.get("response") or cleaned)
    return {
        "final_response": fallback_content,
        "tool_calls": [],
        "messages": state["messages"] + [{"role": "assistant", "content": fallback_content}],
    }


async def tool_execution_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Tool execution node. Validates and dispatches tool requests against the controlled ToolRegistry.
    Injects ToolContext with authenticated user and active database session.
    """
    runtime_context: AgentRuntimeContext = config["configurable"]["runtime_context"]
    pending_calls = state.get("tool_calls", [])
    user_id = state["authenticated_user_id"]

    new_results: List[Dict[str, Any]] = list(state.get("tool_results", []))
    updated_messages: List[Dict[str, Any]] = list(state.get("messages", []))
    tools_used: List[str] = list(state.get("tools_used", []))

    for call in pending_calls:
        tool_name = call.get("tool", "")
        tool_args = call.get("arguments", {})

        t0 = time.perf_counter()
        logger.info("Executing controlled tool '%s' for user %d", tool_name, user_id)

        # 1. Validation: Verify tool is registered in controlled registry
        tool = tool_registry.get(tool_name)
        if tool is None:
            logger.warning("Rejected attempt to execute unregistered tool: '%s'", tool_name)
            error_msg = (
                f"Error: Tool '{tool_name}' is not a registered application capability. "
                f"Available tools: {', '.join(tool_registry.list_tools())}."
            )
            new_results.append({"tool": tool_name, "success": False, "output": error_msg})
            updated_messages.append({"role": "user", "content": error_msg})
            continue

        # 2. Execution through controlled ToolRegistry with authenticated ToolContext
        try:
            raw_result = tool_registry.execute(
                name=tool_name,
                arguments=tool_args,
                context=runtime_context.tool_context,
            )
            duration = time.perf_counter() - t0
            logger.info("Tool '%s' succeeded in %.2fs", tool_name, duration)

            if hasattr(raw_result, "model_dump"):
                result_data = raw_result.model_dump(mode="json")
            elif hasattr(raw_result, "__dict__"):
                result_data = raw_result.__dict__
            else:
                result_data = raw_result

            result_str = json.dumps(result_data, default=str)
            new_results.append({"tool": tool_name, "success": True, "output": result_data})
            updated_messages.append({
                "role": "user",
                "content": f"Tool '{tool_name}' result: {result_str}",
            })

            if tool_name not in tools_used:
                tools_used.append(tool_name)

        except AppException as exc:
            duration = time.perf_counter() - t0
            logger.warning("Tool '%s' returned application error in %.2fs: %s", tool_name, duration, exc.message)
            error_str = f"Error executing '{tool_name}': {exc.message}"
            new_results.append({"tool": tool_name, "success": False, "output": error_str})
            updated_messages.append({"role": "user", "content": error_str})
            if tool_name not in tools_used:
                tools_used.append(tool_name)

        except ValidationError as exc:
            duration = time.perf_counter() - t0
            logger.warning("Tool '%s' input parameter validation failed: %s", tool_name, exc)
            error_str = f"Validation Error for '{tool_name}' arguments: {exc.errors()}"
            new_results.append({"tool": tool_name, "success": False, "output": error_str})
            updated_messages.append({"role": "user", "content": error_str})
            if tool_name not in tools_used:
                tools_used.append(tool_name)

        except Exception as exc:
            duration = time.perf_counter() - t0
            logger.exception("Unexpected error executing tool '%s': %s", tool_name, exc)
            error_str = f"Unexpected error executing '{tool_name}': {str(exc)}"
            new_results.append({"tool": tool_name, "success": False, "output": error_str})
            updated_messages.append({"role": "user", "content": error_str})
            if tool_name not in tools_used:
                tools_used.append(tool_name)

    return {
        "tool_calls": [],
        "tool_results": new_results,
        "messages": updated_messages,
        "tools_used": tools_used,
    }


def should_continue(state: AgentState) -> str:
    """
    Conditional routing edge.
    If the agent produced a final response or hit limits -> route to END.
    If tool calls are queued -> route to tools.
    """
    if state.get("final_response") is not None:
        return "end"
    if state.get("tool_calls"):
        return "tools"
    return "end"
