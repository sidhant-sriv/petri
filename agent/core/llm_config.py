"""
LLM Configuration System
========================

This module provides a centralized configuration system for Large Language Models,
supporting multiple providers (Ollama, OpenAI, Anthropic, etc.) and flexible
per-node configuration through YAML settings.
"""

from typing import Any, Dict, Optional, Union, Literal
from pydantic import BaseModel, Field
import yaml
import os

from langchain_ollama import ChatOllama
from langchain_core.language_models.base import BaseLanguageModel


# LLM Provider Type Definitions
LLMProvider = Literal["ollama", "google", "groq"]


class BaseLLMConfig(BaseModel):
    """Base configuration for all LLM providers."""
    provider: LLMProvider
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 30
    
    class Config:
        extra = "allow"  # Allow provider-specific parameters


class OllamaConfig(BaseLLMConfig):
    """Configuration for Ollama LLM provider."""
    provider: Literal["ollama"] = "ollama"
    base_url: str = "http://host.docker.internal:11434"
    format: Optional[str] = None  # For structured output


class OpenAIConfig(BaseLLMConfig):
    """Configuration for OpenAI LLM provider."""
    provider: Literal["openai"] = "openai"
    api_key: str
    organization: Optional[str] = None
    api_base: Optional[str] = None


class AnthropicConfig(BaseLLMConfig):
    """Configuration for Anthropic LLM provider."""
    provider: Literal["anthropic"] = "anthropic"
    api_key: str
    api_url: Optional[str] = None


class AzureOpenAIConfig(BaseLLMConfig):
    """Configuration for Azure OpenAI LLM provider."""
    provider: Literal["azure_openai"] = "azure_openai"
    api_key: str
    azure_endpoint: str
    api_version: str = "2024-02-15-preview"
    deployment_name: str


class GoogleConfig(BaseLLMConfig):
    """Configuration for Google/Gemini LLM provider."""
    provider: Literal["google"] = "google"
    api_key: str
    model: str = "gemini-pro"


class GroqConfig(BaseLLMConfig):
    """Configuration for Groq LLM provider."""
    provider: Literal["groq"] = "groq"
    api_key: str
    model: str = "llama3-8b-8192"


# Union type for all LLM configurations
LLMConfigType = Union[
    OllamaConfig,
    GoogleConfig,
    GroqConfig
]


class NodeConfig(BaseModel):
    """Configuration for individual nodes."""
    llm_config_name: str  # Reference to LLM config in the main config
    enabled: bool = True
    custom_params: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        extra = "allow"


class AgentLLMConfig(BaseModel):
    """Main configuration container for agent LLM settings."""
    llm_configs: Dict[str, LLMConfigType]  # Named LLM configurations
    node_configs: Dict[str, NodeConfig] = Field(default_factory=dict)  # Per-node configurations
    
    class Config:
        extra = "allow"


class LLMFactory:
    """Factory class for creating LLM instances from configuration."""
    
    @staticmethod
    def create_llm(config: LLMConfigType, **override_params) -> BaseLanguageModel:
        """
        Create an LLM instance from configuration.
        
        Args:
            config: LLM configuration object
            **override_params: Runtime parameter overrides
            
        Returns:
            Configured LLM instance
        """
        # Merge config with override params
        params = config.model_dump()
        params.update(override_params)
        
        if config.provider == "ollama":
            return LLMFactory._create_ollama(params)
        elif config.provider == "openai":
            return LLMFactory._create_openai(params)
        elif config.provider == "anthropic":
            return LLMFactory._create_anthropic(params)
        elif config.provider == "azure_openai":
            return LLMFactory._create_azure_openai(params)
        elif config.provider == "google":
            return LLMFactory._create_google(params)
        elif config.provider == "groq":
            return LLMFactory._create_groq(params)
        else:
            raise ValueError(f"Unsupported LLM provider: {config.provider}")
    
    @staticmethod
    def _create_ollama(params: Dict[str, Any]) -> ChatOllama:
        """Create ChatOllama instance."""
        ollama_params = {
            "base_url": params.get("base_url", "http://host.docker.internal:11434"),
            "model": params["model"],
            "temperature": params.get("temperature", 0.7),
            "timeout": params.get("timeout", 30),
        }
        
        # Add optional parameters
        if params.get("format"):
            ollama_params["format"] = params["format"]
        if params.get("max_tokens"):
            ollama_params["num_predict"] = params["max_tokens"]
            
        return ChatOllama(**ollama_params)
    
    @staticmethod
    def _create_openai(params: Dict[str, Any]) -> BaseLanguageModel:
        """Create OpenAI LLM instance."""
        try:
            from langchain_openai import ChatOpenAI
            
            openai_params = {
                "model": params["model"],
                "temperature": params.get("temperature", 0.7),
                "openai_api_key": params["api_key"],
                "timeout": params.get("timeout", 30),
            }
            
            if params.get("max_tokens"):
                openai_params["max_tokens"] = params["max_tokens"]
            if params.get("organization"):
                openai_params["openai_organization"] = params["organization"]
            if params.get("api_base"):
                openai_params["openai_api_base"] = params["api_base"]
                
            return ChatOpenAI(**openai_params)
        except ImportError:
            raise ImportError("langchain_openai not available. Install with: pip install langchain-openai")
    
    @staticmethod
    def _create_anthropic(params: Dict[str, Any]) -> BaseLanguageModel:
        """Create Anthropic LLM instance."""
        try:
            from langchain_anthropic import ChatAnthropic
            
            anthropic_params = {
                "model": params["model"],
                "temperature": params.get("temperature", 0.7),
                "anthropic_api_key": params["api_key"],
                "timeout": params.get("timeout", 30),
            }
            
            if params.get("max_tokens"):
                anthropic_params["max_tokens"] = params["max_tokens"]
            if params.get("api_url"):
                anthropic_params["anthropic_api_url"] = params["api_url"]
                
            return ChatAnthropic(**anthropic_params)
        except ImportError:
            raise ImportError("langchain_anthropic not available. Install with: pip install langchain-anthropic")
    
    @staticmethod
    def _create_azure_openai(params: Dict[str, Any]) -> BaseLanguageModel:
        """Create Azure OpenAI LLM instance."""
        try:
            from langchain_openai import AzureChatOpenAI
            
            azure_params = {
                "azure_deployment": params["deployment_name"],
                "temperature": params.get("temperature", 0.7),
                "openai_api_key": params["api_key"],
                "azure_endpoint": params["azure_endpoint"],
                "openai_api_version": params.get("api_version", "2024-02-15-preview"),
                "timeout": params.get("timeout", 30),
            }
            
            if params.get("max_tokens"):
                azure_params["max_tokens"] = params["max_tokens"]
                
            return AzureChatOpenAI(**azure_params)
        except ImportError:
            raise ImportError("langchain_openai not available. Install with: pip install langchain-openai")
    
    @staticmethod
    def _create_google(params: Dict[str, Any]) -> BaseLanguageModel:
        """Create Google/Gemini LLM instance."""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            google_params = {
                "model": params.get("model", "gemini-pro"),
                "temperature": params.get("temperature", 0.7),
                "google_api_key": params["api_key"],
                "timeout": params.get("timeout", 30),
            }
            
            if params.get("max_tokens"):
                google_params["max_output_tokens"] = params["max_tokens"]
                
            return ChatGoogleGenerativeAI(**google_params)
        except ImportError:
            raise ImportError("langchain_google_genai not available. Install with: pip install langchain-google-genai")
    
    @staticmethod
    def _create_groq(params: Dict[str, Any]) -> BaseLanguageModel:
        """Create Groq LLM instance."""
        try:
            from langchain_groq import ChatGroq
            
            groq_params = {
                "model": params.get("model", "llama3-8b-8192"),
                "temperature": params.get("temperature", 0.7),
                "groq_api_key": params["api_key"],
                "timeout": params.get("timeout", 30),
            }
            
            if params.get("max_tokens"):
                groq_params["max_tokens"] = params["max_tokens"]
                
            return ChatGroq(**groq_params)
        except ImportError:
            raise ImportError("langchain_groq not available. Install with: pip install langchain-groq")
    
    @staticmethod
    def _create_local(params: Dict[str, Any]) -> BaseLanguageModel:
        """Create local LLM instance."""
        try:
            from langchain_community.llms import HuggingFacePipeline
            from transformers import pipeline
            
            # Create HuggingFace pipeline
            pipe = pipeline(
                "text-generation",
                model=params["model_path"],
                device=params.get("device", "auto"),
                max_new_tokens=params.get("max_tokens", 512),
                temperature=params.get("temperature", 0.7),
            )
            
            return HuggingFacePipeline(pipeline=pipe)
        except ImportError:
            raise ImportError("transformers not available. Install with: pip install transformers torch")


def load_llm_config(config_path: str) -> AgentLLMConfig:
    """
    Load LLM configuration from YAML file.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Parsed AgentLLMConfig object
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        raw_config_data = f.read()
    
    # Expand environment variables like ${VAR}
    expanded_config_data = os.path.expandvars(raw_config_data)
    config_data = yaml.safe_load(expanded_config_data)
    
    # Parse LLM configurations
    llm_configs = {}
    for name, llm_config in config_data.get("llm_configs", {}).items():
        provider = llm_config["provider"]
        
        if provider == "ollama":
            llm_configs[name] = OllamaConfig(**llm_config)
        elif provider == "google":
            llm_configs[name] = GoogleConfig(**llm_config)
        elif provider == "groq":
            llm_configs[name] = GroqConfig(**llm_config)
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    
    # Parse node configurations
    node_configs = {}
    for name, node_config in config_data.get("node_configs", {}).items():
        node_configs[name] = NodeConfig(**node_config)
    
    return AgentLLMConfig(
        llm_configs=llm_configs,
        node_configs=node_configs
    )


def create_default_config_file(config_path: str) -> None:
    """Create a default configuration file with examples."""
    default_config = {
        "llm_configs": {
            "google_gemini": {
                "provider": "google",
                "model": "gemini-1.5-pro",
                "api_key": "${GEMINI_API_KEY}",
                "temperature": 0.7,
                "timeout": 30
            },
            "groq_llama": {
                "provider": "groq",
                "model": "llama3-8b-8192",
                "api_key": "${GROQ_API_KEY}",
                "temperature": 0.7,
                "timeout": 30
            }
        },
        "node_configs": {
            "router_node": {
                "llm_config_name": "google_gemini",
                "enabled": True,
                "custom_params": {
                    "format": "json"
                }
            },
            "memory_node": {
                "llm_config_name": "groq_llama", 
                "enabled": True,
                "custom_params": {
                    "temperature": 0.5
                }
            }
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False, indent=2)
