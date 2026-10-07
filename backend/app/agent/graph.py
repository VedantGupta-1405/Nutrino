"""
LangGraph state graph definition for the Nutrino AI agent.
Defines the cyclical reasoning loop between agent_node and tool_execution_node.
"""

from langgraph.graph import END, START, StateGraph
from app.agent.nodes import agent_node, should_continue, tool_execution_node
from app.agent.state import AgentState


def create_agent_graph():
    """
    Constructs and compiles the bounded LangGraph state graph.
    Cycle: START -> agent -> [tools -> agent]* -> END
    """
    builder = StateGraph(AgentState)

    builder.add_node("agent", agent_node)
    builder.add_node("tools", tool_execution_node)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )
    builder.add_edge("tools", "agent")

    return builder.compile()


# Compiled singleton graph
agent_graph = create_agent_graph()
