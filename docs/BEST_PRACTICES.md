# Claude Agent Framework - Best Practices Guide

> Comprehensive development guide for building multi-agent systems with Claude Agent Framework

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Architecture Patterns](#2-architecture-patterns)
3. [Core Components](#3-core-components)
4. [Multi-Agent Orchestration](#4-multi-agent-orchestration)
5. [Hook Mechanism](#5-hook-mechanism)
6. [Tool Assignment](#6-tool-assignment)
7. [Prompt Engineering](#7-prompt-engineering)
8. [State Management](#8-state-management)
9. [Error Handling](#9-error-handling)
10. [Logging and Auditing](#10-logging-and-auditing)
11. [Configuration Management](#11-configuration-management)
12. [Complete Examples](#12-complete-examples)

---

## 1. Design Philosophy

### 1.1 Why Multi-Agent?

Complex tasks often require multiple specialized capabilities that a single LLM prompt cannot effectively handle. Consider a research task: it needs web searching, data analysis, and report writing - each requiring different tools, prompts, and even models. A monolithic approach leads to:

- **Prompt bloat**: One prompt trying to do everything becomes unwieldy
- **Tool overload**: Agent has access to tools it shouldn't use at certain stages
- **Quality degradation**: Jack-of-all-trades prompts underperform specialized ones
- **Cost inefficiency**: Using expensive models for simple subtasks

The solution: **agent specialization and orchestration** - decompose complex tasks into specialized agents coordinated by a lead agent.

### 1.2 Framework Overview

Claude Agent Framework provides **7 distinct orchestration patterns** for multi-agent systems. While all architectures share common design principles, each implements a unique workflow pattern suited to specific problem domains.

### 1.3 Orchestration Patterns

Each architecture implements a distinct orchestration pattern:

| Architecture | Pattern | Flow | Best For |
|--------------|---------|------|----------|
| **Research** | Fan-out/Fan-in | Lead → [Workers parallel] → Aggregator | Data gathering, deep research |
| **Pipeline** | Sequential Chain | Stage A → B → C → D | Code review, content creation |
| **Critic-Actor** | Iterative Refinement | Generate ↔ Evaluate (loop) | Quality optimization |
| **Specialist Pool** | Dynamic Routing | Router → Expert(s) → Synthesize | Technical support, Q&A |
| **Debate** | Adversarial Deliberation | Pro ↔ Con (N rounds) → Judge | Decision support |
| **Reflexion** | Self-Improvement Loop | Execute → Reflect → Improve | Complex problem solving |
| **MapReduce** | Divide and Conquer | Split → [Map parallel] → Reduce | Large-scale analysis |

### 1.4 Pattern Diagrams

**Fan-out/Fan-in (Research)**
```
Lead Agent ─┬─→ Worker 1 ─┐
            ├─→ Worker 2 ─┼─→ Aggregator → Output
            └─→ Worker 3 ─┘
```

**Sequential Chain (Pipeline)**
```
Stage A → Stage B → Stage C → Stage D → Output
```

**Iterative Refinement (Critic-Actor)**
```
┌─────────────────────────┐
│  Actor ──→ Critic       │
│    ↑         │          │
│    └─────────┘ (repeat) │
└─────────────────────────┘
```

**Dynamic Routing (Specialist Pool)**
```
Query → Router ─┬─→ Expert A ─┐
                ├─→ Expert B ─┼─→ Synthesizer
                └─→ Expert C ─┘
```

**Adversarial Deliberation (Debate)**
```
Topic → Proponent ↔ Opponent (N rounds) → Judge → Verdict
```

**Self-Improvement Loop (Reflexion)**
```
┌─────────────────────────────────┐
│  Executor → Reflector → Improve │
│      ↑                    │     │
│      └────────────────────┘     │
└─────────────────────────────────┘
```

**Divide and Conquer (MapReduce)**
```
Task → Splitter ─┬─→ Mapper 1 ─┐
                 ├─→ Mapper 2 ─┼─→ Reducer → Result
                 └─→ Mapper 3 ─┘
```

### 1.5 Common Design Principles

Despite different orchestration patterns, all architectures share these core principles:

| Principle | Description | Implementation |
|-----------|-------------|----------------|
| **Separation of Concerns** | Each agent does one thing well | Lead orchestrates, subagents execute specific tasks |
| **Tool Constraints** | Limit available tool sets | Precise `allowed_tools` control per agent |
| **Loose Coupling** | Agents exchange data via filesystem | Standard directory structure + Glob/Read/Write |
| **Observability** | Full trace capability | Hook mechanism + JSONL logging |
| **Cost Optimization** | Choose models wisely | Subagents use Haiku for cost efficiency |
| **Extensibility** | Easy to add new patterns | Registry-based architecture system |
| **Type Safety** | Strong typing throughout | Pydantic models, type hints |

### 1.6 Choosing the Right Pattern

| Scenario | Recommended Pattern | Why |
|----------|---------------------|-----|
| Gathering information from multiple sources | **Research** (Fan-out/Fan-in) | Parallel data collection, then synthesis |
| Step-by-step processing with handoffs | **Pipeline** (Sequential) | Clear stage boundaries, progressive refinement |
| Quality improvement through feedback | **Critic-Actor** (Iterative) | Generate-evaluate loop until threshold met |
| Routing queries to domain experts | **Specialist Pool** (Dynamic) | Match query type to expert capabilities |
| Analyzing pros and cons of decisions | **Debate** (Adversarial) | Structured argumentation, balanced analysis |
| Complex problems requiring reflection | **Reflexion** (Self-Improvement) | Learn from attempts, refine strategy |
| Processing large datasets in parallel | **MapReduce** (Divide-Conquer) | Parallel processing, efficient aggregation |

---

## 2. Architecture Patterns

### 2.1 Pattern Selection Guide

| Pattern | Best For | Key Characteristic |
|---------|----------|-------------------|
| **Research** | Data gathering, analysis | Parallel workers → synthesis |
| **Pipeline** | Sequential workflows | Stage A → Stage B → Stage C |
| **Critic-Actor** | Quality iteration | Generate ↔ Evaluate loop |
| **Specialist Pool** | Expert routing | Dynamic dispatch by domain |
| **Debate** | Decision analysis | Pro ↔ Con with judge |
| **Reflexion** | Complex problem solving | Execute → Reflect → Improve |
| **MapReduce** | Large-scale processing | Split → Map parallel → Reduce |

### 2.2 Pattern Internals

#### Research Pattern

```
                    ┌──────────────┐
                    │  Lead Agent  │
                    │ (Coordinator)│
                    └──────┬───────┘
                           │ Task decomposition
            ┌──────────────┼──────────────┐
            ↓              ↓              ↓
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │Researcher│  │Researcher│  │Researcher│
      │    1     │  │    2     │  │    3     │
      └────┬─────┘  └────┬─────┘  └────┬─────┘
           │             │             │
           └──────┬──────┴──────┬──────┘
                  ↓             ↓
           files/research_notes/*.md
                        ↓
                ┌──────────────┐
                │ Data Analyst │
                └──────┬───────┘
                       ↓
                files/charts/*.png
                       ↓
                ┌──────────────┐
                │Report Writer │
                └──────┬───────┘
                       ↓
                files/reports/*.pdf
```

#### Pipeline Pattern

```
┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐
│Architect│ → │ Coder  │ → │Reviewer│ → │ Tester │
└────────┘   └────────┘   └────────┘   └────────┘
     │            │            │            │
     ↓            ↓            ↓            ↓
  Design      Implement    Feedback     Tests
```

#### Critic-Actor Pattern

```
┌─────────────────────────────────────────┐
│                                         │
│   ┌─────────┐         ┌─────────┐      │
│   │  Actor  │ ──────→ │  Critic │      │
│   └────┬────┘         └────┬────┘      │
│        ↑    Content        │           │
│        │                   │ Feedback  │
│        └───────────────────┘           │
│                                         │
│   while quality < threshold             │
└─────────────────────────────────────────┘
```

---

## 3. Core Components

### 3.1 Initialization

The framework provides a simplified entry point:

```python
from claude_agent_framework import init

# Minimal usage - 2 lines to get started
session = init("research")
async for msg in session.run("Analyze AI market trends"):
    print(msg)
```

### 3.2 Architecture Components

Each architecture consists of:

```
architectures/<name>/
├── __init__.py          # Exports
├── config.py            # Architecture-specific configuration
├── orchestrator.py      # Main architecture class
└── prompts/             # Agent prompts
    ├── lead_agent.txt
    ├── agent_a.txt
    └── agent_b.txt
```

### 3.3 BaseArchitecture Interface

```python
from claude_agent_framework.core import BaseArchitecture, register_architecture

@register_architecture("my_architecture")
class MyArchitecture(BaseArchitecture):
    """Custom architecture implementation."""

    name = "my_architecture"
    description = "Description shown in architecture listing"

    def get_agents(self) -> dict[str, AgentDefinitionConfig]:
        """Define subagents and their configurations."""
        return {
            "worker": AgentDefinitionConfig(
                name="worker",
                description="Executes specific tasks",
                tools=["Read", "Write"],
                prompt_file="worker.txt",
            ),
        }

    async def execute(
        self,
        prompt: str,
        tracker: SubagentTracker | None = None,
        transcript: TranscriptWriter | None = None,
    ) -> AsyncIterator[Any]:
        """Execute the architecture workflow."""
        # Implementation
        ...
```

### 3.4 AgentSession

Manages the complete session lifecycle:

```python
session = init("research")

try:
    async for msg in session.run("Query"):
        print(msg)
finally:
    await session.teardown()  # Cleanup

# Or use context manager
async with init("research") as session:
    results = await session.query("Query")
```

---

## 4. Multi-Agent Orchestration

### 4.1 Parallel Dispatch

Lead agents dispatch multiple subagents simultaneously:

```python
# In lead agent prompt:
"""
# Rules
1. You can ONLY use the Task tool to dispatch subagents
2. NEVER perform research, analysis, or writing yourself
3. Decompose requests into 2-4 independent subtopics
4. Dispatch researchers IN PARALLEL (not sequentially)
5. Wait for all research to complete before dispatching analyst
"""
```

### 4.2 Filesystem Coordination

Agents communicate via standard directory structure:

```python
FILE_STRUCTURE = {
    "files/research_notes/": "Researcher output → Analyst input",
    "files/data/":           "Analyst output → Reporter input",
    "files/charts/":         "Analyst charts → Reporter reference",
    "files/reports/":        "Reporter final output",
}
```

### 4.3 Lead Agent Template

```text
# Role Definition
You are the Research Coordinator, responsible for task decomposition
and subagent orchestration.

# Core Rules
1. You can ONLY use the Task tool to dispatch subagents
2. NEVER perform research, analysis, or writing yourself
3. Decompose research requests into 2-4 independent subtopics
4. Dispatch researchers IN PARALLEL (not sequentially)
5. Wait for all research to complete before dispatching analyst
6. Finally dispatch reporter to generate output

# Workflow
1. Analyze user request → Identify subtopics
2. Parallel dispatch researchers → Gather information
3. Dispatch analyst → Process data
4. Dispatch reporter → Generate report
5. Report completion status to user

# Available Subagents
- researcher: Web search and information gathering
- data-analyst: Data processing and visualization
- report-writer: Final report generation
```

---

## 5. Hook Mechanism

### 5.1 Hook Types

| Hook Type | Trigger Point | Purpose |
|-----------|---------------|---------|
| `PreToolUse` | Before tool execution | Input validation, permission checks, logging |
| `PostToolUse` | After tool execution | Result capture, error handling, metrics |
| `Notification` | Notification events | Status updates, progress reporting |

### 5.2 Hook Configuration

```python
from claude_agent_sdk import HookMatcher

hooks = {
    'PreToolUse': [
        HookMatcher(
            matcher=None,  # None = match all tools
            hooks=[tracker.pre_tool_use_hook]
        )
    ],
    'PostToolUse': [
        HookMatcher(
            matcher=None,
            hooks=[tracker.post_tool_use_hook]
        )
    ]
}
```

### 5.3 SubagentTracker Implementation

```python
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime

@dataclass
class ToolCallRecord:
    """Single tool call record."""
    timestamp: str
    tool_name: str
    tool_input: dict[str, Any]
    tool_use_id: str
    subagent_type: str
    parent_tool_use_id: str | None = None
    tool_output: Any = None
    error: str | None = None

class SubagentTracker:
    """Tracks subagent spawning and tool calls."""

    def __init__(self, log_file_path: str):
        self.sessions: dict[str, SubagentSession] = {}
        self.tool_call_records: dict[str, ToolCallRecord] = {}
        self._current_parent_id: str | None = None
        self.subagent_counters: dict[str, int] = {}
        self._log_file = open(log_file_path, 'w')

    def set_current_context(self, parent_tool_use_id: str | None):
        """Set current execution context."""
        self._current_parent_id = parent_tool_use_id

    async def pre_tool_use_hook(
        self,
        hook_input: dict[str, Any],
        tool_use_id: str,
        context: Any
    ) -> dict[str, Any]:
        """Pre-tool execution hook."""
        tool_name = hook_input['tool_name']
        tool_input = hook_input['tool_input']

        # Determine owning agent
        subagent_type = "LEAD"
        if self._current_parent_id and self._current_parent_id in self.sessions:
            subagent_type = self.sessions[self._current_parent_id].subagent_id

        # Create record
        record = ToolCallRecord(
            timestamp=datetime.now().isoformat(),
            tool_name=tool_name,
            tool_input=tool_input,
            tool_use_id=tool_use_id,
            subagent_type=subagent_type,
            parent_tool_use_id=self._current_parent_id
        )
        self.tool_call_records[tool_use_id] = record

        return {'continue_': True}

    async def post_tool_use_hook(
        self,
        hook_input: dict[str, Any],
        tool_use_id: str,
        context: Any
    ) -> dict[str, Any]:
        """Post-tool execution hook."""
        tool_response = hook_input.get('tool_response')
        record = self.tool_call_records.get(tool_use_id)

        if record:
            error = None
            if isinstance(tool_response, dict):
                error = tool_response.get('error')

            record.tool_output = tool_response
            record.error = error

        return {'continue_': True}
```

---

## 6. Tool Assignment

### 6.1 Built-in Tools

| Tool | Purpose | Typical Use Case |
|------|---------|------------------|
| `Task` | Dispatch subagent | Lead agent orchestration |
| `WebSearch` | Web search | Information gathering |
| `Read` | Read file | Load data |
| `Write` | Write file | Save results |
| `Glob` | File pattern matching | Discover files |
| `Grep` | Content search | Find information |
| `Bash` | Execute command | Run scripts |
| `Edit` | Edit file | Modify content |
| `Skill` | Call skill | Complex operations |

### 6.2 Tool Assignment by Role

```python
TOOL_ASSIGNMENTS = {
    "lead":       ["Task"],                              # Orchestration only
    "researcher": ["WebSearch", "Write"],                # Search and save
    "analyst":    ["Glob", "Read", "Bash", "Write"],     # Analyze and execute
    "reporter":   ["Glob", "Read", "Write", "Skill"],    # Generate reports
}
```

### 6.3 Principle of Least Privilege

```python
# BAD: Too many tools
bad_agent = AgentDefinitionConfig(
    tools=["WebSearch", "Read", "Write", "Bash", "Edit", "Glob", "Grep"],
    ...
)

# GOOD: Precise control
good_agent = AgentDefinitionConfig(
    tools=["WebSearch", "Write"],  # Only what's needed
    ...
)
```

---

## 7. Prompt Engineering

### 7.1 Prompt Structure Template

```text
# Role Definition
You are [ROLE NAME], responsible for [CORE RESPONSIBILITY].

# Capability Boundaries
- You CAN: [Specific capability list]
- You CANNOT: [Restriction list]

# Workflow
1. [Step 1]
2. [Step 2]
3. [Step 3]

# Output Specification
- Format: [Expected format]
- Location: [Output path]
- Naming: [Naming convention]

# Quality Standards
- [Standard 1]
- [Standard 2]

# Examples
[Concrete examples]
```

### 7.2 Researcher Prompt Example

```text
# Role Definition
You are a Professional Researcher, responsible for gathering quantitative
data and key information through web search.

# Core Tasks
1. Execute 5-10 targeted searches
2. Prioritize quantitative data (market size, growth rates, rankings)
3. Save research findings as Markdown files

# Search Strategy
- Use specific, targeted queries
- Seek authoritative sources (industry reports, official data)
- Collect multiple data points for cross-validation

# Output Specification
- Path: files/research_notes/{topic_name}.md
- Format: Markdown with structured headings
- Content: 10-15+ specific statistics

# Data Priority
1. Market size and share
2. Growth rates and forecasts
3. Key player rankings
4. Technical parameter comparisons
5. Investment and funding data
```

### 7.3 Prompt Loading

```python
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"

def load_prompt(filename: str) -> str:
    """Load prompt from prompts directory."""
    prompt_path = PROMPTS_DIR / filename
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()
```

---

## 8. State Management

### 8.1 Session State

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class AgentSession:
    """Agent session state."""
    session_id: str
    started_at: str
    user_query: str
    subagents_spawned: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    current_phase: str = "init"  # init, researching, analyzing, reporting, done
    errors: List[str] = field(default_factory=list)
```

### 8.2 Phase Tracking

```python
class PhaseTracker:
    """Workflow phase tracker."""

    PHASES = ["init", "researching", "analyzing", "reporting", "done"]

    def __init__(self):
        self.current_phase = "init"
        self.phase_history = []

    def advance_phase(self, new_phase: str):
        """Advance to new phase."""
        if new_phase not in self.PHASES:
            raise ValueError(f"Unknown phase: {new_phase}")

        self.phase_history.append({
            "from": self.current_phase,
            "to": new_phase,
            "timestamp": datetime.now().isoformat()
        })
        self.current_phase = new_phase

    def is_complete(self) -> bool:
        return self.current_phase == "done"
```

---

## 9. Error Handling

### 9.1 Graceful Degradation

```python
async def post_tool_use_hook(self, hook_input, tool_use_id, context):
    """Error handling example."""
    tool_response = hook_input.get('tool_response')

    # Detect error
    error = None
    if isinstance(tool_response, dict):
        error = tool_response.get('error')

    if error:
        # Log error but don't interrupt execution
        logger.warning(f"Tool error: {error}")
        self.errors.append({
            "tool_use_id": tool_use_id,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

    # Continue execution
    return {'continue_': True}
```

### 9.2 Resource Cleanup

```python
async def main():
    tracker = None
    transcript = None

    try:
        # Initialize resources
        transcript = TranscriptWriter(log_path)
        tracker = SubagentTracker(tool_log_path)

        # Execute main logic
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt=user_input)
            async for msg in client.receive_response():
                process_message(msg, tracker, transcript)

    except Exception as e:
        logger.error(f"Session failed: {e}")
        raise

    finally:
        # Ensure resource cleanup
        if transcript:
            transcript.close()
        if tracker:
            tracker.close()
```

### 9.3 Error Classification

```python
class AgentError(Exception):
    """Base agent error."""
    pass

class ConfigurationError(AgentError):
    """Configuration error."""
    pass

class ToolExecutionError(AgentError):
    """Tool execution error."""
    def __init__(self, tool_name: str, message: str):
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' failed: {message}")

class SubagentError(AgentError):
    """Subagent error."""
    def __init__(self, subagent_id: str, message: str):
        self.subagent_id = subagent_id
        super().__init__(f"Subagent '{subagent_id}' failed: {message}")
```

---

## 10. Logging and Auditing

### 10.1 Dual-Format Logging

```python
class TranscriptWriter:
    """Dual-format log writer."""

    def __init__(self, file_path: Path):
        self.file = open(file_path, 'w', encoding='utf-8')

    def write(self, text: str, end: str = ""):
        """Output to both console and file."""
        print(text, end=end, flush=True)
        self.file.write(text + end)
        self.file.flush()

    def write_to_file_only(self, text: str):
        """Write to file only (detailed logs)."""
        self.file.write(text)
        self.file.flush()

    def close(self):
        self.file.close()
```

### 10.2 JSONL Structured Logging

```python
import json
from datetime import datetime

class ToolCallLogger:
    """Tool call JSONL logger."""

    def __init__(self, file_path: Path):
        self.file = open(file_path, 'w')

    def log_tool_start(self, agent_id: str, tool_name: str,
                       tool_input: dict, tool_use_id: str):
        entry = {
            "event": "tool_call_start",
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "tool_name": tool_name,
            "tool_use_id": tool_use_id,
            "input_summary": self._summarize_input(tool_input)
        }
        self._write(entry)

    def log_tool_complete(self, tool_use_id: str, success: bool,
                         output_size: int = 0, error: str = None):
        entry = {
            "event": "tool_call_complete",
            "timestamp": datetime.now().isoformat(),
            "tool_use_id": tool_use_id,
            "success": success,
            "output_size": output_size,
            "error": error
        }
        self._write(entry)

    def _write(self, entry: dict):
        self.file.write(json.dumps(entry, ensure_ascii=False) + '\n')
        self.file.flush()

    def close(self):
        self.file.close()
```

### 10.3 Session Directory Management

```python
from pathlib import Path
from datetime import datetime

def setup_session() -> tuple[Path, Path, Path]:
    """Create session directory and log files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = Path("logs") / f"session_{timestamp}"
    session_dir.mkdir(parents=True, exist_ok=True)

    transcript_file = session_dir / "transcript.txt"
    tool_log_file = session_dir / "tool_calls.jsonl"

    return session_dir, transcript_file, tool_log_file
```

---

## 11. Configuration Management

### 11.1 Architecture Configuration

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class ResearchConfig:
    """Research architecture configuration."""

    # Model configuration
    lead_model: str = "haiku"
    researcher_model: str = "haiku"
    analyst_model: str = "haiku"
    reporter_model: str = "haiku"

    # Research depth
    research_depth: str = "standard"  # shallow, standard, deep
    max_researchers: int = 4

    # Output directories
    research_notes_dir: str = "research_notes"
    data_dir: str = "data"
    charts_dir: str = "charts"
    reports_dir: str = "reports"

    def get_model_overrides(self) -> dict[str, str]:
        """Get model overrides for agents."""
        return {
            "researcher": self.researcher_model,
            "data-analyst": self.analyst_model,
            "report-writer": self.reporter_model,
        }
```

### 11.2 Environment Configuration

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API configuration
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # Model configuration
    LEAD_MODEL = os.getenv("LEAD_MODEL", "haiku")
    SUBAGENT_MODEL = os.getenv("SUBAGENT_MODEL", "haiku")

    # Path configuration
    PROJECT_ROOT = Path(__file__).parent.parent
    FILES_DIR = PROJECT_ROOT / "files"
    LOGS_DIR = PROJECT_ROOT / "logs"
    PROMPTS_DIR = PROJECT_ROOT / "prompts"

    # Feature flags
    ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
    BYPASS_PERMISSIONS = os.getenv("BYPASS_PERMISSIONS", "true").lower() == "true"

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
```

---

## 12. Complete Examples

### 12.1 Basic Usage

```python
from claude_agent_framework import init
import asyncio

async def research_example():
    """Basic research example."""
    session = init("research")

    async for msg in session.run("Analyze AI market trends in 2024"):
        print(msg)

asyncio.run(research_example())
```

### 12.2 Custom Architecture

```python
from claude_agent_framework import register_architecture, BaseArchitecture, init
from claude_agent_framework.core.base import AgentDefinitionConfig

@register_architecture("qa_expert")
class QAExpertArchitecture(BaseArchitecture):
    """Custom Q&A expert architecture."""

    name = "qa_expert"
    description = "Q&A system with domain expert routing"

    def get_agents(self) -> dict[str, AgentDefinitionConfig]:
        return {
            "code_expert": AgentDefinitionConfig(
                name="code_expert",
                description="Expert in programming and software development",
                tools=["Read", "Write", "Glob", "Grep"],
                prompt_file="code_expert.txt",
            ),
            "data_expert": AgentDefinitionConfig(
                name="data_expert",
                description="Expert in data analysis and statistics",
                tools=["Read", "Write", "Bash"],
                prompt_file="data_expert.txt",
            ),
        }

    async def execute(self, prompt, tracker=None, transcript=None):
        """Execute Q&A workflow."""
        # Build SDK configuration
        options = ClaudeAgentOptions(
            permission_mode="bypassPermissions",
            setting_sources=["project"],
            system_prompt=self.get_lead_prompt(),
            allowed_tools=["Task"],
            agents=self.to_sdk_agents(),
            hooks=self._build_hooks(tracker),
            model=self.model_config.default,
        )

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt=prompt)

            async for msg in client.receive_response():
                yield msg

# Use the custom architecture
async def main():
    session = init("qa_expert")
    async for msg in session.run("How do I optimize database queries?"):
        print(msg)
```

### 12.3 Programmatic Control

```python
from claude_agent_framework import init
from pathlib import Path

async def programmatic_example():
    """Full programmatic control."""

    # Initialize with custom options
    session = init(
        "research",
        model="sonnet",
        verbose=True,
        log_dir=Path("./custom_logs"),
    )

    # Access internal components
    print(f"Architecture: {session.architecture.name}")
    print(f"Session directory: {session.session_dir}")

    # Run query
    query = "Analyze cloud computing market trends"

    try:
        async for msg in session.run(query):
            print(msg)
    finally:
        await session.teardown()
        print(f"Session saved to: {session.session_dir}")
```

---

## Summary

### Key Takeaways

1. **Multiple Patterns**: 7 distinct orchestration patterns for different problem domains
2. **Pattern Selection**: Choose based on task characteristics (parallel vs sequential, iterative vs one-shot)
3. **Separation of Concerns**: Lead Agent orchestrates, Subagents execute specialized tasks
4. **Tool Constraints**: Principle of least privilege, precise tool control per agent
5. **Observability**: Hook mechanism + JSONL audit logs for full traceability
6. **Cost Optimization**: Subagents use Haiku model for cost efficiency
7. **Prompt Engineering**: Structured templates with clear role boundaries
8. **Error Handling**: Graceful degradation, ensure resource cleanup

### Pattern Quick Reference

| Pattern | When to Use |
|---------|-------------|
| **Research** | Need to gather data from multiple sources in parallel |
| **Pipeline** | Sequential stages with clear handoffs |
| **Critic-Actor** | Iterative quality improvement through feedback |
| **Specialist Pool** | Routing queries to domain experts |
| **Debate** | Balanced analysis of pros and cons |
| **Reflexion** | Complex problems requiring self-reflection |
| **MapReduce** | Large-scale parallel processing with aggregation |

### Applicable Scenarios

- Multi-step research tasks
- Data collection and analysis pipelines
- Document generation automation
- Complex workflow orchestration
- Decision support systems
- Large-scale content analysis

---

*Document generated: 2024-12-25*
*Based on: Claude Agent Framework v0.3.0*
