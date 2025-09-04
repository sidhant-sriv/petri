# Redis Agent Caching Implementation

This document describes the Redis caching implementation for agent details in the Petri world service.

## Overview

Agent retrieval operations have been enhanced with Redis caching to improve performance. The implementation uses a cache-aside pattern where:

1. **Cache Hit**: Agent data is returned directly from Redis
2. **Cache Miss**: Data is fetched from PostgreSQL and cached for future requests
3. **Cache Invalidation**: Cache is cleared when agents are created or updated

## Architecture

### Components Added

1. **Redis Configuration** (`core/config.py`)
   - Added `REDIS_URL` setting (defaults to `redis://redis:6379/0`)

2. **Redis Client** (`redis_client.py`)
   - `AgentCache` class with methods for caching agent data
   - Graceful fallback when Redis is unavailable
   - Automatic error handling and logging

3. **Enhanced CRUD Operations** (`crud.py`)
   - Modified `get_agent()` and `get_agent_by_name()` to check cache first
   - Modified `create_agent()` and `update_agent_persona()` to maintain cache consistency

4. **Health Check Endpoint** (`routers/api.py`)
   - Added `/health` endpoint that reports Redis availability

### Cache Strategy

- **Keys**: `agent:{id}` and `agent_name:{name}`
- **TTL**: 1 hour (3600 seconds)
- **Data Format**: JSON with id, name, persona, and created_at fields
- **Consistency**: Cache is invalidated on all write operations

## Performance Benefits

- **Faster Retrieval**: Agent lookups avoid database queries when data is cached
- **Reduced Database Load**: Frequently accessed agents are served from memory
- **Scalability**: Redis can be scaled independently from PostgreSQL

## Reliability Features

- **Graceful Degradation**: Application works normally even if Redis is unavailable
- **Error Handling**: Redis errors don't break application functionality
- **Fallback**: Always falls back to database queries when cache fails

## Usage

The caching is transparent to existing API consumers. No changes are required to client code.

### Health Check

Check Redis status:
```bash
curl -H "X-API-Key: your_api_key" http://localhost:8000/api/health
```

Response:
```json
{
  "status": "ok",
  "redis_available": true
}
```

## Configuration

Redis caching is enabled by default when Redis is available. Configure via environment variables:

- `REDIS_URL`: Redis connection URL (default: `redis://redis:6379/0`)

## Monitoring

Monitor cache effectiveness through:
- Application logs for Redis errors
- Redis metrics (hit rate, memory usage)
- Database query patterns