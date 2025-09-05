"""
Genesis Chamber - Agent creation and population seeding for Petri

This module provides tools for creating the initial population of agents
in your Petri simulation, either from predefined manifests or through
LLM-powered random generation.
"""

from .genesis import GenesisChamber, GenesisAgent, RandomAgentGenerator, GenesisError

__version__ = "1.0.0"
__all__ = ["GenesisChamber", "GenesisAgent", "RandomAgentGenerator", "GenesisError"]
