"""
Debate architecture orchestrator.

Implements pro-con deliberation:
1. Proponent presents supporting arguments
2. Opponent presents counter-arguments
3. Multiple rounds of debate
4. Judge evaluates and decides
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, HookMatcher

from claude_agent_framework.architectures.debate.config import DebateConfig
from claude_agent_framework.core.base import (
    AgentDefinitionConfig,
    AgentModelConfig,
    BaseArchitecture,
)
from claude_agent_framework.core.registry import register_architecture

if TYPE_CHECKING:
    from claude_agent_framework.utils import SubagentTracker, TranscriptWriter


@dataclass
class DebateRound:
    """Record of a single debate round."""

    round_number: int
    proponent_argument: str
    opponent_argument: str


@dataclass
class Verdict:
    """Judge's final verdict."""

    decision: str  # pro, con, neutral
    confidence: str  # high, medium, low
    reasoning: str
    scores: dict[str, float] = field(default_factory=dict)


@register_architecture("debate")
class DebateArchitecture(BaseArchitecture):
    """
    Debate architecture for decision support.

    Pattern: Pro-Con Deliberation
    - Proponent: Argues in favor
    - Opponent: Argues against
    - Judge: Evaluates and decides

    Usage:
        arch = DebateArchitecture()
        async for msg in arch.execute("Should we use microservices?"):
            print(msg)
    """

    name = "debate"
    description = "Pro-con deliberation with judge for decision support and risk assessment"

    def __init__(
        self,
        config: DebateConfig | None = None,
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
        Initialize debate architecture.

        Args:
            config: Debate-specific configuration
            model_config: Model configuration
            prompts_dir: Custom prompts directory
            files_dir: Custom files directory
            business_template: Name of business template to use (optional)
            custom_prompts_dir: Application-level custom prompts directory (optional)
            prompt_overrides: Dict of agent_name -> override prompt content
            template_vars: Dict of template variables for ${var} substitution
        """
        self.debate_config = config or DebateConfig()

        if model_config is None:
            model_config = AgentModelConfig(
                default=self.debate_config.proponent_model,
                overrides=self.debate_config.get_model_overrides(),
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

        self._debate_history: list[DebateRound] = []
        self._verdict: Verdict | None = None

    def get_agents(self) -> dict[str, AgentDefinitionConfig]:
        """Get debate agent definitions."""
        return {
            "proponent": AgentDefinitionConfig(
                name="proponent",
                description="Argue the pro position, provide supporting arguments",
                tools=["Read", "WebSearch"],
                prompt_file="proponent.txt",
            ),
            "opponent": AgentDefinitionConfig(
                name="opponent",
                description="Argue the con position, provide counter-arguments",
                tools=["Read", "WebSearch"],
                prompt_file="opponent.txt",
            ),
            "judge": AgentDefinitionConfig(
                name="judge",
                description="Evaluate both sides' arguments and render final verdict",
                tools=["Read"],
                prompt_file="judge.txt",
            ),
        }

    def get_lead_prompt(self) -> str:
        """Get lead agent prompt for debate coordination."""
        base_prompt = super().get_lead_prompt()

        return (
            base_prompt
            + f"""
# Debate Coordinator

You are responsible for coordinating the debate between proponent and opponent, then requesting the judge to render a verdict.

# Debate Rules
1. Number of rounds: {self.debate_config.debate_rounds}
2. Each round: Proponent speaks → Opponent speaks
3. After all rounds, request judge to render verdict

# Workflow

```
for round in range(debate_rounds):
    # Proponent argues
    pro_arg = Task(proponent, topic + opponent_points)

    # Opponent rebuts
    con_arg = Task(opponent, topic + proponent_points)

# Judge renders verdict
verdict = Task(judge, all_arguments)
```

# Available Agents

## proponent (Pro Side)
- Responsibility: Support argument
- Provide evidence and reasoning supporting the position

## opponent (Con Side)
- Responsibility: Opposition argument
- Provide evidence and reasoning opposing the position

## judge
- Responsibility: Render verdict
- Evaluate both sides' arguments and provide final conclusion

# Output Specification
After each round, report:
- Proponent's main arguments
- Opponent's main arguments
- Current status

Finally output the judge's verdict.
"""
        )

    async def execute(
        self,
        prompt: str,
        tracker: SubagentTracker | None = None,
        transcript: TranscriptWriter | None = None,
    ) -> AsyncIterator[Any]:
        """Execute debate workflow."""
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
            await client.query(prompt=f"Debate Topic: {prompt}")

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

    def get_debate_history(self) -> list[DebateRound]:
        """Get history of all debate rounds."""
        return self._debate_history

    def get_verdict(self) -> Verdict | None:
        """Get the final verdict."""
        return self._verdict
