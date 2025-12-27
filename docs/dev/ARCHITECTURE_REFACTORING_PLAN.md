# 架构重构设计文档与实施计划

## 概述

参照 research 架构的设计模式，重构其他 6 个架构，实现：
1. Role-based 架构（`get_role_definitions()`）
2. 两层 Prompt 组合（Framework层 + 业务层）
3. Skills 实现
4. 生产级示例更新

---

## 一、当前状态

### 1.1 Research 架构（参考模板）

**已完成的设计模式**：
- `get_role_definitions()` 定义角色：worker, processor, synthesizer
- 使用 `RoleCardinality` 控制数量约束
- Framework prompts 是通用模板
- 生产级示例使用 `AgentInstanceConfig` 配置

**目录结构**：
```
architectures/research/
├── orchestrator.py      # get_role_definitions() 实现
├── config.py            # ResearchConfig 数据类
└── prompts/
    ├── lead_agent.txt   # 协调器（通用）
    ├── worker.txt       # 工作者（通用）
    ├── processor.txt    # 处理器（通用）
    └── synthesizer.txt  # 合成器（通用）
```

### 1.2 需要重构的架构

| 架构 | 当前模式 | 角色 | 复杂度 |
|------|---------|------|--------|
| Critic-Actor | `get_agents()` | actor, critic | 低 |
| Debate | `get_agents()` | proponent, opponent, judge | 低 |
| Reflexion | `get_agents()` | executor, reflector | 低 |
| MapReduce | `get_agents()` | mapper, reducer | 中 |
| Specialist Pool | ExpertConfig | router, specialist | 高 |
| Pipeline | StageConfig | stage_executor | 高 |

---

## 二、分阶段安排

### 第一阶段：简单双/三角色架构
- **Critic-Actor**（actor, critic）→ 03_marketing_content
- **Debate**（proponent, opponent, judge）→ 05_tech_decision
- **Reflexion**（executor, reflector）→ 06_code_debugger

### 第二阶段：可扩展角色架构
- **MapReduce**（mapper ONE_OR_MORE, reducer）→ 07_codebase_analysis
- **Specialist Pool**（router, specialist ONE_OR_MORE）→ 04_it_support

### 第三阶段：复杂流程架构
- **Pipeline**（stage_executor ONE_OR_MORE）→ 02_pr_code_review

---

## 三、第一阶段详细设计

### 3.1 Critic-Actor 架构

#### 角色定义

```python
def get_role_definitions(self) -> dict[str, RoleDefinition]:
    return {
        "actor": RoleDefinition(
            role_type=RoleType.EXECUTOR,
            description="Generate or improve content based on task and feedback",
            required_tools=["Read", "Write", "Edit"],
            optional_tools=["Glob", "Bash", "Skill"],
            cardinality=RoleCardinality.EXACTLY_ONE,
            default_model=self.critic_config.actor_model,
            prompt_file="actor.txt",
        ),
        "critic": RoleDefinition(
            role_type=RoleType.CRITIC,
            description="Evaluate content quality and provide improvement feedback",
            required_tools=["Read"],
            optional_tools=["Glob", "Grep", "Skill"],
            cardinality=RoleCardinality.EXACTLY_ONE,
            default_model=self.critic_config.critic_model,
            prompt_file="critic.txt",
        ),
    }
```

#### 生产级示例（03_marketing_content）

```
03_marketing_content/
├── main.py                          # 使用 agent_instances
├── config.yaml                      # 简化配置
├── prompts/
│   ├── content_creator.txt          # actor 业务层
│   └── brand_reviewer.txt           # critic 业务层
└── .claude/skills/
    ├── content-generation/SKILL.md
    └── brand-voice/SKILL.md
```

---

### 3.2 Debate 架构

#### 角色定义

```python
def get_role_definitions(self) -> dict[str, RoleDefinition]:
    return {
        "proponent": RoleDefinition(
            role_type=RoleType.ADVOCATE,
            description="Argue the pro position with evidence-based reasoning",
            required_tools=["Read"],
            optional_tools=["WebSearch", "Skill"],
            cardinality=RoleCardinality.EXACTLY_ONE,
            default_model=self.debate_config.proponent_model,
            prompt_file="proponent.txt",
        ),
        "opponent": RoleDefinition(
            role_type=RoleType.ADVOCATE,
            description="Argue the con position with counter-evidence",
            required_tools=["Read"],
            optional_tools=["WebSearch", "Skill"],
            cardinality=RoleCardinality.EXACTLY_ONE,
            default_model=self.debate_config.opponent_model,
            prompt_file="opponent.txt",
        ),
        "judge": RoleDefinition(
            role_type=RoleType.JUDGE,
            description="Evaluate arguments and render final verdict",
            required_tools=["Read"],
            optional_tools=["Skill"],
            cardinality=RoleCardinality.EXACTLY_ONE,
            default_model=self.debate_config.judge_model,
            prompt_file="judge.txt",
        ),
    }
```

#### 生产级示例（05_tech_decision）

```
05_tech_decision/
├── main.py
├── config.yaml
├── prompts/
│   ├── solution_advocate.txt        # proponent 业务层
│   ├── risk_analyst.txt             # opponent 业务层
│   └── tech_lead.txt                # judge 业务层
└── .claude/skills/
    ├── tech-evaluation/SKILL.md
    └── risk-assessment/SKILL.md
```

---

### 3.3 Reflexion 架构

#### 角色定义

```python
def get_role_definitions(self) -> dict[str, RoleDefinition]:
    return {
        "executor": RoleDefinition(
            role_type=RoleType.EXECUTOR,
            description="Execute tasks and attempt problem solutions",
            required_tools=["Read", "Write", "Edit", "Bash"],
            optional_tools=["Glob", "Grep", "Skill"],
            cardinality=RoleCardinality.EXACTLY_ONE,
            default_model=self.reflexion_config.executor_model,
            prompt_file="executor.txt",
        ),
        "reflector": RoleDefinition(
            role_type=RoleType.REFLECTOR,
            description="Analyze results and provide improvement strategies",
            required_tools=["Read"],
            optional_tools=["Glob", "Skill"],
            cardinality=RoleCardinality.EXACTLY_ONE,
            default_model=self.reflexion_config.reflector_model,
            prompt_file="reflector.txt",
        ),
    }
```

#### 生产级示例（06_code_debugger）

```
06_code_debugger/
├── main.py
├── config.yaml
├── prompts/
│   ├── debug_executor.txt           # executor 业务层
│   └── debug_analyst.txt            # reflector 业务层
└── .claude/skills/
    ├── debugging/SKILL.md
    └── root-cause-analysis/SKILL.md
```

---

## 四、两层 Prompt 组合设计

### 4.1 Framework 层（通用模板）

**设计原则**：
- 只包含角色的通用能力和工作流
- 不包含业务特定内容
- 可被任何业务场景复用

**示例**（actor.txt）：
```markdown
# Role: Content Actor

You are a Content Actor responsible for generating and iteratively improving content.

## Core Responsibilities
1. Generate high-quality initial content based on task requirements
2. Improve content based on Critic feedback
3. Document improvements made in each iteration

## Output Requirements
- Clearly mark improvement notes
- Maintain consistency across iterations
- Follow business-specified output format
```

### 4.2 业务层（应用特定）

**设计原则**：
- 包含具体业务上下文
- 引用可用的 Skills
- 指定输出位置和格式

**示例**（content_creator.txt）：
```markdown
# Business Context: Marketing Content Creation

You are creating marketing content for ${company_name}.

## Available Skills
Use the following Skills for methodology guidance:
- `content-generation`: Content creation best practices
- `brand-voice`: Brand voice and tone guidelines

## Output Location
Save content to: `files/content/{content_type}.md`
```

---

## 五、Skills 设计

### 5.1 SKILL.md 模板

```markdown
---
name: skill-name
description: 技能描述 / Skill description
---

# 技能名称 / Skill Name

## 目标 / Objectives
[技能帮助完成什么任务]

## 方法论 / Methodology
[详细步骤和最佳实践]

## 输出规范 / Output Specification
- 路径: `files/{category}/{filename}`
- 格式: [格式要求]

## 质量标准 / Quality Standards
- [标准列表]

## 错误处理 / Error Handling
- [错误场景和处理方式]
```

### 5.2 各示例 Skills 清单

| 示例 | Skills |
|------|--------|
| 03_marketing_content | content-generation, brand-voice |
| 05_tech_decision | tech-evaluation, risk-assessment |
| 06_code_debugger | debugging, root-cause-analysis |

---

## 六、文件修改清单

### 第一阶段 - Framework 层

| 文件 | 操作 |
|-----|------|
| `architectures/critic_actor/orchestrator.py` | 修改：添加 `get_role_definitions()` |
| `architectures/critic_actor/prompts/actor.txt` | 修改：重写为通用模板 |
| `architectures/critic_actor/prompts/critic.txt` | 修改：重写为通用模板 |
| `architectures/debate/orchestrator.py` | 修改：添加 `get_role_definitions()` |
| `architectures/debate/prompts/proponent.txt` | 修改：重写为通用模板 |
| `architectures/debate/prompts/opponent.txt` | 修改：重写为通用模板 |
| `architectures/debate/prompts/judge.txt` | 修改：重写为通用模板 |
| `architectures/reflexion/orchestrator.py` | 修改：添加 `get_role_definitions()` |
| `architectures/reflexion/prompts/executor.txt` | 修改：重写为通用模板 |
| `architectures/reflexion/prompts/reflector.txt` | 修改：重写为通用模板 |

### 第一阶段 - 生产级示例

| 文件 | 操作 |
|-----|------|
| `examples/production/03_marketing_content/main.py` | 修改 |
| `examples/production/03_marketing_content/prompts/*.txt` | 新建 |
| `examples/production/03_marketing_content/.claude/skills/*` | 新建 |
| `examples/production/05_tech_decision/main.py` | 修改 |
| `examples/production/05_tech_decision/prompts/*.txt` | 新建 |
| `examples/production/05_tech_decision/.claude/skills/*` | 新建 |
| `examples/production/06_code_debugger/main.py` | 修改 |
| `examples/production/06_code_debugger/prompts/*.txt` | 新建 |
| `examples/production/06_code_debugger/.claude/skills/*` | 新建 |

---

## 七、验收标准

### 架构层
- [ ] 三个架构实现 `get_role_definitions()`
- [ ] 通过 `RoleRegistry.validate_agents()` 验证
- [ ] Framework prompts 重写为通用模板
- [ ] 保持向后兼容

### 示例层
- [ ] 三个示例改用 `agent_instances` 配置
- [ ] 每个示例有 `prompts/` 目录
- [ ] 每个示例有 `.claude/skills/` 目录

### 测试
- [ ] 单元测试通过
- [ ] 角色验证测试通过

---

## 八、关键参考文件

- `src/claude_agent_framework/architectures/research/orchestrator.py`
- `src/claude_agent_framework/core/roles.py`
- `src/claude_agent_framework/core/types.py`
- `examples/production/01_competitive_intelligence/main.py`
