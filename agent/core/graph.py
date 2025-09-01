"""
LangGraph Agent Implementation

This module implements the agent's complete thought process as a LangGraph.
The graph orchestrates the agent's lifecycle: Perceive, Remember, Think, and Act.
"""

from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes import load_agent_details, perceive, router_node, route_decision, act


def create_agent_graph() -> StateGraph:
    """
    Create the agent's LangGraph workflow.

    The graph implements the agent's lifecycle:
    1. Load agent details (persona, name)
    2. Perceive the world (fetch feed)
    3. Route/Think (make decision based on persona and feed)
    4. Act (execute decision) or End (do nothing)

    Returns:
        StateGraph: The compiled agent workflow graph
    """
    # Create the graph with AgentState
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("load_agent_details", load_agent_details)
    workflow.add_node("perceive", perceive)
    workflow.add_node("router", router_node)
    workflow.add_node("act", act)

    # Define the flow
    workflow.set_entry_point("load_agent_details")

    # Sequential flow through perception and thinking
    workflow.add_edge("load_agent_details", "perceive")
    workflow.add_edge("perceive", "router")

    # Conditional routing after the decision
    workflow.add_conditional_edges("router", route_decision, {"act": "act", "end": END})

    workflow.add_edge("act", END)

    return workflow.compile()


def run_agent_turn(agent_id: int) -> dict:
    """
    Run a complete agent turn (one execution of the lifecycle).

    Args:
        agent_id: The ID of the agent to run

    Returns:
        dict: The final state after the agent's turn
    """
    print(f"\n🚀 Starting agent turn for agent {agent_id}")
    print("=" * 50)

    # Create the graph
    graph = create_agent_graph()

    # Initialize state
    initial_state = {
        "agent_id": agent_id,
        "persona": "",
        "agent_name": "",
        "new_posts": [],
        "extracted_entities": [],
        "relevant_memories": "",
        "llm_decision": {},
        "action_to_perform": "",
        "output_text": None,
        "target_post_id": None,
        "timestamp": None,
        "execution_id": "",
    }

    try:
        final_state = graph.invoke(initial_state)
        return final_state

    except Exception as e:
        raise
