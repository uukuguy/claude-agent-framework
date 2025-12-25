# Claude Agent Framework - 最佳实践指南

> 使用 Claude Agent Framework 构建多智能体系统的完整开发指南

## 目录

1. [设计理念](#1-设计理念)
2. [架构模式](#2-架构模式)
3. [核心组件](#3-核心组件)
4. [多智能体编排](#4-多智能体编排)
5. [Hook 机制](#5-hook-机制)
6. [工具分配](#6-工具分配)
7. [提示词工程](#7-提示词工程)
8. [状态管理](#8-状态管理)
9. [错误处理](#9-错误处理)
10. [日志与审计](#10-日志与审计)
11. [配置管理](#11-配置管理)
12. [完整示例](#12-完整示例)

---

## 1. 设计理念

### 1.1 为什么需要多智能体？

复杂任务通常需要多种专业能力，单一 LLM 提示词无法有效处理。以研究任务为例：需要网络搜索、数据分析、报告撰写——每个环节需要不同的工具、提示词甚至模型。单体方案会导致：

- **提示词膨胀**：一个提示词试图做所有事情，变得难以维护
- **工具过载**：智能体在某些阶段访问了不该使用的工具
- **质量下降**：万金油式的提示词不如专业化提示词效果好
- **成本浪费**：简单子任务也使用昂贵模型

解决方案：**智能体专业化与编排** - 将复杂任务分解为由主智能体协调的专业化智能体。

### 1.2 框架概述

Claude Agent Framework 为多智能体系统提供 **7 种不同的编排模式**。虽然所有架构共享通用设计原则，但每种架构都实现了适合特定问题领域的独特工作流模式。

### 1.3 编排模式

每种架构实现不同的编排模式：

| 架构 | 模式 | 流程 | 最适用于 |
|------|------|------|----------|
| **Research** | 扇出/扇入 | 主智能体 → [工作者并行] → 聚合器 | 数据收集、深度研究 |
| **Pipeline** | 顺序链 | 阶段 A → B → C → D | 代码审查、内容创作 |
| **Critic-Actor** | 迭代优化 | 生成 ↔ 评估（循环） | 质量优化 |
| **Specialist Pool** | 动态路由 | 路由器 → 专家 → 综合 | 技术支持、问答 |
| **Debate** | 对抗辩论 | 正方 ↔ 反方（N轮）→ 裁判 | 决策支持 |
| **Reflexion** | 自我改进循环 | 执行 → 反思 → 改进 | 复杂问题求解 |
| **MapReduce** | 分治并行 | 分割 → [映射并行] → 归约 | 大规模分析 |

### 1.4 模式图示

**扇出/扇入（Research）**
```
主智能体 ─┬─→ 工作者 1 ─┐
          ├─→ 工作者 2 ─┼─→ 聚合器 → 输出
          └─→ 工作者 3 ─┘
```

**顺序链（Pipeline）**
```
阶段 A → 阶段 B → 阶段 C → 阶段 D → 输出
```

**迭代优化（Critic-Actor）**
```
┌─────────────────────────┐
│  Actor ──→ Critic       │
│    ↑         │          │
│    └─────────┘ (重复)   │
└─────────────────────────┘
```

**动态路由（Specialist Pool）**
```
查询 → 路由器 ─┬─→ 专家 A ─┐
              ├─→ 专家 B ─┼─→ 综合器
              └─→ 专家 C ─┘
```

**对抗辩论（Debate）**
```
议题 → 正方 ↔ 反方（N轮）→ 裁判 → 裁决
```

**自我改进循环（Reflexion）**
```
┌─────────────────────────────────┐
│  执行器 → 反思器 → 改进        │
│      ↑                │        │
│      └────────────────┘        │
└─────────────────────────────────┘
```

**分治并行（MapReduce）**
```
任务 → 分割器 ─┬─→ 映射器 1 ─┐
              ├─→ 映射器 2 ─┼─→ 归约器 → 结果
              └─→ 映射器 3 ─┘
```

### 1.5 通用设计原则

尽管编排模式不同，所有架构共享这些核心原则：

| 原则 | 描述 | 实现方式 |
|------|------|----------|
| **职责分离** | 每个智能体只做一件事 | 主智能体编排，子智能体执行特定任务 |
| **工具约束** | 限制可用工具集 | 每个智能体精确控制 `allowed_tools` |
| **松耦合** | 智能体通过文件系统交换数据 | 标准目录结构 + Glob/Read/Write |
| **可观测性** | 全链路追踪能力 | Hook 机制 + JSONL 日志 |
| **成本优化** | 明智选择模型 | 子智能体使用 Haiku 以降低成本 |
| **可扩展性** | 易于添加新模式 | 基于注册表的架构系统 |
| **类型安全** | 全程强类型 | Pydantic 模型、类型提示 |

### 1.6 选择合适的模式

| 场景 | 推荐模式 | 原因 |
|------|----------|------|
| 从多个来源收集信息 | **Research**（扇出/扇入） | 并行数据收集，然后综合 |
| 有明确交接的逐步处理 | **Pipeline**（顺序链） | 清晰的阶段边界，渐进式优化 |
| 通过反馈进行质量改进 | **Critic-Actor**（迭代） | 生成-评估循环直到达到阈值 |
| 将查询路由到领域专家 | **Specialist Pool**（动态） | 将查询类型匹配到专家能力 |
| 分析决策的利弊 | **Debate**（对抗） | 结构化论证，平衡分析 |
| 需要反思的复杂问题 | **Reflexion**（自我改进） | 从尝试中学习，优化策略 |
| 并行处理大型数据集 | **MapReduce**（分治） | 并行处理，高效聚合 |

---

## 2. 架构模式

### 2.1 模式选择指南

| 模式 | 最适用于 | 关键特征 |
|------|----------|----------|
| **Research** | 数据收集、分析 | 并行工作者 → 综合 |
| **Pipeline** | 顺序工作流 | 阶段 A → 阶段 B → 阶段 C |
| **Critic-Actor** | 质量迭代 | 生成 ↔ 评估循环 |
| **Specialist Pool** | 专家路由 | 按领域动态分发 |
| **Debate** | 决策分析 | 正反辩论 + 裁判 |
| **Reflexion** | 复杂问题求解 | 执行 → 反思 → 改进 |
| **MapReduce** | 大规模处理 | 分割 → 并行映射 → 归约 |

### 2.2 模式内部结构

#### Research 模式

```
                    ┌──────────────┐
                    │   主智能体    │
                    │  （协调者）   │
                    └──────┬───────┘
                           │ 任务分解
            ┌──────────────┼──────────────┐
            ↓              ↓              ↓
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │ 研究员 1 │  │ 研究员 2 │  │ 研究员 3 │
      └────┬─────┘  └────┬─────┘  └────┬─────┘
           │             │             │
           └──────┬──────┴──────┬──────┘
                  ↓             ↓
           files/research_notes/*.md
                        ↓
                ┌──────────────┐
                │   数据分析师  │
                └──────┬───────┘
                       ↓
                files/charts/*.png
                       ↓
                ┌──────────────┐
                │   报告撰写者  │
                └──────┬───────┘
                       ↓
                files/reports/*.pdf
```

#### Pipeline 模式

```
┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐
│ 架构师 │ → │ 编码者 │ → │ 审查者 │ → │ 测试者 │
└────────┘   └────────┘   └────────┘   └────────┘
     │            │            │            │
     ↓            ↓            ↓            ↓
   设计         实现         反馈         测试
```

#### Critic-Actor 模式

```
┌─────────────────────────────────────────┐
│                                         │
│   ┌─────────┐         ┌─────────┐      │
│   │  Actor  │ ──────→ │  Critic │      │
│   └────┬────┘         └────┬────┘      │
│        ↑    内容           │           │
│        │                   │ 反馈      │
│        └───────────────────┘           │
│                                         │
│   while 质量 < 阈值                     │
└─────────────────────────────────────────┘
```

---

## 3. 核心组件

### 3.1 初始化

框架提供简化的入口点：

```python
from claude_agent_framework import init

# 最简用法 - 两行代码启动
session = init("research")
async for msg in session.run("分析 AI 市场趋势"):
    print(msg)
```

### 3.2 架构组件

每个架构包含：

```
architectures/<name>/
├── __init__.py          # 导出
├── config.py            # 架构特定配置
├── orchestrator.py      # 主架构类
└── prompts/             # 智能体提示词
    ├── lead_agent.txt
    ├── agent_a.txt
    └── agent_b.txt
```

### 3.3 BaseArchitecture 接口

```python
from claude_agent_framework.core import BaseArchitecture, register_architecture

@register_architecture("my_architecture")
class MyArchitecture(BaseArchitecture):
    """自定义架构实现。"""

    name = "my_architecture"
    description = "在架构列表中显示的描述"

    def get_agents(self) -> dict[str, AgentDefinitionConfig]:
        """定义子智能体及其配置。"""
        return {
            "worker": AgentDefinitionConfig(
                name="worker",
                description="执行特定任务",
                tools=["Read", "Write"],
                prompt_file="worker.txt",
            ),
        }

    async def execute(
        self,
        prompt: str,
        tracker: SubagentTracker | None = None,
        transcript: TranscriptWriter | None = None,
    ) -> AsyncIterator[Any]:
        """执行架构工作流。"""
        # 实现
        ...
```

### 3.4 AgentSession

管理完整的会话生命周期：

```python
session = init("research")

try:
    async for msg in session.run("查询"):
        print(msg)
finally:
    await session.teardown()  # 清理

# 或使用上下文管理器
async with init("research") as session:
    results = await session.query("查询")
```

---

## 4. 多智能体编排

### 4.1 并行派发

主智能体同时派发多个子智能体：

```python
# 在主智能体提示词中：
"""
# 规则
1. 你只能使用 Task 工具派发子智能体
2. 绝不自己执行研究、分析或写作
3. 将请求分解为 2-4 个独立的子主题
4. 并行派发研究员（不是顺序）
5. 等待所有研究完成后再派发分析师
"""
```

### 4.2 文件系统协调

智能体通过标准目录结构通信：

```python
FILE_STRUCTURE = {
    "files/research_notes/": "研究员输出 → 分析师输入",
    "files/data/":           "分析师输出 → 报告者输入",
    "files/charts/":         "分析师图表 → 报告者引用",
    "files/reports/":        "报告者最终输出",
}
```

### 4.3 主智能体模板

```text
# 角色定义
你是研究协调员，负责任务分解和子智能体编排。

# 核心规则
1. 你只能使用 Task 工具派发子智能体
2. 绝不自己执行研究、分析或写作
3. 将研究请求分解为 2-4 个独立的子主题
4. 并行派发研究员（不是顺序）
5. 等待所有研究完成后再派发分析师
6. 最后派发报告者生成输出

# 工作流程
1. 分析用户请求 → 识别子主题
2. 并行派发研究员 → 收集信息
3. 派发分析师 → 处理数据
4. 派发报告者 → 生成报告
5. 向用户报告完成状态

# 可用子智能体
- researcher: 网络搜索和信息收集
- data-analyst: 数据处理和可视化
- report-writer: 最终报告生成
```

---

## 5. Hook 机制

### 5.1 Hook 类型

| Hook 类型 | 触发时机 | 用途 |
|-----------|----------|------|
| `PreToolUse` | 工具执行前 | 输入验证、权限检查、日志记录 |
| `PostToolUse` | 工具执行后 | 结果捕获、错误处理、指标收集 |
| `Notification` | 通知事件 | 状态更新、进度报告 |

### 5.2 Hook 配置

```python
from claude_agent_sdk import HookMatcher

hooks = {
    'PreToolUse': [
        HookMatcher(
            matcher=None,  # None = 匹配所有工具
            hooks=[tracker.pre_tool_use_hook]
        )
    ],
    'PostToolUse': [
        HookMatcher(
            matcher=None,
            hooks=[tracker.post_tool_use_hook]
        )
    ]
}
```

### 5.3 SubagentTracker 实现

```python
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime

@dataclass
class ToolCallRecord:
    """单个工具调用记录。"""
    timestamp: str
    tool_name: str
    tool_input: dict[str, Any]
    tool_use_id: str
    subagent_type: str
    parent_tool_use_id: str | None = None
    tool_output: Any = None
    error: str | None = None

class SubagentTracker:
    """追踪子智能体生成和工具调用。"""

    def __init__(self, log_file_path: str):
        self.sessions: dict[str, SubagentSession] = {}
        self.tool_call_records: dict[str, ToolCallRecord] = {}
        self._current_parent_id: str | None = None
        self.subagent_counters: dict[str, int] = {}
        self._log_file = open(log_file_path, 'w')

    async def pre_tool_use_hook(
        self,
        hook_input: dict[str, Any],
        tool_use_id: str,
        context: Any
    ) -> dict[str, Any]:
        """工具执行前 Hook。"""
        tool_name = hook_input['tool_name']
        tool_input = hook_input['tool_input']

        # 确定所属智能体
        subagent_type = "LEAD"
        if self._current_parent_id and self._current_parent_id in self.sessions:
            subagent_type = self.sessions[self._current_parent_id].subagent_id

        # 创建记录
        record = ToolCallRecord(
            timestamp=datetime.now().isoformat(),
            tool_name=tool_name,
            tool_input=tool_input,
            tool_use_id=tool_use_id,
            subagent_type=subagent_type,
            parent_tool_use_id=self._current_parent_id
        )
        self.tool_call_records[tool_use_id] = record

        return {'continue_': True}
```

---

## 6. 工具分配

### 6.1 内置工具

| 工具 | 用途 | 典型使用场景 |
|------|------|--------------|
| `Task` | 派发子智能体 | 主智能体编排 |
| `WebSearch` | 网络搜索 | 信息收集 |
| `Read` | 读取文件 | 加载数据 |
| `Write` | 写入文件 | 保存结果 |
| `Glob` | 文件模式匹配 | 发现文件 |
| `Grep` | 内容搜索 | 查找信息 |
| `Bash` | 执行命令 | 运行脚本 |
| `Edit` | 编辑文件 | 修改内容 |
| `Skill` | 调用技能 | 复杂操作 |

### 6.2 按角色分配工具

```python
TOOL_ASSIGNMENTS = {
    "lead":       ["Task"],                              # 仅编排
    "researcher": ["WebSearch", "Write"],                # 搜索和保存
    "analyst":    ["Glob", "Read", "Bash", "Write"],     # 分析和执行
    "reporter":   ["Glob", "Read", "Write", "Skill"],    # 生成报告
}
```

### 6.3 最小权限原则

```python
# 错误：工具过多
bad_agent = AgentDefinitionConfig(
    tools=["WebSearch", "Read", "Write", "Bash", "Edit", "Glob", "Grep"],
    ...
)

# 正确：精确控制
good_agent = AgentDefinitionConfig(
    tools=["WebSearch", "Write"],  # 只需要的工具
    ...
)
```

---

## 7. 提示词工程

### 7.1 提示词结构模板

```text
# 角色定义
你是 [角色名称]，负责 [核心职责]。

# 能力边界
- 你可以：[具体能力列表]
- 你不可以：[限制列表]

# 工作流程
1. [步骤 1]
2. [步骤 2]
3. [步骤 3]

# 输出规范
- 格式：[期望格式]
- 位置：[输出路径]
- 命名：[命名约定]

# 质量标准
- [标准 1]
- [标准 2]

# 示例
[具体示例]
```

### 7.2 研究员提示词示例

```text
# 角色定义
你是专业研究员，负责通过网络搜索收集定量数据和关键信息。

# 核心任务
1. 执行 5-10 次有针对性的搜索
2. 优先收集定量数据（市场规模、增长率、排名）
3. 将研究发现保存为 Markdown 文件

# 搜索策略
- 使用具体、有针对性的查询
- 寻找权威来源（行业报告、官方数据）
- 收集多个数据点进行交叉验证

# 输出规范
- 路径：files/research_notes/{topic_name}.md
- 格式：带结构化标题的 Markdown
- 内容：10-15+ 条具体统计数据

# 数据优先级
1. 市场规模和份额
2. 增长率和预测
3. 主要参与者排名
4. 技术参数对比
5. 投资和融资数据
```

### 7.3 提示词加载

```python
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"

def load_prompt(filename: str) -> str:
    """从提示词目录加载提示词。"""
    prompt_path = PROMPTS_DIR / filename
    if not prompt_path.exists():
        raise FileNotFoundError(f"未找到提示词文件：{prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()
```

---

## 8. 状态管理

### 8.1 会话状态

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class AgentSession:
    """智能体会话状态。"""
    session_id: str
    started_at: str
    user_query: str
    subagents_spawned: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    current_phase: str = "init"  # init, researching, analyzing, reporting, done
    errors: List[str] = field(default_factory=list)
```

### 8.2 阶段追踪

```python
class PhaseTracker:
    """工作流阶段追踪器。"""

    PHASES = ["init", "researching", "analyzing", "reporting", "done"]

    def __init__(self):
        self.current_phase = "init"
        self.phase_history = []

    def advance_phase(self, new_phase: str):
        """推进到新阶段。"""
        if new_phase not in self.PHASES:
            raise ValueError(f"未知阶段：{new_phase}")

        self.phase_history.append({
            "from": self.current_phase,
            "to": new_phase,
            "timestamp": datetime.now().isoformat()
        })
        self.current_phase = new_phase

    def is_complete(self) -> bool:
        return self.current_phase == "done"
```

---

## 9. 错误处理

### 9.1 优雅降级

```python
async def post_tool_use_hook(self, hook_input, tool_use_id, context):
    """错误处理示例。"""
    tool_response = hook_input.get('tool_response')

    # 检测错误
    error = None
    if isinstance(tool_response, dict):
        error = tool_response.get('error')

    if error:
        # 记录错误但不中断执行
        logger.warning(f"工具错误：{error}")
        self.errors.append({
            "tool_use_id": tool_use_id,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

    # 继续执行
    return {'continue_': True}
```

### 9.2 资源清理

```python
async def main():
    tracker = None
    transcript = None

    try:
        # 初始化资源
        transcript = TranscriptWriter(log_path)
        tracker = SubagentTracker(tool_log_path)

        # 执行主逻辑
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt=user_input)
            async for msg in client.receive_response():
                process_message(msg, tracker, transcript)

    except Exception as e:
        logger.error(f"会话失败：{e}")
        raise

    finally:
        # 确保资源清理
        if transcript:
            transcript.close()
        if tracker:
            tracker.close()
```

### 9.3 错误分类

```python
class AgentError(Exception):
    """基础智能体错误。"""
    pass

class ConfigurationError(AgentError):
    """配置错误。"""
    pass

class ToolExecutionError(AgentError):
    """工具执行错误。"""
    def __init__(self, tool_name: str, message: str):
        self.tool_name = tool_name
        super().__init__(f"工具 '{tool_name}' 失败：{message}")

class SubagentError(AgentError):
    """子智能体错误。"""
    def __init__(self, subagent_id: str, message: str):
        self.subagent_id = subagent_id
        super().__init__(f"子智能体 '{subagent_id}' 失败：{message}")
```

---

## 10. 日志与审计

### 10.1 双格式日志

```python
class TranscriptWriter:
    """双格式日志写入器。"""

    def __init__(self, file_path: Path):
        self.file = open(file_path, 'w', encoding='utf-8')

    def write(self, text: str, end: str = ""):
        """同时输出到控制台和文件。"""
        print(text, end=end, flush=True)
        self.file.write(text + end)
        self.file.flush()

    def write_to_file_only(self, text: str):
        """仅写入文件（详细日志）。"""
        self.file.write(text)
        self.file.flush()

    def close(self):
        self.file.close()
```

### 10.2 JSONL 结构化日志

```python
import json
from datetime import datetime

class ToolCallLogger:
    """工具调用 JSONL 日志器。"""

    def __init__(self, file_path: Path):
        self.file = open(file_path, 'w')

    def log_tool_start(self, agent_id: str, tool_name: str,
                       tool_input: dict, tool_use_id: str):
        entry = {
            "event": "tool_call_start",
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "tool_name": tool_name,
            "tool_use_id": tool_use_id,
            "input_summary": self._summarize_input(tool_input)
        }
        self._write(entry)

    def log_tool_complete(self, tool_use_id: str, success: bool,
                         output_size: int = 0, error: str = None):
        entry = {
            "event": "tool_call_complete",
            "timestamp": datetime.now().isoformat(),
            "tool_use_id": tool_use_id,
            "success": success,
            "output_size": output_size,
            "error": error
        }
        self._write(entry)

    def _write(self, entry: dict):
        self.file.write(json.dumps(entry, ensure_ascii=False) + '\n')
        self.file.flush()

    def close(self):
        self.file.close()
```

### 10.3 会话目录管理

```python
from pathlib import Path
from datetime import datetime

def setup_session() -> tuple[Path, Path, Path]:
    """创建会话目录和日志文件。"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = Path("logs") / f"session_{timestamp}"
    session_dir.mkdir(parents=True, exist_ok=True)

    transcript_file = session_dir / "transcript.txt"
    tool_log_file = session_dir / "tool_calls.jsonl"

    return session_dir, transcript_file, tool_log_file
```

---

## 11. 配置管理

### 11.1 架构配置

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class ResearchConfig:
    """Research 架构配置。"""

    # 模型配置
    lead_model: str = "haiku"
    researcher_model: str = "haiku"
    analyst_model: str = "haiku"
    reporter_model: str = "haiku"

    # 研究深度
    research_depth: str = "standard"  # shallow, standard, deep
    max_researchers: int = 4

    # 输出目录
    research_notes_dir: str = "research_notes"
    data_dir: str = "data"
    charts_dir: str = "charts"
    reports_dir: str = "reports"

    def get_model_overrides(self) -> dict[str, str]:
        """获取智能体模型覆盖。"""
        return {
            "researcher": self.researcher_model,
            "data-analyst": self.analyst_model,
            "report-writer": self.reporter_model,
        }
```

### 11.2 环境配置

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API 配置
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # 模型配置
    LEAD_MODEL = os.getenv("LEAD_MODEL", "haiku")
    SUBAGENT_MODEL = os.getenv("SUBAGENT_MODEL", "haiku")

    # 路径配置
    PROJECT_ROOT = Path(__file__).parent.parent
    FILES_DIR = PROJECT_ROOT / "files"
    LOGS_DIR = PROJECT_ROOT / "logs"
    PROMPTS_DIR = PROJECT_ROOT / "prompts"

    # 功能开关
    ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
    BYPASS_PERMISSIONS = os.getenv("BYPASS_PERMISSIONS", "true").lower() == "true"

    @classmethod
    def validate(cls):
        """验证必需配置。"""
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("需要设置 ANTHROPIC_API_KEY 环境变量")
```

---

## 12. 完整示例

### 12.1 基础用法

```python
from claude_agent_framework import init
import asyncio

async def research_example():
    """基础研究示例。"""
    session = init("research")

    async for msg in session.run("分析 2024 年 AI 市场趋势"):
        print(msg)

asyncio.run(research_example())
```

### 12.2 自定义架构

```python
from claude_agent_framework import register_architecture, BaseArchitecture, init
from claude_agent_framework.core.base import AgentDefinitionConfig

@register_architecture("qa_expert")
class QAExpertArchitecture(BaseArchitecture):
    """自定义问答专家架构。"""

    name = "qa_expert"
    description = "带领域专家路由的问答系统"

    def get_agents(self) -> dict[str, AgentDefinitionConfig]:
        return {
            "code_expert": AgentDefinitionConfig(
                name="code_expert",
                description="编程和软件开发专家",
                tools=["Read", "Write", "Glob", "Grep"],
                prompt_file="code_expert.txt",
            ),
            "data_expert": AgentDefinitionConfig(
                name="data_expert",
                description="数据分析和统计专家",
                tools=["Read", "Write", "Bash"],
                prompt_file="data_expert.txt",
            ),
        }

    async def execute(self, prompt, tracker=None, transcript=None):
        """执行问答工作流。"""
        # 构建 SDK 配置
        options = ClaudeAgentOptions(
            permission_mode="bypassPermissions",
            setting_sources=["project"],
            system_prompt=self.get_lead_prompt(),
            allowed_tools=["Task"],
            agents=self.to_sdk_agents(),
            hooks=self._build_hooks(tracker),
            model=self.model_config.default,
        )

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt=prompt)

            async for msg in client.receive_response():
                yield msg

# 使用自定义架构
async def main():
    session = init("qa_expert")
    async for msg in session.run("如何优化数据库查询？"):
        print(msg)
```

### 12.3 编程控制

```python
from claude_agent_framework import init
from pathlib import Path

async def programmatic_example():
    """完全编程控制。"""

    # 使用自定义选项初始化
    session = init(
        "research",
        model="sonnet",
        verbose=True,
        log_dir=Path("./custom_logs"),
    )

    # 访问内部组件
    print(f"架构：{session.architecture.name}")
    print(f"会话目录：{session.session_dir}")

    # 运行查询
    query = "分析云计算市场趋势"

    try:
        async for msg in session.run(query):
            print(msg)
    finally:
        await session.teardown()
        print(f"会话已保存到：{session.session_dir}")
```

---

## 总结

### 核心要点

1. **多种模式**：7 种不同的编排模式适用于不同问题领域
2. **模式选择**：根据任务特征选择（并行 vs 顺序，迭代 vs 一次性）
3. **职责分离**：主智能体编排，子智能体执行专业化任务
4. **工具约束**：最小权限原则，每个智能体精确控制工具
5. **可观测性**：Hook 机制 + JSONL 审计日志实现全链路追踪
6. **成本优化**：子智能体使用 Haiku 模型以降低成本
7. **提示词工程**：结构化模板，清晰的角色边界
8. **错误处理**：优雅降级，确保资源清理

### 模式快速参考

| 模式 | 何时使用 |
|------|----------|
| **Research** | 需要从多个来源并行收集数据 |
| **Pipeline** | 有明确交接的顺序阶段 |
| **Critic-Actor** | 通过反馈进行迭代质量改进 |
| **Specialist Pool** | 将查询路由到领域专家 |
| **Debate** | 利弊平衡分析 |
| **Reflexion** | 需要自我反思的复杂问题 |
| **MapReduce** | 大规模并行处理与聚合 |

### 适用场景

- 多步骤研究任务
- 数据收集和分析流水线
- 文档生成自动化
- 复杂工作流编排
- 决策支持系统
- 大规模内容分析

---

*文档生成日期：2024-12-25*
*基于：Claude Agent Framework v0.3.0*
