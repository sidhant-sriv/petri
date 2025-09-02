"""
LangGraph Nodes for Agent Workflow

This module contains the individual nodes that make up the agent's
LangGraph workflow. Each node represents a discrete step in the agent's
thought process: Perceive, Remember, Think, and Act.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

from .state import AgentState
from .schemas import AgentDecision, PostSummary, FeedContext
from .config import settings
from .prompts import create_router_prompt
from ..tools.world_tools import get_feed, get_agent, ACTION_TOOLS

# Constants
DEFAULT_PERSONA = "A curious agent exploring the world."
DEFAULT_AGENT_PREFIX = "Agent_"
CONTENT_PREVIEW_LENGTH = 100
MIN_CONFIDENCE = 0.1
CONFIDENCE_REDUCTION_FACTORS = {
    'valid_unaware': 0.7,
    'aware_unclear': 0.8,
    'questionable': 0.5
}

VALID_SELF_COMMENT_KEYWORDS = {
    "clarif", "update", "correct", "add", "respond", 
    "evolv", "reflect", "context", "follow-up", 
    "expand", "detail"
}

SUPPORTED_ACTIONS = {"POST", "COMMENT", "UPDATE_PERSONA"}

# Cache for action tools
_ACTION_TOOL_CACHE = {tool.name: tool for tool in ACTION_TOOLS}


def _get_action_tool(tool_name: str):
    """Helper function to get an action tool by name from ACTION_TOOLS collection."""
    return _ACTION_TOOL_CACHE.get(tool_name)


def _set_default_agent_state(state: AgentState, agent_id: str) -> None:
    """Set default values for agent state when loading fails."""
    state.update({
        "persona": DEFAULT_PERSONA,
        "agent_name": f"{DEFAULT_AGENT_PREFIX}{agent_id}",
        "timestamp": datetime.now(),
        "execution_id": str(uuid.uuid4())
    })


def _extract_post_data(post: Any) -> Tuple[str, str, str, str, int]:
    """Extract data from a post object, handling both dict and object formats."""
    if isinstance(post, dict):
        author_name = post.get("author", {}).get("name", "Unknown")
        return (
            post["id"],
            author_name,
            post["text"], 
            str(post["created_at"]),
            len(post.get("comments", []))
        )
    
    # Handle object format
    author_name = getattr(getattr(post, "author", object()), "name", "Unknown")
    return (
        post.id,
        author_name,
        post.text,
        str(post.created_at),
        len(getattr(post, "comments", []))
    )


def _create_post_summary(post: Any) -> Optional[PostSummary]:
    """Create a PostSummary from a post object."""
    try:
        post_id, author_name, text, timestamp, comment_count = _extract_post_data(post)
        return PostSummary(
            id=post_id,
            author=author_name,
            text=text,
            timestamp=timestamp,
            has_comments=comment_count > 0,
        )
    except Exception as e:
        print(f"⚠️ Warning: Failed to process post: {e}")
        return None


def _categorize_posts_by_author(posts: List[Any], agent_name: str) -> Tuple[List[PostSummary], List[PostSummary]]:
    """Categorize posts into own and others' posts."""
    own_posts, other_posts = [], []
    
    for post in posts:
        summary = _create_post_summary(post)
        if summary is None:
            continue
            
        target_list = own_posts if summary.author == agent_name else other_posts
        target_list.append(summary)
    
    return own_posts, other_posts


def _clean_llm_response(content: str) -> str:
    """Clean and extract JSON from LLM response."""
    content = content.strip()
    
    if content.startswith("{"):
        return content
    
    # Extract JSON block
    start = content.find("{")
    end = content.rfind("}") + 1
    
    if start != -1 and end > start:
        extracted = content[start:end]
        print(f"🔧 Extracted JSON: {extracted}")
        return extracted
    
    return content


def _has_valid_self_comment_reason(reasoning: str) -> bool:
    """Check if the reasoning contains valid keywords for self-commenting."""
    reasoning_lower = reasoning.lower()
    return any(keyword in reasoning_lower for keyword in VALID_SELF_COMMENT_KEYWORDS)


def _calculate_adjusted_confidence(decision: AgentDecision, has_valid_reason: bool, is_self_aware: bool) -> float:
    """Calculate adjusted confidence based on self-comment validation."""
    if has_valid_reason and is_self_aware:
        print("   ✅ APPROVED: Valid self-aware self-comment")
        return decision.confidence
    
    if has_valid_reason and not is_self_aware:
        print("   ⚠️ VALID BUT UNAWARE: Good reason but agent didn't acknowledge self-comment")
        factor = CONFIDENCE_REDUCTION_FACTORS['valid_unaware']
    elif not has_valid_reason and is_self_aware:
        print("   ⚠️ SELF-AWARE BUT UNCLEAR: Agent knows it's self-commenting but reason unclear")
        factor = CONFIDENCE_REDUCTION_FACTORS['aware_unclear']
    else:
        print("   ❌ QUESTIONABLE: Unclear reason and not self-aware")
        factor = CONFIDENCE_REDUCTION_FACTORS['questionable']
    
    return max(MIN_CONFIDENCE, decision.confidence * factor)


def _find_target_post_author(posts: List[Any], target_post_id: str) -> Optional[str]:
    """Find the author of the target post."""
    for post in posts:
        post_id = post.get("id") if isinstance(post, dict) else getattr(post, "id", None)
        if post_id == target_post_id:
            if isinstance(post, dict):
                return post.get("author", {}).get("name")
            return getattr(getattr(post, "author", object()), "name", None)
    return None


def _validate_self_comment_decision(decision: AgentDecision, state: AgentState) -> AgentDecision:
    """Validate and adjust decision for self-commenting scenarios."""
    if decision.action != "comment" or not decision.target_post_id:
        return decision
    
    target_post_author = _find_target_post_author(state["new_posts"], decision.target_post_id)
    agent_name = state["agent_name"]
    
    if target_post_author == agent_name:
        print(f"🪞 SELF-COMMENT DETECTED: Agent wants to comment on own post {decision.target_post_id}")
        print(f"   Reasoning: {decision.reasoning}")
        
        has_valid_reason = _has_valid_self_comment_reason(decision.reasoning)
        is_self_aware = getattr(decision, 'is_self_comment', None) is True
        
        decision.confidence = _calculate_adjusted_confidence(decision, has_valid_reason, is_self_aware)
    
    elif getattr(decision, "is_self_comment", None) is True:
        print("   ⚠️ INCONSISTENCY: Agent marked is_self_comment=true but targeting others' post")
        # Create corrected decision
        decision = AgentDecision(
            action=decision.action,
            reasoning=decision.reasoning,
            confidence=decision.confidence,
            content=decision.content,
            target_post_id=decision.target_post_id,
            new_persona=decision.new_persona,
            is_self_comment=False,
        )
    
    return decision


def _create_fallback_decision(reason: str, confidence: float = MIN_CONFIDENCE) -> Dict[str, Any]:
    """Create a fallback decision when processing fails."""
    return {
        "action": "do_nothing",
        "reasoning": reason,
        "confidence": confidence,
    }


def _update_state_with_decision(state: AgentState, decision: AgentDecision) -> None:
    """Update state with the agent's decision."""
    state.update({
        "llm_decision": decision.model_dump(),
        "action_to_perform": decision.action.upper(),
        "output_text": decision.content,
        "target_post_id": decision.target_post_id
    })


def _log_decision(decision: AgentDecision) -> None:
    """Log the agent's decision details."""
    print(f"🎯 Decision: {decision.action}")
    print(f"💭 Reasoning: {decision.reasoning}")
    print(f"🎲 Confidence: {decision.confidence:.2f}")
    
    if decision.content:
        print(f"📝 Content: {decision.content[:CONTENT_PREVIEW_LENGTH]}...")


def _execute_post_action(state: AgentState) -> Dict[str, Any]:
    """Execute post creation action."""
    content = state.get("output_text", "")
    if not content:
        return {
            "success": False,
            "action": "post",
            "error": "No content provided"
        }
    
    print(f"📄 Creating new post: {content[:CONTENT_PREVIEW_LENGTH]}...")
    
    create_post_tool = _get_action_tool("create_post")
    if not create_post_tool:
        return {"success": False, "error": "create_post tool not found"}
    
    result = create_post_tool.invoke({
        "agent_id": state["agent_id"], 
        "text": content
    })
    
    if result.get("success"):
        print(f"✅ Post created successfully: ID {result['post']['id']}")
        return {
            "success": True,
            "action": "post",
            "post_id": result["post"]["id"],
            "message": "Post created successfully",
        }
    
    print(f"❌ Failed to create post: {result.get('error', 'Unknown error')}")
    return {
        "success": False,
        "action": "post",
        "error": result.get("error", "Unknown error"),
    }


def _execute_comment_action(state: AgentState) -> Dict[str, Any]:
    """Execute comment creation action."""
    content = state.get("output_text", "")
    target_post_id = state.get("target_post_id")
    
    missing_fields = []
    if not content:
        missing_fields.append("content")
    if not target_post_id:
        missing_fields.append("target_post_id")
    
    if missing_fields:
        error_msg = f"Missing required fields: {', '.join(missing_fields)}"
        print(f"⚠️ {error_msg}")
        return {
            "success": False,
            "action": "comment",
            "error": error_msg,
        }
    
    print(f"💬 Commenting on post {target_post_id}: {content[:CONTENT_PREVIEW_LENGTH]}...")
    
    create_comment_tool = _get_action_tool("create_comment")
    if not create_comment_tool:
        return {"success": False, "error": "create_comment tool not found"}
    
    result = create_comment_tool.invoke({
        "agent_id": state["agent_id"],
        "post_id": target_post_id,
        "text": content,
    })
    
    if result.get("success"):
        print(f"✅ Comment created successfully: ID {result['comment']['id']}")
        return {
            "success": True,
            "action": "comment",
            "comment_id": result["comment"]["id"],
            "post_id": target_post_id,
            "message": "Comment created successfully",
        }
    
    print(f"❌ Failed to create comment: {result.get('error', 'Unknown error')}")
    return {
        "success": False,
        "action": "comment",
        "error": result.get("error", "Unknown error"),
    }


def _execute_persona_update_action(state: AgentState) -> Dict[str, Any]:
    """Execute persona update action."""
    new_persona = state["llm_decision"].get("new_persona")
    
    if not new_persona:
        print("⚠️ No new persona provided for update")
        return {
            "success": False,
            "action": "update_persona",
            "error": "No new persona provided",
        }
    
    print(f"🔄 Updating persona to: {new_persona[:CONTENT_PREVIEW_LENGTH]}...")
    
    update_persona_tool = _get_action_tool("update_agent_persona")
    if not update_persona_tool:
        return {"success": False, "error": "update_agent_persona tool not found"}
    
    result = update_persona_tool.invoke({
        "agent_id": state["agent_id"], 
        "new_persona": new_persona
    })
    
    if result.get("success"):
        print("✅ Persona updated successfully")
        # Update the state to reflect the new persona
        state["persona"] = new_persona
        return {
            "success": True,
            "action": "update_persona",
            "new_persona": new_persona,
            "message": "Persona updated successfully",
        }
    
    print(f"❌ Failed to update persona: {result.get('error', 'Unknown error')}")
    return {
        "success": False,
        "action": "update_persona",
        "error": result.get("error", "Unknown error"),
    }


# Main node functions
def load_agent_details(state: AgentState) -> AgentState:
    """Load agent details from the world API."""
    print(f"🔍 Loading details for agent {state['agent_id']}")

    try:
        agent_data = get_agent(state["agent_id"])
        state.update({
            "persona": agent_data["persona"],
            "agent_name": agent_data["name"],
            "timestamp": datetime.now(),
            "execution_id": str(uuid.uuid4())
        })
        
        print(f"✅ Loaded agent '{state['agent_name']}' with persona: {state['persona'][:CONTENT_PREVIEW_LENGTH]}...")

    except Exception as e:
        print(f"❌ Failed to load agent details: {e}")
        _set_default_agent_state(state, state["agent_id"])

    return state


def perceive(state: AgentState) -> AgentState:
    """Perceive the current world state by fetching the feed."""
    print(f"👁️  {state['agent_name']} is perceiving the world...")

    try:
        posts = get_feed()
        state["new_posts"] = posts
        print(f"✅ Perceived {len(posts)} posts from the feed")
    except Exception as e:
        print(f"❌ Failed to perceive world: {e}")
        state["new_posts"] = []

    return state


def router_node(state: AgentState) -> AgentState:
    """Router node that makes decisions based on persona and feed."""
    print(f"🤔 {state['agent_name']} is making a decision...")

    # Prepare the feed context
    own_posts, other_posts = _categorize_posts_by_author(
        state["new_posts"], state["agent_name"]
    )

    print(f"📊 Feed analysis: {len(own_posts)} own posts, {len(other_posts)} others' posts")

    # Create the prompt for the LLM
    prompt = create_router_prompt(
        agent_name=state["agent_name"],
        persona=state["persona"],
        own_posts=own_posts,
        other_posts=other_posts,
    )

    try:
        # Initialize ChatOllama with structured output
        llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL, 
            model="llama3.1:8b", 
            format="json"
        )

        # Get LLM response
        response = llm.invoke([HumanMessage(content=prompt)])
        print(f"🔍 Raw LLM response: {response.content}")

        # Parse and validate the response
        try:
            cleaned_content = _clean_llm_response(response.content)
            decision_data = json.loads(cleaned_content)
            decision = AgentDecision(**decision_data)
            
            # Validate self-commenting decisions
            decision = _validate_self_comment_decision(decision, state)

        except (json.JSONDecodeError, ValueError) as e:
            print(f"⚠️ Failed to parse LLM response as JSON: {e}")
            print(f"Raw response: {response.content}")
            
            decision = AgentDecision(**_create_fallback_decision(
                "Failed to parse LLM response, staying quiet"
            ))

        # Update state and log decision
        _update_state_with_decision(state, decision)
        _log_decision(decision)

    except Exception as e:
        print(f"❌ Router failed: {e}")
        fallback_decision = _create_fallback_decision(f"Router failed due to error: {str(e)}", 0.0)
        
        state.update({
            "llm_decision": fallback_decision,
            "action_to_perform": "DO_NOTHING",
            "output_text": None,
            "target_post_id": None
        })

    return state


def route_decision(state: AgentState) -> str:
    """Conditional edge function that routes based on the agent's decision."""
    action = state.get("action_to_perform", "DO_NOTHING")
    print(f"🛤️  Routing to action: {action}")
    
    return "act" if action in SUPPORTED_ACTIONS else "end"


def act(state: AgentState) -> AgentState:
    """Execute the agent's decision by interacting with the world."""
    action = state.get("action_to_perform", "DO_NOTHING")
    print(f"🎬 {state['agent_name']} is executing action: {action}")

    try:
        action_handlers = {
            "POST": lambda: _execute_post_action(state),
            "COMMENT": lambda: _execute_comment_action(state),
            "UPDATE_PERSONA": lambda: _execute_persona_update_action(state),
        }
        
        if action in action_handlers:
            execution_result = action_handlers[action]()
        else:
            print("😴 Doing nothing, staying quiet")
            execution_result = {
                "success": True,
                "action": "do_nothing",
                "message": "Agent chose to remain quiet",
            }
        
        state["execution_result"] = execution_result

    except Exception as e:
        print(f"❌ Unexpected error during action execution: {e}")
        state["execution_result"] = {
            "success": False,
            "action": action.lower(),
            "error": f"Unexpected error: {str(e)}",
        }

    print(f"🏁 Action {action} execution completed")
    return state