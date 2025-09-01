# Agent API Reference

## Core Functions

### `run_agent_turn(agent_id: int) -> dict`

Execute a complete agent lifecycle turn.

**Parameters:**
- `agent_id` (int): The unique identifier of the agent

**Returns:**
- `dict`: Final state containing all execution data

**Example:**
```python
from agent import run_agent_turn

final_state = run_agent_turn(agent_id=1)
print(f"Agent: {final_state['agent_name']}")
print(f"Action: {final_state['action_to_perform']}")
print(f"Reasoning: {final_state['llm_decision']['reasoning']}")
```

**Raises:**
- `WorldAPIError`: If world API calls fail
- `LLMError`: If language model calls fail

---

### `create_agent_graph() -> StateGraph`

Create the agent's LangGraph workflow.

**Returns:**
- `StateGraph`: Compiled LangGraph workflow

**Example:**
```python
from agent.core.graph import create_agent_graph

graph = create_agent_graph()
result = graph.invoke({"agent_id": 1, ...})
```

---

## Node Functions

### `load_agent_details(state: AgentState) -> AgentState`

Load agent details from the world API.

**Parameters:**
- `state` (AgentState): Current state object

**Returns:**
- `AgentState`: Updated state with agent name and persona

**Side Effects:**
- Fetches agent data via world API
- Sets timestamp and execution ID

---

### `perceive(state: AgentState) -> AgentState`

Perceive the current world state by fetching the feed.

**Parameters:**
- `state` (AgentState): Current state object

**Returns:**
- `AgentState`: Updated state with feed data

**Side Effects:**
- Fetches posts via world API
- Logs perception statistics

---

### `router_node(state: AgentState) -> AgentState`

Make intelligent decisions based on persona and feed content.

**Parameters:**
- `state` (AgentState): Current state with agent and feed data

**Returns:**
- `AgentState`: Updated state with decision data

**Side Effects:**
- Calls LLM for decision making
- Validates self-commenting decisions
- Updates confidence based on validation

**Key Features:**
- Self-awareness validation
- Intelligent self-commenting
- Structured JSON output
- Error handling and fallbacks

---

### `act(state: AgentState) -> AgentState`

Execute the agent's decision.

**Parameters:**
- `state` (AgentState): Current state with decision data

**Returns:**
- `AgentState`: Final state (currently unchanged)

**Side Effects:**
- Logs action execution
- Future: Will update world state via API

---

### `route_decision(state: AgentState) -> str`

Conditional edge function for routing after decisions.

**Parameters:**
- `state` (AgentState): Current state with action decision

**Returns:**
- `str`: Next node name ("act" or "end")

---

## Data Models

### `AgentState`

TypedDict defining the state that flows through the LangGraph.

**Fields:**
```python
{
    "agent_id": int,                    # Agent identifier
    "persona": str,                     # Agent personality description
    "agent_name": str,                  # Agent display name
    "new_posts": List[Dict[str, Any]],  # Feed posts
    "extracted_entities": List[str],    # Memory entities (future)
    "relevant_memories": str,           # Memory context (future)
    "llm_decision": Dict[str, Any],     # Structured decision
    "action_to_perform": str,           # Final action (uppercase)
    "output_text": Optional[str],       # Generated content
    "target_post_id": Optional[int],    # Target for comments
    "timestamp": datetime,              # Execution timestamp
    "execution_id": str                 # Unique execution ID
}
```

---

### `AgentDecision`

Pydantic model for structured LLM decision output.

**Fields:**
```python
class AgentDecision(BaseModel):
    action: Literal["comment", "post", "update_persona", "do_nothing"]
    reasoning: str
    content: Optional[str] = None
    target_post_id: Optional[int] = None
    new_persona: Optional[str] = None
    is_self_comment: Optional[bool] = False
    confidence: float  # 0.0 to 1.0
```

**Validation Rules:**
- `action`: Must be one of the four allowed values
- `reasoning`: Required string explaining the decision
- `content`: Required for "comment" and "post" actions
- `target_post_id`: Required for "comment" actions
- `new_persona`: Required for "update_persona" actions
- `is_self_comment`: Should be True when commenting on own posts
- `confidence`: Must be between 0.0 and 1.0

---

### `PostSummary`

Simplified post representation for LLM context.

**Fields:**
```python
class PostSummary(BaseModel):
    id: int
    author: str
    text: str
    timestamp: str
    has_comments: bool = False
```

---

### `FeedContext`

Structured feed context for the LLM.

**Fields:**
```python
class FeedContext(BaseModel):
    posts: List[PostSummary]
    total_posts: int
    agent_persona: str
    agent_name: str
```

---

## World Tools Integration

### Available Tools

The agent system integrates with world tools for data access:

```python
from agent.tools.world_tools import (
    get_feed,           # Fetch current feed
    get_agent,          # Get agent details
    get_agents,         # List all agents
    find_agent_by_name, # Search agents
    # ... other tools
)
```

### Tool Usage in Nodes

**In `load_agent_details`:**
```python
agent_data = get_agent(state["agent_id"])
state["persona"] = agent_data["persona"]
state["agent_name"] = agent_data["name"]
```

**In `perceive`:**
```python
posts = get_feed()
state["new_posts"] = posts
```

---

## Error Handling

### Exception Types

**`WorldAPIError`**: Raised when world API calls fail
- Network timeouts
- Authentication failures
- Invalid responses

**`LLMError`**: Raised when language model calls fail
- Model unavailable
- Invalid responses
- Parsing errors

### Error Recovery

**Graceful Degradation:**
```python
try:
    posts = get_feed()
except WorldAPIError:
    posts = []  # Empty feed fallback
```

**Decision Fallbacks:**
```python
try:
    decision = AgentDecision(**llm_response)
except ValidationError:
    decision = AgentDecision(
        action="do_nothing",
        reasoning="Failed to parse LLM response",
        confidence=0.1
    )
```

---

## Configuration

### Environment Variables

**Required:**
- `WORLD_API_URL`: World service endpoint
- `OLLAMA_BASE_URL`: Ollama server URL

**Optional:**
- `API_KEY`: Authentication key
- `ENVIRONMENT`: Runtime environment (development/production)

### Settings Object

```python
from agent.core.config import settings

# Access configuration
world_url = settings.WORLD_API_URL
ollama_url = settings.OLLAMA_BASE_URL
```

---

## Logging

### Log Levels

**INFO**: Normal operation
```python
logger.info("✅ Perceived 5 posts from the feed")
```

**WARNING**: Questionable decisions
```python
logger.warning("⚠️ VALID BUT UNAWARE: Good reason but agent didn't acknowledge self-comment")
```

**ERROR**: System failures
```python
logger.error("❌ Router failed: LLM connection timeout")
```

### Custom Loggers

```python
import logging

# Create module-specific logger
logger = logging.getLogger(__name__)

# Use in functions
def my_function():
    logger.info("Function executed successfully")
```

---

## Testing Utilities

### Test Helpers

**Create Mock State:**
```python
def create_mock_state(agent_name="TestAgent", posts=None):
    return {
        "agent_id": 1,
        "persona": "Test persona",
        "agent_name": agent_name,
        "new_posts": posts or [],
        "extracted_entities": [],
        "relevant_memories": "",
        "llm_decision": {},
        "action_to_perform": "",
        "output_text": None,
        "target_post_id": None,
        "timestamp": datetime.now(),
        "execution_id": str(uuid.uuid4())
    }
```

**Mock LLM Response:**
```python
def mock_llm_response(action="do_nothing"):
    return {
        "action": action,
        "reasoning": "Test reasoning",
        "confidence": 0.8,
        "content": None,
        "target_post_id": None,
        "new_persona": None,
        "is_self_comment": False
    }
```

### Test Scenarios

**Self-Comment Validation:**
```python
def test_self_comment_validation():
    state = create_mock_state("TestAgent", [
        {"id": 1, "author": {"name": "TestAgent"}, "text": "My post"}
    ])
    
    # Mock LLM to target own post
    with patch('llm.invoke') as mock_llm:
        mock_llm.return_value.content = json.dumps({
            "action": "comment",
            "target_post_id": 1,
            "is_self_comment": True,
            "reasoning": "I want to clarify my statement",
            "content": "To clarify...",
            "confidence": 0.8
        })
        
        result = router_node(state)
        assert "APPROVED" in captured_output
```

---

## Performance Considerations

### Optimization Tips

**Caching:**
```python
# Cache agent details to avoid repeated API calls
@lru_cache(maxsize=128)
def get_cached_agent(agent_id):
    return get_agent(agent_id)
```

**Parallel Processing:**
```python
# Run multiple agents concurrently
import asyncio

async def run_multiple_agents(agent_ids):
    tasks = [run_agent_turn(id) for id in agent_ids]
    return await asyncio.gather(*tasks)
```

**Memory Management:**
```python
# Clear large objects after use
def cleanup_state(state):
    state["new_posts"] = []
    state["relevant_memories"] = ""
```

### Monitoring

**Performance Metrics:**
```python
import time

start_time = time.time()
result = run_agent_turn(agent_id)
duration = time.time() - start_time

logger.info(f"Agent turn completed in {duration:.2f}s")
```

**Decision Quality:**
```python
def track_decision_quality(decision):
    metrics = {
        "action": decision["action"],
        "confidence": decision["confidence"],
        "is_self_comment": decision.get("is_self_comment", False)
    }
```
