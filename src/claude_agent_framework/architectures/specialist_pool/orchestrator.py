"""
Specialist Pool architecture orchestrator.

Implements expert routing and dispatch:
1. Router analyzes incoming query
2. Selects appropriate expert(s)
3. Dispatches query to expert(s)
4. Aggregates responses
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, HookMatcher

from claude_agent_framework.architectures.specialist_pool.config import (
    SpecialistPoolConfig,
)
from claude_agent_framework.architectures.specialist_pool.router import ExpertRouter
from claude_agent_framework.core.base import (
    AgentDefinitionConfig,
    AgentModelConfig,
    BaseArchitecture,
)
from claude_agent_framework.core.registry import register_architecture

if TYPE_CHECKING:
    from claude_agent_framework.utils import SubagentTracker, TranscriptWriter


@register_architecture("specialist_pool")
class SpecialistPoolArchitecture(BaseArchitecture):
    """
    Specialist Pool architecture for expert routing.

    Pattern: Expert Pool Dispatch
    - Router: Analyzes query and selects experts
    - Experts: Domain specialists handle specific topics
    - Aggregator: Combines expert responses

    Usage:
        arch = SpecialistPoolArchitecture()
        async for msg in arch.execute("How do I fix this SQL injection?"):
            print(msg)
    """

    name = "specialist_pool"
    description = "Expert routing and dispatch for technical support and diagnostics"

    def __init__(
        self,
        config: SpecialistPoolConfig | None = None,
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
        Initialize specialist pool architecture.

        Args:
            config: Specialist pool configuration
            model_config: Model configuration
            prompts_dir: Custom prompts directory
            files_dir: Custom files directory
            business_template: Name of business template to use (optional)
            custom_prompts_dir: Application-level custom prompts directory (optional)
            prompt_overrides: Dict of agent_name -> override prompt content
            template_vars: Dict of template variables for ${var} substitution
        """
        self.pool_config = config or SpecialistPoolConfig()
        self.router = ExpertRouter(self.pool_config)

        if model_config is None:
            model_config = AgentModelConfig(default=self.pool_config.router_model)

        super().__init__(
            model_config=model_config,
            prompts_dir=prompts_dir,
            files_dir=files_dir,
            business_template=business_template,
            custom_prompts_dir=custom_prompts_dir,
            prompt_overrides=prompt_overrides,
            template_vars=template_vars,
        )

    def get_agents(self) -> dict[str, AgentDefinitionConfig]:
        """Get all expert agent definitions."""
        return {expert.agent.name: expert.agent for expert in self.pool_config.experts}

    def get_lead_prompt(self) -> str:
        """Get lead agent prompt for routing."""
        base_prompt = super().get_lead_prompt()

        # Build expert descriptions
        expert_desc = "\n".join(
            f"## {e.name}\n- Domain: {e.domain}\n- Responsibility: {e.agent.description}"
            for e in self.pool_config.experts
        )

        return (
            base_prompt
            + f"""
# Specialist Pool Coordinator

You are the routing coordinator for the expert pool architecture, responsible for analyzing user questions and dispatching to appropriate experts.

# Rules
1. Analyze user question and determine which experts are needed
2. Use the Task tool to dispatch questions to experts
3. Can dispatch to multiple experts in parallel
4. Aggregate expert responses for the user

# Available Experts

{expert_desc}

# Routing Strategy
- Match experts based on question keywords
- Complex questions can be dispatched to multiple experts
- Security-related questions should prioritize security_expert

# Output Specification
1. Explain selected experts and reasoning
2. Dispatch tasks to experts
3. Aggregate expert responses
"""
        )

    async def execute(
        self,
        prompt: str,
        tracker: SubagentTracker | None = None,
        transcript: TranscriptWriter | None = None,
    ) -> AsyncIterator[Any]:
        """Execute expert routing and dispatch."""
        prompt = self._apply_before_execute(prompt)

        # Pre-route for context (optional, routing done by lead agent)
        routing = self.router.route(prompt)

        hooks = self._build_hooks(tracker)
        lead_prompt = self.get_lead_prompt()

        # Add routing context to prompt
        enhanced_prompt = f"""
User Question: {prompt}

Routing Analysis:
- Recommended Experts: {", ".join(routing.experts)}
- Confidence: {routing.confidence:.2f}
- Reasoning: {routing.reasoning}

Please dispatch tasks to appropriate experts based on the above analysis.
"""

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
            await client.query(prompt=enhanced_prompt)

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

    def add_expert(self, expert_config) -> None:
        """Add a new expert to the pool."""
        self.router.add_expert(expert_config)

    def remove_expert(self, name: str) -> bool:
        """Remove an expert from the pool."""
        return self.router.remove_expert(name)
