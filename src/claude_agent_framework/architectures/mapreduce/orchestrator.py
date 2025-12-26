"""
MapReduce architecture orchestrator.

Implements parallel map with aggregation:
1. Splitter divides task into chunks
2. Mappers process chunks in parallel
3. Reducer aggregates all results
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, HookMatcher

from claude_agent_framework.architectures.mapreduce.config import MapReduceConfig
from claude_agent_framework.architectures.mapreduce.splitter import TaskSplitter
from claude_agent_framework.core.base import (
    AgentDefinitionConfig,
    AgentModelConfig,
    BaseArchitecture,
)
from claude_agent_framework.core.registry import register_architecture

if TYPE_CHECKING:
    from claude_agent_framework.utils import SubagentTracker, TranscriptWriter


@register_architecture("mapreduce")
class MapReduceArchitecture(BaseArchitecture):
    """
    MapReduce architecture for parallel processing.

    Pattern: Parallel Map with Aggregation
    - Splitter: Divides task into chunks
    - Mappers: Process chunks in parallel
    - Reducer: Aggregates results

    Usage:
        arch = MapReduceArchitecture()
        async for msg in arch.execute("Analyze all Python files"):
            print(msg)
    """

    name = "mapreduce"
    description = "Parallel map with aggregation for large-scale analysis"

    def __init__(
        self,
        config: MapReduceConfig | None = None,
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
        Initialize mapreduce architecture.

        Args:
            config: MapReduce-specific configuration
            model_config: Model configuration
            prompts_dir: Custom prompts directory
            files_dir: Custom files directory
            business_template: Name of business template to use (optional)
            custom_prompts_dir: Application-level custom prompts directory (optional)
            prompt_overrides: Dict of agent_name -> override prompt content
            template_vars: Dict of template variables for ${var} substitution
        """
        self.mapreduce_config = config or MapReduceConfig()
        self.splitter = TaskSplitter(chunk_size=self.mapreduce_config.chunk_size)

        if model_config is None:
            model_config = AgentModelConfig(
                default=self.mapreduce_config.mapper_model,
                overrides=self.mapreduce_config.get_model_overrides(),
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

        self._mapper_results: list[str] = []

    def get_agents(self) -> dict[str, AgentDefinitionConfig]:
        """Get mapper and reducer agent definitions."""
        return {
            "mapper": AgentDefinitionConfig(
                name="mapper",
                description="Process assigned data chunks and generate intermediate results",
                tools=["Read", "Glob", "Grep", "Write"],
                prompt_file="mapper.txt",
            ),
            "reducer": AgentDefinitionConfig(
                name="reducer",
                description="Aggregate all mapper results and generate final output",
                tools=["Read", "Glob", "Write"],
                prompt_file="reducer.txt",
            ),
        }

    def get_lead_prompt(self) -> str:
        """Get lead agent prompt for mapreduce coordination."""
        base_prompt = super().get_lead_prompt()

        return (
            base_prompt
            + f"""
# MapReduce Coordinator

You are responsible for coordinating large-scale parallel processing tasks, splitting tasks for parallel processing then aggregating results.

# Rules
1. Maximum parallel mappers: {self.mapreduce_config.max_mappers}
2. Chunk size per mapper: {self.mapreduce_config.chunk_size}
3. Split strategy: {self.mapreduce_config.split_strategy}
4. Aggregation method: {self.mapreduce_config.aggregation_method}

# Workflow

```
# Phase 1: Split
Determine data to process based on task type (file list, topic list, etc.)
Split data into multiple chunks

# Phase 2: Map (parallel)
for chunk in chunks:
    Task(mapper, chunk)  # Dispatch in parallel

Wait for all mappers to complete

# Phase 3: Reduce
Task(reducer, all_mapper_results)
```

# Available Agents

## mapper
- Responsibility: Process single data chunk
- Input: Data chunk (file list/topic/content fragment)
- Output: Processing result

## reducer
- Responsibility: Aggregate all results
- Input: All mapper outputs
- Output: Final aggregated result

# Split Strategies

## files
- Use for: Code analysis, batch file processing
- Each mapper processes a group of files

## topic
- Use for: Multi-perspective research
- Each mapper researches one aspect

## content
- Use for: Long text processing
- Each mapper processes one text fragment

# Output Specification

```markdown
# MapReduce Execution Report

## Task
[Task description]

## Split Result
- Strategy: [files/topic/content]
- Number of chunks: N
- Chunk size: ~{self.mapreduce_config.chunk_size}

## Map Phase
| Mapper | Content | Result Summary |
|--------|---------|----------------|
| 1 | [content] | [summary] |
| 2 | [content] | [summary] |
| ... | ... | ... |

## Reduce Phase
[Aggregated result]

## Final Output
[Final result or output file location]
```
"""
        )

    async def execute(
        self,
        prompt: str,
        tracker: SubagentTracker | None = None,
        transcript: TranscriptWriter | None = None,
    ) -> AsyncIterator[Any]:
        """Execute mapreduce workflow."""
        prompt = self._apply_before_execute(prompt)
        hooks = self._build_hooks(tracker)
        lead_prompt = self.get_lead_prompt()
        agents = self.to_sdk_agents()

        options = ClaudeAgentOptions(
            permission_mode="bypassPermissions",
            setting_sources=["project"],
            system_prompt=lead_prompt,
            allowed_tools=["Task", "Glob"],  # Lead needs Glob for file discovery
            agents=agents,
            hooks=hooks,
            model=self.model_config.default,
        )

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt=f"MapReduce Task: {prompt}")

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

    def get_mapper_results(self) -> list[str]:
        """Get results from all mappers."""
        return self._mapper_results
