"""
Core abstraction layer for multi-architecture agent framework.

Provides:
- BaseArchitecture: Abstract base class for all architectures
- AgentSession: Unified session management
- Registry: Architecture registration and discovery
"""

from claude_agent_framework.core.base import (
    AgentDefinitionConfig,
    BaseArchitecture,
)
from claude_agent_framework.core.registry import (
    get_architecture,
    list_architectures,
    register_architecture,
)
from claude_agent_framework.core.session import AgentSession

__all__ = [
    # Base classes
    "BaseArchitecture",
    "AgentDefinitionConfig",
    # Session management
    "AgentSession",
    # Registry
    "register_architecture",
    "get_architecture",
    "list_architectures",
]
