"""
Base architecture abstraction.

Provides abstract base class that all architecture implementations must inherit.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncIterator, Protocol, runtime_checkable

if TYPE_CHECKING:
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
    ) -> None:
        """
        Initialize architecture.

        Args:
            model_config: Model configuration for agents
            prompts_dir: Directory containing prompt files
            files_dir: Working directory for file operations
        """
        self.model_config = model_config or AgentModelConfig()
        self._prompts_dir = prompts_dir
        self._files_dir = files_dir
        self._plugins: list[ArchitecturePlugin] = []
        self._result: Any = None

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

        Override in subclasses to customize.
        """
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

    def add_plugin(self, plugin: ArchitecturePlugin) -> None:
        """Add a plugin to the architecture."""
        self._plugins.append(plugin)

    def remove_plugin(self, plugin: ArchitecturePlugin) -> None:
        """Remove a plugin from the architecture."""
        if plugin in self._plugins:
            self._plugins.remove(plugin)

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

        Returns:
            Dict suitable for ClaudeAgentOptions.agents parameter
        """
        from claude_agent_sdk import AgentDefinition

        agents = self.get_agents()
        return {
            name: AgentDefinition(
                description=config.description,
                tools=config.tools,
                prompt=config.load_prompt(self.prompts_dir),
                model=self.model_config.get_model(name),
            )
            for name, config in agents.items()
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r})>"
