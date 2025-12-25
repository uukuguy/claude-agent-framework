"""
Simplified initialization API for Claude Agent Framework.

Provides a single entry point that handles:
- API key validation
- Directory creation
- Logging setup
- Architecture instantiation
- Session creation

Example:
    >>> from claude_agent_framework import init
    >>> session = init("research")
    >>> async for msg in session.run("Analyze AI trends"):
    ...     print(msg)
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from claude_agent_framework.core.session import AgentSession

# Type aliases
ArchitectureType = Literal[
    "research", "pipeline", "critic_actor",
    "specialist_pool", "debate", "reflexion", "mapreduce"
]
ModelType = Literal["haiku", "sonnet", "opus"]


class InitializationError(Exception):
    """Raised when framework initialization fails.

    Common causes:
    - ANTHROPIC_API_KEY environment variable not set
    - Unknown architecture name
    - Configuration errors
    """
    pass


def init(
    architecture: ArchitectureType = "research",
    *,
    model: ModelType = "haiku",
    verbose: bool = False,
    log_dir: Path | str | None = None,
    files_dir: Path | str | None = None,
    auto_setup: bool = True,
) -> "AgentSession":
    """
    Initialize Claude Agent Framework with minimal configuration.

    This is the recommended entry point for most users. It handles:
    - Validating ANTHROPIC_API_KEY environment variable
    - Creating necessary directories
    - Setting up logging and tracking
    - Returning a ready-to-use session

    Args:
        architecture: Architecture pattern to use. Options:
            - "research": Deep research with parallel workers
            - "pipeline": Sequential stage processing
            - "critic_actor": Generate-evaluate iteration
            - "specialist_pool": Expert routing
            - "debate": Pro-con deliberation
            - "reflexion": Execute-reflect-improve
            - "mapreduce": Parallel map with aggregation
        model: Model to use (haiku/sonnet/opus). Default: haiku
        verbose: Enable debug logging. Default: False
        log_dir: Custom directory for logs. Default: framework logs/
        files_dir: Custom directory for output files. Default: framework files/
        auto_setup: Automatically create directories. Default: True

    Returns:
        AgentSession ready for use with run() or query() methods

    Raises:
        InitializationError: If API key not set or architecture not found

    Example:
        >>> from claude_agent_framework import init
        >>>
        >>> # Simple usage
        >>> session = init("research")
        >>> async for msg in session.run("Analyze AI market trends"):
        ...     print(msg)
        >>>
        >>> # With options
        >>> session = init("pipeline", model="sonnet", verbose=True)
    """
    # Import here to avoid circular imports
    from claude_agent_framework.config import FrameworkConfig, validate_api_key
    from claude_agent_framework.core import AgentSession, get_architecture
    from claude_agent_framework.core.base import AgentModelConfig

    # 1. Validate API key
    if not validate_api_key():
        raise InitializationError(
            "ANTHROPIC_API_KEY environment variable is not set.\n"
            "Please set it before running:\n"
            "  export ANTHROPIC_API_KEY='your-api-key'\n\n"
            "You can get an API key from: https://console.anthropic.com/"
        )

    # 2. Configure logging
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )

    # 3. Get architecture class
    try:
        arch_class = get_architecture(architecture)
    except KeyError as e:
        from claude_agent_framework.core import list_architectures
        available = ", ".join(list_architectures())
        raise InitializationError(
            f"Unknown architecture: '{architecture}'\n"
            f"Available architectures: {available}"
        ) from e

    # 4. Create model configuration
    model_config = AgentModelConfig(default=model)

    # 5. Create architecture instance
    arch = arch_class(model_config=model_config)

    # 6. Create framework config
    config = FrameworkConfig(lead_agent_model=model)
    if log_dir:
        config.logs_dir = Path(log_dir)
    if files_dir:
        config.files_dir = Path(files_dir)

    # 7. Setup directories if requested
    if auto_setup:
        config.ensure_directories()

    # 8. Create and return session
    session = AgentSession(arch, config)

    return session


async def quick_query(
    prompt: str,
    architecture: ArchitectureType = "research",
    model: ModelType = "haiku",
) -> list:
    """
    Execute a single query and return all messages.

    Convenience function for quick, one-off queries. For multiple queries
    or streaming output, use init() instead.

    Args:
        prompt: The query to execute
        architecture: Architecture to use
        model: Model to use

    Returns:
        List of all response messages

    Example:
        >>> import asyncio
        >>> from claude_agent_framework import quick_query
        >>>
        >>> results = asyncio.run(quick_query("Analyze Python trends"))
        >>> print(results[-1])  # Print final message
    """
    session = init(architecture, model=model)
    try:
        return await session.query(prompt)
    finally:
        await session.teardown()


def get_available_architectures() -> dict[str, str]:
    """
    Get all available architectures with their descriptions.

    Returns:
        Dictionary mapping architecture names to descriptions

    Example:
        >>> from claude_agent_framework import get_available_architectures
        >>> for name, desc in get_available_architectures().items():
        ...     print(f"{name}: {desc}")
    """
    from claude_agent_framework.core.registry import get_architecture_info
    return {name: info["description"] for name, info in get_architecture_info().items()}
