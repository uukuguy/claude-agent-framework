"""
Claude Agent Framework

A multi-architecture agent framework built on Claude Agent SDK.
Supports 7 architecture patterns for research, development, and decision support.

Quick Start:
    >>> from claude_agent_framework import init
    >>> session = init("research")
    >>> async for msg in session.run("Analyze AI market trends"):
    ...     print(msg)

Available Architectures:
- research: Master-worker pattern for deep research
- pipeline: Sequential stage processing for code review
- critic_actor: Generate-evaluate iteration for quality improvement
- specialist_pool: Expert routing for technical support
- debate: Pro-con deliberation for decision support
- reflexion: Execute-reflect-improve for complex problem solving
- mapreduce: Parallel map with aggregation for large-scale analysis

CLI Usage:
    python -m claude_agent_framework.cli --arch research -q "Analyze AI trends"
    python -m claude_agent_framework.cli --list
"""

# Primary API - simplified initialization (recommended)
# Legacy imports for backwards compatibility
from claude_agent_framework.agent import main, run_research_session
from claude_agent_framework.config import (
    AgentConfig,
    FrameworkConfig,
    default_config,
    validate_api_key,
)
from claude_agent_framework.core import (
    AgentSession,
    BaseArchitecture,
    get_architecture,
    list_architectures,
    register_architecture,
)
from claude_agent_framework.init import (
    InitializationError,
    get_available_architectures,
    init,
    quick_query,
)
from claude_agent_framework.utils import (
    QuietTranscriptWriter,
    SubagentSession,
    SubagentTracker,
    ToolCallRecord,
    TranscriptWriter,
    process_message,
    setup_session,
)

__version__ = "0.3.0"
__all__ = [
    # Primary API (new simplified interface)
    "init",
    "quick_query",
    "InitializationError",
    "get_available_architectures",
    # Core architecture
    "BaseArchitecture",
    "AgentSession",
    "register_architecture",
    "get_architecture",
    "list_architectures",
    # Configuration
    "FrameworkConfig",
    "AgentConfig",
    "default_config",
    "validate_api_key",
    # Tracking
    "SubagentTracker",
    "SubagentSession",
    "ToolCallRecord",
    # Transcript
    "TranscriptWriter",
    "QuietTranscriptWriter",
    "setup_session",
    # Message handling
    "process_message",
    # Legacy entry points
    "run_research_session",
    "main",
]
