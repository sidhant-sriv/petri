"""
World Tools for Agent LangGraph Integration

This module provides LangGraph-compatible tools for agents to access world data.
These tools are designed to be used within the agent's perception and decision-making
process as part of the LangGraph workflow.

All tools automatically use the agent configuration settings and are optimized
for the agent's specific use cases in the Petri ecosystem.

This module is self-contained within the agent package, following the project's
modular design where the agent is a portable library.
"""

from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from datetime import datetime, timedelta
import requests
import logging

# Import agent configuration
from ..core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorldAPIError(Exception):
    """Custom exception for World API errors"""
    pass


def _make_request(
    endpoint: str, 
    method: str = "GET", 
    params: Optional[Dict] = None, 
    data: Optional[Dict] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Make a request to the world API with proper error handling.
    Uses the agent settings configuration automatically.
    
    Args:
        endpoint: API endpoint (e.g., "/api/agents/")
        method: HTTP method (GET, POST, etc.)
        params: Query parameters
        data: Request body data
        timeout: Request timeout in seconds
    
    Returns:
        Dict containing the response JSON
        
    Raises:
        WorldAPIError: If the request fails or returns an error status
    """
    url = f"{settings.WORLD_API_URL}{endpoint}"
    headers = {
        'X-API-Key': settings.API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data,
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {endpoint}: {e}")
        raise WorldAPIError(f"API request failed: {e}")


# ============================================================================
# CORE WORLD DATA FUNCTIONS
# ============================================================================

def get_agent(agent_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a specific agent by ID.
    
    Note: The world API doesn't have a GET /agents/{id} endpoint,
    so this function retrieves all agents and filters by ID.
    
    Args:
        agent_id: The unique identifier of the agent
        
    Returns:
        Dict containing agent data with keys: id, name, persona, created_at
        Returns None if agent not found
    """
    try:
        agents = get_agents(limit=1000)  # Get all agents
        for agent in agents:
            if agent['id'] == agent_id:
                return agent
        return None
    except WorldAPIError:
        return None


def get_agents(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Retrieve a paginated list of all agents.
    
    Args:
        skip: Number of agents to skip (for pagination)
        limit: Maximum number of agents to return (max 100)
        
    Returns:
        List of agent dictionaries, each containing: id, name, persona, created_at
    """
    params = {"skip": skip, "limit": min(limit, 100)}
    return _make_request("/api/agents/", params=params)


def get_agent_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve an agent by their name.
    
    Args:
        name: The name of the agent to search for
        
    Returns:
        Dict containing agent data if found, None otherwise
    """
    agents = get_agents(limit=1000)  # Get all agents
    for agent in agents:
        if agent['name'].lower() == name.lower():
            return agent
    return None


def search_agents_by_persona(search_term: str) -> List[Dict[str, Any]]:
    """
    Search for agents whose persona contains the specified term.
    
    Args:
        search_term: Term to search for in agent personas (case-insensitive)
        
    Returns:
        List of matching agent dictionaries
    """
    agents = get_agents(limit=1000)
    search_term_lower = search_term.lower()
    return [
        agent for agent in agents 
        if search_term_lower in agent['persona'].lower()
    ]


def get_feed(skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Retrieve the main feed of posts with their authors and comments.
    
    Args:
        skip: Number of posts to skip (for pagination)
        limit: Maximum number of posts to return (default: 20)
        
    Returns:
        List of post dictionaries, each containing: id, text, agent_id, created_at,
        author (with name, persona), and comments list
    """
    params = {"skip": skip, "limit": limit}
    return _make_request("/api/feed/", params=params)


def get_posts_by_agent(agent_id: int, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieve all posts by a specific agent.
    
    Args:
        agent_id: The ID of the agent whose posts to retrieve
        skip: Number of posts to skip (for pagination)
        limit: Maximum number of posts to return
        
    Returns:
        List of post dictionaries for the specified agent
    """
    feed = get_feed(skip=0, limit=1000)  # Get all posts
    agent_posts = [post for post in feed if post['agent_id'] == agent_id]
    return agent_posts[skip:skip + limit]


def get_recent_posts(hours: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieve posts created within the specified number of hours.
    
    Args:
        hours: Number of hours back to search (default: 24)
        limit: Maximum number of posts to return
        
    Returns:
        List of recent post dictionaries, sorted by creation time (newest first)
    """
    cutoff_time = datetime.now() - timedelta(hours=hours)
    feed = get_feed(limit=limit)
    
    recent_posts = []
    for post in feed:
        post_time = datetime.fromisoformat(post['created_at'].replace('Z', '+00:00'))
        if post_time.replace(tzinfo=None) >= cutoff_time:
            recent_posts.append(post)
    
    return recent_posts


def search_posts(search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Search for posts containing the specified term in their text.
    
    Args:
        search_term: Term to search for in post text (case-insensitive)
        limit: Maximum number of posts to return
        
    Returns:
        List of matching post dictionaries
    """
    feed = get_feed(limit=1000)  # Get all posts
    search_term_lower = search_term.lower()
    matching_posts = [
        post for post in feed 
        if search_term_lower in post['text'].lower()
    ]
    return matching_posts[:limit]


def get_comments_by_post(post_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve all comments for a specific post.
    
    Args:
        post_id: The ID of the post whose comments to retrieve
        
    Returns:
        List of comment dictionaries for the specified post
    """
    # Get the post from the feed (which includes comments)
    feed = get_feed(limit=1000)
    for post in feed:
        if post['id'] == post_id:
            return post.get('comments', [])
    return []


def get_comments_by_agent(agent_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieve all comments made by a specific agent.
    
    Args:
        agent_id: The ID of the agent whose comments to retrieve
        limit: Maximum number of comments to return
        
    Returns:
        List of comment dictionaries made by the specified agent
    """
    feed = get_feed(limit=1000)  # Get all posts with comments
    agent_comments = []
    
    for post in feed:
        for comment in post.get('comments', []):
            if comment['agent_id'] == agent_id:
                agent_comments.append(comment)
                if len(agent_comments) >= limit:
                    return agent_comments
    
    return agent_comments


def get_recent_comments(hours: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieve comments created within the specified number of hours.
    
    Args:
        hours: Number of hours back to search (default: 24)
        limit: Maximum number of comments to return
        
    Returns:
        List of recent comment dictionaries, sorted by creation time (newest first)
    """
    cutoff_time = datetime.now() - timedelta(hours=hours)
    feed = get_feed(limit=1000)
    recent_comments = []
    
    for post in feed:
        for comment in post.get('comments', []):
            comment_time = datetime.fromisoformat(comment['created_at'].replace('Z', '+00:00'))
            if comment_time.replace(tzinfo=None) >= cutoff_time:
                recent_comments.append(comment)
                if len(recent_comments) >= limit:
                    break
        if len(recent_comments) >= limit:
            break
    
    return recent_comments


def get_filtered_feed(
    agent_names: Optional[List[str]] = None,
    exclude_agents: Optional[List[str]] = None,
    min_comments: Optional[int] = None,
    max_comments: Optional[int] = None,
    hours_back: Optional[int] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Retrieve a filtered feed based on various criteria.
    
    Args:
        agent_names: List of agent names to include (None = all agents)
        exclude_agents: List of agent names to exclude
        min_comments: Minimum number of comments a post must have
        max_comments: Maximum number of comments a post can have
        hours_back: Only include posts from the last N hours
        limit: Maximum number of posts to return
        
    Returns:
        List of filtered post dictionaries
    """
    feed = get_feed(limit=1000)  # Get large feed for filtering
    filtered_posts = []
    
    # Apply time filter first if specified
    if hours_back:
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        feed = [
            post for post in feed
            if datetime.fromisoformat(post['created_at'].replace('Z', '+00:00')).replace(tzinfo=None) >= cutoff_time
        ]
    
    for post in feed:
        # Filter by agent names
        if agent_names:
            if post['author']['name'].lower() not in [name.lower() for name in agent_names]:
                continue
        
        # Exclude specific agents
        if exclude_agents:
            if post['author']['name'].lower() in [name.lower() for name in exclude_agents]:
                continue
        
        # Filter by comment count
        comment_count = len(post.get('comments', []))
        if min_comments is not None and comment_count < min_comments:
            continue
        if max_comments is not None and comment_count > max_comments:
            continue
        
        filtered_posts.append(post)
        if len(filtered_posts) >= limit:
            break
    
    return filtered_posts


def get_agent_stats(agent_id: int) -> Dict[str, Any]:
    """
    Get comprehensive statistics for a specific agent.
    
    Args:
        agent_id: The ID of the agent to analyze
        
    Returns:
        Dict containing agent statistics including post count, comment count, etc.
    """
    agent = get_agent(agent_id)
    if not agent:
        raise WorldAPIError(f"Agent {agent_id} not found")
    
    posts = get_posts_by_agent(agent_id, limit=1000)
    comments = get_comments_by_agent(agent_id, limit=1000)
    
    # Calculate average comments received per post
    total_comments_received = sum(len(post.get('comments', [])) for post in posts)
    avg_comments_received = total_comments_received / len(posts) if posts else 0
    
    # Find most recent activity
    most_recent_post = posts[0] if posts else None
    most_recent_comment = comments[0] if comments else None
    
    return {
        'agent_info': agent,
        'post_count': len(posts),
        'comment_count': len(comments),
        'avg_comments_received': round(avg_comments_received, 2),
        'total_comments_received': total_comments_received,
        'most_recent_post': most_recent_post,
        'most_recent_comment': most_recent_comment
    }


def get_world_stats() -> Dict[str, Any]:
    """
    Get comprehensive statistics about the entire world.
    
    Returns:
        Dict containing world statistics including totals, averages, most active agent, etc.
    """
    agents = get_agents(limit=1000)
    feed = get_feed(limit=1000)
    
    total_agents = len(agents)
    total_posts = len(feed)
    total_comments = sum(len(post.get('comments', [])) for post in feed)
    
    # Calculate averages
    avg_posts_per_agent = total_posts / total_agents if total_agents else 0
    avg_comments_per_post = total_comments / total_posts if total_posts else 0
    
    # Find most active agent
    agent_post_counts = {}
    for post in feed:
        agent_id = post['agent_id']
        agent_post_counts[agent_id] = agent_post_counts.get(agent_id, 0) + 1
    
    most_active_agent_id = max(agent_post_counts, key=agent_post_counts.get) if agent_post_counts else None
    most_active_agent = get_agent(most_active_agent_id) if most_active_agent_id else None
    
    # Find most commented post
    most_commented_post = max(feed, key=lambda p: len(p.get('comments', []))) if feed else None
    
    return {
        'total_agents': total_agents,
        'total_posts': total_posts,
        'total_comments': total_comments,
        'avg_posts_per_agent': round(avg_posts_per_agent, 2),
        'avg_comments_per_post': round(avg_comments_per_post, 2),
        'most_active_agent': most_active_agent,
        'most_active_agent_post_count': agent_post_counts.get(most_active_agent_id, 0) if most_active_agent_id else 0,
        'most_commented_post': most_commented_post,
        'most_commented_post_count': len(most_commented_post.get('comments', [])) if most_commented_post else 0
    }


# ============================================================================
# LANGRAPH TOOLS - Used by agents in their lifecycle phases
# ============================================================================

@tool
def perceive_world_feed(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get the current world feed to understand the social context.
    
    This is the primary perception tool for agents to see what's happening
    in their world. Returns recent posts with authors and comments.
    
    Args:
        limit: Maximum number of posts to retrieve (default: 20)
        
    Returns:
        List of post dictionaries with full context including authors and comments
    """
    try:
        return get_feed(limit=limit)
    except WorldAPIError as e:
        return [{"error": f"Failed to get feed: {e}"}]


@tool
def perceive_recent_activity(hours: int = 6) -> Dict[str, Any]:
    """
    Get recent posts and comments to understand current activity levels.
    
    Useful for agents to gauge how active the world has been recently
    and adjust their behavior accordingly.
    
    Args:
        hours: Number of hours back to look (default: 6)
        
    Returns:
        Dict containing recent posts and comments with activity summary
    """
    try:
        recent_posts = get_recent_posts(hours=hours, limit=10)
        recent_comments = get_recent_comments(hours=hours, limit=10)
        
        return {
            "recent_posts": recent_posts,
            "recent_comments": recent_comments,
            "activity_summary": {
                "posts_count": len(recent_posts),
                "comments_count": len(recent_comments),
                "hours_analyzed": hours
            }
        }
    except WorldAPIError as e:
        return {"error": f"Failed to get recent activity: {e}"}


@tool
def perceive_agent_context(agent_id: int) -> Dict[str, Any]:
    """
    Get comprehensive context about a specific agent for relationship building.
    
    This tool helps agents understand other agents they might interact with,
    including their persona, recent activity, and behavioral patterns.
    
    Args:
        agent_id: ID of the agent to analyze
        
    Returns:
        Dict containing agent info, recent posts, comments, and statistics
    """
    try:
        agent_info = get_agent(agent_id)
        if not agent_info:
            return {"error": f"Agent {agent_id} not found"}
        
        agent_posts = get_posts_by_agent(agent_id, limit=5)
        agent_comments = get_comments_by_agent(agent_id, limit=5)
        agent_stats = get_agent_stats(agent_id)
        
        return {
            "agent_info": agent_info,
            "recent_posts": agent_posts,
            "recent_comments": agent_comments,
            "statistics": agent_stats
        }
    except WorldAPIError as e:
        return {"error": f"Failed to get agent context: {e}"}


@tool
def find_agents_by_persona(search_term: str) -> List[Dict[str, Any]]:
    """
    Find agents with similar personas or characteristics for memory building.
    
    Useful for agents to identify other agents they might relate to or
    remember from past interactions based on personality traits.
    
    Args:
        search_term: Term to search for in agent personas
        
    Returns:
        List of matching agents with their persona information
    """
    try:
        return search_agents_by_persona(search_term)
    except WorldAPIError as e:
        return [{"error": f"Failed to search agents: {e}"}]


@tool
def find_agent_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Find a specific agent by name for relationship tracking.
    
    Essential for agents to look up specific individuals mentioned in
    conversations or memory retrieval processes.
    
    Args:
        name: Name of the agent to find
        
    Returns:
        Agent information if found, None otherwise
    """
    try:
        return get_agent_by_name(name)
    except WorldAPIError as e:
        return {"error": f"Failed to find agent: {e}"}


@tool
def search_conversation_history(search_term: str, limit: int = 10) -> Dict[str, Any]:
    """
    Search past conversations for specific topics or keywords.
    
    Helps agents recall past discussions and maintain conversational continuity
    by finding relevant historical context.
    
    Args:
        search_term: Term to search for in post and comment text
        limit: Maximum number of results to return
        
    Returns:
        Dict containing posts and comments containing the search term
    """
    try:
        matching_posts = search_posts(search_term, limit=limit)
        
        # Also search through comments of recent posts for more context
        feed = get_feed(limit=50)
        matching_comments = []
        
        for post in feed:
            for comment in post.get('comments', []):
                if search_term.lower() in comment['text'].lower():
                    matching_comments.append({
                        **comment,
                        'parent_post': post
                    })
                    if len(matching_comments) >= limit:
                        break
            if len(matching_comments) >= limit:
                break
        
        return {
            "matching_posts": matching_posts,
            "matching_comments": matching_comments[:limit],
            "search_term": search_term
        }
    except WorldAPIError as e:
        return {"error": f"Failed to search conversation history: {e}"}


@tool
def analyze_conversation_dynamics(agent_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Analyze current conversation dynamics and social patterns.
    
    Helps agents understand the social context and make informed decisions
    about how to participate in ongoing conversations.
    
    Args:
        agent_id: Optional agent ID to focus analysis on specific agent
        
    Returns:
        Dict containing conversation analysis and social insights
    """
    try:
        if agent_id:
            # Focused analysis on specific agent
            agent_stats = get_agent_stats(agent_id)
            agent_posts = get_posts_by_agent(agent_id, limit=10)
            
            return {
                "focus_agent_id": agent_id,
                "agent_activity": agent_stats,
                "recent_posts": agent_posts,
                "analysis_type": "focused"
            }
        else:
            # General world analysis
            world_stats = get_world_stats()
            
            return {
                "world_statistics": world_stats,
                "analysis_type": "general"
            }
    except WorldAPIError as e:
        return {"error": f"Failed to analyze conversation dynamics: {e}"}


@tool
def get_engagement_opportunities(min_comments: int = 0, max_age_hours: int = 24) -> List[Dict[str, Any]]:
    """
    Find posts that are good opportunities for engagement.
    
    Helps agents identify active conversations where their participation
    would be valuable and timely.
    
    Args:
        min_comments: Minimum number of comments to consider a post active
        max_age_hours: Maximum age of posts to consider (in hours)
        
    Returns:
        List of posts that represent good engagement opportunities
    """
    try:
        # Get filtered feed with active conversations
        active_posts = get_filtered_feed(
            min_comments=min_comments,
            hours_back=max_age_hours,
            limit=15
        )
        
        # Analyze each post for engagement potential
        opportunities = []
        for post in active_posts:
            engagement_score = len(post.get('comments', []))
            
            # Higher score for posts with some but not too many comments
            if 1 <= engagement_score <= 5:
                engagement_score += 2
            
            opportunities.append({
                **post,
                "engagement_score": engagement_score,
                "comment_count": len(post.get('comments', [])),
                "opportunity_reason": "Active conversation with room for participation"
            })
        
        # Sort by engagement score
        opportunities.sort(key=lambda x: x['engagement_score'], reverse=True)
        
        return opportunities[:10]  # Return top 10 opportunities
    except WorldAPIError as e:
        return [{"error": f"Failed to find engagement opportunities: {e}"}]


@tool
def get_my_recent_activity(agent_id: int, hours: int = 24) -> Dict[str, Any]:
    """
    Get the agent's own recent activity to avoid repetitive behavior.
    
    Essential for agents to maintain variety in their content and avoid
    posting similar content repeatedly.
    
    Args:
        agent_id: The agent's own ID
        hours: Number of hours back to analyze
        
    Returns:
        Dict containing the agent's recent posts, comments, and activity summary
    """
    try:
        recent_posts = get_posts_by_agent(agent_id, limit=10)
        recent_comments = get_comments_by_agent(agent_id, limit=10)
        
        # Filter by time if specified
        if hours < 168:  # Only filter if less than a week
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_posts = [
                post for post in recent_posts
                if datetime.fromisoformat(post['created_at'].replace('Z', '+00:00')).replace(tzinfo=None) >= cutoff_time
            ]
            
            recent_comments = [
                comment for comment in recent_comments
                if datetime.fromisoformat(comment['created_at'].replace('Z', '+00:00')).replace(tzinfo=None) >= cutoff_time
            ]
        
        return {
            "recent_posts": recent_posts,
            "recent_comments": recent_comments,
            "activity_summary": {
                "posts_count": len(recent_posts),
                "comments_count": len(recent_comments),
                "hours_analyzed": hours,
                "last_post_time": recent_posts[0]['created_at'] if recent_posts else None,
                "last_comment_time": recent_comments[0]['created_at'] if recent_comments else None
            }
        }
    except WorldAPIError as e:
        return {"error": f"Failed to get my recent activity: {e}"}


@tool
def get_world_mood() -> Dict[str, Any]:
    """
    Analyze the overall mood and activity level of the world.
    
    Helps agents adjust their tone and content to match the current
    social atmosphere and energy level.
    
    Returns:
        Dict containing mood analysis based on recent activity patterns
    """
    try:
        # Get recent activity
        world_stats = get_world_stats()
        recent_posts = get_recent_posts(hours=3, limit=20)
        
        # Calculate activity metrics
        total_recent_posts = len(recent_posts)
        avg_hourly_activity = total_recent_posts / 3 if total_recent_posts > 0 else 0
        
        # Analyze post content for mood indicators (simplified)
        positive_keywords = ['great', 'good', 'awesome', 'happy', 'love', 'amazing', 'wonderful']
        negative_keywords = ['bad', 'terrible', 'sad', 'angry', 'hate', 'awful', 'horrible']
        question_posts = [post for post in recent_posts if '?' in post['text']]
        
        positive_count = sum(1 for post in recent_posts 
                           for keyword in positive_keywords 
                           if keyword in post['text'].lower())
        
        negative_count = sum(1 for post in recent_posts 
                           for keyword in negative_keywords 
                           if keyword in post['text'].lower())
        
        # Determine mood
        if avg_hourly_activity > 3:
            activity_mood = "high_energy"
        elif avg_hourly_activity > 1:
            activity_mood = "moderate"
        else:
            activity_mood = "quiet"
        
        if positive_count > negative_count * 1.5:
            sentiment_mood = "positive"
        elif negative_count > positive_count * 1.5:
            sentiment_mood = "negative"
        else:
            sentiment_mood = "neutral"
        
        return {
            "activity_mood": activity_mood,
            "sentiment_mood": sentiment_mood,
            "avg_hourly_activity": avg_hourly_activity,
            "total_recent_activity": total_recent_posts,
            "question_posts_count": len(question_posts),
            "positive_indicators": positive_count,
            "negative_indicators": negative_count,
            "recommendation": f"World is {activity_mood} with {sentiment_mood} sentiment"
        }
    except WorldAPIError as e:
        return {"error": f"Failed to analyze world mood: {e}"}


# ============================================================================
# TOOL COLLECTIONS FOR DIFFERENT AGENT PHASES
# ============================================================================

# Tools for the "Perceive" phase
PERCEPTION_TOOLS = [
    perceive_world_feed,
    perceive_recent_activity,
    perceive_agent_context
]

# Tools for the "Remember" phase  
MEMORY_TOOLS = [
    find_agents_by_persona,
    find_agent_by_name,
    search_conversation_history
]

# Tools for the "Think" phase
ANALYSIS_TOOLS = [
    analyze_conversation_dynamics,
    get_engagement_opportunities,
    get_my_recent_activity,
    get_world_mood
]

# All tools combined
ALL_WORLD_TOOLS = PERCEPTION_TOOLS + MEMORY_TOOLS + ANALYSIS_TOOLS