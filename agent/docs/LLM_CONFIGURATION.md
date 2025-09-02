# LLM Configuration System

This document describes the centralized LLM configuration system that supports multiple providers and per-node configuration through YAML settings.

## Overview

The LLM configuration system provides:

- **Multiple Provider Support**: Ollama, Google Gemini, and Groq
- **Centralized Configuration**: Single YAML file for all LLM settings
- **Per-Node Configuration**: Different LLM configurations for different nodes
- **Runtime Parameter Overrides**: Dynamic parameter adjustment
- **Caching**: Efficient LLM instance reuse
- **Environment-Specific Settings**: Different configurations for dev/prod/test

## Configuration File Structure

The configuration is defined in `agent/config/llm_config.yml`:

```yaml
# Default LLM configuration to use when none is specified
default_llm: "ollama_llama"

# LLM Provider Configurations
llm_configs:
  ollama_llama:
    provider: "ollama"
    model: "llama3.1:8b"
    base_url: "http://host.docker.internal:11434"
    temperature: 0.7
    format: "json"
    timeout: 30
    max_tokens: 2000

  openai_gpt4:
    provider: "openai"
    model: "gpt-4o"
    api_key: "${OPENAI_API_KEY}"
    temperature: 0.7
    max_tokens: 2000
    timeout: 30

  anthropic_claude:
    provider: "anthropic"
    model: "claude-3-5-sonnet-20241022"
    api_key: "${ANTHROPIC_API_KEY}"
    temperature: 0.7
    max_tokens: 2000

# Node-Specific Configurations
node_configs:
  router_node:
    llm_config_name: "ollama_llama"
    enabled: true
    custom_params:
      format: "json"
      temperature: 0.7
      
  memory_node:
    llm_config_name: "ollama_fast"
    enabled: true
    custom_params:
      temperature: 0.3
      max_tokens: 1000
```

## Supported Providers

### Ollama (Local)
```yaml
ollama_config:
  provider: "ollama"
  model: "llama3.1:8b"
  base_url: "http://host.docker.internal:11434"
  format: "json"  # Optional: For structured output
  temperature: 0.7
  max_tokens: 2000
  timeout: 30
```

### Google/Gemini
```yaml
google_config:
  provider: "google"
  model: "gemini-1.5-pro"
  api_key: "${GEMINI_API_KEY}"
  temperature: 0.7
  max_tokens: 2000
  timeout: 30
```

### Groq
```yaml
groq_config:
  provider: "groq"
  model: "llama3-8b-8192"
  api_key: "${GROQ_API_KEY}"
  temperature: 0.7
  max_tokens: 2000
  timeout: 30
```

### Azure OpenAI
```yaml
azure_config:
  provider: "azure_openai"
  model: "gpt-4"
  deployment_name: "gpt-4-deployment"
  api_key: "${AZURE_OPENAI_API_KEY}"
  azure_endpoint: "${AZURE_OPENAI_ENDPOINT}"
  api_version: "2024-02-15-preview"
  temperature: 0.7
  max_tokens: 2000
  timeout: 30
```

### Local Models (HuggingFace)
```yaml
local_config:
  provider: "local"
  model_path: "microsoft/DialoGPT-medium"
  device: "auto"
  temperature: 0.7
  max_tokens: 512
  timeout: 30
```

## Usage

### Basic Usage
```python
from agent.core.config import llm_manager

# Get LLM for a specific node
llm = llm_manager.get_llm(node_name="router_node")
response = llm.invoke([HumanMessage(content="Hello")])

# Get LLM by configuration name
llm = llm_manager.get_llm(llm_name="google_gemini")

# Get default LLM
llm = llm_manager.get_llm()
```

### Runtime Parameter Overrides
```python
# Override temperature for this call
llm = llm_manager.get_llm(
    node_name="router_node", 
    temperature=0.9,
    max_tokens=500
)
```

### Node Configuration
```python
# Check if a node is enabled
if llm_manager.is_node_enabled("router_node"):
    llm = llm_manager.get_llm(node_name="router_node")

# Get node configuration
config = llm_manager.get_node_config("router_node")
print(config["custom_params"])
```

## Environment Variables

LLM configurations support environment variable substitution using `${VAR_NAME}` syntax:

```bash
# .env file
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
```

## Environment-Specific Configuration

The configuration file supports environment-specific overrides:

```yaml
environments:
  development:
    # default_llm is set in .env as DEFAULT_LLM
    
  production:
    # default_llm is set in .env as DEFAULT_LLM
    node_configs:
      router_node:
        llm_config_name: "groq_llama"
      memory_node:
        llm_config_name: "groq_llama"
        
  testing:
    default_llm: "ollama_fast"  # Fast local models for testing
```

## Migration from Legacy Configuration

### Before (Old System)
```python
# In nodes.py
llm = ChatOllama(
    base_url=settings.OLLAMA_BASE_URL, 
    model="llama3.1:8b", 
    format="json"
)
```

### After (New System)
```python
# In nodes.py
llm = llm_manager.get_llm(node_name="router_node")
```

The LLM configuration is now centralized in the YAML file, making it easier to:
- Switch between different models
- Configure different models for different environments
- Override parameters per node
- Add new LLM providers without code changes

## Adding New LLM Providers

To add a new LLM provider:

1. **Create Configuration Schema**:
   ```python
   class NewProviderConfig(BaseLLMConfig):
       provider: Literal["new_provider"] = "new_provider"
       custom_param: str
   ```

2. **Add to Union Type**:
   ```python
   LLMConfigType = Union[
       OllamaConfig,
       # ... existing providers
       NewProviderConfig
   ]
   ```

3. **Implement Factory Method**:
   ```python
   @staticmethod
   def _create_new_provider(params: Dict[str, Any]) -> BaseLanguageModel:
       # Implementation here
       pass
   ```

4. **Update Configuration Loading**:
   ```python
   elif provider == "new_provider":
       llm_configs[name] = NewProviderConfig(**llm_config)
   ```

## Best Practices

1. **Use Node-Specific Configurations**: Configure different LLMs for different purposes
   - Fast models for memory/extraction tasks
   - Powerful models for decision-making
   - Specialized models for specific domains

2. **Environment Separation**: Use different models for dev/test/prod
   - Local models for development
   - Reliable cloud models for production
   - Fast models for testing

3. **Parameter Tuning**: Adjust parameters per use case
   - Lower temperature for factual tasks
   - Higher temperature for creative tasks
   - Appropriate max_tokens for response length

4. **Caching**: The system automatically caches LLM instances
   - Same configuration = same cached instance
   - Different parameters = new instance
   - Clear cache when needed: `llm_manager.clear_cache()`

5. **Error Handling**: The system provides fallback mechanisms
   - Missing config files create defaults
   - Invalid configurations fall back to working setup
   - Import errors for optional providers are handled gracefully

## Troubleshooting

### Configuration Not Loading
```bash
# Check if config file exists
ls -la agent/config/llm_config.yml

# Verify YAML syntax
python -c "import yaml; yaml.safe_load(open('agent/config/llm_config.yml'))"
```

### Provider Dependencies Missing
```bash
# Install optional dependencies as needed
pip install langchain-google-genai # For Google/Gemini
pip install langchain-groq         # For Groq
```

### Environment Variables Not Found
```bash
# Check environment variables
echo $GEMINI_API_KEY
echo $GROQ_API_KEY

# Source environment file
source .env
```