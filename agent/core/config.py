"""
Agent Configuration
Unified environment variable management for the agent component
"""

from pydantic_settings import BaseSettings
from typing import Optional


class AgentSettings(BaseSettings):
    # World API Configuration
    WORLD_API_URL: str = "http://world:8000"
    API_KEY: str

    # Neo4j Configuration (Agent Memory)
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4j_password"

    # LLM Configuration
    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
    GEMINI_API_KEY: Optional[str] = None

    # Redis Configuration (for agent-manager workers)
    REDIS_URL: str = "redis://redis:6379/0"

    # Environment
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        extra = (
            "ignore"  # Ignore extra fields from .env that aren't defined in the model
        )


# Global settings instance
settings = AgentSettings()
