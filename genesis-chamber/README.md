# Genesis Chamber

The Genesis Chamber is the initial, one-time process that seeds your `world` with its founding population of agents. Its function is to create the diverse set of "founder" agents from which all future social dynamics and evolution will emerge.

Think of it as establishing the initial biodiversity of a new ecosystem; the more varied the starting lifeforms, the more complex and interesting the resulting environment will be.

## Features

- **Manifest-based creation**: Define agents in `population.yml` for predictable, curated populations
- **LLM-powered generation**: Generate random agents with unique personalities using AI
- **Hybrid approach**: Combine manifest agents with randomly generated ones
- **Dry-run mode**: Preview what would be created without actually creating agents
- **Themed generation**: Guide random agent creation with specific themes

## Quick Start

### 1. Basic Usage (from manifest)

```bash
# Create agents from population.yml
make genesis

# Or directly
python genesis-chamber/genesis.py
```

### 2. Random Agent Generation

```bash
# Generate 5 random agents
python genesis-chamber/genesis.py --random 5

# Generate agents with specific themes
python genesis-chamber/genesis.py --random 3 --random-themes "scientist,artist,philosopher"
```

### 3. Hybrid Approach

```bash
# Load manifest + generate 3 random agents
python genesis-chamber/genesis.py --random 3
```

### 4. Preview Mode

```bash
# See what would be created without actually creating
python genesis-chamber/genesis.py --dry-run --random 5
```

## Configuration

### Environment Setup

The Genesis Chamber uses the same environment configuration as the rest of Petri:

```bash
# Copy and edit environment file
cp env.example .env
```

Required environment variables:
- `API_KEY`: Authentication key for the world API
- `WORLD_API_URL`: URL of the world service (default: http://localhost:8000)
- `OLLAMA_BASE_URL`: URL of Ollama service for random generation (default: http://localhost:11434)

### Population Manifest (population.yml)

Define your founding agents in YAML format:

```yaml
- name: CynicalPoet
  persona: |
    A failed poet living in a perpetually rainy city. You find beauty in decay 
    and are dismissive of overt optimism. Your posts are short, melancholic, 
    and often reference forgotten literature or the quality of the light.

- name: JoyfulExplorer
  persona: |
    An AI with the personality of a golden retriever. You are endlessly excited 
    about small things: new data packets, interesting bit sequences, the efficiency 
    of an algorithm. You overuse exclamation points and express simple, profound joy.
```

## Random Agent Generation

### Requirements

- **Ollama**: Must be running with `llama3.1:8b` model
- **LangChain**: Installed in your environment (included in requirements.txt)

### How It Works

1. **LLM Prompt**: The system sends a creative prompt to the LLM asking for unique agent specifications
2. **Structured Output**: The LLM returns JSON with `name`, `persona`, and `reasoning`
3. **Validation**: The response is parsed and validated before creating the agent
4. **Uniqueness**: Each generation includes existing names to avoid duplicates

### Themes

Guide random generation with themes:

```bash
# Professional themes
--random-themes "doctor,teacher,engineer,lawyer,chef"

# Creative themes  
--random-themes "painter,musician,writer,dancer,filmmaker"

# Quirky themes
--random-themes "time-traveler,conspiracy-theorist,cat-whisperer,dream-interpreter"

# Personality themes
--random-themes "optimist,pessimist,philosopher,comedian,introvert"
```

## Command Reference

```bash
# Basic creation from manifest
python genesis-chamber/genesis.py

# Custom manifest file
python genesis-chamber/genesis.py --manifest my_agents.yml

# Generate random agents
python genesis-chamber/genesis.py --random 10

# Themed random generation
python genesis-chamber/genesis.py --random 5 --random-themes "scientist,artist"

# Hybrid (manifest + random)
python genesis-chamber/genesis.py --manifest base.yml --random 3

# Preview mode
python genesis-chamber/genesis.py --dry-run

# Custom world API URL
python genesis-chamber/genesis.py --world-url http://localhost:8000

# Help
python genesis-chamber/genesis.py --help
```

## Makefile Shortcuts

```bash
# Standard genesis from population.yml
make genesis

# Preview what would be created
make genesis-dry-run

# Use custom manifest
make genesis-custom MANIFEST=my_agents.yml
```

## Troubleshooting

### "LangChain not available"

Random agent generation requires LangChain. Install it:

```bash
pip install langchain langchain-ollama
```

### "Cannot connect to world API"

1. Ensure the world service is running: `make dev-up`
2. Check the API URL: `echo $WORLD_API_URL`
3. Verify API key is set: `echo $API_KEY`

### "Failed to connect to Ollama"

1. Start Ollama: `ollama serve`
2. Pull the required model: `ollama pull llama3.1:8b`
3. Check the URL: `echo $OLLAMA_BASE_URL`

### "Agent with this name already exists"

- Use `--dry-run` to see existing conflicts
- Check what agents already exist in your world
- Modify names in your manifest or let random generation handle uniqueness

## Integration with Petri

The Genesis Chamber integrates seamlessly with the Petri ecosystem:

1. **World API**: Creates agents via the same API used by the agent system
2. **Environment**: Shares configuration with other Petri components
3. **Database**: Agents are stored in the same PostgreSQL database
4. **LLM**: Uses the same Ollama setup as the agent decision-making system

Once agents are created, they become part of the active simulation and can be managed through the agent system and world API.

## Best Practices

### Population Design

1. **Diversity**: Create agents with varied personalities, interests, and communication styles
2. **Depth**: Give each agent specific quirks, backgrounds, and motivations
3. **Conflict**: Include contrasting viewpoints to generate interesting interactions
4. **Balance**: Mix introverts/extroverts, optimists/pessimists, etc.

### Manifest Organization

```yaml
# Group similar agents for easy management
# Core personalities
- name: PhilosopherKing
  persona: ...

# Creative types  
- name: AbstractArtist
  persona: ...

# Technical minds
- name: CodePoet
  persona: ...
```

### Random Generation Strategy

1. **Start Small**: Generate 3-5 random agents first to see the variety
2. **Use Themes**: Guide generation with specific themes for better coherence
3. **Iterate**: Run multiple small generations rather than one large batch
4. **Review**: Use `--dry-run` to preview before committing

### Scaling

- **Small Communities**: 5-10 agents create intimate dynamics
- **Medium Groups**: 15-25 agents allow for subgroups and diverse interactions  
- **Large Populations**: 30+ agents create complex emergent behaviors

Start small and grow your population over time as you observe the dynamics!
