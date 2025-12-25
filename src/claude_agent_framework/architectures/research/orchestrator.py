"""
Research architecture orchestrator.

Implements master-worker coordination pattern:
1. Lead agent decomposes research task into subtopics
2. Multiple researcher agents gather information in parallel
3. Data analyst processes and visualizes findings
4. Report writer generates final output
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, HookMatcher

from claude_agent_framework.architectures.research.config import ResearchConfig
from claude_agent_framework.core.base import (
    AgentDefinitionConfig,
    AgentModelConfig,
    BaseArchitecture,
)
from claude_agent_framework.core.registry import register_architecture

if TYPE_CHECKING:
    from claude_agent_framework.utils import SubagentTracker, TranscriptWriter


@register_architecture("research")
class ResearchArchitecture(BaseArchitecture):
    """
    Research architecture for deep research tasks.

    Pattern: Master-Worker Coordination
    - Lead agent: Task decomposition and orchestration
    - Researchers: Parallel information gathering
    - Data analyst: Processing and visualization
    - Report writer: Final report generation

    Usage:
        arch = ResearchArchitecture()
        async for msg in arch.execute("Research AI market trends"):
            print(msg)
    """

    name = "research"
    description = "Master-worker pattern for deep research with parallel data gathering"

    def __init__(
        self,
        config: ResearchConfig | None = None,
        model_config: AgentModelConfig | None = None,
        prompts_dir: Path | None = None,
        files_dir: Path | None = None,
    ) -> None:
        """
        Initialize research architecture.

        Args:
            config: Research-specific configuration
            model_config: Model configuration (overridden by config if provided)
            prompts_dir: Custom prompts directory
            files_dir: Custom files directory
        """
        self.research_config = config or ResearchConfig()

        # Build model config from research config
        if model_config is None:
            model_config = AgentModelConfig(
                default=self.research_config.lead_model,
                overrides=self.research_config.get_model_overrides(),
            )

        super().__init__(
            model_config=model_config,
            prompts_dir=prompts_dir,
            files_dir=files_dir,
        )

    def get_agents(self) -> dict[str, AgentDefinitionConfig]:
        """Get research agent definitions."""
        return {
            "researcher": AgentDefinitionConfig(
                name="researcher",
                description="Gather research data via web search, save to files/research_notes/",
                tools=["WebSearch", "Write"],
                prompt_file="researcher.txt",
            ),
            "data-analyst": AgentDefinitionConfig(
                name="data-analyst",
                description="Analyze research data and generate visualizations, save to files/charts/",
                tools=["Glob", "Read", "Bash", "Write"],
                prompt_file="data_analyst.txt",
            ),
            "report-writer": AgentDefinitionConfig(
                name="report-writer",
                description="Generate final PDF reports, save to files/reports/",
                tools=["Skill", "Write", "Glob", "Read", "Bash"],
                prompt_file="report_writer.txt",
            ),
        }

    def get_lead_prompt(self) -> str:
        """Get lead agent prompt with research-specific context."""
        base_prompt = super().get_lead_prompt()

        # Add research depth context
        depth_context = (
            f"\n\n# Research Depth\nCurrently set to {self.research_config.research_depth} mode."
        )
        if self.research_config.research_depth == "shallow":
            depth_context += (
                "\n- Quick overview, 2-3 key data points\n- Dispatch 2 researchers in parallel"
            )
        elif self.research_config.research_depth == "deep":
            depth_context += (
                "\n- Deep analysis, 15+ data points\n- Dispatch 4 researchers in parallel"
            )
        else:
            depth_context += (
                "\n- Standard depth, 5-10 data points\n- Dispatch 3 researchers in parallel"
            )

        return base_prompt + depth_context

    async def setup(self) -> None:
        """Setup research directories."""
        await super().setup()

        # Create research-specific subdirectories
        for subdir in [
            self.research_config.research_notes_dir,
            self.research_config.data_dir,
            self.research_config.charts_dir,
            self.research_config.reports_dir,
        ]:
            (self.files_dir / subdir).mkdir(parents=True, exist_ok=True)

    async def execute(
        self,
        prompt: str,
        tracker: SubagentTracker | None = None,
        transcript: TranscriptWriter | None = None,
    ) -> AsyncIterator[Any]:
        """
        Execute research workflow.

        Args:
            prompt: Research topic or question
            tracker: Optional subagent tracker
            transcript: Optional transcript writer

        Yields:
            Messages from Claude SDK response stream
        """
        # Apply plugins
        prompt = self._apply_before_execute(prompt)

        # Build hooks
        hooks = self._build_hooks(tracker)

        # Get lead prompt and agents
        lead_prompt = self.get_lead_prompt()
        agents = self.to_sdk_agents()

        # Configure SDK options
        options = ClaudeAgentOptions(
            permission_mode="bypassPermissions",
            setting_sources=["project"],
            system_prompt=lead_prompt,
            allowed_tools=["Task"],  # Lead only uses Task tool
            agents=agents,
            hooks=hooks,
            model=self.model_config.default,
        )

        # Execute with SDK client
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt=prompt)

            async for msg in client.receive_response():
                yield msg

                # Track result
                if hasattr(msg, "content") and msg.content:
                    self._result = msg.content

    def _build_hooks(self, tracker: SubagentTracker | None) -> dict[str, list]:
        """Build hook configuration."""
        hooks: dict[str, list] = {}

        if tracker:
            hooks["PreToolUse"] = [
                HookMatcher(
                    matcher=None,
                    hooks=[tracker.pre_tool_use_hook],
                )
            ]
            hooks["PostToolUse"] = [
                HookMatcher(
                    matcher=None,
                    hooks=[tracker.post_tool_use_hook],
                )
            ]

        # Merge with custom hooks
        custom_hooks = self.get_hooks()
        for hook_type, matchers in custom_hooks.items():
            if hook_type not in hooks:
                hooks[hook_type] = []
            hooks[hook_type].extend(matchers)

        return hooks
