# Claude Agent Framework

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

基于 [Claude Agent SDK](https://github.com/anthropics/claude-code-sdk-python) 的生产级多智能体编排框架。设计、组合和部署复杂的 AI 工作流，提供开箱即用的架构模式。

[English Documentation](README.md) | [最佳实践指南](docs/BEST_PRACTICES_CN.md) | [角色类型系统](docs/ROLE_BASED_ARCHITECTURE_CN.md)

## 概述

Claude Agent Framework 是一个生产级的多智能体 AI 系统编排层。它解决了复杂任务需要多种专业能力（研究、分析、代码生成、决策支持）而单一 LLM 提示词无法有效处理的根本性挑战。框架将这些任务分解为协调的工作流：主智能体编排专业化的子智能体，每个子智能体拥有专注的提示词、受限的工具访问权限和适配的模型选择。基于 Claude Agent SDK 构建，它提供了从实际应用中提炼的成熟模式、通过 Hook 机制实现的全链路可观测性，以及让你能在几分钟内从概念到可运行系统的简洁 API。

**核心特性：**

- **7 种预置模式** - Research、Pipeline、Critic-Actor、Specialist Pool、Debate、Reflexion、MapReduce
- **两行代码启动** - 极简初始化和运行
- **角色类型架构** - 角色定义与智能体实例分离，灵活配置
- **生产级插件系统** - 生命周期钩子支持指标收集、成本追踪、重试处理
- **两层提示词** - 框架提示词 + 业务提示词，工作流可复用
- **全链路可观测** - 结构化 JSONL 日志、会话追踪、调试工具
- **成本可控** - 自动模型选择、单代理成本分解
- **可扩展架构** - 通过简单装饰器注册自定义模式

```python
from claude_agent_framework import create_session

session = create_session("research")
async for msg in session.run("分析 AI 市场趋势"):
    print(msg)
```

## 设计理念

### 为什么需要多智能体？

复杂任务通常需要多种专业能力，单一 LLM 提示词无法有效处理。以研究任务为例：需要网络搜索、数据分析、报告撰写——每个环节需要不同的工具、提示词甚至模型。单体方案会导致：

- **提示词膨胀**：一个提示词试图做所有事情，变得难以维护
- **工具过载**：智能体在某些阶段访问了不该使用的工具
- **质量下降**：万金油式的提示词不如专业化提示词效果好
- **成本浪费**：简单子任务也使用昂贵模型

### 核心架构

Claude Agent Framework 通过**智能体专业化与编排**解决这个问题：

```
用户请求
    ↓
主智能体（编排者）
    │
    ├── 分析任务需求
    ├── 分解为子任务
    ├── 派发给专业子智能体
    ├── 协调执行流程
    └── 综合最终输出
          ↓
    子智能体（专家）
    │
    ├── 针对特定任务的专注提示词
    ├── 最小化工具访问（最小权限）
    ├── 适当使用高性价比模型
    └── 通过文件系统通信（松耦合）
```

### 设计原则

| 原则 | 理由 |
|------|------|
| **职责分离** | 主智能体编排，子智能体执行——职责清晰 |
| **工具约束** | 每个智能体只获得所需工具——安全且专注 |
| **松耦合** | 基于文件系统的数据交换——智能体相互独立 |
| **可观测性** | Hook 机制捕获所有工具调用——便于调试和审计 |
| **成本优化** | 根据任务复杂度匹配模型能力 |

## 快速开始

```bash
pip install claude-agent-framework
export ANTHROPIC_API_KEY="your-api-key"
```

```python
from claude_agent_framework import create_session
import asyncio

async def main():
    session = create_session("research")
    async for msg in session.run("分析 2024 年 AI 市场趋势"):
        print(msg)

asyncio.run(main())
```

## 可用架构

| 架构 | 适用场景 | 核心模式 |
|------|----------|----------|
| **research** | 深度研究 | 主从协调、并行数据收集 |
| **pipeline** | 代码审查、内容创作 | 顺序阶段处理 |
| **critic_actor** | 质量迭代 | 生成-评审循环 |
| **specialist_pool** | 技术支持 | 专家路由和派发 |
| **debate** | 决策支持 | 正反辩论 + 裁判 |
| **reflexion** | 复杂问题求解 | 执行-反思-改进循环 |
| **mapreduce** | 大规模分析 | 并行映射 + 聚合 |

## 角色类型架构

框架采用**角色类型架构**，将抽象的角色定义与具体的智能体实例分离。这使得单一架构能够通过灵活的智能体配置支持多种业务场景。

### 核心概念

| 概念 | 描述 |
|------|------|
| **RoleType** | 语义角色类型（WORKER、PROCESSOR、SYNTHESIZER 等） |
| **RoleCardinality** | 数量约束（EXACTLY_ONE、ONE_OR_MORE 等） |
| **RoleDefinition** | 架构级角色规范，含工具和约束定义 |
| **AgentInstanceConfig** | 业务级具体智能体配置 |

### 使用示例

```python
from claude_agent_framework import create_session
from claude_agent_framework.core.roles import AgentInstanceConfig

# 为特定业务需求定义智能体实例
agents = [
    AgentInstanceConfig(
        name="market-researcher",
        role="worker",
        description="市场数据收集专员",
        prompt_file="prompts/market_researcher.txt",
    ),
    AgentInstanceConfig(
        name="tech-researcher",
        role="worker",
        description="技术趋势分析师",
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

# 使用角色配置创建会话
session = create_session("research", agent_instances=agents)
async for msg in session.run("分析 AI 市场趋势"):
    print(msg)
```

详细文档请参阅 [角色类型系统指南](docs/ROLE_BASED_ARCHITECTURE_CN.md)。

## 生产级示例

框架包含 **7 个生产级示例**，展示真实业务场景的应用。每个示例演示特定架构模式如何解决实际的企业挑战。

**📁 位置**：[`examples/production/`](examples/production/)
**📊 状态**：全部 7 个示例已完成并可投入生产
**📚 文档**：每个示例包含双语 README（EN/CN）、配置指南和架构文档

### 示例概览

| 示例 | 架构 | 业务场景 | 核心设计模式 | 状态 |
|------|------|----------|-------------|------|
| [**01_competitive_intelligence**](examples/production/01_competitive_intelligence/) | Research | SaaS 竞品分析 | 并行数据收集 → 综合分析 | ✅ 已完成 |
| [**02_pr_code_review**](examples/production/02_pr_code_review/) | Pipeline | 自动化 PR 审查 | 顺序阶段门控 + 质量阈值 | ✅ 已完成 |
| [**03_marketing_content**](examples/production/03_marketing_content/) | Critic-Actor | 营销文案优化 | 生成 → 评估 → 改进循环 | ✅ 已完成 |
| [**04_it_support**](examples/production/04_it_support/) | Specialist Pool | IT 支持路由 | 关键词专家分发 + 紧急度分类 | ✅ 已完成 |
| [**05_tech_decision**](examples/production/05_tech_decision/) | Debate | 技术决策支持 | 多轮辩论 + 加权标准评估 | ✅ 已完成 |
| [**06_code_debugger**](examples/production/06_code_debugger/) | Reflexion | 自适应调试 | 执行 → 反思 → 调整策略 | ✅ 已完成 |
| [**07_codebase_analysis**](examples/production/07_codebase_analysis/) | MapReduce | 大规模代码库分析 | 智能分片 → 并行映射 → 聚合 | ✅ 已完成 |

### 运行示例

```bash
# 进入示例目录
cd examples/production/01_competitive_intelligence

# 安装依赖
pip install -e ".[all]"

# 配置
cp config.example.yaml config.yaml
# 编辑 config.yaml 设置参数

# 运行
python main.py
```

## 架构图解

### Research 架构

```
用户请求
    ↓
Lead Agent (协调者)
    ├─→ Researcher-1 ─┐
    ├─→ Researcher-2 ─┼─→ 并行研究
    └─→ Researcher-3 ─┘
           ↓
    Data-Analyst
           ↓
    Report-Writer
           ↓
    输出文件
```

### Pipeline 架构

```
请求 → Architect → Coder → Reviewer → Tester → 输出
```

### Critic-Actor 架构

```
while quality < threshold:
    content = Actor.generate()
    feedback = Critic.evaluate()
    if approved: break
```

### Specialist Pool 架构

```
用户问题 → Router → [Code Expert, Data Expert, Security Expert, ...] → 汇总
```

### Debate 架构

```
辩题 → Proponent ↔ Opponent (N轮) → Judge → 裁决
```

### Reflexion 架构

```
while not success:
    result = Executor.execute()
    reflection = Reflector.analyze()
    strategy = reflection.improved_strategy
```

### MapReduce 架构

```
任务 → Splitter → [Mapper-1, Mapper-2, ...] → Reducer → 结果
```

## CLI 使用

### 运行架构

```bash
# 列出可用架构
python -m claude_agent_framework.cli --list

# 运行指定架构
python -m claude_agent_framework.cli --arch research -q "分析 AI 市场趋势"

# 交互模式
python -m claude_agent_framework.cli --arch pipeline -i

# 选择模型
python -m claude_agent_framework.cli --arch debate -m sonnet -q "是否应该使用微服务？"
```

## Python API

### 基本用法

```python
from claude_agent_framework import create_session

session = create_session("research")

async for msg in session.run("研究量子计算应用"):
    print(msg)
```

### 带选项

```python
session = create_session(
    "pipeline",
    model="sonnet",      # haiku, sonnet, 或 opus
    verbose=True,        # 启用调试日志
    log_dir="./logs",    # 自定义日志目录
)
```

### 单次查询

```python
from claude_agent_framework import quick_query
import asyncio

# 快速一次性查询
results = asyncio.run(quick_query("分析 Python 趋势", architecture="research"))
print(results[-1])
```

### 自定义架构

```python
from claude_agent_framework import register_architecture, BaseArchitecture
from claude_agent_framework.core.roles import RoleDefinition
from claude_agent_framework.core.types import RoleType, RoleCardinality

@register_architecture("my_custom")
class MyCustomArchitecture(BaseArchitecture):
    name = "my_custom"
    description = "我的自定义工作流"

    def get_role_definitions(self) -> dict[str, RoleDefinition]:
        return {
            "worker": RoleDefinition(
                role_type=RoleType.WORKER,
                description="执行任务",
                required_tools=["Read", "Write"],
                cardinality=RoleCardinality.ONE_OR_MORE,
            ),
        }

    async def execute(self, prompt, tracker=None, transcript=None):
        # 实现逻辑
        ...
```

### 会话生命周期

```python
# 手动管理
session = create_session("research")
try:
    async for msg in session.run(prompt):
        process(msg)
finally:
    await session.teardown()

# 上下文管理器（AgentSession 实现了 __aenter__/__aexit__）
async with create_session("research") as session:
    results = await session.query(prompt)
```

### 使用插件

```python
from claude_agent_framework import create_session
from claude_agent_framework.plugins.builtin import (
    MetricsCollectorPlugin,
    CostTrackerPlugin,
    RetryHandlerPlugin
)

session = create_session("research")

# 添加指标追踪
metrics_plugin = MetricsCollectorPlugin()
session.architecture.add_plugin(metrics_plugin)

# 添加成本追踪（带预算限制）
cost_plugin = CostTrackerPlugin(budget_usd=5.0)
session.architecture.add_plugin(cost_plugin)

# 运行会话
async for msg in session.run("分析市场"):
    print(msg)

# 获取指标
metrics = metrics_plugin.get_metrics()
print(f"成本: ${metrics.estimated_cost_usd:.4f}")
```

### 动态代理注册

```python
session = create_session("specialist_pool")

# 运行时添加新代理
session.architecture.add_agent(
    name="security_expert",
    description="网络安全专家",
    tools=["WebSearch", "Read"],
    prompt="你是一名网络安全专家...",
    model="sonnet"
)

# 列出所有代理（静态 + 动态）
agents = session.architecture.list_dynamic_agents()
print(f"动态代理: {agents}")
```

## 输出

每次会话生成：

- `logs/session_YYYYMMDD_HHMMSS/transcript.txt` - 人类可读对话日志
- `logs/session_YYYYMMDD_HHMMSS/tool_calls.jsonl` - 结构化工具调用记录
- `files/<architecture>/` - 架构特定输出（报告、图表等）

## 安装选项

```bash
# 基础安装
pip install claude-agent-framework

# 支持 PDF 生成
pip install "claude-agent-framework[pdf]"

# 支持图表生成
pip install "claude-agent-framework[charts]"

# 完整安装（所有功能）
pip install "claude-agent-framework[all]"

# 开发安装
pip install "claude-agent-framework[dev]"
```

## 项目结构

```
src/claude_agent_framework/
├── __init__.py              # 包导出 (v0.4.0)
├── session.py               # create_session() 入口点
├── cli.py                   # 命令行界面
├── architectures/           # 7 种内置架构实现
│   ├── research/            # ResearchArchitecture
│   ├── pipeline/            # PipelineArchitecture
│   ├── critic_actor/        # CriticActorArchitecture
│   ├── specialist_pool/     # SpecialistPoolArchitecture
│   ├── debate/              # DebateArchitecture
│   ├── reflexion/           # ReflexionArchitecture
│   └── mapreduce/           # MapReduceArchitecture
├── config/                  # 配置系统
│   ├── legacy.py            # FrameworkConfig, AgentConfig
│   └── schema.py            # Pydantic 验证模式
├── core/                    # 核心抽象
│   ├── base.py              # BaseArchitecture, AgentDefinitionConfig
│   ├── prompt.py            # PromptComposer - 两层提示词组合
│   ├── registry.py          # @register_architecture, get_architecture
│   ├── roles.py             # RoleDefinition, AgentInstanceConfig
│   ├── session.py           # AgentSession, CompositeSession
│   └── types.py             # RoleType, RoleCardinality, ModelType
├── dynamic/                 # 动态代理注册
├── metrics/                 # 性能追踪
├── observability/           # 结构化日志和可视化
├── plugins/                 # 插件系统及生命周期钩子
│   ├── base.py              # BasePlugin, PluginManager
│   └── builtin/             # MetricsCollector, CostTracker, RetryHandler
├── utils/                   # 工具模块
│   ├── tracker.py           # SubagentTracker, 工具调用记录
│   ├── transcript.py        # TranscriptWriter, 会话日志
│   ├── message_handler.py   # 消息处理
│   └── helpers.py           # quick_query 便捷函数
├── files/                   # 工作目录
└── logs/                    # 会话日志
```

## 开发

```bash
# 克隆并安装
git clone https://github.com/your-org/claude-agent-framework
cd claude-agent-framework
pip install -e ".[all]"

# 运行测试
make test

# 格式化代码
make format

# 代码检查
make lint
```

## Makefile 命令

```bash
make run              # 运行默认架构（research）
make run-research     # 运行 Research 架构
make run-pipeline     # 运行 Pipeline 架构
make run-critic       # 运行 Critic-Actor 架构
make run-specialist   # 运行 Specialist Pool 架构
make run-debate       # 运行 Debate 架构
make run-reflexion    # 运行 Reflexion 架构
make run-mapreduce    # 运行 MapReduce 架构
make list-archs       # 列出所有架构
make test             # 运行测试
make format           # 格式化代码
make lint             # 代码检查
```

## 文档

### 快速参考

- [README (English)](README.md) - 英文文档
- [Best Practices Guide](docs/BEST_PRACTICES.md) - 模式选择和实现技巧
- [最佳实践指南（中文）](docs/BEST_PRACTICES_CN.md)

### 架构与设计

- [Role-Based Architecture Guide](docs/ROLE_BASED_ARCHITECTURE.md) - 角色类型、约束和智能体实例化
- [角色类型系统指南（中文）](docs/ROLE_BASED_ARCHITECTURE_CN.md)
- [Prompt Writing Guide](docs/PROMPT_WRITING_GUIDE.md) - 两层提示词架构

### API 参考

- [Core API Reference](docs/api/core.md) - create_session(), AgentSession, BaseArchitecture
- [核心 API 参考（中文）](docs/api/core_cn.md)

## 环境要求

- Python 3.10+
- Claude Agent SDK
- ANTHROPIC_API_KEY 环境变量

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解指南。
