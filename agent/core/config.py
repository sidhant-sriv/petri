"""
Agent Configuration
Unified environment variable management for the agent component
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
from functools import lru_cache

from .llm_config import (
    load_llm_config, 
    create_default_config_file, 
    LLMFactory, 
    AgentLLMConfig,
    LLMConfigType
)


class AgentSettings(BaseSettings):
    # World API Configuration
    WORLD_API_URL: str = "http://world:8000"
    API_KEY: str

    # Neo4j Configuration (Agent Memory)
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4j_password"

    # LLM Configuration (Legacy - for backward compatibility)
    OLLAMA_BASE_URL: str = "http://host.docker.internal:114434"
    
    # LLM Configuration File
    LLM_CONFIG_PATH: str = "agent/config/llm_config.yml"
    DEFAULT_LLM: str = "ollama_llama"

    # Redis Configuration (for agent-manager workers)
    REDIS_URL: str = "redis://redis:6379/0"

    # Environment
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        extra = (
            "ignore"  # Ignore extra fields from .env that aren't defined in the model
        )


class LLMManager:
    """Manager class for LLM configurations and instances."""
    
    def __init__(self, config: AgentLLMConfig):
        self.config = config
        self._llm_instances: Dict[str, Any] = {}
    
    def get_llm(self, node_name: str = None, llm_name: str = None, **override_params):
        """
        Get an LLM instance for a specific node or by name.
        
        Args:
            node_name: Name of the node (e.g., 'router_node')
            llm_name: Specific LLM configuration name to use
            **override_params: Runtime parameter overrides
            
        Returns:
            Configured LLM instance
        """
        # Determine which LLM config to use
        if llm_name:
            config_name = llm_name
        elif node_name and node_name in self.config.node_configs:
            node_config = self.config.node_configs[node_name]
            config_name = node_config.llm_config_name
            # Merge node-specific parameters
            override_params.update(node_config.custom_params)
        else:
            config_name = settings.DEFAULT_LLM
        
        # Create cache key
        cache_key = f"{config_name}_{hash(frozenset(override_params.items()))}"
        
        # Return cached instance if available
        if cache_key in self._llm_instances:
            return self._llm_instances[cache_key]
        
        # Get LLM configuration
        if config_name not in self.config.llm_configs:
            raise ValueError(f"LLM configuration '{config_name}' not found")
        
        llm_config = self.config.llm_configs[config_name]
        
        # Create LLM instance
        llm_instance = LLMFactory.create_llm(llm_config, **override_params)
        
        # Cache the instance
        self._llm_instances[cache_key] = llm_instance
        
        return llm_instance
    
    def get_node_config(self, node_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific node."""
        if node_name in self.config.node_configs:
            return self.config.node_configs[node_name].model_dump()
        return None
    
    def is_node_enabled(self, node_name: str) -> bool:
        """Check if a node is enabled."""
        if node_name in self.config.node_configs:
            return self.config.node_configs[node_name].enabled
        return True  # Default to enabled if not configured
    
    def clear_cache(self):
        """Clear the LLM instance cache."""
        self._llm_instances.clear()


@lru_cache(maxsize=1)
def _load_llm_config() -> AgentLLMConfig:
    """Load LLM configuration with caching."""
    config_path = settings.LLM_CONFIG_PATH
    
    # Create default config if it doesn't exist
    if not os.path.exists(config_path):
        print(f"⚠️ LLM config file not found at {config_path}")
        print("Creating default configuration...")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        create_default_config_file(config_path)
        print(f"✅ Created default LLM config at {config_path}")
    
    try:
        config = load_llm_config(config_path)
        print(f"✅ Loaded LLM configuration from {config_path}")
        return config
    except Exception as e:
        print(f"❌ Failed to load LLM configuration: {e}")
        print("Using fallback configuration...")
        
        # Create fallback configuration
        from .llm_config import AgentLLMConfig, OllamaConfig
        
        fallback_config = AgentLLMConfig(
            llm_configs={
                "fallback_ollama": OllamaConfig(
                    model="llama3.1:8b",
                    base_url=settings.OLLAMA_BASE_URL,
                    format="json"
                )
            }
        )
        return fallback_config


# Global settings instance
settings = AgentSettings()

# Global LLM manager instance
llm_manager = LLMManager(_load_llm_config())
