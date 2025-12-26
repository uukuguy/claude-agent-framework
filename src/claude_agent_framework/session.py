"""
Session creation API for Claude Agent Framework.

Provides the main entry point for creating agent sessions with automatic
setup and configuration.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from claude_agent_framework.core.types import ArchitectureType, ModelTypeStr

if TYPE_CHECKING:
    from claude_agent_framework.core.session import AgentSession


class InitializationError(Exception):
    """Raised when framework initialization fails.

    Common causes:
    - ANTHROPIC_API_KEY environment variable not set
    - Unknown architecture name
    - Configuration errors
    """

    pass


def create_session(
    architecture: ArchitectureType = "research",
    *,
    model: ModelTypeStr = "haiku",
    verbose: bool = False,
    log_dir: Path | str | None = None,
    files_dir: Path | str | None = None,
    auto_setup: bool = True,
    # New: Business template and prompt customization
    business_template: str | None = None,
    prompts_dir: Path | str | None = None,
    prompt_overrides: dict[str, str] | None = None,
    template_vars: dict[str, Any] | None = None,
) -> AgentSession:
    """
    Create a ready-to-use agent session with minimal configuration.

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
        business_template: Name of business template to use (optional).
            Available templates can be listed with:
            `from claude_agent_framework.business_templates import list_templates`
        prompts_dir: Application-level custom prompts directory (optional).
            Files in this directory override business template prompts.
        prompt_overrides: Dict of agent_name -> override prompt content.
            Highest priority, overrides all other prompt sources.
        template_vars: Dict of template variables for ${var} substitution
            in prompts.

    Returns:
        AgentSession ready for use with run() or query() methods

    Raises:
        InitializationError: If API key not set or architecture not found

    Example:
        >>> from claude_agent_framework import create_session
        >>>
        >>> # Simple usage
        >>> session = create_session("research")
        >>> async for msg in session.run("Analyze AI market trends"):
        ...     print(msg)
        >>>
        >>> # With business template
        >>> session = create_session(
        ...     "research",
        ...     business_template="competitive_intelligence",
        ...     template_vars={"company_name": "Tesla Inc"}
        ... )
        >>>
        >>> # With custom prompts
        >>> session = create_session(
        ...     "research",
        ...     prompts_dir="./my_prompts",
        ...     prompt_overrides={"researcher": "Custom researcher instructions..."}
        ... )
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
            f"Unknown architecture: '{architecture}'\nAvailable architectures: {available}"
        ) from e

    # 4. Create model configuration
    model_config = AgentModelConfig(default=model)

    # 5. Validate business template if specified
    if business_template:
        from claude_agent_framework.business_templates import template_exists

        if not template_exists(business_template):
            from claude_agent_framework.business_templates import list_templates

            available = list_templates()
            raise InitializationError(
                f"Business template '{business_template}' not found.\n"
                f"Available templates: {', '.join(available) if available else 'none'}"
            )

    # 6. Create architecture instance with new prompt customization options
    arch = arch_class(
        model_config=model_config,
        business_template=business_template,
        custom_prompts_dir=Path(prompts_dir) if prompts_dir else None,
        prompt_overrides=prompt_overrides,
        template_vars=template_vars,
    )

    # 7. Create framework config
    config = FrameworkConfig(lead_agent_model=model)
    if log_dir:
        config.logs_dir = Path(log_dir)
    if files_dir:
        config.files_dir = Path(files_dir)

    # 8. Setup directories if requested
    if auto_setup:
        config.ensure_directories()

    # 9. Create and return session
    session = AgentSession(arch, config)

    return session
