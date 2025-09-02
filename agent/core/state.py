"""
Agent State Definition for LangGraph

This module defines the state structure that flows through the agent's
LangGraph workflow. The state captures all data needed for the agent's
perception, memory, thinking, and action phases.
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime


class AgentState(TypedDict):
    """
    State object that flows through the agent's LangGraph workflow.

    This state contains all the data needed for an agent's turn, including
    its identity, perception of the world, memories, and decision-making process.
    """

    # Initial input
    agent_id: int

    # Data populated by the graph
    persona: str
    agent_name: str
    new_posts: List[Dict[str, Any]]  # Raw post data from the world API

    # Memory and thought process
    extracted_entities: List[str]
    relevant_memories: str  # A string summarizing retrieved memories

    # The final decision and action
    llm_decision: Dict[str, Any]  # Structured JSON output from the LLM
    action_to_perform: str  # "POST", "COMMENT", "UPDATE_PERSONA", or "DO_NOTHING"
    output_text: Optional[str]
    target_post_id: Optional[int]  # For comments

    # Execution result
    execution_result: Optional[Dict[str, Any]]  # Result of action execution

    # Metadata
    timestamp: datetime
    execution_id: str  # Unique identifier for this execution
