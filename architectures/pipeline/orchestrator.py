"""
Pipeline architecture orchestrator.

Implements sequential stage processing:
1. Each stage processes input and produces output
2. Output flows to next stage as input
3. Final stage produces the result
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncIterator

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, HookMatcher

from claude_agent_framework.architectures.pipeline.config import PipelineConfig
from claude_agent_framework.core.base import (
    AgentDefinitionConfig,
    AgentModelConfig,
    BaseArchitecture,
)
from claude_agent_framework.core.registry import register_architecture

if TYPE_CHECKING:
    from claude_agent_framework.utils import SubagentTracker, TranscriptWriter


@register_architecture("pipeline")
class PipelineArchitecture(BaseArchitecture):
    """
    Pipeline architecture for sequential processing.

    Pattern: Sequential Stage Processing
    - Architect: Design implementation approach
    - Coder: Implement the design
    - Reviewer: Code quality review
    - Tester: Write and run tests

    Each stage's output becomes input for the next.

    Usage:
        arch = PipelineArchitecture()
        async for msg in arch.execute("Implement user authentication"):
            print(msg)
    """

    name = "pipeline"
    description = "Sequential stage processing for code review and content creation"

    def __init__(
        self,
        config: PipelineConfig | None = None,
        model_config: AgentModelConfig | None = None,
        prompts_dir: Path | None = None,
        files_dir: Path | None = None,
        stages: list[str] | None = None,
    ) -> None:
        """
        Initialize pipeline architecture.

        Args:
            config: Pipeline-specific configuration
            model_config: Model configuration
            prompts_dir: Custom prompts directory
            files_dir: Custom files directory
            stages: Custom stage names (uses config stages if None)
        """
        self.pipeline_config = config or PipelineConfig()

        # Allow overriding stages via constructor
        if stages:
            self.pipeline_config.stages = [
                s for s in self.pipeline_config.stages if s.name in stages
            ]

        if model_config is None:
            model_config = AgentModelConfig(default=self.pipeline_config.lead_model)

        super().__init__(
            model_config=model_config,
            prompts_dir=prompts_dir,
            files_dir=files_dir,
        )

        self._stage_results: dict[str, Any] = {}

    def get_agents(self) -> dict[str, AgentDefinitionConfig]:
        """Get agent definitions for all pipeline stages."""
        return {stage.agent.name: stage.agent for stage in self.pipeline_config.stages}

    def get_lead_prompt(self) -> str:
        """Get lead agent prompt for pipeline coordination."""
        base_prompt = super().get_lead_prompt()

        # Build stage description
        stage_names = self.pipeline_config.get_stage_names()
        stages_desc = " → ".join(stage_names)

        pipeline_context = f"""
# Pipeline Coordinator

You are the coordinator for the Pipeline architecture, responsible for dispatching stage agents in sequence.

# Execution Flow
{stages_desc}

# Rules
1. Execute each stage in order
2. After each stage completes, pass its output to the next stage
3. Use the Task tool to dispatch each stage agent
4. Wait for each stage to complete before proceeding to the next

# Available Stages
"""
        for stage in self.pipeline_config.stages:
            pipeline_context += f"\n## {stage.name}\n- {stage.agent.description}\n"

        return base_prompt + pipeline_context

    async def execute(
        self,
        prompt: str,
        tracker: SubagentTracker | None = None,
        transcript: TranscriptWriter | None = None,
    ) -> AsyncIterator[Any]:
        """
        Execute pipeline stages sequentially.

        Args:
            prompt: Initial task description
            tracker: Optional subagent tracker
            transcript: Optional transcript writer

        Yields:
            Messages from each stage's execution
        """
        prompt = self._apply_before_execute(prompt)
        hooks = self._build_hooks(tracker)
        lead_prompt = self.get_lead_prompt()
        agents = self.to_sdk_agents()

        options = ClaudeAgentOptions(
            permission_mode="bypassPermissions",
            setting_sources=["project"],
            system_prompt=lead_prompt,
            allowed_tools=["Task"],
            agents=agents,
            hooks=hooks,
            model=self.model_config.default,
        )

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt=prompt)

            async for msg in client.receive_response():
                yield msg

                if hasattr(msg, "content") and msg.content:
                    self._result = msg.content

    def _build_hooks(self, tracker: SubagentTracker | None) -> dict[str, list]:
        """Build hook configuration."""
        hooks: dict[str, list] = {}

        if tracker:
            hooks["PreToolUse"] = [
                HookMatcher(matcher=None, hooks=[tracker.pre_tool_use_hook])
            ]
            hooks["PostToolUse"] = [
                HookMatcher(matcher=None, hooks=[tracker.post_tool_use_hook])
            ]

        return hooks

    def get_stage_result(self, stage_name: str) -> Any:
        """Get result from a specific stage."""
        return self._stage_results.get(stage_name)

    def configure_stages(self, stages: list[str]) -> None:
        """
        Configure which stages to run.

        Args:
            stages: List of stage names to include
        """
        self.pipeline_config.stages = [
            s for s in self.pipeline_config.stages if s.name in stages
        ]

    def transform_stage_output(self, stage: str, output: str) -> str:
        """
        Transform stage output before passing to next stage.

        Override in subclasses for custom transformation.

        Args:
            stage: Stage name
            output: Stage output content

        Returns:
            Transformed output for next stage
        """
        return f"## {stage} Stage Output\n{output}\n\nPlease continue with the next stage based on the above results."
