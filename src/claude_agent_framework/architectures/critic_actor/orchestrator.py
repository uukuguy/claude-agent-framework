"""
Critic-Actor architecture orchestrator.

Implements generate-evaluate loop:
1. Actor generates content
2. Critic evaluates with feedback
3. Actor improves based on feedback
4. Repeat until quality threshold or max iterations
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, HookMatcher

from claude_agent_framework.architectures.critic_actor.config import CriticActorConfig
from claude_agent_framework.core.base import (
    AgentDefinitionConfig,
    AgentModelConfig,
    BaseArchitecture,
)
from claude_agent_framework.core.registry import register_architecture

if TYPE_CHECKING:
    from claude_agent_framework.utils import SubagentTracker, TranscriptWriter


@dataclass
class IterationRecord:
    """Record of a single iteration."""

    iteration: int
    actor_output: str
    critic_feedback: str
    quality_score: float
    approved: bool


@register_architecture("critic_actor")
class CriticActorArchitecture(BaseArchitecture):
    """
    Critic-Actor architecture for iterative improvement.

    Pattern: Generate-Evaluate Loop
    - Actor: Generates or improves content
    - Critic: Evaluates and provides feedback
    - Loop: Iterate until quality threshold

    Usage:
        arch = CriticActorArchitecture()
        async for msg in arch.execute("Write a Python function for sorting"):
            print(msg)
    """

    name = "critic_actor"
    description = "Generate-evaluate iteration loop for code optimization and quality"

    def __init__(
        self,
        config: CriticActorConfig | None = None,
        model_config: AgentModelConfig | None = None,
        prompts_dir: Path | None = None,
        files_dir: Path | None = None,
        # Business template and prompt customization
        business_template: str | None = None,
        custom_prompts_dir: Path | str | None = None,
        prompt_overrides: dict[str, str] | None = None,
        template_vars: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize critic-actor architecture.

        Args:
            config: Critic-Actor specific configuration
            model_config: Model configuration
            prompts_dir: Custom prompts directory
            files_dir: Custom files directory
            business_template: Name of business template to use (optional)
            custom_prompts_dir: Application-level custom prompts directory (optional)
            prompt_overrides: Dict of agent_name -> override prompt content
            template_vars: Dict of template variables for ${var} substitution
        """
        self.critic_config = config or CriticActorConfig()

        if model_config is None:
            model_config = AgentModelConfig(
                default=self.critic_config.actor_model,
                overrides=self.critic_config.get_model_overrides(),
            )

        super().__init__(
            model_config=model_config,
            prompts_dir=prompts_dir,
            files_dir=files_dir,
            business_template=business_template,
            custom_prompts_dir=custom_prompts_dir,
            prompt_overrides=prompt_overrides,
            template_vars=template_vars,
        )

        self._iteration_history: list[IterationRecord] = []

    def get_agents(self) -> dict[str, AgentDefinitionConfig]:
        """Get actor and critic agent definitions."""
        return {
            "actor": AgentDefinitionConfig(
                name="actor",
                description="Generate or improve content, iterate based on feedback",
                tools=["Read", "Write", "Edit"],
                prompt_file="actor.txt",
            ),
            "critic": AgentDefinitionConfig(
                name="critic",
                description="Evaluate content quality and provide improvement feedback",
                tools=["Read", "Glob"],
                prompt_file="critic.txt",
            ),
        }

    def get_lead_prompt(self) -> str:
        """Get lead agent prompt for critic-actor coordination."""
        base_prompt = super().get_lead_prompt()

        return (
            base_prompt
            + f"""
# Critic-Actor Coordinator

You are responsible for coordinating the iterative improvement loop between Actor and Critic.

# Rules
1. Maximum iterations: {self.critic_config.max_iterations}
2. Quality threshold: {self.critic_config.quality_threshold}
3. Must first dispatch Actor to generate content
4. Then dispatch Critic to evaluate
5. If quality is below threshold, continue iterating

# Workflow
```
while iteration < max_iterations:
    content = Actor.generate(task, feedback)
    evaluation = Critic.evaluate(content)
    if evaluation.score >= threshold:
        break
    feedback = evaluation.feedback
```

# Available Agents

## actor
- Responsibility: Generate or improve content
- Input: Task description + previous feedback (if any)
- Output: Generated content

## critic
- Responsibility: Evaluate quality and provide feedback
- Input: Content to evaluate
- Output: Score + improvement suggestions

# Final Output
- Final version of content
- Number of iterations
- Final quality score
"""
        )

    async def execute(
        self,
        prompt: str,
        tracker: SubagentTracker | None = None,
        transcript: TranscriptWriter | None = None,
    ) -> AsyncIterator[Any]:
        """Execute critic-actor iteration loop."""
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
            hooks["PreToolUse"] = [HookMatcher(matcher=None, hooks=[tracker.pre_tool_use_hook])]
            hooks["PostToolUse"] = [HookMatcher(matcher=None, hooks=[tracker.post_tool_use_hook])]

        return hooks

    def get_iteration_history(self) -> list[IterationRecord]:
        """Get history of all iterations."""
        return self._iteration_history

    def clear_history(self) -> None:
        """Clear iteration history."""
        self._iteration_history.clear()
