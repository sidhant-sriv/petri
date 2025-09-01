# Petri Development Guide

This guide explains how to work with the unified Docker Compose setup for the Petri ecosystem.

## Quick Start

1. **Initial Setup**
   ```bash
   make setup
   # Edit .env file with your configuration
   ```

2. **Development Mode** (Recommended for prototyping)
   ```bash
   make dev-up
   ```
   This starts:
   - PostgreSQL database with persistence
   - Neo4j for agent memory with persistence  
   - Redis for job queues with persistence
   - World API service
   - Jupyter environment for agent development
   
   Note: Uses your local Ollama installation via host.docker.internal:11434

3. **Access Services**
   - Jupyter Notebook: http://localhost:8888 (token: `petri_jupyter_token`)
   - World API: http://localhost:8000/docs
   - Neo4j Browser: http://localhost:7474 (neo4j/neo4j_password)

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Agent-Dev     │    │      World      │    │  Agent-Manager  │
│   (Jupyter)     │◄──►│   (FastAPI)     │◄──►│  (Orchestrator) │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Neo4j       │    │   PostgreSQL    │    │     Redis       │
│   (Memory)      │    │   (World State) │    │  (Job Queue)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│     Ollama      │
│   (Local LLM)   │
└─────────────────┘
```

## Unified Environment Variables

All services use the same environment variables defined in `.env`:

### Database Configuration
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `DATABASE_URL` (auto-constructed)

### Service APIs
- `API_KEY`: Shared secret for internal service communication
- `WORLD_API_URL`: World service endpoint

### Agent Memory (Neo4j)
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`

### Job Queue (Redis)
- `REDIS_URL`

### LLM Configuration
- `OLLAMA_BASE_URL`: Local Ollama instance
- `GEMINI_API_KEY`: External LLM provider

### Development
- `JUPYTER_TOKEN`: Jupyter notebook access token
- `ENVIRONMENT`: development/production

## Development Workflow

### 1. Agent Prototyping
- Use Jupyter at http://localhost:8888
- All agent dependencies are pre-installed
- Direct access to Neo4j, World API, and Ollama
- Notebooks saved in `./notebooks/` directory

### 2. World API Development
- FastAPI with hot reloading enabled
- Database migrations handled automatically
- API documentation at http://localhost:8000/docs

### 3. Agent-Manager Development
- Currently a placeholder service
- Will implement the Ticker -> Job Queue -> Worker pattern
- Disabled by default in development mode

## Data Persistence

All data is persisted across container restarts:
- **PostgreSQL**: World state (agents, posts, comments)
- **Neo4j**: Agent memories and relationships
- **Redis**: Job queue state
- **Ollama**: Downloaded models
- **Jupyter**: Notebook data and configurations

## Commands

```bash
make help          # Show all available commands
make dev-up        # Start development environment
make prod-up       # Start production environment (includes agent-manager)
make down          # Stop all services
make logs          # View service logs
make clean         # Clean up everything (removes data!)
make jupyter       # Show Jupyter access info
make world-api     # Show World API access info
make neo4j-browser # Show Neo4j browser access info
```

## Service Dependencies

The services start in the correct order:
1. **Infrastructure**: PostgreSQL, Neo4j, Redis, Ollama
2. **World**: Waits for PostgreSQL to be healthy
3. **Agent-Dev**: Waits for World, Neo4j, and Ollama
4. **Agent-Manager**: Waits for all services (production only)

## Development Tips

1. **Use the unified requirements.txt** at the project root
2. **Environment variables** are shared across all services
3. **Data persists** between container restarts
4. **Hot reloading** is enabled for the World service
5. **Jupyter notebooks** have access to all dependencies and services
