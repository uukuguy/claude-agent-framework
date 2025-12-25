# Claude Agent Framework

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A production-ready multi-agent orchestration framework built on [Claude Agent SDK](https://github.com/anthropics/claude-code-sdk-python). Design, compose, and deploy complex AI workflows with pre-built architecture patterns.

[中文文档](README_CN.md) | [Best Practices Guide](docs/BEST_PRACTICES.md)

## Overview

Claude Agent Framework is a production-ready orchestration layer for building multi-agent AI systems. It addresses the fundamental challenge of complex tasks that require diverse specialized capabilities—research, analysis, code generation, decision-making—which cannot be effectively handled by a single LLM prompt. The framework decomposes these tasks into coordinated workflows where a lead agent orchestrates specialized subagents, each with focused prompts, constrained tool access, and appropriate model selection. Built on Claude Agent SDK, it provides battle-tested patterns extracted from real-world applications, comprehensive observability through hook-based tracking, and a simple API that lets you go from concept to working system in minutes.

**Key Features:**

- **7 Pre-built Patterns** - Research, Pipeline, Critic-Actor, Specialist Pool, Debate, Reflexion, MapReduce
- **2-Line Quick Start** - Initialize and run with minimal code
- **Full Observability** - Hook-based tracking with structured JSONL logging
- **Cost Control** - Automatic model selection based on task complexity
- **Extensible Architecture** - Register custom patterns with a simple decorator

```python
from claude_agent_framework import init

session = init("research")
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

### Orchestration Patterns

The framework provides 7 patterns for different workflow needs:

| Pattern | Use Case | Flow |
|---------|----------|------|
| **Research** | Data gathering | Parallel workers → Aggregation |
| **Pipeline** | Sequential processing | Stage A → B → C → D |
| **Critic-Actor** | Quality iteration | Generate ↔ Evaluate loop |
| **Specialist Pool** | Expert routing | Router → Domain experts |
| **Debate** | Decision analysis | Pro ↔ Con → Judge |
| **Reflexion** | Complex problem solving | Execute → Reflect → Improve |
| **MapReduce** | Large-scale processing | Split → Map → Reduce |

For implementation details, see [Best Practices Guide](docs/BEST_PRACTICES.md).

## Quick Start

```bash
pip install claude-agent-framework
export ANTHROPIC_API_KEY="your-api-key"
```

```python
from claude_agent_framework import init
import asyncio

async def main():
    session = init("research")
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

## Production Examples

The framework includes 7 production-grade examples demonstrating real-world business scenarios:

| Example | Architecture | Business Scenario | Features |
|---------|--------------|-------------------|----------|
| **01_competitive_intelligence** | Research | SaaS competitive analysis | Parallel competitor research, multi-channel data collection, SWOT analysis, PDF reports |
| **02_pr_code_review** | Pipeline | Automated PR review | Architecture review, code quality check, security scan, performance analysis, test coverage |
| **03_marketing_content** | Critic-Actor | Marketing copy optimization | Draft generation, multi-dimensional evaluation, A/B test variants, brand guideline integration |
| **04_it_support** | Specialist Pool | IT support routing | Intelligent classification, expert routing, parallel collaboration, knowledge base integration |
| **05_tech_decision** | Debate | Technical decision support | Pro-con debate, multi-round deliberation, expert judgment, risk analysis |
| **06_code_debugger** | Reflexion | Adaptive debugging | Strategy execution, result reflection, dynamic adjustment, root cause identification |
| **07_codebase_analysis** | MapReduce | Large codebase analysis | Intelligent partitioning, parallel analysis, issue aggregation, prioritized reports |

Each example includes:
- ✅ Complete runnable code with error handling
- ✅ Configuration files and custom components
- ✅ Unit tests, integration tests, and end-to-end tests
- ✅ Comprehensive documentation (English + Chinese)
- ✅ Usage guides and customization instructions

See [Production Examples Design Document](docs/PRODUCTION_EXAMPLES_DESIGN.md) for detailed implementation specifications.

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
from claude_agent_framework import init

session = init("research")

async for msg in session.run("Research quantum computing applications"):
    print(msg)
```

### With Options

```python
session = init(
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

@register_architecture("my_custom")
class MyCustomArchitecture(BaseArchitecture):
    name = "my_custom"
    description = "Custom workflow for my use case"

    def get_agents(self):
        return {...}

    async def execute(self, prompt, tracker=None, transcript=None):
        # Implementation
        ...
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
claude_agent_framework/
├── init.py              # Simplified initialization
├── cli.py               # Command-line interface
├── config.py            # Configuration management
├── core/                # Core abstractions
│   ├── base.py          # BaseArchitecture class
│   ├── session.py       # AgentSession management
│   └── registry.py      # Architecture registry
├── architectures/       # Built-in architectures
│   ├── research/        # Research pattern
│   ├── pipeline/        # Pipeline pattern
│   ├── critic_actor/    # Critic-actor pattern
│   ├── specialist_pool/ # Specialist pool pattern
│   ├── debate/          # Debate pattern
│   ├── reflexion/       # Reflexion pattern
│   └── mapreduce/       # MapReduce pattern
├── utils/               # Utility modules
│   ├── tracker.py       # Hook tracking
│   ├── transcript.py    # Logging
│   └── message_handler.py
├── files/               # Working directory
└── logs/                # Session logs
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

## Requirements

- Python 3.10+
- Claude Agent SDK
- ANTHROPIC_API_KEY environment variable

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
