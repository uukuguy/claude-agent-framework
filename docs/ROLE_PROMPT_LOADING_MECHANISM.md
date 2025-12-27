# Role Prompt 加载与构造机制

## 概述

本文档分析 claude-agent-framework 中 role prompt 的加载位置和最终 agent prompt 的构造过程。

---

## 1. Role Prompt 文件定义位置

### 核心定义：RoleDefinition

**文件**: `src/claude_agent_framework/core/roles.py`

```python
@dataclass
class RoleDefinition:
    role_type: RoleType
    description: str = ""
    required_tools: list[str] = field(default_factory=list)
    optional_tools: list[str] = field(default_factory=list)
    cardinality: RoleCardinality = RoleCardinality.EXACTLY_ONE
    default_model: str = "haiku"
    prompt_file: str = ""  # <-- 角色 prompt 文件名
    constraints: dict[str, Any] = field(default_factory=dict)
```

### 架构中的使用示例

**文件**: `src/claude_agent_framework/architectures/research/orchestrator.py`

```python
def get_role_definitions(self) -> dict[str, RoleDefinition]:
    return {
        "worker": RoleDefinition(
            role_type=RoleType.WORKER,
            prompt_file="worker.txt",  # 指向 prompts/worker.txt
            ...
        ),
        "synthesizer": RoleDefinition(
            role_type=RoleType.SYNTHESIZER,
            prompt_file="synthesizer.txt",
            ...
        ),
    }
```

### Prompt 文件物理位置

```
src/claude_agent_framework/architectures/{arch_name}/prompts/{role_name}.txt
```

例如：
- `architectures/research/prompts/worker.txt`
- `architectures/research/prompts/processor.txt`
- `architectures/research/prompts/synthesizer.txt`

---

## 2. Prompt 加载的完整流程

### 流程图

```
create_session()
    ↓
BaseArchitecture.__init__()
    ↓
_register_roles() → get_role_definitions()
    ↓
configure_agents() → _build_configured_agents()
    ↓
AgentInstanceConfig.to_agent_definition()
    ↓
session.run() → architecture.execute()
    ↓
to_sdk_agents() ← ★ 关键：这里加载所有 prompt
    ↓
AgentDefinitionConfig.load_merged_prompt()
    ↓
最终 prompt → SDK AgentDefinition
```

### 关键步骤详解

#### 步骤 1：AgentInstanceConfig 转换

**文件**: `src/claude_agent_framework/core/roles.py`

```python
class AgentInstanceConfig:
    def to_agent_definition(self, role_def: RoleDefinition, ...) -> AgentDefinitionConfig:
        return AgentDefinitionConfig(
            name=self.name,
            prompt_file=self.prompt_file,        # 业务层 prompt
            role_prompt_file=role_def.prompt_file,  # Framework 层 prompt
            ...
        )
```

#### 步骤 2：to_sdk_agents() - 核心加载点

**文件**: `src/claude_agent_framework/core/base.py`

```python
def to_sdk_agents(self) -> dict[str, Any]:
    """
    两层 prompt 组合：
    1. Role prompt (framework 层): 来自 RoleDefinition.prompt_file
    2. Instance prompt (业务层): 来自 AgentInstanceConfig.prompt_file

    最终 prompt = role_prompt + "\n\n# Business Context\n\n" + instance_prompt
    """
    agents = self.get_agents()
    result = {}

    for name, config in agents.items():
        # ★ 关键：加载并合并 prompt
        merged_prompt = config.load_merged_prompt(
            arch_prompts_dir=self.prompts_dir,
            custom_prompts_dir=self._custom_prompts_dir,
        )

        if merged_prompt:
            prompt = merged_prompt
        else:
            # 备选：使用 PromptComposer
            prompt = composer.compose(name)

        # 模板变量替换
        if self._template_vars and prompt:
            prompt = Template(prompt).safe_substitute(self._template_vars)

        result[name] = AgentDefinition(
            prompt=prompt,  # <-- 最终 prompt
            ...
        )
    return result
```

#### 步骤 3：load_merged_prompt() - 实际文件加载

**文件**: `src/claude_agent_framework/core/base.py`

```python
def load_merged_prompt(self, arch_prompts_dir: Path, custom_prompts_dir: Path | None = None) -> str:
    # 优先级 1：内联 prompt（最高）
    if self.prompt:
        return self.prompt

    # 优先级 2：加载 Framework 层 prompt
    role_prompt = ""
    if self.role_prompt_file:
        role_path = arch_prompts_dir / self.role_prompt_file
        if role_path.exists():
            role_prompt = role_path.read_text(encoding="utf-8").strip()

    # 优先级 3：加载业务层 prompt
    instance_prompt = ""
    if self.prompt_file and custom_prompts_dir:
        instance_path = custom_prompts_dir / self.prompt_file
        if instance_path.exists():
            instance_prompt = instance_path.read_text(encoding="utf-8").strip()

    # ★ 合并两层 prompt
    if role_prompt and instance_prompt:
        return f"{role_prompt}\n\n# Business Context\n\n{instance_prompt}"
    elif role_prompt:
        return role_prompt
    elif instance_prompt:
        return instance_prompt
    else:
        return ""
```

---

## 3. Prompt 优先级体系

### 完整优先级（从高到低）

```
优先级 1: 内联 prompt (AgentDefinitionConfig.prompt)
    ↓
优先级 2: 两层组合
    ├─ Framework 层: role_prompt_file
    │  └─ 位置: architectures/{arch}/prompts/{role}.txt
    │
    └─ 业务层: prompt_file
       └─ 位置: custom_prompts_dir/{agent}.txt
    ↓
优先级 3: PromptComposer 备选
    ├─ prompt_overrides[agent_name]  (代码级覆盖)
    ├─ custom_prompts_dir/{agent}.txt
    └─ business_templates/{template}/{agent}.txt
```

---

## 4. 最终 Prompt 构造示例

### 输入

**Framework 层** (`architectures/research/prompts/worker.txt`):
```
# Role: Research Worker

You are a Research Worker responsible for gathering information.

## Core Responsibilities
1. Execute targeted search queries
2. Collect quantitative data
...
```

**业务层** (`custom_prompts/market_context.txt`):
```
# Business Context: Market Research

Focus on:
- Market size and growth rates
- Competitive landscape
...
```

### 输出（最终 Agent Prompt）

```
# Role: Research Worker

You are a Research Worker responsible for gathering information.

## Core Responsibilities
1. Execute targeted search queries
2. Collect quantitative data
...

# Business Context

# Business Context: Market Research

Focus on:
- Market size and growth rates
- Competitive landscape
...
```

---

## 5. 关键代码文件索引

| 文件 | 功能 | 关键方法/属性 |
|-----|------|-------------|
| `core/roles.py` | Role 定义 | `RoleDefinition.prompt_file` |
| `core/roles.py` | Agent 实例配置 | `AgentInstanceConfig.to_agent_definition()` |
| `core/base.py` | Architecture 基类 | `to_sdk_agents()` ★ |
| `core/base.py` | Agent 配置 | `AgentDefinitionConfig.load_merged_prompt()` ★ |
| `core/prompt.py` | Prompt 合成器 | `PromptComposer.compose()` |
| `core/session.py` | 会话执行 | `AgentSession.run()` |

---

## 6. 总结

1. **定义位置**: `RoleDefinition.prompt_file` 在各架构的 `get_role_definitions()` 中定义

2. **文件位置**: `architectures/{arch}/prompts/{role}.txt`

3. **加载位置**: `BaseArchitecture.to_sdk_agents()` → `AgentDefinitionConfig.load_merged_prompt()`

4. **构造方式**: 两层组合（Framework 层 + 业务层），通过 `"\n\n# Business Context\n\n"` 连接

5. **最终传递**: 构造好的 prompt 传入 SDK 的 `AgentDefinition(prompt=...)`
