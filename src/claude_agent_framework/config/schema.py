"""
Pydantic validation schemas for configuration.

Provides type-safe configuration with validation and defaults.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from claude_agent_framework.core.types import ModelType

try:
    from pydantic import BaseModel, Field, field_validator, model_validator
except ImportError as e:
    raise ImportError(
        "Pydantic is required for advanced configuration. "
        "Install with: pip install 'claude-agent-framework[config]' or pip install pydantic>=2.0.0"
    ) from e


class PermissionMode(str, Enum):
    """SDK permission modes."""

    BYPASS = "bypassPermissions"
    PROMPT = "prompt"
    DENY = "deny"


# List of all valid tool names
VALID_TOOLS = [
    "Task",
    "WebSearch",
    "WebFetch",
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    "Bash",
    "Skill",
    "LSP",
    "NotebookEdit",
    "NotebookRead",
    "AskUserQuestion",
    "TodoWrite",
    "EnterPlanMode",
    "ExitPlanMode",
    "KillShell",
    "TaskOutput",
]


class AgentConfigSchema(BaseModel):
    """
    Pydantic schema for single agent configuration.

    Attributes:
        name: Agent identifier (lowercase with hyphens)
        description: When to use this agent
        tools: List of allowed tools
        prompt: Prompt content (if prompt_file not provided)
        prompt_file: Prompt filename (relative to prompts directory)
        model: Model to use
    """

    name: str = Field(
        ...,
        pattern=r"^[a-z][a-z0-9-]*$",
        description="Agent name (lowercase with hyphens, e.g., 'my-agent')",
    )
    description: str = Field(..., min_length=10, description="Agent description")
    tools: list[str] = Field(default_factory=list, description="Allowed tools")
    prompt: str = Field(default="", description="Inline prompt content")
    prompt_file: str = Field(default="", description="Prompt file path")
    model: ModelType = Field(default=ModelType.HAIKU, description="Model to use")

    @field_validator("tools")
    @classmethod
    def validate_tools(cls, v: list[str]) -> list[str]:
        """Validate that all tools are valid."""
        if not v:
            return v

        invalid = [tool for tool in v if tool not in VALID_TOOLS]
        if invalid:
            raise ValueError(f"Invalid tools: {invalid}. Valid tools are: {', '.join(VALID_TOOLS)}")
        return v

    @model_validator(mode="after")
    def validate_prompt_source(self) -> AgentConfigSchema:
        """Ensure either prompt or prompt_file is provided."""
        if not self.prompt and not self.prompt_file:
            raise ValueError("Either 'prompt' or 'prompt_file' must be provided")
        if self.prompt and self.prompt_file:
            raise ValueError("Cannot specify both 'prompt' and 'prompt_file'")
        return self


class AgentPromptOverrideSchema(BaseModel):
    """
    Schema for agent-level prompt override configuration.

    Used in YAML config to customize prompts for specific agents.

    Attributes:
        business_prompt: Inline business prompt content (overrides template)
        business_prompt_file: Business prompt file path
        template_vars: Agent-specific template variables
    """

    business_prompt: str = Field(
        default="", description="Inline business prompt content"
    )
    business_prompt_file: str = Field(
        default="", description="Business prompt file path"
    )
    template_vars: dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific template variables"
    )


class PromptsConfigSchema(BaseModel):
    """
    Schema for prompts configuration block.

    Configures business templates and prompt customization.

    Attributes:
        business_template: Name of business template to use
        prompts_dir: Application-level custom prompts directory
        template_vars: Global template variables for all agents
        agents: Agent-specific prompt overrides
    """

    business_template: str | None = Field(
        default=None,
        description="Name of business template (e.g., 'competitive_intelligence')",
    )
    prompts_dir: str | None = Field(
        default=None,
        description="Application-level custom prompts directory",
    )
    template_vars: dict[str, Any] = Field(
        default_factory=dict,
        description="Global template variables for ${var} substitution",
    )
    agents: dict[str, AgentPromptOverrideSchema] = Field(
        default_factory=dict,
        description="Agent-specific prompt overrides",
    )

    def get_prompt_overrides(self) -> dict[str, str]:
        """
        Extract prompt overrides from agent configurations.

        Returns:
            Dict of agent_name -> business_prompt for agents with inline prompts
        """
        overrides = {}
        for agent_name, config in self.agents.items():
            if config.business_prompt:
                overrides[agent_name] = config.business_prompt
        return overrides

    def get_merged_template_vars(self, agent_name: str) -> dict[str, Any]:
        """
        Get merged template variables for an agent.

        Agent-specific variables override global variables.

        Args:
            agent_name: Name of the agent

        Returns:
            Merged template variables dict
        """
        result = dict(self.template_vars)
        if agent_name in self.agents:
            result.update(self.agents[agent_name].template_vars)
        return result


class FrameworkConfigSchema(BaseModel):
    """
    Pydantic schema for framework configuration.

    Attributes:
        lead_agent_prompt_file: Lead agent prompt file
        lead_agent_tools: Lead agent allowed tools
        lead_agent_model: Lead agent model
        subagents: List of subagent configurations
        permission_mode: Permission mode
        setting_sources: Configuration sources
        enable_logging: Whether to enable logging
        logs_dir: Logs directory
        files_dir: Files directory
        max_parallel_agents: Maximum parallel agent spawns
        enable_metrics: Whether to enable metrics collection
        enable_plugins: Whether to enable plugin system
    """

    # Lead agent configuration
    lead_agent_prompt_file: str = Field(
        default="lead_agent.txt", description="Lead agent prompt file"
    )
    lead_agent_tools: list[str] = Field(
        default_factory=lambda: ["Task"], description="Lead agent allowed tools"
    )
    lead_agent_model: ModelType = Field(default=ModelType.HAIKU, description="Lead agent model")

    # Subagent configuration
    subagents: list[AgentConfigSchema] = Field(
        default_factory=list, description="Subagent configurations"
    )

    # SDK configuration
    permission_mode: PermissionMode = Field(
        default=PermissionMode.BYPASS, description="Permission mode"
    )
    setting_sources: list[str] = Field(
        default_factory=lambda: ["project"], description="Configuration sources"
    )

    # Logging configuration
    enable_logging: bool = Field(default=True, description="Enable logging")
    logs_dir: Path = Field(default=Path("logs"), description="Logs directory")
    files_dir: Path = Field(default=Path("files"), description="Files directory")

    # Performance configuration
    max_parallel_agents: int = Field(
        default=5, ge=1, le=20, description="Maximum parallel agent spawns"
    )

    # Feature flags
    enable_metrics: bool = Field(default=False, description="Enable metrics collection")
    enable_plugins: bool = Field(default=True, description="Enable plugin system")

    # Prompts configuration (NEW)
    prompts: PromptsConfigSchema = Field(
        default_factory=PromptsConfigSchema,
        description="Prompts configuration for business templates and customization",
    )

    @field_validator("lead_agent_tools")
    @classmethod
    def validate_lead_tools(cls, v: list[str]) -> list[str]:
        """Validate that all lead agent tools are valid."""
        if not v:
            raise ValueError("Lead agent must have at least one tool")

        invalid = [tool for tool in v if tool not in VALID_TOOLS]
        if invalid:
            raise ValueError(f"Invalid tools: {invalid}. Valid tools are: {', '.join(VALID_TOOLS)}")
        return v

    @field_validator("logs_dir", "files_dir")
    @classmethod
    def validate_path(cls, v: Path | str) -> Path:
        """Convert string paths to Path objects."""
        if isinstance(v, str):
            return Path(v)
        return v

    model_config = {"use_enum_values": True}


class ProfileConfigSchema(BaseModel):
    """
    Environment profile configuration.

    Allows override of framework settings per environment.
    """

    name: str = Field(..., description="Profile name (dev/staging/prod)")
    framework: dict[str, Any] = Field(
        default_factory=dict, description="Framework config overrides"
    )
    agents: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Agent config overrides"
    )

    def apply_to_config(self, config: FrameworkConfigSchema) -> FrameworkConfigSchema:
        """
        Apply profile overrides to framework config.

        Args:
            config: Base configuration

        Returns:
            Updated configuration with profile overrides
        """
        # Create a copy with framework overrides
        config_dict = config.model_dump()
        config_dict.update(self.framework)

        # Apply agent-specific overrides
        for agent_name, overrides in self.agents.items():
            for agent in config_dict.get("subagents", []):
                if agent["name"] == agent_name:
                    agent.update(overrides)

        return FrameworkConfigSchema(**config_dict)
