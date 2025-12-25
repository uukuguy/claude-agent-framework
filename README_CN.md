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

## 生产级示例

框架包含 7 个生产级示例,展示真实业务场景的应用。每个示例演示特定架构模式如何解决真实的企业挑战。

### 示例概览

| 示例 | 架构 | 业务场景 | 核心设计模式 |
|------|------|----------|-------------|
| **01_competitive_intelligence** | Research | SaaS 竞品分析 | 并行数据收集 → 综合分析 |
| **02_pr_code_review** | Pipeline | 自动化 PR 审查 | 顺序阶段门控 + 质量阈值 |
| **03_marketing_content** | Critic-Actor | 营销文案优化 | 生成 → 评估 → 改进循环 |
| **04_it_support** | Specialist Pool | IT 支持路由 | 关键词专家分发 + 紧急度分类 |
| **05_tech_decision** | Debate | 技术决策支持 | 多轮辩论 + 加权标准评估 |
| **06_code_debugger** | Reflexion | 自适应调试 | 执行 → 反思 → 调整策略 |
| **07_codebase_analysis** | MapReduce | 大规模代码库分析 | 智能分片 → 并行映射 → 聚合 |

### 设计亮点

#### 1. 竞品情报分析(Research 架构)

**模式**:扇出/扇入并行工作者协调

**关键设计决策**:
- **并行派发**:多个研究员同时分析不同竞争对手
- **多渠道聚合**:官网、市场报告、客户评论 → 统一视图
- **SWOT 生成**:自动化优势/劣势/机会/威胁分析
- **结构化输出**:JSON/Markdown/PDF 报告,格式一致

**技术亮点**:
```python
# 并行研究员派发
主智能体 → [行业研究员, 竞品分析师 1, 竞品分析师 2, ...] → 报告生成器
# 每个研究员独立工作,结果由主智能体聚合
```

**使用场景**:需要快速收集多个目标的竞品情报,采用并行数据收集方式

---

#### 2. PR 代码审查(Pipeline 架构)

**模式**:顺序阶段处理 + 质量门控

**关键设计决策**:
- **5 阶段流水线**:架构 → 代码质量 → 安全 → 性能 → 测试覆盖率
- **可配置阈值**:最大复杂度(10)、最小覆盖率(80%)、最大文件大小(500行)
- **失败策略**:`stop_on_critical`(快速失败) vs `continue_all`(完整审计)
- **渐进式优化**:每个阶段基于前一阶段的发现

**技术亮点**:
```python
# 顺序执行 + 条件门控
阶段 1(架构) → [通过] → 阶段 2(质量) → [警告] → 阶段 3(安全) → ...
                                      ↓ [严重]
                                    停止(如果 stop_on_critical)
```

**使用场景**:代码变更必须通过多个独立审查检查点才能批准

---

#### 3. 营销内容优化(Critic-Actor 架构)

**模式**:通过生成-评估循环进行迭代优化

**关键设计决策**:
- **加权评估**:SEO(25%)、吸引力(30%)、品牌(25%)、准确性(20%)
- **品牌语调强制**:禁用短语检测、语调一致性检查
- **质量阈值**:得分 ≥ 85% 或达到最大迭代次数时停止
- **A/B 变体生成**:为同一信息生成多个角度

**技术亮点**:
```python
# 迭代改进循环
while 质量得分 < 阈值 and 迭代次数 < 最大值:
    内容 = Actor.generate()
    得分 = Critic.evaluate(内容)  # 多维度加权评分
    if 得分.总分 >= 阈值: break
    内容 = Actor.improve(得分.反馈)
```

**使用场景**:内容质量必须通过迭代优化达到严格的品牌和吸引力标准

---

#### 4. IT 支持(Specialist Pool 架构)

**模式**:动态专家路由 + 优先级派发

**关键设计决策**:
- **紧急度分类**:Critical(1小时 SLA)、High(4小时)、Medium(24小时)、Low(72小时)
- **关键词路由**:匹配问题关键词到专家专业领域
- **并行咨询**:复杂问题可触发多个专家(最多 3 个)
- **回退机制**:通用 IT 专家处理未匹配问题

**技术亮点**:
```python
# 动态专家选择
问题 → 紧急度分类器 → 关键词匹配器 → [网络, 数据库, 安全] → 结果整合
                                  ↓ (无匹配)
                              [通用 IT 专家]
```

**使用场景**:支持问题需要根据内容和紧急度智能路由到领域专家

---

#### 5. 技术决策(Debate 架构)

**模式**:对抗性辩论 + 结构化论证

**关键设计决策**:
- **3 轮结构**:开场论证 → 深度分析 → 反驳
- **加权标准**:技术(30%)、实施(25%)、成本(25%)、风险(20%)
- **证据基础**:论点必须引用数据、行业研究或技术规范
- **专家组评判**:多专家评估,允许不同意见

**技术亮点**:
```python
# 结构化多轮辩论
轮次 1: Proponent.argue() ↔ Opponent.argue()  # 开场立场
轮次 2: Proponent.analyze() ↔ Opponent.analyze()  # 证据基础
轮次 3: Proponent.rebuttal() ↔ Opponent.rebuttal()  # 反驳论证
最终: Judge.evaluate(所有论点, 加权标准)
```

**使用场景**:技术决策需要结构化辩论对权衡进行平衡分析

---

#### 6. 代码调试器(Reflexion 架构)

**模式**:通过反思循环进行自我改进

**关键设计决策**:
- **策略库**:错误跟踪分析、代码检查、假设测试、依赖检查
- **自适应策略选择**:反思器分析为何之前尝试失败并建议下一方法
- **根因分类**:对错误分类(逻辑错误、竞态条件、资源泄漏等)
- **预防建议**:从错误模式中学习并提出预防措施

**技术亮点**:
```python
# 执行-反思-改进循环
while not 找到根因 and 迭代次数 < 最大值:
    结果 = Executor.execute(当前策略)
    反思 = Reflector.analyze(结果, 历史)  # 为何失败?学到什么?
    下一策略 = Improver.select_strategy(反思)  # 调整方法
    历史.append({策略, 结果, 反思})
```

**使用场景**:调试复杂问题需要系统性探索并从失败尝试中学习

---

#### 7. 代码库分析(MapReduce 架构)

**模式**:分治并行 + 智能分片和聚合

**关键设计决策**:
- **分片策略**:按模块、按文件类型、按大小、按 git 变更频率
- **并行映射**:最多 10 个并发映射器分析不同代码块
- **加权评分**:质量(25%)、安全(30%)、可维护性(25%)、覆盖率(20%)
- **问题聚合**:去重、基于严重性的优先级排序、模块健康度评分

**技术亮点**:
```python
# 并行 map-reduce 工作流
代码库 → 智能分片器 → [映射器 1, 映射器 2, ..., 映射器 N] → 归约器
        (by_module)   (并行分析)                        (聚合、去重、优先级)
```

**使用场景**:分析大型代码库(500+ 文件)需要并行处理和智能结果聚合

---

### 通用实现模式

所有示例都演示了这些生产就绪的模式:

| 模式 | 实现方式 | 好处 |
|------|---------|------|
| **配置驱动** | YAML 配置 + 验证 | 无需代码更改即可轻松定制 |
| **结构化结果** | 一致的 JSON 输出格式 | 程序化访问和集成 |
| **错误处理** | Try/catch + 优雅降级 | 健壮的生产部署 |
| **日志记录** | 结构化 JSONL + 人类可读日志 | 调试和审计追踪 |
| **测试** | 单元 + 集成 + 端到端测试 | 质量保证和回归预防 |

### 快速开始

每个示例包含:
- ✅ 完整可运行代码,包含错误处理
- ✅ 配置文件,带详细注释
- ✅ 自定义组件和提示词工程
- ✅ 单元测试、集成测试、端到端测试
- ✅ 完整文档(中英双语)
- ✅ 使用指南和定制说明

详细实现规范请参阅 [生产级示例设计文档](docs/PRODUCTION_EXAMPLES_DESIGN_CN.md)。

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
