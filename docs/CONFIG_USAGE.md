# Advanced Configuration System Usage Examples

This document demonstrates how to use the new advanced configuration system.

## Installation

```bash
# Install with config extras (includes pydantic and pyyaml)
pip install 'claude-agent-framework[config]'

# Or install separately
pip install pydantic pyyaml
```

## Basic Usage

### 1. Using Default Configuration

```python
from claude_agent_framework.config import FrameworkConfigSchema

# Create with defaults
config = FrameworkConfigSchema()
print(f"Model: {config.lead_agent_model}")  # haiku
print(f"Max agents: {config.max_parallel_agents}")  # 5
```

### 2. Loading from YAML File

```python
from claude_agent_framework.config import ConfigLoader

# config.yaml:
# lead_agent_model: sonnet
# enable_logging: true
# max_parallel_agents: 10

config = ConfigLoader.from_yaml("config.yaml")
```

### 3. Loading from Environment Variables

```python
import os
from claude_agent_framework.config import ConfigLoader

# Set environment variables
os.environ["CLAUDE_LEAD_AGENT_MODEL"] = "opus"
os.environ["CLAUDE_MAX_PARALLEL_AGENTS"] = "15"

config = ConfigLoader.from_env()
```

### 4. Using Environment Profiles

```python
from claude_agent_framework.config import ConfigLoader

# Load development profile
dev_config = ConfigLoader.load_with_profile(profile="development")
# Uses haiku model, max 3 parallel agents

# Load production profile
prod_config = ConfigLoader.load_with_profile(profile="production")
# Uses sonnet model, max 10 parallel agents
```

### 5. Merging Configurations

```python
from claude_agent_framework.config import ConfigLoader, FrameworkConfigSchema

# Start with base config
base = FrameworkConfigSchema(
    lead_agent_model="haiku",
    max_parallel_agents=5,
)

# Load environment overrides
env_config = ConfigLoader.from_env()

# Merge (env overrides base)
final_config = ConfigLoader.merge_configs(base, env_config)
```

## Creating Custom Configurations

### Define Agents with Validation

```python
from claude_agent_framework.config import AgentConfigSchema, FrameworkConfigSchema

# Create custom agent
researcher = AgentConfigSchema(
    name="my-researcher",
    description="Custom research agent with specific focus",
    tools=["WebSearch", "Write"],
    prompt="You are a research specialist focusing on...",
    model="sonnet",
)

# Create framework config with custom agent
config = FrameworkConfigSchema(
    lead_agent_model="sonnet",
    subagents=[researcher],
    max_parallel_agents=8,
)
```

### Validation

```python
from claude_agent_framework.config import ConfigValidator, FrameworkConfigSchema
from pathlib import Path

config = FrameworkConfigSchema()
prompts_dir = Path("prompts")

# Validate configuration
errors = ConfigValidator.validate_config(config, prompts_dir)

if errors:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("Configuration is valid!")
```

### Strict Validation (Raises on Error)

```python
from claude_agent_framework.config import ConfigValidator

try:
    ConfigValidator.validate_and_raise(config, prompts_dir, strict=True)
    print("Config validated successfully!")
except ValueError as e:
    print(f"Validation failed: {e}")
```

## Custom YAML Configuration

Create a custom `my_config.yaml`:

```yaml
# Framework settings
lead_agent_model: sonnet
lead_agent_tools:
  - Task
  - Read
enable_logging: true
max_parallel_agents: 8
enable_metrics: true

# Custom agents
subagents:
  - name: web-researcher
    description: Research information from web sources
    tools:
      - WebSearch
      - Write
    prompt: "You are a web research specialist..."
    model: haiku

  - name: data-processor
    description: Process and analyze collected data
    tools:
      - Read
      - Write
      - Bash
    prompt: "You are a data processing specialist..."
    model: sonnet
```

Load it:

```python
from claude_agent_framework.config import ConfigLoader

config = ConfigLoader.from_yaml("my_config.yaml")
```

## Environment Profiles

The framework includes three built-in profiles:

### Development Profile (`development.yaml`)
- Model: haiku (fast, cheap)
- Max parallel agents: 3
- Metrics enabled: true

### Staging Profile (`staging.yaml`)
- Model: sonnet (balanced)
- Max parallel agents: 5
- Metrics enabled: true

### Production Profile (`production.yaml`)
- Model: sonnet (high quality)
- Max parallel agents: 10
- Metrics enabled: true

Custom profiles can be created in `src/claude_agent_framework/config/profiles/`.

## Backward Compatibility

The legacy configuration API is still fully supported:

```python
from claude_agent_framework.config import FrameworkConfig, AgentConfig

# Old API still works
config = FrameworkConfig()
agent = AgentConfig(
    name="researcher",
    description="Research agent",
    tools=["WebSearch", "Write"],
    prompt_file="researcher.txt",
)
```

## Type Safety

The new config system provides full type safety:

```python
from claude_agent_framework.config import ModelType, PermissionMode

config = FrameworkConfigSchema(
    lead_agent_model=ModelType.SONNET,  # Type-safe enum
    permission_mode=PermissionMode.BYPASS,
    max_parallel_agents=5,  # Must be 1-20
)
```

## Error Handling

The system provides clear validation errors:

```python
from claude_agent_framework.config import AgentConfigSchema

try:
    # This will fail: invalid tool name
    agent = AgentConfigSchema(
        name="test-agent",
        description="Test agent",
        tools=["InvalidTool"],
        prompt="Test",
    )
except ValueError as e:
    print(e)  # "Invalid tools: ['InvalidTool']. Valid tools are: Task, WebSearch, ..."
```

## Best Practices

1. **Use environment profiles** for different deployment environments
2. **Validate configs** before using them in production
3. **Store secrets** in environment variables, not YAML files
4. **Use type-safe enums** (ModelType, PermissionMode) instead of strings
5. **Enable metrics** in production for observability

## Advanced: Multi-Source Configuration

Combine file, environment, and profile configurations:

```python
from claude_agent_framework.config import ConfigLoader

# Priority order: file < env vars < profile
config = ConfigLoader.load_with_profile(
    config_path="base_config.yaml",  # Base settings
    profile="production",  # Production overrides
)
# Environment variables (CLAUDE_*) are also applied automatically
```
