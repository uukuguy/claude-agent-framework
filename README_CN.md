# Claude Agent Framework

基于 [Claude Agent SDK](https://github.com/anthropics/claude-code-sdk-python) 的生产级多智能体编排框架。设计、组合和部署复杂的 AI 工作流，提供开箱即用的架构模式。

[English Documentation](README.md) | [最佳实践指南](docs/BEST_PRACTICES_CN.md)

## 概述

Claude Agent Framework 是一个生产级的多智能体 AI 系统编排层。它解决了复杂任务需要多种专业能力（研究、分析、代码生成、决策支持）而单一 LLM 提示词无法有效处理的根本性挑战。框架将这些任务分解为协调的工作流：主智能体编排专业化的子智能体，每个子智能体拥有专注的提示词、受限的工具访问权限和适配的模型选择。基于 Claude Agent SDK 构建，它提供了从实际应用中提炼的成熟模式、通过 Hook 机制实现的全链路可观测性，以及让你能在几分钟内从概念到可运行系统的简洁 API。

**核心特性：**

- **7 种预置模式** - Research、Pipeline、Critic-Actor、Specialist Pool、Debate、Reflexion、MapReduce
- **两行代码启动** - 极简初始化和运行
- **全链路可观测** - 基于 Hook 机制的结构化 JSONL 日志
- **成本可控** - 根据任务复杂度自动选择模型
- **可扩展架构** - 通过简单装饰器注册自定义模式

```python
from claude_agent_framework import init

session = init("research")
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

### 编排模式

框架提供 7 种模式，满足不同工作流需求：

| 模式 | 适用场景 | 流程 |
|------|----------|------|
| **Research** | 数据收集 | 并行工作者 → 聚合 |
| **Pipeline** | 顺序处理 | 阶段 A → B → C → D |
| **Critic-Actor** | 质量迭代 | 生成 ↔ 评估循环 |
| **Specialist Pool** | 专家路由 | 路由器 → 领域专家 |
| **Debate** | 决策分析 | 正方 ↔ 反方 → 裁判 |
| **Reflexion** | 复杂问题求解 | 执行 → 反思 → 改进 |
| **MapReduce** | 大规模处理 | 分割 → 映射 → 归约 |

详细实现指南请参阅 [最佳实践指南](docs/BEST_PRACTICES_CN.md)。

## 可用架构

| 架构 | 适用场景 | 核心模式 |
|------|----------|----------|
| **research** | 深度研究 | 主从协调、并行派发 |
| **pipeline** | 代码审查、内容创作 | 顺序流水线 |
| **critic_actor** | 代码优化、质量迭代 | 生成-评审循环 |
| **specialist_pool** | 技术支持、智能路由 | 专家池按需调用 |
| **debate** | 决策支持、风险评估 | 正反辩论 + 裁判 |
| **reflexion** | 复杂问题求解、调试 | 执行-反思-改进循环 |
| **mapreduce** | 大规模分析、批量处理 | 分治并行 + 聚合 |

## 快速开始

### 安装

```bash
# 基础安装
pip install -e .

# 安装所有依赖（包括 PDF 生成、图表等）
pip install -e ".[all]"
```

### 设置 API Key

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

### 运行

```bash
# 列出所有可用架构
python -m claude_agent_framework.cli --list

# 使用指定架构运行
python -m claude_agent_framework.cli --arch research -q "研究AI市场趋势"
python -m claude_agent_framework.cli --arch pipeline -q "实现用户登录功能"
python -m claude_agent_framework.cli --arch debate -q "是否应该使用微服务架构"

# 交互式模式
python -m claude_agent_framework.cli --arch research -i
```

### Makefile 命令

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
```

## 项目结构

```
claude_agent_framework/
├── cli.py                 # 统一 CLI 入口
├── config.py              # 配置管理
├── core/                  # 核心抽象层
│   ├── base.py            # BaseArchitecture 基类
│   ├── session.py         # AgentSession 会话管理
│   └── registry.py        # 架构注册表
├── architectures/         # 架构实现
│   ├── research/          # 研究架构
│   ├── pipeline/          # 流水线架构
│   ├── critic_actor/      # 评审架构
│   ├── specialist_pool/   # 专家池架构
│   ├── debate/            # 辩论架构
│   ├── reflexion/         # 反思架构
│   └── mapreduce/         # MapReduce 架构
├── utils/                 # 工具模块
│   ├── tracker.py         # Hook 追踪器
│   ├── transcript.py      # 日志记录
│   └── message_handler.py # 消息处理
├── files/                 # 工作目录
└── logs/                  # 会话日志
```

## 架构详解

### Research（研究架构）

主从协调模式，适用于深度研究任务。

```
用户请求
    ↓
Lead Agent (协调者)
    ├─→ Researcher-1 ──┐
    ├─→ Researcher-2 ──┼─→ 并行研究
    └─→ Researcher-3 ──┘
         ↓
    Data-Analyst (分析)
         ↓
    Report-Writer (报告)
         ↓
    输出文件
```

### Pipeline（流水线架构）

顺序执行模式，适用于代码审查和内容创作。

```
用户需求 → Architect → Coder → Reviewer → Tester → 输出
```

### Critic-Actor（评审架构）

生成-评审迭代模式，适用于代码优化。

```
while quality < threshold:
    content = Actor.generate()
    feedback = Critic.evaluate()
    if approved: break
```

### Specialist Pool（专家池架构）

智能路由模式，适用于技术支持。

```
用户问题 → Router → [Code Expert, Data Expert, Security Expert, ...] → 汇总
```

### Debate（辩论架构）

正反辩论模式，适用于决策支持。

```
辩题 → Proponent ↔ Opponent (N轮) → Judge → 裁决
```

### Reflexion（反思架构）

执行-反思-改进循环，适用于复杂问题求解。

```
while not success:
    result = Executor.execute()
    reflection = Reflector.analyze()
    strategy = reflection.improved_strategy
```

### MapReduce（分治架构）

并行分治模式，适用于大规模分析。

```
任务 → Splitter → [Mapper-1, Mapper-2, ...] → Reducer → 结果
```

## Python API

```python
from claude_agent_framework import get_architecture, AgentSession
import asyncio

# 获取架构
arch = get_architecture("research")()

# 创建会话
session = AgentSession(arch)

async def main():
    async for msg in session.run("研究AI市场趋势"):
        print(msg)

asyncio.run(main())
```

### 自定义架构

```python
from claude_agent_framework import register_architecture, BaseArchitecture

@register_architecture("my_custom_arch")
class MyCustomArchitecture(BaseArchitecture):
    name = "my_custom_arch"
    description = "我的自定义架构"

    def get_agents(self):
        return {...}

    async def execute(self, prompt, tracker=None, transcript=None):
        ...
```

## 日志输出

每次会话生成：
- `logs/session_YYYYMMDD_HHMMSS/transcript.txt` - 人类可读日志
- `logs/session_YYYYMMDD_HHMMSS/tool_calls.jsonl` - 结构化工具调用日志

## 开发

```bash
# 安装开发依赖
make dev

# 运行测试
make test

# 代码格式化
make format

# 代码检查
make lint
```

## 许可证

MIT License
