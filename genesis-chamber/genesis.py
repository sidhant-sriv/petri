#!/usr/bin/env python3
"""
Genesis Chamber - The initial agent creation tool for Petri

This script reads agent definitions from population.yml and creates them
via the world API to establish the founding population of your simulation.

It can also generate random agents using LLM calls for creative diversity.
"""

import sys
import os
import yaml
import requests
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings

# LLM imports (matching the agent codebase pattern)
try:
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️  LangChain not available. Random agent generation will be disabled.")


class GenesisSettings(BaseSettings):
    """Settings for Genesis Chamber, following the agent config pattern"""
    # World API Configuration
    WORLD_API_URL: str = "http://localhost:8000"
    API_KEY: str = ""
    
    # LLM Configuration (matching agent settings)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    GEMINI_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class RandomAgentSpec(BaseModel):
    """Schema for LLM-generated random agent specification"""
    name: str
    persona: str
    reasoning: str


class GenesisError(Exception):
    """Custom exception for Genesis Chamber errors"""
    pass


class GenesisAgent:
    """Represents an agent to be created"""
    def __init__(self, name: str, persona: str, source: str = "manifest"):
        self.name = name
        self.persona = persona
        self.source = source  # "manifest" or "generated"

    def __repr__(self):
        return f"GenesisAgent(name='{self.name}', source='{self.source}')"


class RandomAgentGenerator:
    """Generates random agents using LLM calls"""
    
    def __init__(self, settings: GenesisSettings):
        self.settings = settings
        if not LANGCHAIN_AVAILABLE:
            raise GenesisError("LangChain is required for random agent generation")
    
    def _get_llm(self):
        """Initialize LLM following the agent codebase pattern"""
        return ChatOllama(
            base_url=self.settings.OLLAMA_BASE_URL,
            model="llama3.1:8b",
            format="json"
        )
    
    def _create_generation_prompt(self, existing_names: List[str] = None, theme: str = None) -> str:
        """Create a prompt for generating a random agent"""
        existing_names = existing_names or []
        
        base_prompt = """You are a creative agent designer for a social media simulation called Petri.

Your task is to create a unique, interesting agent with a distinct personality that would create engaging social dynamics.

Requirements:
- The agent must have a unique name (not generic like "User123")
- The persona should be detailed, specific, and give the agent a clear voice
- The agent should have quirks, interests, and a distinctive communication style
- Avoid stereotypes and create nuanced, complex personalities
- The agent should feel like a real person with depth

Output your response as valid JSON in this exact format:
{
    "name": "AgentName",
    "persona": "Detailed persona description that defines how this agent thinks, speaks, and behaves...",
    "reasoning": "Brief explanation of why this agent would be interesting in a social simulation"
}"""

        if existing_names:
            base_prompt += f"\n\nExisting agent names to avoid duplicating: {', '.join(existing_names)}"
        
        if theme:
            base_prompt += f"\n\nTheme/inspiration for this agent: {theme}"
        
        base_prompt += "\n\nCreate one unique agent now:"
        
        return base_prompt
    
    def generate_random_agent(self, existing_names: List[str] = None, theme: str = None) -> GenesisAgent:
        """Generate a single random agent using LLM"""
        try:
            llm = self._get_llm()
            prompt = self._create_generation_prompt(existing_names, theme)
            
            print(f"🎲 Generating random agent (theme: {theme or 'general'})...")
            response = llm.invoke([HumanMessage(content=prompt)])
            
            # Parse JSON response
            try:
                agent_data = json.loads(response.content)
                spec = RandomAgentSpec(**agent_data)
            except (json.JSONDecodeError, Exception) as e:
                raise GenesisError(f"Failed to parse LLM response: {e}\nResponse: {response.content}")
            
            print(f"✨ Generated: {spec.name}")
            print(f"   Reasoning: {spec.reasoning}")
            
            return GenesisAgent(
                name=spec.name,
                persona=spec.persona,
                source="generated"
            )
            
        except Exception as e:
            raise GenesisError(f"Random agent generation failed: {e}")
    
    def generate_multiple_agents(self, count: int, existing_names: List[str] = None, themes: List[str] = None) -> List[GenesisAgent]:
        """Generate multiple random agents"""
        if themes and len(themes) < count:
            # Cycle through themes if we have fewer themes than requested agents
            themes = (themes * ((count // len(themes)) + 1))[:count]
        
        agents = []
        current_names = list(existing_names or [])
        
        for i in range(count):
            theme = themes[i] if themes else None
            try:
                agent = self.generate_random_agent(current_names, theme)
                agents.append(agent)
                current_names.append(agent.name)
            except GenesisError as e:
                print(f"⚠️  Failed to generate agent {i+1}: {e}")
        
        return agents


class GenesisChamber:
    """Main Genesis Chamber class that orchestrates agent creation"""
    
    def __init__(self, world_api_url: str = None, api_key: str = None, settings: GenesisSettings = None):
        self.settings = settings or GenesisSettings()
        
        # Override with provided parameters
        if world_api_url:
            self.settings.WORLD_API_URL = world_api_url
        if api_key:
            self.settings.API_KEY = api_key
        
        if not self.settings.API_KEY:
            raise GenesisError(
                "API_KEY is required. Set it via environment variable or .env file"
            )
        
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': self.settings.API_KEY,
            'Content-Type': 'application/json'
        })
        
        # Initialize random generator if available
        if LANGCHAIN_AVAILABLE:
            try:
                self.random_generator = RandomAgentGenerator(self.settings)
            except GenesisError:
                self.random_generator = None
        else:
            self.random_generator = None
    
    def load_population_manifest(self, manifest_path: str = "population.yml") -> List[GenesisAgent]:
        """Load agent definitions from YAML manifest"""
        manifest_file = Path(manifest_path)
        
        if not manifest_file.exists():
            raise GenesisError(
                f"Population manifest not found at {manifest_path}. "
                f"Please create this file with your agent definitions."
            )
        
        try:
            with open(manifest_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise GenesisError(f"Error parsing YAML manifest: {e}")
        
        if not isinstance(data, list):
            raise GenesisError(
                "Population manifest must contain a list of agent definitions"
            )
        
        agents = []
        for i, agent_data in enumerate(data):
            if not isinstance(agent_data, dict):
                raise GenesisError(f"Agent definition {i} must be a dictionary")
            
            if 'name' not in agent_data:
                raise GenesisError(f"Agent definition {i} missing required 'name' field")
            
            if 'persona' not in agent_data:
                raise GenesisError(f"Agent definition {i} missing required 'persona' field")
            
            agents.append(GenesisAgent(
                name=agent_data['name'],
                persona=agent_data['persona'].strip(),
                source="manifest"
            ))
        
        return agents
    
    def test_connection(self) -> bool:
        """Test connection to the world API"""
        try:
            response = self.session.get(f"{self.settings.WORLD_API_URL}/")
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"✗ Failed to connect to world API at {self.settings.WORLD_API_URL}")
            print(f"  Error: {e}")
            return False
    
    def create_agent(self, agent: GenesisAgent) -> Dict[str, Any]:
        """Create a single agent via the world API"""
        agent_data = {
            "name": agent.name,
            "persona": agent.persona
        }
        
        try:
            response = self.session.post(
                f"{self.settings.WORLD_API_URL}/api/agents/",
                json=agent_data
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 400:
                    error_detail = e.response.json().get('detail', 'Unknown error')
                    raise GenesisError(f"Agent creation failed: {error_detail}")
                else:
                    raise GenesisError(f"HTTP {e.response.status_code}: {e.response.text}")
            else:
                raise GenesisError(f"Network error: {e}")
    
    def genesis(self, manifest_path: str = "population.yml", dry_run: bool = False, 
                random_count: int = 0, random_themes: List[str] = None) -> None:
        """Execute the genesis process"""
        print("🧬 Genesis Chamber - Initializing founding population")
        print("=" * 60)
        
        # Test connection first
        print(f"🔗 Testing connection to world API at {self.settings.WORLD_API_URL}...")
        if not self.test_connection():
            raise GenesisError("Cannot proceed without world API connection")
        print("✓ Connection established")
        
        # Load agents from manifest
        agents = []
        if Path(manifest_path).exists():
            print(f"📖 Loading population manifest from {manifest_path}...")
            try:
                manifest_agents = self.load_population_manifest(manifest_path)
                agents.extend(manifest_agents)
            except GenesisError:
                raise
            except Exception as e:
                raise GenesisError(f"Unexpected error loading manifest: {e}")
            
            print(f"✓ Found {len(manifest_agents)} agents in manifest")
        else:
            print(f"📖 No manifest found at {manifest_path}, skipping...")
        
        # Generate random agents if requested
        if random_count > 0:
            if not self.random_generator:
                raise GenesisError("Random agent generation is not available (LangChain not installed)")
            
            print(f"🎲 Generating {random_count} random agents...")
            existing_names = [agent.name for agent in agents]
            
            try:
                random_agents = self.random_generator.generate_multiple_agents(
                    count=random_count,
                    existing_names=existing_names,
                    themes=random_themes
                )
                agents.extend(random_agents)
                print(f"✓ Generated {len(random_agents)} random agents")
            except Exception as e:
                print(f"⚠️  Random generation partially failed: {e}")
        
        if not agents:
            raise GenesisError("No agents to create. Provide a manifest file or use --random option.")
        
        print(f"\n📊 Total agents to create: {len(agents)}")
        manifest_count = len([a for a in agents if a.source == "manifest"])
        generated_count = len([a for a in agents if a.source == "generated"])
        if manifest_count > 0:
            print(f"  • From manifest: {manifest_count}")
        if generated_count > 0:
            print(f"  • Generated: {generated_count}")
        
        if dry_run:
            print("\n🔍 DRY RUN - No agents will be created:")
            for agent in agents:
                source_emoji = "📋" if agent.source == "manifest" else "🎲"
                print(f"  {source_emoji} {agent.name}")
                print(f"    Persona: {agent.persona[:100]}{'...' if len(agent.persona) > 100 else ''}")
            return
        
        # Create agents
        print(f"\n🚀 Creating {len(agents)} founding agents...")
        created_count = 0
        failed_count = 0
        
        for i, agent in enumerate(agents, 1):
            try:
                source_emoji = "📋" if agent.source == "manifest" else "🎲"
                print(f"  [{i}/{len(agents)}] {source_emoji} Creating {agent.name}...", end=" ")
                result = self.create_agent(agent)
                created_count += 1
                print(f"✓ (ID: {result['id']})")
            except GenesisError as e:
                failed_count += 1
                print(f"✗ {e}")
            except Exception as e:
                failed_count += 1
                print(f"✗ Unexpected error: {e}")
        
        # Summary
        print(f"\n📊 Genesis Complete!")
        print(f"  • Created: {created_count} agents")
        print(f"  • Failed: {failed_count} agents")
        
        if failed_count > 0:
            print(f"\n⚠️  Some agents could not be created. Check the errors above.")
            sys.exit(1)
        else:
            print(f"\n🎉 All agents successfully created! Your world is ready.")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Genesis Chamber - Create founding population of agents",
        epilog="""Examples:
  python genesis.py                              # Create from population.yml
  python genesis.py --random 5                   # Generate 5 random agents
  python genesis.py --random 3 --random-themes "scientist,artist,philosopher"
  python genesis.py --manifest custom.yml --random 2"""
    )
    parser.add_argument(
        "--manifest", 
        default="population.yml",
        help="Path to population manifest YAML file (default: population.yml)"
    )
    parser.add_argument(
        "--world-url",
        help="World API URL (default: from WORLD_API_URL env var or http://localhost:8000)"
    )
    parser.add_argument(
        "--api-key",
        help="API key for world service (default: from API_KEY env var)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without actually creating agents"
    )
    parser.add_argument(
        "--random",
        type=int,
        default=0,
        help="Generate N random agents using LLM (requires Ollama)"
    )
    parser.add_argument(
        "--random-themes",
        help="Comma-separated themes for random agent generation (e.g., 'scientist,artist,philosopher')"
    )
    
    args = parser.parse_args()
    
    try:
        # Load environment variables from .env file if it exists
        env_file = Path(".env")
        if env_file.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv()
            except ImportError:
                pass  # python-dotenv not available, that's ok
        
        # Parse random themes
        random_themes = None
        if args.random_themes:
            random_themes = [theme.strip() for theme in args.random_themes.split(",")]
        
        chamber = GenesisChamber(
            world_api_url=args.world_url,
            api_key=args.api_key
        )
        chamber.genesis(
            manifest_path=args.manifest, 
            dry_run=args.dry_run,
            random_count=args.random,
            random_themes=random_themes
        )
        
    except GenesisError as e:
        print(f"\n❌ Genesis failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n⏹️  Genesis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()