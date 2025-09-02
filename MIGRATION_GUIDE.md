# Migration Guide: Centralized LLM Configuration

This guide helps you migrate from the old direct LLM instantiation to the new centralized configuration system.

## Overview of Changes

The agent system now uses a centralized LLM configuration approach that:
- Moves LLM configuration from Python code to YAML files
- Supports multiple LLM providers (Ollama, OpenAI, Anthropic, etc.)
- Enables per-node LLM configuration
- Provides environment-specific settings
- Offers runtime parameter overrides

## Key Changes

### 1. Configuration Location
- **Before**: LLM settings hardcoded in `nodes.py`
- **After**: Centralized in `agent/config/llm_config.yml`

### 2. LLM Instantiation
- **Before**: Direct `ChatOllama()` calls in node functions
- **After**: `llm_manager.get_llm(node_name="router_node")`

### 3. Configuration Management
- **Before**: Environment variables in `config.py`
- **After**: YAML configuration with environment variable substitution

## Migration Steps

### Step 1: Update Your Code

If you have custom nodes that use LLMs directly, update them:

**Before:**
```python
from langchain_ollama import ChatOllama
from .config import settings

def my_custom_node(state):
    llm = ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model="llama3.1:8b",
        format="json"
    )
    response = llm.invoke([HumanMessage(content=prompt)])
```

**After:**
```python
from .config import llm_manager

def my_custom_node(state):
    llm = llm_manager.get_llm(node_name="my_custom_node")
    response = llm.invoke([HumanMessage(content=prompt)])
```

### Step 2: Configure Your Node

Add your node configuration to `agent/config/llm_config.yml`:

```yaml
node_configs:
  my_custom_node:
    llm_config_name: "ollama_llama"  # or any other configured LLM
    enabled: true
    custom_params:
      temperature: 0.5
      max_tokens: 1000
```

### Step 3: Environment Variables

Update your `.env` file to include API keys for cloud providers:

```bash
# For OpenAI
OPENAI_API_KEY=sk-your-openai-key

# For Anthropic
ANTHROPIC_API_KEY=your-anthropic-key

# For Azure OpenAI
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# For Google/Gemini
GOOGLE_API_KEY=your-google-key
```

## Advanced Migration Scenarios

### Custom LLM Parameters

**Before:**
```python
llm = ChatOllama(
    base_url="http://custom-host:11434",
    model="custom-model:7b",
    temperature=0.8,
    format="json"
)
```

**After:**
```yaml
# In llm_config.yml
llm_configs:
  custom_ollama:
    provider: "ollama"
    model: "custom-model:7b"
    base_url: "http://custom-host:11434"
    temperature: 0.8
    format: "json"

node_configs:
  my_node:
    llm_config_name: "custom_ollama"
```

### Runtime Parameter Overrides

**Before:**
```python
# Had to create new LLM instance
llm_high_temp = ChatOllama(
    base_url=settings.OLLAMA_BASE_URL,
    model="llama3.1:8b",
    temperature=0.9
)
```

**After:**
```python
# Override parameters at runtime
llm = llm_manager.get_llm(
    node_name="my_node",
    temperature=0.9
)
```

### Multiple Model Usage

**Before:**
```python
# Had to manage multiple LLM instances manually
fast_llm = ChatOllama(model="llama3.2:3b", ...)
powerful_llm = ChatOllama(model="llama3.1:8b", ...)
```

**After:**
```yaml
# In llm_config.yml
llm_configs:
  fast_model:
    provider: "ollama"
    model: "llama3.2:3b"
    # ... other config
  
  powerful_model:
    provider: "ollama"
    model: "llama3.1:8b"
    # ... other config
```

```python
# Get different models as needed
fast_llm = llm_manager.get_llm(llm_name="fast_model")
powerful_llm = llm_manager.get_llm(llm_name="powerful_model")
```

## Breaking Changes

### Removed Direct Imports
These imports are no longer needed in node files:
- `from langchain_ollama import ChatOllama`
- Direct LLM provider imports

### Changed Configuration Access
- `settings.OLLAMA_BASE_URL` is still available for backward compatibility
- New configurations should use the YAML system

### Node Function Signatures
Node functions remain the same, but internal LLM usage changes:
- Input/output interfaces unchanged
- Internal LLM instantiation updated

## Testing Your Migration

1. **Verify Configuration Loading**:
```python
from agent.core.config import llm_manager
print(f"Default LLM: {llm_manager.config.default_llm}")
print(f"Available configs: {list(llm_manager.config.llm_configs.keys())}")
```

2. **Test LLM Creation**:
```python
llm = llm_manager.get_llm(node_name="router_node")
print(f"LLM type: {type(llm).__name__}")
```

3. **Run Agent Workflow**:
```python
from agent import run_agent_turn
result = run_agent_turn(agent_id=1)
```

## Rollback Plan

If you need to rollback:

1. **Restore Old Node Code**: Use git to restore the previous version of modified node files
2. **Remove New Files**: Delete `agent/core/llm_config.py` and `agent/config/llm_config.yml`
3. **Restore Config**: Revert `agent/core/config.py` to the previous version

## Getting Help

- **Configuration Issues**: See [LLM Configuration Guide](agent/docs/LLM_CONFIGURATION.md)
- **API Reference**: See [API Reference](agent/docs/API_REFERENCE.md)
- **Provider Setup**: Check provider-specific documentation in the configuration guide

## Benefits After Migration

✅ **Easier Configuration**: Change models without touching code
✅ **Multiple Providers**: Use different providers for different tasks
✅ **Environment Management**: Different configs for dev/test/prod
✅ **Performance**: LLM instance caching and reuse
✅ **Flexibility**: Runtime parameter overrides
✅ **Maintainability**: Centralized configuration management
