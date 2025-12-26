"""
Base architecture abstraction.

Provides abstract base class that all architecture implementations must inherit.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from claude_agent_framework.plugins.base import BasePlugin
    from claude_agent_framework.utils import SubagentTracker, TranscriptWriter


@dataclass
class AgentDefinitionConfig:
    """
    Configuration for a single agent within an architecture.

    Attributes:
        name: Agent identifier (used as subagent_type)
        description: When to use this agent
        tools: List of allowed tools
        prompt: Prompt content or file path
        model: Model to use (haiku/sonnet/opus)
        prompt_file: Path to prompt file (relative to architecture prompts dir)
    """

    name: str
    description: str
    tools: list[str] = field(default_factory=list)
    prompt: str = ""
    prompt_file: str = ""
    model: str = "haiku"

    def load_prompt(self, prompts_dir: Path) -> str:
        """Load prompt content from file if prompt_file is set."""
        if self.prompt:
            return self.prompt
        if self.prompt_file:
            prompt_path = prompts_dir / self.prompt_file
            if prompt_path.exists():
                return prompt_path.read_text(encoding="utf-8").strip()
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        return ""


@dataclass
class AgentModelConfig:
    """
    Model configuration for architecture agents.

    Allows specifying default model and per-agent overrides.

    Attributes:
        default: Default model for all agents
        overrides: Per-agent model overrides {agent_name: model}
    """

    default: str = "haiku"
    overrides: dict[str, str] = field(default_factory=dict)

    def get_model(self, agent_name: str) -> str:
        """Get model for specific agent, falling back to default."""
        return self.overrides.get(agent_name, self.default)


@runtime_checkable
class ArchitecturePlugin(Protocol):
    """
    Protocol for architecture plugins.

    Plugins can hook into architecture lifecycle events.
    """

    def on_before_execute(self, prompt: str) -> str:
        """Called before execution, can modify prompt."""
        ...

    def on_after_stage(self, stage: str, result: Any) -> Any:
        """Called after each stage completes."""
        ...

    def on_error(self, error: Exception) -> bool:
        """Called on error, returns whether to continue."""
        ...


class BaseArchitecture(ABC):
    """
    Abstract base class for all architecture implementations.

    All architectures must inherit from this class and implement:
    - execute(): Main execution logic returning async message stream
    - get_agents(): Returns agent definitions for the architecture

    Optional overrides:
    - get_hooks(): Custom hook configuration
    - setup(): Pre-execution initialization
    - teardown(): Post-execution cleanup
    """

    # Class attributes - override in subclasses
    name: str = "base"
    description: str = "Base architecture (abstract)"

    def __init__(
        self,
        model_config: AgentModelConfig | None = None,
        prompts_dir: Path | None = None,
        files_dir: Path | None = None,
        # New: Business template and prompt customization
        business_template: str | None = None,
        custom_prompts_dir: Path | str | None = None,
        prompt_overrides: dict[str, str] | None = None,
        template_vars: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize architecture.

        Args:
            model_config: Model configuration for agents
            prompts_dir: Directory containing prompt files
            files_dir: Working directory for file operations
            business_template: Name of business template to use (optional)
            custom_prompts_dir: Application-level custom prompts directory (optional)
            prompt_overrides: Dict of agent_name -> override prompt content
            template_vars: Dict of template variables for ${var} substitution
        """
        self.model_config = model_config or AgentModelConfig()
        self._prompts_dir = prompts_dir
        self._files_dir = files_dir
        self._plugins: list[ArchitecturePlugin] = []  # Legacy plugin support
        self._result: Any = None

        # Business template and prompt customization
        self._business_template = business_template
        self._custom_prompts_dir = Path(custom_prompts_dir) if custom_prompts_dir else None
        self._prompt_overrides = prompt_overrides or {}
        self._template_vars = template_vars or {}

        # New plugin system
        from claude_agent_framework.plugins.base import PluginManager

        self._plugin_manager = PluginManager()

        # Dynamic agent registry
        from claude_agent_framework.dynamic.agent_registry import DynamicAgentRegistry

        self._dynamic_agents = DynamicAgentRegistry()

    @property
    def prompts_dir(self) -> Path:
        """Get prompts directory for this architecture."""
        if self._prompts_dir:
            return self._prompts_dir
        # Default: architectures/<name>/prompts/
        from claude_agent_framework.config import FRAMEWORK_ROOT

        return FRAMEWORK_ROOT / "architectures" / self.name / "prompts"

    @property
    def files_dir(self) -> Path:
        """Get files directory for this architecture."""
        if self._files_dir:
            return self._files_dir
        from claude_agent_framework.config import FILES_DIR

        return FILES_DIR / self.name

    @property
    def business_template(self) -> str | None:
        """Get the business template name."""
        return self._business_template

    @property
    def custom_prompts_dir(self) -> Path | None:
        """Get the custom prompts directory."""
        return self._custom_prompts_dir

    @property
    def prompt_overrides(self) -> dict[str, str]:
        """Get prompt overrides dict."""
        return self._prompt_overrides

    @property
    def template_vars(self) -> dict[str, Any]:
        """Get template variables dict."""
        return self._template_vars

    @property
    def prompt_composer(self):
        """
        Get a PromptComposer configured for this architecture.

        Returns:
            PromptComposer instance for composing layered prompts
        """
        from claude_agent_framework.core.prompt import PromptComposer

        return PromptComposer(
            architecture_prompts_dir=self.prompts_dir,
            business_template=self._business_template,
            custom_prompts_dir=self._custom_prompts_dir,
            prompt_overrides=self._prompt_overrides,
            template_vars=self._template_vars,
        )

    @abstractmethod
    async def execute(
        self,
        prompt: str,
        tracker: SubagentTracker | None = None,
        transcript: TranscriptWriter | None = None,
    ) -> AsyncIterator[Any]:
        """
        Execute the architecture's main logic.

        Args:
            prompt: User input prompt
            tracker: Optional subagent tracker for hook tracking
            transcript: Optional transcript writer for logging

        Yields:
            Messages from Claude SDK response stream
        """
        pass

    @abstractmethod
    def get_agents(self) -> dict[str, AgentDefinitionConfig]:
        """
        Get agent definitions for this architecture.

        Returns:
            Dict mapping agent name to AgentDefinitionConfig
        """
        pass

    def get_lead_prompt(self) -> str:
        """
        Get the lead agent's system prompt.

        Uses PromptComposer to combine architecture core prompt with
        business prompt if configured.

        Override in subclasses to customize.
        """
        # Use PromptComposer if business template or customization is configured
        if self._business_template or self._custom_prompts_dir or self._prompt_overrides:
            return self.prompt_composer.compose("lead_agent")

        # Fallback to legacy behavior for backward compatibility
        prompt_path = self.prompts_dir / "lead_agent.txt"
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8").strip()
        return self._default_lead_prompt()

    def _default_lead_prompt(self) -> str:
        """Default lead agent prompt - override in subclasses."""
        return f"You are a {self.name} architecture coordinator."

    def get_hooks(self) -> dict[str, list]:
        """
        Get hook configuration for the architecture.

        Returns default hooks that can be overridden by subclasses.
        """
        return {}

    async def setup(self) -> None:
        """
        Setup resources before execution.

        Override to perform initialization tasks.
        """
        # Ensure directories exist
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(parents=True, exist_ok=True)

    async def teardown(self) -> None:
        """
        Cleanup resources after execution.

        Override to perform cleanup tasks.
        """
        pass

    def add_plugin(self, plugin: ArchitecturePlugin | BasePlugin) -> None:
        """
        Add a plugin to the architecture.

        Supports both legacy ArchitecturePlugin (Protocol) and new BasePlugin.

        Args:
            plugin: Plugin instance (legacy or new style)
        """
        from claude_agent_framework.plugins.base import BasePlugin

        if isinstance(plugin, BasePlugin):
            # New style plugin
            self._plugin_manager.register(plugin)
        elif isinstance(plugin, ArchitecturePlugin):
            # Legacy style plugin
            self._plugins.append(plugin)
        else:
            raise TypeError(f"Plugin must be BasePlugin or ArchitecturePlugin, got {type(plugin)}")

    def remove_plugin(self, plugin: ArchitecturePlugin | BasePlugin) -> None:
        """
        Remove a plugin from the architecture.

        Args:
            plugin: Plugin instance to remove
        """
        from claude_agent_framework.plugins.base import BasePlugin

        if isinstance(plugin, BasePlugin):
            self._plugin_manager.unregister(plugin)
        elif plugin in self._plugins:
            self._plugins.remove(plugin)

    @property
    def plugin_manager(self):
        """
        Get the plugin manager instance.

        Returns:
            PluginManager instance for advanced plugin management
        """
        return self._plugin_manager

    @property
    def dynamic_agents(self):
        """
        Get the dynamic agent registry.

        Returns:
            DynamicAgentRegistry instance for runtime agent management
        """
        return self._dynamic_agents

    def add_agent(
        self,
        name: str,
        description: str,
        tools: list[str],
        prompt: str,
        model: str = "haiku",
    ) -> None:
        """
        Add an agent dynamically at runtime.

        This allows adding new agents without modifying the architecture class.
        Dynamic agents are merged with static agents from get_agents().

        Args:
            name: Unique agent name (used as subagent_type)
            description: Description of when to use this agent
            tools: List of allowed tool names
            prompt: Agent system prompt
            model: Model to use (default: haiku)

        Raises:
            AgentConfigError: If configuration is invalid
            ValueError: If agent name already exists

        Example:
            >>> session = init("research")
            >>> session.architecture.add_agent(
            ...     name="social_analyst",
            ...     description="Analyze social media trends",
            ...     tools=["WebSearch", "Write"],
            ...     prompt="You analyze social media trends...",
            ...     model="haiku"
            ... )
        """
        self._dynamic_agents.register(
            name=name,
            description=description,
            tools=tools,
            prompt=prompt,
            model=model,
        )

    def remove_agent(self, name: str) -> None:
        """
        Remove a dynamically registered agent.

        Args:
            name: Agent name to remove

        Raises:
            KeyError: If agent not found in dynamic registry

        Example:
            >>> session.architecture.remove_agent("social_analyst")
        """
        self._dynamic_agents.unregister(name)

    def list_dynamic_agents(self) -> list[str]:
        """
        List all dynamically registered agent names.

        Returns:
            List of dynamic agent names

        Example:
            >>> session.architecture.list_dynamic_agents()
            ['social_analyst', 'custom_agent']
        """
        return self._dynamic_agents.list_agents()

    def _apply_before_execute(self, prompt: str) -> str:
        """Apply all plugin before_execute hooks."""
        for plugin in self._plugins:
            prompt = plugin.on_before_execute(prompt)
        return prompt

    def _apply_after_stage(self, stage: str, result: Any) -> Any:
        """Apply all plugin after_stage hooks."""
        for plugin in self._plugins:
            result = plugin.on_after_stage(stage, result)
        return result

    def _apply_on_error(self, error: Exception) -> bool:
        """Apply all plugin on_error hooks. Returns True if should continue."""
        for plugin in self._plugins:
            if not plugin.on_error(error):
                return False
        return True

    def get_result(self) -> Any:
        """Get the final result after execution."""
        return self._result

    def to_sdk_agents(self) -> dict[str, Any]:
        """
        Convert agent configs to Claude SDK AgentDefinition format.

        Uses PromptComposer to combine architecture core prompts with
        business prompts if configured.

        Merges static agents from get_agents() with dynamically registered agents.
        Dynamic agents take precedence if names conflict.

        Returns:
            Dict suitable for ClaudeAgentOptions.agents parameter
        """
        from claude_agent_sdk import AgentDefinition

        # Get composer for layered prompt composition
        composer = self.prompt_composer

        # Start with static agents
        agents = self.get_agents()
        result = {}

        for name, config in agents.items():
            # Use PromptComposer if business template or customization is configured
            if self._business_template or self._custom_prompts_dir or self._prompt_overrides:
                prompt = composer.compose(name)
            else:
                # Fallback to legacy behavior for backward compatibility
                prompt = config.load_prompt(self.prompts_dir)

            result[name] = AgentDefinition(
                description=config.description,
                tools=config.tools,
                prompt=prompt,
                model=self.model_config.get_model(name),
            )

        # Merge dynamic agents (they override static ones with same name)
        dynamic_agents = self._dynamic_agents.get_all()
        result.update(dynamic_agents)

        return result

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r})>"
