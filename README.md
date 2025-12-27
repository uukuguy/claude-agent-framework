# Claude Agent Framework

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A production-ready multi-agent orchestration framework built on [Claude Agent SDK](https://github.com/anthropics/claude-code-sdk-python). Design, compose, and deploy complex AI workflows with pre-built architecture patterns.

[中文文档](README_CN.md) | [Best Practices Guide](docs/BEST_PRACTICES.md) | [Role-Based Architecture](docs/ROLE_BASED_ARCHITECTURE.md)

## Overview

Claude Agent Framework is a production-ready orchestration layer for building multi-agent AI systems. It addresses the fundamental challenge of complex tasks that require diverse specialized capabilities—research, analysis, code generation, decision-making—which cannot be effectively handled by a single LLM prompt. The framework decomposes these tasks into coordinated workflows where a lead agent orchestrates specialized subagents, each with focused prompts, constrained tool access, and appropriate model selection. Built on Claude Agent SDK, it provides battle-tested patterns extracted from real-world applications, comprehensive observability through hook-based tracking, and a simple API that lets you go from concept to working system in minutes.

**Key Features:**

- **7 Pre-built Patterns** - Research, Pipeline, Critic-Actor, Specialist Pool, Debate, Reflexion, MapReduce
- **2-Line Quick Start** - Initialize and run with minimal code
- **Role-Based Architecture** - Separate role definitions from agent instances for flexible configuration
- **Production Plugin System** - Lifecycle hooks for metrics, cost tracking, retry handling
- **Two-Layer Prompts** - Framework prompts + business prompts for reusable workflows
- **Full Observability** - Structured JSONL logging, session tracking, debugging tools
- **Cost Control** - Automatic model selection, per-agent cost breakdown
- **Extensible** - Register custom architectures with a simple decorator

```python
from claude_agent_framework import create_session

session = create_session("research")
async for msg in session.run("Analyze AI market trends"):
    print(msg)
```

## Design Philosophy

### Why Multi-Agent?

Complex tasks often require multiple specialized capabilities that a single LLM prompt cannot effectively handle. Consider a research task: it needs web searching, data analysis, and report writing - each requiring different tools, prompts, and even models. A monolithic approach leads to:

- **Prompt bloat**: One prompt trying to do everything becomes unwieldy
- **Tool overload**: Agent has access to tools it shouldn't use at certain stages
- **Quality degradation**: Jack-of-all-trades prompts underperform specialized ones
- **Cost inefficiency**: Using expensive models for simple subtasks

### Core Architecture

Claude Agent Framework solves this through **agent specialization and orchestration**:

```
User Request
      ↓
Lead Agent (Orchestrator)
      │
      ├── Analyzes task requirements
      ├── Decomposes into subtasks
      ├── Dispatches to specialized subagents
      ├── Coordinates execution flow
      └── Synthesizes final output
            ↓
      Subagents (Specialists)
      │
      ├── Focused prompts for specific tasks
      ├── Minimal tool access (least privilege)
      ├── Cost-effective models where appropriate
      └── Communicate via filesystem (loose coupling)
```

### Design Principles

| Principle | Rationale |
|-----------|-----------|
| **Separation of Concerns** | Lead orchestrates, subagents execute - clear responsibilities |
| **Tool Constraints** | Each agent gets only the tools it needs - security and focus |
| **Loose Coupling** | Filesystem-based data exchange - agents are independent |
| **Observability** | Hook mechanism captures all tool calls - debugging and audit |
| **Cost Optimization** | Match model capability to task complexity |

## Quick Start

```bash
pip install claude-agent-framework
export ANTHROPIC_API_KEY="your-api-key"
```

```python
from claude_agent_framework import create_session
import asyncio

async def main():
    session = create_session("research")
    async for msg in session.run("Analyze AI market trends in 2024"):
        print(msg)

asyncio.run(main())
```

## Available Architectures

| Architecture | Use Case | Pattern |
|--------------|----------|---------|
| **research** | Deep research tasks | Master-worker with parallel data gathering |
| **pipeline** | Code review, content creation | Sequential stage processing |
| **critic_actor** | Quality improvement | Generate-evaluate iteration loop |
| **specialist_pool** | Technical support | Expert routing and dispatch |
| **debate** | Decision support | Pro-con deliberation with judge |
| **reflexion** | Complex problem solving | Execute-reflect-improve cycle |
| **mapreduce** | Large-scale analysis | Parallel map with aggregation |

## Role-Based Architecture

The framework uses a **Role-Based Architecture** that separates abstract role definitions from concrete agent instances. This enables a single architecture to support multiple business scenarios through flexible agent configuration.

### Key Concepts

| Concept | Description |
|---------|-------------|
| **RoleType** | Semantic role type (WORKER, PROCESSOR, SYNTHESIZER, etc.) |
| **RoleCardinality** | Quantity constraints (EXACTLY_ONE, ONE_OR_MORE, etc.) |
| **RoleDefinition** | Architecture-level role specification with tools and constraints |
| **AgentInstanceConfig** | Business-level concrete agent configuration |

### Usage Example

```python
from claude_agent_framework import create_session
from claude_agent_framework.core.roles import AgentInstanceConfig

# Define agent instances for specific business needs
agents = [
    AgentInstanceConfig(
        name="market-researcher",
        role="worker",
        description="Market data collection specialist",
        prompt_file="prompts/market_researcher.txt",
    ),
    AgentInstanceConfig(
        name="tech-researcher",
        role="worker",
        description="Technology trends analyst",
    ),
    AgentInstanceConfig(
        name="data-analyst",
        role="processor",
        model="sonnet",
    ),
    AgentInstanceConfig(
        name="report-writer",
        role="synthesizer",
    ),
]

# Create session with role-based configuration
session = create_session("research", agent_instances=agents)
async for msg in session.run("Analyze AI market trends"):
    print(msg)
```

For detailed documentation, see [Role-Based Architecture Guide](docs/ROLE_BASED_ARCHITECTURE.md).

## Production Examples

The framework includes **7 production-grade examples** demonstrating real-world business scenarios. Each example showcases a specific architecture pattern applied to solve genuine enterprise challenges.

**📁 Location**: [`examples/production/`](examples/production/)
**📊 Status**: All 7 examples complete and production-ready
**📚 Documentation**: Each example includes bilingual README (EN/CN), configuration guide, and architecture documentation

### Example Overview

| Example | Architecture | Business Scenario | Core Design Pattern | Status |
|---------|--------------|-------------------|---------------------|--------|
| [**01_competitive_intelligence**](examples/production/01_competitive_intelligence/) | Research | SaaS competitive analysis | Parallel data gathering → Synthesis | ✅ Complete |
| [**02_pr_code_review**](examples/production/02_pr_code_review/) | Pipeline | Automated PR review | Sequential stage gating with quality thresholds | ✅ Complete |
| [**03_marketing_content**](examples/production/03_marketing_content/) | Critic-Actor | Marketing copy optimization | Generate → Evaluate → Improve loop | ✅ Complete |
| [**04_it_support**](examples/production/04_it_support/) | Specialist Pool | IT support routing | Keyword-based expert dispatch with urgency categorization | ✅ Complete |
| [**05_tech_decision**](examples/production/05_tech_decision/) | Debate | Technical decision support | Multi-round deliberation with weighted criteria | ✅ Complete |
| [**06_code_debugger**](examples/production/06_code_debugger/) | Reflexion | Adaptive debugging | Execute → Reflect → Adapt strategy | ✅ Complete |
| [**07_codebase_analysis**](examples/production/07_codebase_analysis/) | MapReduce | Large codebase analysis | Intelligent chunking → Parallel map → Aggregate | ✅ Complete |

### Running Examples

```bash
# Navigate to example directory
cd examples/production/01_competitive_intelligence

# Install dependencies
pip install -e ".[all]"

# Configure
cp config.example.yaml config.yaml
# Edit config.yaml with your settings

# Run
python main.py
```

## Architecture Diagrams

### Research Architecture

```
User Request
      ↓
Lead Agent (Coordinator)
      ├─→ Researcher-1 ─┐
      ├─→ Researcher-2 ─┼─→ Parallel Research
      └─→ Researcher-3 ─┘
             ↓
      Data-Analyst
             ↓
      Report-Writer
             ↓
      Output Files
```

### Pipeline Architecture

```
Request → Architect → Coder → Reviewer → Tester → Output
```

### Critic-Actor Architecture

```
while quality < threshold:
    content = Actor.generate()
    feedback = Critic.evaluate()
    if approved: break
```

### Specialist Pool Architecture

```
User Question → Router → [Code Expert, Data Expert, Security Expert, ...] → Summary
```

### Debate Architecture

```
Topic → Proponent ↔ Opponent (N rounds) → Judge → Verdict
```

### Reflexion Architecture

```
while not success:
    result = Executor.execute()
    reflection = Reflector.analyze()
    strategy = reflection.improved_strategy
```

### MapReduce Architecture

```
Task → Splitter → [Mapper-1, Mapper-2, ...] → Reducer → Result
```

## CLI Usage

### Running Architectures

```bash
# List available architectures
python -m claude_agent_framework.cli --list

# Run with specific architecture
python -m claude_agent_framework.cli --arch research -q "Analyze AI market trends"

# Interactive mode
python -m claude_agent_framework.cli --arch pipeline -i

# Choose model
python -m claude_agent_framework.cli --arch debate -m sonnet -q "Should we use microservices?"
```

## Python API

### Basic Usage

```python
from claude_agent_framework import create_session

session = create_session("research")

async for msg in session.run("Research quantum computing applications"):
    print(msg)
```

### With Options

```python
session = create_session(
    "pipeline",
    model="sonnet",      # haiku, sonnet, or opus
    verbose=True,        # Enable debug logging
    log_dir="./logs",    # Custom log directory
)
```

### Single Query

```python
from claude_agent_framework import quick_query
import asyncio

# Quick one-off query
results = asyncio.run(quick_query("Analyze Python trends", architecture="research"))
print(results[-1])
```

### Custom Architecture

```python
from claude_agent_framework import register_architecture, BaseArchitecture
from claude_agent_framework.core.roles import RoleDefinition
from claude_agent_framework.core.types import RoleType, RoleCardinality

@register_architecture("my_custom")
class MyCustomArchitecture(BaseArchitecture):
    name = "my_custom"
    description = "Custom workflow for my use case"

    def get_role_definitions(self) -> dict[str, RoleDefinition]:
        return {
            "worker": RoleDefinition(
                role_type=RoleType.WORKER,
                description="Execute tasks",
                required_tools=["Read", "Write"],
                cardinality=RoleCardinality.ONE_OR_MORE,
            ),
        }

    async def execute(self, prompt, tracker=None, transcript=None):
        # Implementation
        ...
```

### Session Lifecycle

```python
# Manual management
session = create_session("research")
try:
    async for msg in session.run(prompt):
        process(msg)
finally:
    await session.teardown()

# Context manager (AgentSession implements __aenter__/__aexit__)
async with create_session("research") as session:
    results = await session.query(prompt)
```

### Using Plugins

```python
from claude_agent_framework import create_session
from claude_agent_framework.plugins.builtin import (
    MetricsCollectorPlugin,
    CostTrackerPlugin,
    RetryHandlerPlugin
)

session = create_session("research")

# Add metrics tracking
metrics_plugin = MetricsCollectorPlugin()
session.architecture.add_plugin(metrics_plugin)

# Add cost tracking with budget limit
cost_plugin = CostTrackerPlugin(budget_usd=5.0)
session.architecture.add_plugin(cost_plugin)

# Run session
async for msg in session.run("Analyze market"):
    print(msg)

# Get metrics
metrics = metrics_plugin.get_metrics()
print(f"Cost: ${metrics.estimated_cost_usd:.4f}")
```

### Dynamic Agent Registration

```python
session = create_session("specialist_pool")

# Add new agent at runtime
session.architecture.add_agent(
    name="security_expert",
    description="Cybersecurity specialist",
    tools=["WebSearch", "Read"],
    prompt="You are a cybersecurity expert...",
    model="sonnet"
)

# List all agents (static + dynamic)
agents = session.architecture.list_dynamic_agents()
print(f"Dynamic agents: {agents}")
```

## Output

Each session generates:

- `logs/session_YYYYMMDD_HHMMSS/transcript.txt` - Human-readable conversation log
- `logs/session_YYYYMMDD_HHMMSS/tool_calls.jsonl` - Structured tool call records
- `files/<architecture>/` - Architecture-specific outputs (reports, charts, etc.)

## Installation Options

```bash
# Basic installation
pip install claude-agent-framework

# With PDF generation support
pip install "claude-agent-framework[pdf]"

# With chart generation support
pip install "claude-agent-framework[charts]"

# Full installation (all features)
pip install "claude-agent-framework[all]"

# Development installation
pip install "claude-agent-framework[dev]"
```

## Project Structure

```
src/claude_agent_framework/
├── __init__.py              # Package exports (v0.4.0)
├── session.py               # create_session() entry point
├── cli.py                   # Command-line interface
├── architectures/           # 7 built-in architecture implementations
│   ├── research/            # ResearchArchitecture
│   ├── pipeline/            # PipelineArchitecture
│   ├── critic_actor/        # CriticActorArchitecture
│   ├── specialist_pool/     # SpecialistPoolArchitecture
│   ├── debate/              # DebateArchitecture
│   ├── reflexion/           # ReflexionArchitecture
│   └── mapreduce/           # MapReduceArchitecture
├── config/                  # Configuration system
│   ├── legacy.py            # FrameworkConfig, AgentConfig
│   └── schema.py            # Pydantic validation schemas
├── core/                    # Core abstractions
│   ├── base.py              # BaseArchitecture, AgentDefinitionConfig
│   ├── prompt.py            # PromptComposer - two-layer prompt composition
│   ├── registry.py          # @register_architecture, get_architecture
│   ├── roles.py             # RoleDefinition, AgentInstanceConfig
│   ├── session.py           # AgentSession, CompositeSession
│   └── types.py             # RoleType, RoleCardinality, ModelType
├── dynamic/                 # Dynamic agent registry
├── metrics/                 # Performance tracking
├── observability/           # Structured logging and visualization
├── plugins/                 # Plugin system with lifecycle hooks
│   ├── base.py              # BasePlugin, PluginManager
│   └── builtin/             # MetricsCollector, CostTracker, RetryHandler
├── utils/                   # Utilities
│   ├── tracker.py           # SubagentTracker, tool call recording
│   ├── transcript.py        # TranscriptWriter, session logging
│   ├── message_handler.py   # Message processing
│   └── helpers.py           # quick_query convenience function
├── files/                   # Working directory
└── logs/                    # Session logs
```

## Development

```bash
# Clone and install
git clone https://github.com/your-org/claude-agent-framework
cd claude-agent-framework
pip install -e ".[all]"

# Run tests
make test

# Format code
make format

# Lint
make lint
```

## Makefile Commands

```bash
make run              # Run default architecture (research)
make run-research     # Run Research architecture
make run-pipeline     # Run Pipeline architecture
make run-critic       # Run Critic-Actor architecture
make run-specialist   # Run Specialist Pool architecture
make run-debate       # Run Debate architecture
make run-reflexion    # Run Reflexion architecture
make run-mapreduce    # Run MapReduce architecture
make list-archs       # List all architectures
make test             # Run tests
make format           # Format code
make lint             # Lint code
```

## Documentation

### Quick Reference

- [README (Chinese)](README_CN.md) - 中文文档
- [Best Practices Guide](docs/BEST_PRACTICES.md) - Pattern selection and implementation tips
- [Best Practices (Chinese)](docs/BEST_PRACTICES_CN.md) - 最佳实践指南（中文）

### Architecture & Design

- [Role-Based Architecture Guide](docs/ROLE_BASED_ARCHITECTURE.md) - Role types, constraints, and agent instantiation
- [角色类型系统指南（中文）](docs/ROLE_BASED_ARCHITECTURE_CN.md)
- [Prompt Writing Guide](docs/PROMPT_WRITING_GUIDE.md) - Two-layer prompt architecture

### API Reference

- [Core API Reference](docs/api/core.md) - create_session(), AgentSession, BaseArchitecture
- [核心API参考（中文）](docs/api/core_cn.md)

## Requirements

- Python 3.10+
- Claude Agent SDK
- ANTHROPIC_API_KEY environment variable

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
