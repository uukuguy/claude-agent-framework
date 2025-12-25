# Core API Reference

**Version**: 1.0.0
**Last Updated**: 2025-12-26

This document provides complete API reference for Claude Agent Framework's core components.

---

## Table of Contents

1. [Initialization API](#initialization-api)
2. [AgentSession](#agentsession)
3. [BaseArchitecture](#basearchitecture)
4. [Configuration Classes](#configuration-classes)
5. [Utility Functions](#utility-functions)

---

## Initialization API

### `init()`

The recommended entry point for initializing the framework.

```python
def init(
    architecture: ArchitectureType = "research",
    *,
    model: ModelType = "haiku",
    verbose: bool = False,
    log_dir: Path | str | None = None,
    files_dir: Path | str | None = None,
    auto_setup: bool = True,
) -> AgentSession
```

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `architecture` | `ArchitectureType` | `"research"` | Architecture pattern to use. Options: `"research"`, `"pipeline"`, `"critic_actor"`, `"specialist_pool"`, `"debate"`, `"reflexion"`, `"mapreduce"` |
| `model` | `ModelType` | `"haiku"` | Default model for agents. Options: `"haiku"`, `"sonnet"`, `"opus"` |
| `verbose` | `bool` | `False` | Enable debug logging |
| `log_dir` | `Path \| str \| None` | `None` | Custom directory for logs (default: `logs/`) |
| `files_dir` | `Path \| str \| None` | `None` | Custom directory for output files (default: `files/`) |
| `auto_setup` | `bool` | `True` | Automatically create directories |

**Returns**: `AgentSession` - Ready-to-use session object

**Raises**:
- `InitializationError` - If `ANTHROPIC_API_KEY` not set or unknown architecture

**Example**:

```python
from claude_agent_framework import init

# Simple usage
session = init("research")

# With options
session = init(
    "pipeline",
    model="sonnet",
    verbose=True,
    log_dir="my_logs"
)

# Use the session
async for msg in session.run("Analyze market trends"):
    print(msg)
```

---

### `quick_query()`

Convenience function for one-off queries.

```python
async def quick_query(
    prompt: str,
    architecture: ArchitectureType = "research",
    model: ModelType = "haiku",
) -> list
```

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | `str` | (required) | The query to execute |
| `architecture` | `ArchitectureType` | `"research"` | Architecture to use |
| `model` | `ModelType` | `"haiku"` | Model to use |

**Returns**: `list` - All response messages from execution

**Example**:

```python
import asyncio
from claude_agent_framework import quick_query

# Quick single query
results = asyncio.run(quick_query("Analyze Python trends"))
print(results[-1])  # Print final message
```

**Note**: For multiple queries or streaming output, use `init()` instead.

---

### `get_available_architectures()`

Get all available architectures with descriptions.

```python
def get_available_architectures() -> dict[str, str]
```

**Returns**: `dict[str, str]` - Mapping of architecture names to descriptions

**Example**:

```python
from claude_agent_framework import get_available_architectures

architectures = get_available_architectures()
for name, desc in architectures.items():
    print(f"{name}: {desc}")

# Output:
# research: Deep research with parallel workers
# pipeline: Sequential stage processing
# ...
```

---

## AgentSession

Main session management class that wraps architecture execution.

### Class Definition

```python
class AgentSession:
    def __init__(
        self,
        architecture: BaseArchitecture,
        config: FrameworkConfig | None = None,
    ) -> None
```

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `architecture` | `BaseArchitecture` | (required) | Architecture instance to use |
| `config` | `FrameworkConfig \| None` | `None` | Framework configuration (uses default if None) |

---

### Methods

#### `setup()`

Initialize session resources.

```python
async def setup(self) -> None
```

**Description**: Sets up directories, logging, and initializes the architecture. Called automatically by `run()` if not already called.

**Raises**:
- `RuntimeError` - If `ANTHROPIC_API_KEY` not set

**Example**:

```python
session = init("research")
await session.setup()  # Optional - run() calls this automatically
```

---

#### `teardown()`

Cleanup session resources.

```python
async def teardown(self) -> None
```

**Description**: Closes transcript writers, cleans up architecture resources.

**Example**:

```python
session = init("research")
try:
    async for msg in session.run(prompt):
        print(msg)
finally:
    await session.teardown()
```

---

#### `run()`

Run the session with streaming output.

```python
async def run(self, prompt: str) -> AsyncIterator[Any]
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `prompt` | `str` | User input prompt |

**Yields**: Messages from architecture execution (text content, tool calls, etc.)

**Example**:

```python
session = init("research")

async for message in session.run("Analyze AI market trends"):
    # message can be:
    # - str: Text content
    # - dict: Tool call/result
    # - other: Architecture-specific data
    print(message)
```

---

#### `query()`

Convenience method to run and collect all messages.

```python
async def query(self, prompt: str) -> list[Any]
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `prompt` | `str` | User input prompt |

**Returns**: `list[Any]` - All messages from execution

**Example**:

```python
session = init("research")

messages = await session.query("Analyze market trends")
print(f"Received {len(messages)} messages")
print(messages[-1])  # Final result
```

---

### Context Manager Support

`AgentSession` supports async context manager for automatic cleanup:

```python
async with init("research") as session:
    result = await session.query("Analyze trends")
    # Teardown happens automatically
```

---

### Properties

#### `architecture`

Get the architecture instance.

```python
@property
def architecture(self) -> BaseArchitecture
```

**Example**:

```python
session = init("research")
print(session.architecture.name)  # "research"
print(session.architecture.description)
```

---

#### `config`

Get the framework configuration.

```python
@property
def config(self) -> FrameworkConfig
```

**Example**:

```python
session = init("research")
print(session.config.logs_dir)  # Path to logs directory
```

---

#### `session_dir`

Get current session log directory.

```python
@property
def session_dir(self) -> Path | None
```

**Returns**: `Path` to session directory, or `None` if not initialized

**Example**:

```python
session = init("research")
await session.setup()
print(f"Session logs: {session.session_dir}")
# Output: Session logs: logs/session-20251226-103045/
```

---

#### `tracker`

Get subagent tracker instance.

```python
@property
def tracker(self) -> SubagentTracker | None
```

**Returns**: `SubagentTracker` instance for inspecting tool calls

---

#### `transcript`

Get transcript writer instance.

```python
@property
def transcript(self) -> TranscriptWriter | None
```

**Returns**: `TranscriptWriter` instance for logging

---

## BaseArchitecture

Abstract base class that all architectures must inherit from.

### Class Definition

```python
class BaseArchitecture(ABC):
    name: str = "base"
    description: str = "Base architecture (abstract)"

    def __init__(
        self,
        model_config: AgentModelConfig | None = None,
        prompts_dir: Path | None = None,
        files_dir: Path | None = None,
    ) -> None
```

**Class Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Architecture identifier (override in subclass) |
| `description` | `str` | Human-readable description (override in subclass) |

**Init Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_config` | `AgentModelConfig \| None` | `None` | Model configuration for agents |
| `prompts_dir` | `Path \| None` | `None` | Directory containing prompt files |
| `files_dir` | `Path \| None` | `None` | Working directory for file operations |

---

### Abstract Methods

Subclasses **must** implement these methods:

#### `execute()`

Main execution logic.

```python
@abstractmethod
async def execute(
    self,
    prompt: str,
    tracker: SubagentTracker | None = None,
    transcript: TranscriptWriter | None = None,
) -> AsyncIterator[Any]
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `prompt` | `str` | User input |
| `tracker` | `SubagentTracker \| None` | Tool call tracker |
| `transcript` | `TranscriptWriter \| None` | Transcript writer |

**Yields**: Messages to display to user

---

#### `get_agents()`

Return agent definitions for this architecture.

```python
@abstractmethod
def get_agents(self) -> dict[str, AgentDefinitionConfig]
```

**Returns**: `dict[str, AgentDefinitionConfig]` - Mapping of agent names to their configurations

**Example**:

```python
def get_agents(self) -> dict[str, AgentDefinitionConfig]:
    return {
        "researcher": AgentDefinitionConfig(
            name="researcher",
            description="Conducts research on specific topics",
            tools=["WebSearch", "Read", "Write"],
            prompt_file="researcher.txt",
            model="haiku"
        ),
        "synthesizer": AgentDefinitionConfig(
            name="synthesizer",
            description="Synthesizes research findings",
            tools=["Read", "Write"],
            prompt_file="synthesizer.txt",
            model="sonnet"
        )
    }
```

---

### Optional Methods

Subclasses **may** override these methods:

#### `setup()`

Pre-execution initialization.

```python
async def setup(self) -> None
```

**Example**:

```python
async def setup(self) -> None:
    # Initialize resources
    self.cache = {}
    await super().setup()
```

---

#### `teardown()`

Post-execution cleanup.

```python
async def teardown(self) -> None
```

**Example**:

```python
async def teardown(self) -> None:
    # Cleanup resources
    self.cache.clear()
    await super().teardown()
```

---

#### `get_hooks()`

Custom hook configuration.

```python
def get_hooks(self) -> dict[str, list]
```

**Returns**: `dict[str, list]` - Hook configuration for Claude SDK

**Example**:

```python
def get_hooks(self) -> dict[str, list]:
    return {
        "PreToolUse": [HookMatcher(...)],
        "PostToolUse": [HookMatcher(...)],
    }
```

---

### Plugin Support

#### `add_plugin()`

Add a plugin to the architecture.

```python
def add_plugin(self, plugin: BasePlugin) -> None
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `plugin` | `BasePlugin` | Plugin instance to add |

**Example**:

```python
from claude_agent_framework.plugins.builtin import MetricsCollectorPlugin

session = init("research")
metrics = MetricsCollectorPlugin()
session.architecture.add_plugin(metrics)

await session.query("Analyze trends")
print(metrics.get_metrics())
```

---

#### `remove_plugin()`

Remove a plugin by name.

```python
def remove_plugin(self, plugin_name: str) -> None
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `plugin_name` | `str` | Name of plugin to remove |

---

### Properties

#### `prompts_dir`

Get prompts directory for this architecture.

```python
@property
def prompts_dir(self) -> Path
```

**Returns**: `Path` to prompts directory (default: `architectures/<name>/prompts/`)

---

#### `files_dir`

Get working directory for file operations.

```python
@property
def files_dir(self) -> Path
```

**Returns**: `Path` to files directory (default: `files/`)

---

## Configuration Classes

### `AgentModelConfig`

Model configuration for architecture agents.

```python
@dataclass
class AgentModelConfig:
    default: str = "haiku"
    overrides: dict[str, str] = field(default_factory=dict)
```

**Attributes**:

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `default` | `str` | `"haiku"` | Default model for all agents |
| `overrides` | `dict[str, str]` | `{}` | Per-agent model overrides |

**Methods**:

```python
def get_model(self, agent_name: str) -> str:
    """Get model for specific agent, falling back to default."""
```

**Example**:

```python
from claude_agent_framework.core.base import AgentModelConfig

config = AgentModelConfig(
    default="haiku",
    overrides={
        "lead": "sonnet",
        "synthesizer": "sonnet"
    }
)

print(config.get_model("researcher"))    # "haiku" (default)
print(config.get_model("lead"))          # "sonnet" (override)
```

---

### `AgentDefinitionConfig`

Configuration for a single agent.

```python
@dataclass
class AgentDefinitionConfig:
    name: str
    description: str
    tools: list[str] = field(default_factory=list)
    prompt: str = ""
    prompt_file: str = ""
    model: str = "haiku"
```

**Attributes**:

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | (required) | Agent identifier (used as subagent_type) |
| `description` | `str` | (required) | When to use this agent |
| `tools` | `list[str]` | `[]` | List of allowed tools |
| `prompt` | `str` | `""` | Inline prompt content |
| `prompt_file` | `str` | `""` | Path to prompt file (relative to prompts dir) |
| `model` | `str` | `"haiku"` | Model to use |

**Methods**:

```python
def load_prompt(self, prompts_dir: Path) -> str:
    """Load prompt content from file if prompt_file is set."""
```

**Example**:

```python
from claude_agent_framework.core.base import AgentDefinitionConfig

agent = AgentDefinitionConfig(
    name="researcher",
    description="Conducts web research",
    tools=["WebSearch", "Read", "Write"],
    prompt_file="researcher.txt",
    model="haiku"
)

# Load prompt from file
prompt_content = agent.load_prompt(Path("prompts"))
```

---

### `FrameworkConfig`

Global framework configuration.

```python
@dataclass
class FrameworkConfig:
    lead_agent_model: str = "haiku"
    logs_dir: Path = Path("logs")
    files_dir: Path = Path("files")
    enable_tracking: bool = True
    enable_transcripts: bool = True
```

**Attributes**:

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `lead_agent_model` | `str` | `"haiku"` | Default model for lead agent |
| `logs_dir` | `Path` | `Path("logs")` | Directory for session logs |
| `files_dir` | `Path` | `Path("files")` | Working directory for outputs |
| `enable_tracking` | `bool` | `True` | Enable tool call tracking |
| `enable_transcripts` | `bool` | `True` | Enable transcript logging |

**Methods**:

```python
def ensure_directories(self) -> None:
    """Create logs and files directories if they don't exist."""
```

**Example**:

```python
from claude_agent_framework.config import FrameworkConfig

config = FrameworkConfig(
    lead_agent_model="sonnet",
    logs_dir=Path("my_logs"),
    files_dir=Path("my_files")
)

config.ensure_directories()  # Create directories
```

---

## Utility Functions

### `validate_api_key()`

Check if ANTHROPIC_API_KEY is set.

```python
def validate_api_key() -> bool
```

**Returns**: `bool` - True if API key is set

**Example**:

```python
from claude_agent_framework.config import validate_api_key

if not validate_api_key():
    print("Please set ANTHROPIC_API_KEY environment variable")
```

---

### `get_architecture()`

Get architecture class by name.

```python
def get_architecture(name: str) -> type[BaseArchitecture]
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|---------|
| `name` | `str` | Architecture name |

**Returns**: `type[BaseArchitecture]` - Architecture class

**Raises**:
- `KeyError` - If architecture not found

**Example**:

```python
from claude_agent_framework.core import get_architecture

ArchClass = get_architecture("research")
arch = ArchClass()
```

---

### `register_architecture()`

Decorator to register custom architecture.

```python
def register_architecture(name: str) -> Callable
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|---------|
| `name` | `str` | Architecture name |

**Returns**: Decorator function

**Example**:

```python
from claude_agent_framework.core import register_architecture, BaseArchitecture

@register_architecture("my_custom")
class MyCustomArchitecture(BaseArchitecture):
    name = "my_custom"
    description = "My custom architecture"

    def get_agents(self):
        return {...}

    async def execute(self, prompt, tracker=None, transcript=None):
        ...

# Now usable with init()
session = init("my_custom")
```

---

## Type Aliases

```python
ArchitectureType = Literal[
    "research",
    "pipeline",
    "critic_actor",
    "specialist_pool",
    "debate",
    "reflexion",
    "mapreduce"
]

ModelType = Literal["haiku", "sonnet", "opus"]
```

---

## Exceptions

### `InitializationError`

Raised when framework initialization fails.

**Common Causes**:
- `ANTHROPIC_API_KEY` environment variable not set
- Unknown architecture name
- Configuration errors

**Example**:

```python
from claude_agent_framework import init, InitializationError

try:
    session = init("unknown_architecture")
except InitializationError as e:
    print(f"Initialization failed: {e}")
```

---

## Further Reading

- [Plugins API Reference](plugins.md) - Plugin system API
- [Architectures API Reference](architectures.md) - Built-in architecture APIs
- [Best Practices](../BEST_PRACTICES.md) - Usage guidelines
- [Architecture Guide](../guides/architecture_selection/GUIDE.md) - Choosing the right architecture

---

**Questions?** Open an issue on [GitHub](https://github.com/anthropics/claude-agent-framework).
