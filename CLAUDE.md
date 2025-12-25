# CLAUDE.md

Development guidance for Claude Agent Framework.

## Project Overview

Claude Agent Framework is a multi-architecture agent framework built on Claude Agent SDK. It provides 7 pre-built architecture patterns for common multi-agent workflows including research, development, decision support, and large-scale analysis.

### Core Design

The framework solves the problem of complex tasks requiring multiple specialized capabilities through **agent specialization and orchestration**:

- **Lead Agent**: Orchestrates workflow, decomposes tasks, dispatches subagents
- **Subagents**: Execute specific tasks with focused prompts and minimal tool access
- **Communication**: Agents exchange data via filesystem (loose coupling)
- **Observability**: Hook mechanism captures all tool calls for debugging and audit

### Key Principles

| Principle | Implementation |
|-----------|----------------|
| Separation of Concerns | Lead orchestrates, subagents execute |
| Tool Constraints | Each agent gets only needed tools |
| Loose Coupling | Filesystem-based data exchange |
| Cost Optimization | Match model to task complexity |

## Important Notes

- **Bilingual Documentation Required**: README and BEST_PRACTICES must have both English and Chinese versions (README.md/README_CN.md, BEST_PRACTICES.md/BEST_PRACTICES_CN.md)
- **Documentation Sync**: When major features are added or modified, all related documentation files must be updated synchronously

## Development Workflow

### Git Commit Strategy

**IMPORTANT**: Commit changes after each phase completion.

- ✅ **DO** commit immediately after completing each implementation phase
- ✅ **DO** include comprehensive commit messages with phase details
- ✅ **DO** ensure all tests pass before committing
- ✅ **DO** update work log (docs/dev/WORK_LOG.md) before committing

**Rationale**: Phase-by-phase commits provide:
- Clear development history and progress tracking
- Easy rollback to specific phase if needed
- Better code review and collaboration
- Atomic, well-documented changes

## Development Commands

```bash
# Sync dependencies (creates/updates uv.lock)
uv sync

# Sync with all optional groups
uv sync --all-groups

# Install package in editable mode
uv pip install -e .

# Install all dependencies (including dev, pdf, charts)
uv pip install -e ".[all]"

# Run tests
uv run pytest tests/ -v

# Run tests with coverage
uv run pytest tests/ -v --cov=claude_agent_framework --cov-report=html

# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Type check
uv run mypy claude_agent_framework

# Or use make commands (see Makefile)
make sync      # Sync dependencies
make dev       # Install with all groups
make test      # Run tests
make lint      # Lint code
make format    # Format code
```

## Project Structure

```
claude_agent_framework/
├── init.py              # Simplified entry point (init function)
├── __init__.py          # Package exports
├── config.py            # Configuration management
├── cli.py               # Command-line interface
├── agent.py             # Legacy entry point
├── core/                # Core abstractions
│   ├── base.py          # BaseArchitecture abstract class
│   ├── registry.py      # Architecture registration
│   └── session.py       # AgentSession lifecycle management
├── architectures/       # Built-in architecture implementations
│   ├── research/        # Master-worker pattern
│   ├── pipeline/        # Sequential stages
│   ├── critic_actor/    # Generate-evaluate loop
│   ├── specialist_pool/ # Expert routing
│   ├── debate/          # Pro-con deliberation
│   ├── reflexion/       # Execute-reflect cycle
│   └── mapreduce/       # Parallel map-reduce
├── utils/               # Utilities
│   ├── tracker.py       # SubagentTracker, tool call recording
│   ├── transcript.py    # TranscriptWriter, session logging
│   └── message_handler.py # Message processing
├── examples/            # Example code
├── files/               # Working directory for outputs
└── logs/                # Session logs
```

## Key Patterns

### 1. Simplified Initialization

```python
from claude_agent_framework import init

session = init("research")  # Returns ready-to-use session
async for msg in session.run("Analyze AI trends"):
    print(msg)
```

### 2. Architecture Registration

```python
from claude_agent_framework import register_architecture, BaseArchitecture

@register_architecture("my_arch")
class MyArchitecture(BaseArchitecture):
    name = "my_arch"
    description = "Custom architecture"

    def get_agents(self):
        return {...}

    async def execute(self, prompt, tracker=None, transcript=None):
        ...
```

### 3. Session Lifecycle

```python
session = init("research")
try:
    async for msg in session.run(prompt):
        process(msg)
finally:
    await session.teardown()

# Or use context manager
async with init("research") as session:
    results = await session.query(prompt)
```

## Adding New Architectures

1. Create directory: `architectures/new_arch/`
2. Create files:
   - `__init__.py` - exports
   - `config.py` - architecture-specific config
   - `orchestrator.py` - main architecture class
   - `prompts/` - agent prompts

3. Implement orchestrator:
```python
from claude_agent_framework.core import register_architecture, BaseArchitecture

@register_architecture("new_arch")
class NewArchitecture(BaseArchitecture):
    name = "new_arch"
    description = "Description of the architecture"

    def get_agents(self) -> dict[str, AgentDefinitionConfig]:
        # Return agent definitions
        ...

    async def execute(self, prompt, tracker=None, transcript=None):
        # Implementation
        ...
```

4. Add import to `architectures/__init__.py`
5. Add tests in `tests/`

## Code Style

- **Python version**: 3.10+
- **Line length**: 100 characters (enforced by ruff)
- **Type hints**: Required for all public APIs
- **Docstrings**: Google-style for public APIs
- **Async**: All I/O operations use async/await
- **Imports**: Use `TYPE_CHECKING` to avoid circular imports

## Testing

```python
import pytest
from claude_agent_framework import init

@pytest.mark.asyncio
async def test_architecture():
    session = init("research")
    assert session.architecture.name == "research"
    await session.teardown()
```

## Architecture Overview

| Architecture | Pattern | Use Case | Production Example |
|--------------|---------|----------|-------------------|
| research | Master-worker parallel | Deep research, data gathering | 01_competitive_intelligence |
| pipeline | Sequential stages | Code review, content creation | 02_pr_code_review |
| critic_actor | Generate-evaluate loop | Quality improvement, optimization | 03_marketing_content |
| specialist_pool | Expert routing | Technical support, Q&A | 04_it_support |
| debate | Pro-con deliberation | Decision support, risk assessment | 05_tech_decision |
| reflexion | Execute-reflect-improve | Complex problem solving | 06_code_debugger |
| mapreduce | Parallel map + reduce | Large-scale analysis | 07_codebase_analysis |

## Production Implementation Patterns

The framework includes 7 production-grade examples (`examples/production/`) demonstrating real-world business scenarios. Each example showcases proven implementation patterns:

### Common Patterns

1. **Configuration-Driven Design**
   - All parameters in YAML config files with validation
   - Environment-specific settings (development, staging, production)
   - No hardcoded values in source code

2. **Structured Results**
   - Consistent JSON output schema across all examples
   - Programmatic access for automation and integration
   - Multiple output formats (JSON, Markdown, PDF)

3. **Robust Error Handling**
   - Try/catch blocks at all I/O boundaries
   - Graceful degradation (partial results better than total failure)
   - Detailed error messages with context
   - Resource cleanup in finally blocks

4. **Comprehensive Logging**
   - Structured JSONL for tool call tracking
   - Human-readable transcript logs
   - Separate log levels (DEBUG, INFO, WARNING, ERROR)
   - Session-based log organization

5. **Production Testing**
   - Unit tests for core functions
   - Integration tests for end-to-end workflows
   - Mock-based testing for external dependencies
   - 100% test pass requirement before release

### Architecture-Specific Patterns

| Example | Architecture | Key Implementation Patterns |
|---------|--------------|----------------------------|
| **Competitive Intelligence** | Research | Parallel worker dispatch, SWOT analysis generation, multi-channel data aggregation |
| **PR Code Review** | Pipeline | Sequential stage gating, configurable failure strategies, threshold-based quality gates |
| **Marketing Content** | Critic-Actor | Weighted multi-dimensional scoring, brand voice enforcement, A/B variant generation |
| **IT Support** | Specialist Pool | Keyword-based routing, urgency categorization, parallel specialist consultation |
| **Tech Decision** | Debate | Multi-round deliberation, weighted criteria evaluation, evidence-based argumentation |
| **Code Debugger** | Reflexion | Strategy execution, reflection analysis, adaptive improvement, root cause taxonomy |
| **Codebase Analysis** | MapReduce | Intelligent chunking strategies, parallel mapping, weighted scoring, issue aggregation |

### When to Use Each Pattern

**Research Architecture** - Use when:
- Task requires gathering data from multiple independent sources
- Sources can be queried in parallel
- Final result needs aggregation from all sources
- Example: Market research, competitive analysis, literature reviews

**Pipeline Architecture** - Use when:
- Task has clear sequential stages
- Each stage depends on previous stage's output
- Need quality gates between stages
- Example: Code review, content creation workflows, multi-step approval processes

**Critic-Actor Architecture** - Use when:
- Output quality needs iterative improvement
- Can define clear evaluation criteria
- Have quality threshold to meet
- Example: Content optimization, code refactoring, design iteration

**Specialist Pool Architecture** - Use when:
- Requests need routing to domain experts
- Can define keywords/criteria for routing
- Multiple specialists may be needed for complex requests
- Example: Technical support, Q&A systems, diagnostic systems

**Debate Architecture** - Use when:
- Decision requires examining tradeoffs
- Want balanced pro/con analysis
- Need evidence-based evaluation
- Example: Technology selection, architecture decisions, vendor evaluation

**Reflexion Architecture** - Use when:
- Problem requires trial-and-error exploration
- Can learn from failed attempts
- Strategy needs adapting based on results
- Example: Debugging, root cause analysis, optimization problems

**MapReduce Architecture** - Use when:
- Large dataset needs processing (500+ files)
- Work can be divided into independent chunks
- Results need aggregation and deduplication
- Example: Codebase analysis, batch processing, large-scale audits

## Related Documentation

- README.md / README_CN.md - User documentation (English/Chinese)
- docs/BEST_PRACTICES.md / docs/BEST_PRACTICES_CN.md - Best practices guide (English/Chinese)
- examples/production/*/README.md - Individual example documentation
