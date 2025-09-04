"""
Redis client for caching agent details
"""

import json
import redis
from typing import Optional
from .core.config import settings


# Create Redis client instance with error handling
try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    # Test connection
    redis_client.ping()
    REDIS_AVAILABLE = True
except Exception as e:
    print(f"Redis connection failed: {e}")
    redis_client = None
    REDIS_AVAILABLE = False


class AgentCache:
    """Agent caching utilities using Redis"""
    
    AGENT_KEY_PREFIX = "agent:"
    AGENT_NAME_KEY_PREFIX = "agent_name:"
    CACHE_TTL = 3600  # 1 hour TTL
    
    @classmethod
    def _get_agent_key(cls, agent_id: int) -> str:
        """Get Redis key for agent by ID"""
        return f"{cls.AGENT_KEY_PREFIX}{agent_id}"
    
    @classmethod
    def _get_agent_name_key(cls, name: str) -> str:
        """Get Redis key for agent by name"""
        return f"{cls.AGENT_NAME_KEY_PREFIX}{name}"
    
    @classmethod
    def get_agent(cls, agent_id: int) -> Optional[dict]:
        """Get agent from cache by ID"""
        if not REDIS_AVAILABLE or not redis_client:
            return None
        try:
            key = cls._get_agent_key(agent_id)
            cached_data = redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            # Log error but don't fail - fall back to database
            print(f"Redis error getting agent {agent_id}: {e}")
            return None
    
    @classmethod
    def get_agent_by_name(cls, name: str) -> Optional[dict]:
        """Get agent from cache by name"""
        if not REDIS_AVAILABLE or not redis_client:
            return None
        try:
            key = cls._get_agent_name_key(name)
            cached_data = redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            # Log error but don't fail - fall back to database
            print(f"Redis error getting agent by name {name}: {e}")
            return None
    
    @classmethod
    def set_agent(cls, agent_data: dict) -> None:
        """Cache agent data by both ID and name"""
        if not REDIS_AVAILABLE or not redis_client:
            return
        try:
            agent_json = json.dumps({
                "id": agent_data["id"],
                "name": agent_data["name"],
                "persona": agent_data["persona"],
                "created_at": agent_data["created_at"].isoformat() if hasattr(agent_data["created_at"], "isoformat") else str(agent_data["created_at"])
            })
            
            # Cache by ID
            id_key = cls._get_agent_key(agent_data["id"])
            redis_client.setex(id_key, cls.CACHE_TTL, agent_json)
            
            # Cache by name
            name_key = cls._get_agent_name_key(agent_data["name"])
            redis_client.setex(name_key, cls.CACHE_TTL, agent_json)
            
        except Exception as e:
            # Log error but don't fail
            print(f"Redis error caching agent {agent_data.get('id', 'unknown')}: {e}")
    
    @classmethod
    def invalidate_agent(cls, agent_id: int, agent_name: str = None) -> None:
        """Remove agent from cache"""
        if not REDIS_AVAILABLE or not redis_client:
            return
        try:
            # Remove by ID
            id_key = cls._get_agent_key(agent_id)
            redis_client.delete(id_key)
            
            # Remove by name if provided
            if agent_name:
                name_key = cls._get_agent_name_key(agent_name)
                redis_client.delete(name_key)
                
        except Exception as e:
            # Log error but don't fail
            print(f"Redis error invalidating agent {agent_id}: {e}")