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
- **Production Plugin System** - 9 lifecycle hooks for metrics, cost tracking, retry handling, and custom logic
- **Advanced Configuration** - Pydantic validation, multi-source loading (YAML/env), environment profiles
- **Performance Tracking** - Token usage, cost estimation, memory profiling, multi-format export (JSON/CSV/Prometheus)
- **Dynamic Agent Registry** - Register and modify agents at runtime without code changes
- **Full Observability** - Structured JSONL logging, interactive dashboards, session debugging tools
- **CLI Enhancement** - Metrics viewing, session visualization, HTML report generation
- **Cost Control** - Automatic model selection, budget limits, per-agent cost breakdown
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

The framework includes 7 production-grade examples demonstrating real-world business scenarios. Each example showcases a specific architecture pattern applied to solve genuine enterprise challenges.

### Example Overview

| Example | Architecture | Business Scenario | Core Design Pattern |
|---------|--------------|-------------------|---------------------|
| **01_competitive_intelligence** | Research | SaaS competitive analysis | Parallel data gathering → Synthesis |
| **02_pr_code_review** | Pipeline | Automated PR review | Sequential stage gating with quality thresholds |
| **03_marketing_content** | Critic-Actor | Marketing copy optimization | Generate → Evaluate → Improve loop |
| **04_it_support** | Specialist Pool | IT support routing | Keyword-based expert dispatch with urgency categorization |
| **05_tech_decision** | Debate | Technical decision support | Multi-round deliberation with weighted criteria |
| **06_code_debugger** | Reflexion | Adaptive debugging | Execute → Reflect → Adapt strategy |
| **07_codebase_analysis** | MapReduce | Large codebase analysis | Intelligent chunking → Parallel map → Aggregate |

### Design Highlights

#### 1. Competitive Intelligence (Research Architecture)

**Pattern**: Fan-out/Fan-in with parallel worker coordination

**Key Design Decisions**:
- **Parallel Dispatch**: Multiple researchers analyze different competitors simultaneously
- **Multi-Channel Aggregation**: Official websites, market reports, customer reviews → single unified view
- **SWOT Generation**: Automated strengths/weaknesses/opportunities/threats analysis
- **Structured Output**: JSON/Markdown/PDF reports with consistent formatting

**Technical Highlights**:
```python
# Parallel researcher dispatch
Lead Agent → [Industry Researcher, Competitor Analyst 1, Competitor Analyst 2, ...] → Report Generator
# Each researcher works independently, results aggregated by lead
```

**Use Case**: When you need to quickly gather competitive intelligence across multiple targets with parallel data collection

---

#### 2. PR Code Review (Pipeline Architecture)

**Pattern**: Sequential stage processing with quality gates

**Key Design Decisions**:
- **5-Stage Pipeline**: Architecture → Code Quality → Security → Performance → Test Coverage
- **Configurable Thresholds**: Max complexity (10), min coverage (80%), max file size (500 lines)
- **Failure Strategies**: `stop_on_critical` (fail fast) vs `continue_all` (full audit)
- **Progressive Refinement**: Each stage builds on previous stage's findings

**Technical Highlights**:
```python
# Sequential execution with conditional gating
Stage 1 (Architecture) → [Pass] → Stage 2 (Quality) → [Warning] → Stage 3 (Security) → ...
                                                    ↓ [CRITICAL]
                                                  STOP (if stop_on_critical)
```

**Use Case**: When code changes must pass through multiple independent review checkpoints before approval

---

#### 3. Marketing Content (Critic-Actor Architecture)

**Pattern**: Iterative refinement through generate-evaluate loops

**Key Design Decisions**:
- **Weighted Evaluation**: SEO (25%), Engagement (30%), Brand (25%), Accuracy (20%)
- **Brand Voice Enforcement**: Prohibited phrases detection, tone consistency checks
- **Quality Threshold**: Stop when score ≥ 85% or max iterations reached
- **A/B Variant Generation**: Generate multiple angles for the same message

**Technical Highlights**:
```python
# Iterative improvement loop
while quality_score < threshold and iterations < max:
    content = Actor.generate()
    scores = Critic.evaluate(content)  # Multi-dimensional weighted scoring
    if scores.overall >= threshold: break
    content = Actor.improve(scores.feedback)
```

**Use Case**: When content quality must meet strict brand and engagement standards through iterative refinement

---

#### 4. IT Support (Specialist Pool Architecture)

**Pattern**: Dynamic expert routing with priority-based dispatch

**Key Design Decisions**:
- **Urgency Categorization**: Critical (1hr SLA), High (4hr), Medium (24hr), Low (72hr)
- **Keyword-Based Routing**: Match issue keywords to specialist expertise domains
- **Parallel Consultation**: Complex issues can trigger multiple specialists (up to 3)
- **Fallback Mechanism**: General IT specialist handles unmatched issues

**Technical Highlights**:
```python
# Dynamic specialist selection
Issue → Urgency Categorizer → Keyword Matcher → [Network, Database, Security] → Consolidator
                                              ↓ (if no match)
                                          [General IT Specialist]
```

**Use Case**: When support issues need intelligent routing to domain experts based on content and urgency

---

#### 5. Tech Decision (Debate Architecture)

**Pattern**: Adversarial deliberation with structured argumentation

**Key Design Decisions**:
- **3-Round Structure**: Opening Arguments → Deep Analysis → Rebuttals
- **Weighted Criteria**: Technical (30%), Implementation (25%), Cost (25%), Risk (20%)
- **Evidence-Based**: Arguments must cite data, industry research, or technical specs
- **Expert Panel Judgment**: Multi-expert evaluation with dissenting opinions allowed

**Technical Highlights**:
```python
# Structured multi-round debate
Round 1: Proponent.argue() ↔ Opponent.argue()  # Opening positions
Round 2: Proponent.analyze() ↔ Opponent.analyze()  # Evidence-based
Round 3: Proponent.rebuttal() ↔ Opponent.rebuttal()  # Counter-arguments
Final: Judge.evaluate(all_arguments, weighted_criteria)
```

**Use Case**: When technical decisions require balanced analysis of tradeoffs with structured deliberation

---

#### 6. Code Debugger (Reflexion Architecture)

**Pattern**: Self-improving execution through reflection loops

**Key Design Decisions**:
- **Strategy Library**: Error trace analysis, code inspection, hypothesis testing, dependency check
- **Adaptive Strategy Selection**: Reflector analyzes why previous attempts failed and suggests next approach
- **Root Cause Taxonomy**: Categorize bugs (logic error, race condition, resource leak, etc.)
- **Prevention Recommendations**: Learn from bug patterns to suggest prevention measures

**Technical Highlights**:
```python
# Execute-reflect-improve loop
while not root_cause_found and iterations < max:
    result = Executor.execute(current_strategy)
    reflection = Reflector.analyze(result, history)  # Why failed? What learned?
    next_strategy = Improver.select_strategy(reflection)  # Adapt approach
    history.append({strategy, result, reflection})
```

**Use Case**: When debugging complex issues requires systematic exploration with learning from failed attempts

---

#### 7. Codebase Analysis (MapReduce Architecture)

**Pattern**: Divide-conquer with intelligent chunking and aggregation

**Key Design Decisions**:
- **Chunking Strategies**: By module, by file type, by size, by git change frequency
- **Parallel Mapping**: Up to 10 concurrent mappers analyzing different chunks
- **Weighted Scoring**: Quality (25%), Security (30%), Maintainability (25%), Coverage (20%)
- **Issue Aggregation**: Deduplication, severity-based prioritization, module health scoring

**Technical Highlights**:
```python
# Parallel map-reduce workflow
Codebase → Smart Chunker → [Mapper 1, Mapper 2, ..., Mapper N] → Reducer
           (by_module)      (parallel analysis)                   (aggregate, dedupe, prioritize)
```

**Use Case**: When analyzing large codebases (500+ files) requires parallel processing with intelligent result aggregation

---

### Common Implementation Patterns

All examples demonstrate these production-ready patterns:

| Pattern | Implementation | Benefit |
|---------|----------------|---------|
| **Configuration-Driven** | YAML config with validation | Easy customization without code changes |
| **Structured Results** | Consistent JSON output format | Programmatic access and integration |
| **Error Handling** | Try/catch with graceful degradation | Robust production deployment |
| **Logging** | Structured JSONL + human-readable logs | Debugging and audit trail |
| **Testing** | Unit + integration + end-to-end tests | Quality assurance and regression prevention |

### Getting Started

Each example includes:
- ✅ Complete runnable code with error handling
- ✅ Configuration files with detailed comments
- ✅ Custom components and prompt engineering
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

### Session Observability (New in v0.4.0)

```bash
# View session metrics
claude-agent metrics <session-id>
# Shows: duration, token usage, cost, agent/tool statistics

# Open interactive dashboard
claude-agent view <session-id>
# Opens browser with timeline, tool graphs, performance analysis

# Generate HTML report
claude-agent report <session-id> --output report.html
# Creates comprehensive session report with charts
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

### Using Plugins (New in v0.4.0)

```python
from claude_agent_framework import init
from claude_agent_framework.plugins.builtin import (
    MetricsCollectorPlugin,
    CostTrackerPlugin,
    RetryHandlerPlugin
)

session = init("research")

# Add metrics tracking
metrics_plugin = MetricsCollectorPlugin()
session.architecture.add_plugin(metrics_plugin)

# Add cost tracking with budget limit
cost_plugin = CostTrackerPlugin(budget_usd=5.0)
session.architecture.add_plugin(cost_plugin)

# Add automatic retry on errors
retry_plugin = RetryHandlerPlugin(max_retries=3)
session.architecture.add_plugin(retry_plugin)

# Run session
async for msg in session.run("Analyze market"):
    print(msg)

# Get metrics
metrics = metrics_plugin.get_metrics()
print(f"Cost: ${metrics.estimated_cost_usd:.4f}")
print(f"Tokens: {metrics.tokens.total_tokens}")
```

### Advanced Configuration (New in v0.4.0)

```python
from claude_agent_framework.config import ConfigLoader, FrameworkConfigSchema

# Load from YAML
config = ConfigLoader.from_yaml("config.yaml")

# Load with environment profile
config = ConfigLoader.load_with_profile("production")

# Override with environment variables
config = ConfigLoader.from_env(prefix="CLAUDE_")

# Validate configuration
from claude_agent_framework.config import ConfigValidator
errors = ConfigValidator.validate_config(config)
if errors:
    print(f"Configuration errors: {errors}")
```

### Dynamic Agent Registration (New in v0.4.0)

```python
session = init("specialist_pool")

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

# With advanced configuration (Pydantic, YAML) - New in v0.4.0
pip install "claude-agent-framework[config]"

# With metrics export (Prometheus) - New in v0.4.0
pip install "claude-agent-framework[metrics]"

# With visualization (Matplotlib, Jinja2) - New in v0.4.0
pip install "claude-agent-framework[viz]"

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
├── config/              # Configuration system (v0.4.0)
│   ├── schema.py        # Pydantic validation models
│   ├── loader.py        # Multi-source config loading
│   ├── validator.py     # Configuration validation
│   └── profiles/        # Environment configs (dev/staging/prod)
├── core/                # Core abstractions
│   ├── base.py          # BaseArchitecture class
│   ├── session.py       # AgentSession management
│   └── registry.py      # Architecture registry
├── plugins/             # Plugin system (v0.4.0)
│   ├── base.py          # BasePlugin, PluginManager
│   └── builtin/         # Built-in plugins
│       ├── metrics_collector.py
│       ├── cost_tracker.py
│       └── retry_handler.py
├── metrics/             # Performance tracking (v0.4.0)
│   ├── collector.py     # Metrics collection
│   └── exporter.py      # JSON/CSV/Prometheus export
├── dynamic/             # Dynamic agent registry (v0.4.0)
│   ├── agent_registry.py
│   ├── loader.py
│   └── validator.py
├── observability/       # Observability tools (v0.4.0)
│   ├── logger.py        # Structured logging
│   ├── visualizer.py    # Session visualization
│   └── debugger.py      # Interactive debugging
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

## Documentation

### Quick Reference

- [README (Chinese)](README_CN.md) - 中文文档
- [Best Practices Guide](docs/BEST_PRACTICES.md) - Pattern selection and implementation tips
- [Best Practices (Chinese)](docs/BEST_PRACTICES_CN.md) - 最佳实践指南（中文）

### Architecture & Design (New in v0.4.0)

- [Architecture Selection Guide](docs/guides/architecture_selection/GUIDE.md) - Decision flowchart and comparison
- [架构选择指南（中文）](docs/guides/architecture_selection/GUIDE_CN.md)

### Customization Guides (New in v0.4.0)

- [Plugin Development Guide](docs/guides/customization/CUSTOM_PLUGINS.md) - Create custom plugins with lifecycle hooks
- [插件开发指南（中文）](docs/guides/customization/CUSTOM_PLUGINS_CN.md)

### Advanced Topics (New in v0.4.0)

- [Performance Tuning Guide](docs/guides/advanced/PERFORMANCE_TUNING.md) - Optimize latency and cost
- [性能优化指南（中文）](docs/guides/advanced/PERFORMANCE_TUNING_CN.md)

### API Reference (New in v0.4.0)

- [Core API Reference](docs/api/core.md) - init(), AgentSession, BaseArchitecture
- [核心API参考（中文）](docs/api/core_cn.md)
- [Plugins API Reference](docs/api/plugins.md) - BasePlugin, PluginManager, built-in plugins
- [插件API参考（中文）](docs/api/plugins_cn.md)

## Requirements

- Python 3.10+
- Claude Agent SDK
- ANTHROPIC_API_KEY environment variable

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
