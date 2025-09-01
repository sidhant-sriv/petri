"""
LangGraph Nodes for Agent Workflow

This module contains the individual nodes that make up the agent's
LangGraph workflow. Each node represents a discrete step in the agent's
thought process: Perceive, Remember, Think, and Act.
"""

import json
import uuid
from datetime import datetime

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

from .state import AgentState
from .schemas import AgentDecision, PostSummary, FeedContext
from .config import settings
from .prompts import create_router_prompt
from ..tools.world_tools import get_feed, get_agent, ACTION_TOOLS


def _get_action_tool(tool_name: str):
    """Helper function to get an action tool by name from ACTION_TOOLS collection."""
    for tool in ACTION_TOOLS:
        if tool.name == tool_name:
            return tool
    return None


def load_agent_details(state: AgentState) -> AgentState:
    """
    Load agent details from the world API.
    
    Entry point node that fetches the agent's name and persona.
    """
    print(f"🔍 Loading details for agent {state['agent_id']}")
    
    try:
        agent_data = get_agent(state["agent_id"])
        state["persona"] = agent_data["persona"]
        state["agent_name"] = agent_data["name"]
        state["timestamp"] = datetime.now()
        state["execution_id"] = str(uuid.uuid4())
        
        print(f"✅ Loaded agent '{state['agent_name']}' with persona: {state['persona'][:100]}...")
        
    except Exception as e:
        print(f"❌ Failed to load agent details: {e}")
        # Set defaults to allow the graph to continue
        state["persona"] = "A curious agent exploring the world."
        state["agent_name"] = f"Agent_{state['agent_id']}"
        state["timestamp"] = datetime.now()
        state["execution_id"] = str(uuid.uuid4())
    
    return state


def perceive(state: AgentState) -> AgentState:
    """
    Perceive the current world state by fetching the feed.
    
    This node fetches the latest posts from the world to understand
    the current context of the conversation.
    """
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
    """
    Router node that makes decisions based on persona and feed.
    
    This node uses ChatOllama with structured output to decide what action
    the agent should take: comment, post, update_persona, or do_nothing.
    """
    print(f"🤔 {state['agent_name']} is making a decision...")
    
    # Prepare the feed context for the LLM
    post_summaries = []
    own_posts = []
    other_posts = []
    
    for post in state["new_posts"]:
        try:
            # Handle both dictionary and object formats
            if isinstance(post, dict):
                author_name = post["author"]["name"] if "author" in post else "Unknown"
                summary = PostSummary(
                    id=post["id"],
                    author=author_name,
                    text=post["text"],
                    timestamp=str(post["created_at"]),
                    has_comments=len(post.get("comments", [])) > 0
                )
            else:
                # Assume it's already a Post object with attributes
                author_name = post.author.name if hasattr(post, 'author') else "Unknown"
                summary = PostSummary(
                    id=post.id,
                    author=author_name,
                    text=post.text,
                    timestamp=str(post.created_at),
                    has_comments=len(post.comments) > 0 if hasattr(post, 'comments') else False
                )
            
            # Categorize posts by ownership
            if author_name == state["agent_name"]:
                own_posts.append(summary)
            else:
                other_posts.append(summary)
            
            post_summaries.append(summary)
        except Exception as e:
            print(f"⚠️ Warning: Failed to process post: {e}")
            continue
    
    print(f"📊 Feed analysis: {len(own_posts)} own posts, {len(other_posts)} others' posts")
    
    feed_context = FeedContext(
        posts=post_summaries,
        total_posts=len(post_summaries),
        agent_persona=state["persona"],
        agent_name=state["agent_name"]
    )
    
    # Create the prompt for the LLM
    prompt = create_router_prompt(
        agent_name=state['agent_name'],
        persona=state['persona'],
        own_posts=own_posts,
        other_posts=other_posts
    )

    try:
        # Initialize ChatOllama with structured output
        llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model="llama3.1:8b",
            format="json"
        )
        
        # Create message
        message = HumanMessage(content=prompt)
        
        # Get LLM response
        response = llm.invoke([message])
        
        # Parse the JSON response
        try:
            print(f"🔍 Raw LLM response: {response.content}")
            
            # Clean the response - sometimes models add extra text
            content = response.content.strip()
            
            # Try to extract JSON if there's extra text
            if not content.startswith('{'):
                # Look for JSON block
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end > start:
                    content = content[start:end]
                    print(f"🔧 Extracted JSON: {content}")
            
            decision_data = json.loads(content)
             
            # Validate with Pydantic
            decision = AgentDecision(**decision_data)
            
            # Intelligent validation: analyze self-commenting decisions
            if decision.action == "comment" and decision.target_post_id:
                target_post_author = None
                for post in state["new_posts"]:
                    post_id = post.get("id") if isinstance(post, dict) else getattr(post, "id", None)
                    if post_id == decision.target_post_id:
                        if isinstance(post, dict):
                            target_post_author = post.get("author", {}).get("name")
                        else:
                            target_post_author = getattr(post.author, "name", None) if hasattr(post, "author") else None
                        break
                
                if target_post_author == state["agent_name"]:
                    print(f"🪞 SELF-COMMENT DETECTED: Agent wants to comment on own post {decision.target_post_id}")
                    print(f"   Reasoning: {decision.reasoning}")
                    print(f"   Self-aware: {getattr(decision, 'is_self_comment', 'Not specified')}")
                    
                    # Check if the reasoning seems valid for self-commenting
                    reasoning_lower = decision.reasoning.lower()
                    valid_reasons = [
                        "clarif", "update", "correct", "add", "respond", "evolv", 
                        "reflect", "context", "follow-up", "expand", "detail"
                    ]
                    
                    has_valid_reason = any(keyword in reasoning_lower for keyword in valid_reasons)
                    is_self_aware = getattr(decision, 'is_self_comment', None) is True
                    
                    if has_valid_reason and is_self_aware:
                        print(f"   ✅ APPROVED: Valid self-aware self-comment")
                        print(f"   🎯 Agent explicitly acknowledges commenting on own post")
                    elif has_valid_reason and not is_self_aware:
                        print(f"   ⚠️ VALID BUT UNAWARE: Good reason but agent didn't acknowledge self-comment")
                        print(f"   🤔 Proceeding but with reduced confidence")
                        decision.confidence = max(0.1, decision.confidence * 0.7)
                    elif not has_valid_reason and is_self_aware:
                        print(f"   ⚠️ SELF-AWARE BUT UNCLEAR: Agent knows it's self-commenting but reason unclear")
                        print(f"   🤔 Proceeding but with reduced confidence")
                        decision.confidence = max(0.1, decision.confidence * 0.8)
                    else:
                        print(f"   ❌ QUESTIONABLE: Unclear reason and not self-aware")
                        print(f"   🤔 Proceeding but with significantly reduced confidence")
                        decision.confidence = max(0.1, decision.confidence * 0.5)
                else:
                    if getattr(decision, 'is_self_comment', None) is True:
                        print(f"   ⚠️ INCONSISTENCY: Agent marked is_self_comment=true but targeting others' post")
                        # Create a new decision with corrected field
                        decision = AgentDecision(
                            action=decision.action,
                            reasoning=decision.reasoning,
                            confidence=decision.confidence,
                            content=decision.content,
                            target_post_id=decision.target_post_id,
                            new_persona=decision.new_persona,
                            is_self_comment=False
                        )
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"⚠️ Failed to parse LLM response as JSON: {e}")
            print(f"Raw response: {response.content}")
            # Fallback decision
            decision = AgentDecision(
                action="do_nothing",
                reasoning="Failed to parse LLM response, staying quiet",
                confidence=0.1
            )
        
        # Update state with decision
        state["llm_decision"] = decision.dict()
        state["action_to_perform"] = decision.action.upper()
        state["output_text"] = decision.content
        state["target_post_id"] = decision.target_post_id
        
        # Log the decision
        print(f"🎯 Decision: {decision.action}")
        print(f"💭 Reasoning: {decision.reasoning}")
        print(f"🎲 Confidence: {decision.confidence:.2f}")
        
        if decision.content:
            print(f"📝 Content: {decision.content[:100]}...")
        
    except Exception as e:
        print(f"❌ Router failed: {e}")
        # Fallback to do nothing
        state["llm_decision"] = {
            "action": "do_nothing",
            "reasoning": f"Router failed due to error: {str(e)}",
            "confidence": 0.0
        }
        state["action_to_perform"] = "DO_NOTHING"
        state["output_text"] = None
        state["target_post_id"] = None
    
    return state


def route_decision(state: AgentState) -> str:
    """
    Conditional edge function that routes based on the agent's decision.
    
    Returns the next node name based on the action_to_perform.
    """
    action = state.get("action_to_perform", "DO_NOTHING")
    
    print(f"🛤️  Routing to action: {action}")
    
    if action in ["POST", "COMMENT", "UPDATE_PERSONA"]:
        return "act"
    else:
        return "end"


def act(state: AgentState) -> AgentState:
    """
    Execute the agent's decision by interacting with the world.
    
    This function implements the actual world interactions by calling
    the appropriate world API tools based on the agent's decision.
    """
    action = state.get("action_to_perform", "DO_NOTHING")
    agent_id = state["agent_id"]
    
    print(f"🎬 {state['agent_name']} is executing action: {action}")
    
    try:
        if action == "POST":
            content = state.get('output_text', '')
            if content:
                print(f"📄 Creating new post: {content[:100]}...")
                create_post_tool = _get_action_tool('create_post')
                if create_post_tool:
                    result = create_post_tool.invoke({"agent_id": agent_id, "text": content})
                else:
                    result = {"success": False, "error": "create_post tool not found"}
                
                if result.get("success"):
                    print(f"✅ Post created successfully: ID {result['post']['id']}")
                    state["execution_result"] = {
                        "success": True,
                        "action": "post",
                        "post_id": result['post']['id'],
                        "message": "Post created successfully"
                    }
                else:
                    print(f"❌ Failed to create post: {result.get('error', 'Unknown error')}")
                    state["execution_result"] = {
                        "success": False,
                        "action": "post",
                        "error": result.get("error", "Unknown error")
                    }
            else:
                print("⚠️ No content provided for post creation")
                state["execution_result"] = {
                    "success": False,
                    "action": "post",
                    "error": "No content provided"
                }
                
        elif action == "COMMENT":
            content = state.get('output_text', '')
            target_post_id = state.get('target_post_id')
            
            if content and target_post_id:
                print(f"💬 Commenting on post {target_post_id}: {content[:100]}...")
                create_comment_tool = _get_action_tool('create_comment')
                if create_comment_tool:
                    result = create_comment_tool.invoke({
                        "agent_id": agent_id, 
                        "post_id": target_post_id, 
                        "text": content
                    })
                else:
                    result = {"success": False, "error": "create_comment tool not found"}
                
                if result.get("success"):
                    print(f"✅ Comment created successfully: ID {result['comment']['id']}")
                    state["execution_result"] = {
                        "success": True,
                        "action": "comment",
                        "comment_id": result['comment']['id'],
                        "post_id": target_post_id,
                        "message": "Comment created successfully"
                    }
                else:
                    print(f"❌ Failed to create comment: {result.get('error', 'Unknown error')}")
                    state["execution_result"] = {
                        "success": False,
                        "action": "comment",
                        "error": result.get("error", "Unknown error")
                    }
            else:
                missing = []
                if not content:
                    missing.append("content")
                if not target_post_id:
                    missing.append("target_post_id")
                error_msg = f"Missing required fields: {', '.join(missing)}"
                print(f"⚠️ {error_msg}")
                state["execution_result"] = {
                    "success": False,
                    "action": "comment",
                    "error": error_msg
                }
                
        elif action == "UPDATE_PERSONA":
            new_persona = state["llm_decision"].get("new_persona")
            
            if new_persona:
                print(f"🔄 Updating persona to: {new_persona[:100]}...")
                update_persona_tool = _get_action_tool('update_agent_persona')
                if update_persona_tool:
                    result = update_persona_tool.invoke({
                        "agent_id": agent_id, 
                        "new_persona": new_persona
                    })
                else:
                    result = {"success": False, "error": "update_agent_persona tool not found"}
                
                if result.get("success"):
                    print(f"✅ Persona updated successfully")
                    # Update the state to reflect the new persona
                    state["persona"] = new_persona
                    state["execution_result"] = {
                        "success": True,
                        "action": "update_persona",
                        "new_persona": new_persona,
                        "message": "Persona updated successfully"
                    }
                else:
                    print(f"❌ Failed to update persona: {result.get('error', 'Unknown error')}")
                    state["execution_result"] = {
                        "success": False,
                        "action": "update_persona",
                        "error": result.get("error", "Unknown error")
                    }
            else:
                print("⚠️ No new persona provided for update")
                state["execution_result"] = {
                    "success": False,
                    "action": "update_persona",
                    "error": "No new persona provided"
                }
                
        else:
            print("😴 Doing nothing, staying quiet")
            state["execution_result"] = {
                "success": True,
                "action": "do_nothing",
                "message": "Agent chose to remain quiet"
            }
        
    except Exception as e:
        print(f"❌ Unexpected error during action execution: {e}")
        state["execution_result"] = {
            "success": False,
            "action": action.lower(),
            "error": f"Unexpected error: {str(e)}"
        }
    
    print(f"🏁 Action {action} execution completed")
    
    return state
