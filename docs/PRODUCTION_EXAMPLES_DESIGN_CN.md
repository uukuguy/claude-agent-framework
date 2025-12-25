# 生产级示例设计文档

本文档详细说明了 Claude Agent Framework 的7个生产级示例的设计、功能和实现要点。

## 概述

每个示例都展示了一个架构在真实业务场景中的应用，包含：

- ✅ **完整可运行代码** - 主程序、配置文件、自定义组件
- ✅ **错误处理** - Try/except包装、友好错误消息、失败回退逻辑
- ✅ **日志记录** - 结构化日志、进度指示器、调试信息
- ✅ **测试覆盖** - 单元测试、集成测试、端到端测试
- ✅ **完整文档** - 使用说明、架构说明、定制指南

## 示例目录结构

```
examples/production/
├── README.md                        # 总览（EN）
├── README_CN.md                     # 总览（CN）
├── common/                          # 共享工具
│   ├── __init__.py
│   ├── utils.py                     # 通用工具函数
│   └── templates/                   # 共享模板
│
├── 01_competitive_intelligence/     # Research示例
│   ├── __init__.py
│   ├── README.md                    # 示例文档（EN）
│   ├── README_CN.md                 # 示例文档（CN）
│   ├── main.py                      # 主入口
│   ├── config.yaml                  # 配置文件
│   ├── prompts/                     # 定制提示词
│   ├── plugins/                     # 定制插件
│   ├── tests/                       # 测试
│   └── docs/                        # 详细文档
│
└── [其他示例遵循相同结构]
```

---

## 示例 1: 竞品情报分析系统 (Research)

### 业务场景

SaaS公司自动化竞争情报收集与分析系统，帮助产品团队和市场团队了解竞争态势。

### 功能特性

**核心功能**：
- **并行竞品调研** - 同时调研多个竞品（AWS、Azure、Google Cloud等）
- **多渠道数据收集** - 官网、社交媒体、用户评论、行业新闻
- **自动分析生成** - 生成对比分析和可视化图表
- **结构化报告** - 输出PDF竞品分析报告

**定制化特性**：
- 自定义分析维度（功能、定价、市场份额、技术栈）
- 行业特定数据源配置
- SWOT分析模板
- 趋势跟踪和历史对比

### 架构设计

```
Lead Agent (Research Orchestrator)
    ├─> Industry Researcher (调研行业趋势)
    ├─> Competitor Analyst 1 (调研竞品A)
    ├─> Competitor Analyst 2 (调研竞品B)
    ├─> Competitor Analyst 3 (调研竞品C)
    └─> Report Generator (生成最终报告)
```

### 技术实现要点

**自定义 Agents**：
```python
agents = {
    "industry_researcher": AgentDefinitionConfig(
        name="Industry Researcher",
        description="Research industry trends and market landscape",
        tools=["WebSearch", "WebFetch", "Write"],
        prompt="prompts/industry_researcher.txt"
    ),
    "competitor_analyst": AgentDefinitionConfig(
        name="Competitor Analyst",
        description="Deep dive analysis of specific competitor",
        tools=["WebSearch", "WebFetch", "Write"],
        prompt="prompts/competitor_analyst.txt"
    )
}
```

**自定义插件 - 数据验证**：
```python
class CompetitorDataValidator(BasePlugin):
    """验证收集的竞品数据完整性"""

    async def on_agent_complete(self, agent_type, result, context):
        if agent_type == "competitor_analyst":
            # 验证必需字段
            required_fields = ["company_name", "products", "pricing", "features"]
            missing = [f for f in required_fields if f not in result]
            if missing:
                logger.warning(f"Missing fields: {missing}")
```

**配置文件示例** (config.yaml):
```yaml
architecture: research
competitors:
  - name: "AWS"
    website: "https://aws.amazon.com"
  - name: "Azure"
    website: "https://azure.microsoft.com"
  - name: "Google Cloud"
    website: "https://cloud.google.com"

analysis_dimensions:
  - "Product Features"
  - "Pricing Model"
  - "Market Share"
  - "Technology Stack"
  - "Customer Reviews"

output:
  format: "pdf"
  include_charts: true
  include_swot: true
```

### 输出示例

```
outputs/competitive_intelligence_report_20250125.pdf
    - Executive Summary
    - Industry Overview
    - Competitor Comparison Matrix
    - Feature-by-Feature Analysis
    - Pricing Comparison
    - SWOT Analysis
    - Recommendations
```

---

## 示例 2: PR代码审查流水线 (Pipeline)

### 业务场景

自动化GitHub Pull Request代码审查流程，提供多维度代码质量分析。

### 功能特性

**核心功能**：
- **架构设计评审** - 分析设计模式、依赖关系
- **代码质量检查** - 风格、复杂度、可维护性
- **安全漏洞扫描** - SAST分析（SQL注入、XSS等）
- **性能基准测试** - 性能影响评估
- **测试覆盖率验证** - 确保测试充分

**定制化特性**：
- 可选阶段配置（跳过某些检查）
- 阶段间数据转换
- 失败策略（停止 vs 继续）
- 结构化审查报告

### 架构设计

```
Lead Agent (Review Coordinator)
    ├─> Stage 1: Architecture Reviewer
    ├─> Stage 2: Code Quality Checker
    ├─> Stage 3: Security Scanner
    ├─> Stage 4: Performance Analyzer
    └─> Stage 5: Test Coverage Validator
```

### 技术实现要点

**Pipeline配置**：
```python
pipeline_config = {
    "stages": [
        {
            "name": "architecture_review",
            "agent": "architecture_reviewer",
            "required": True,
            "timeout": 300
        },
        {
            "name": "code_quality",
            "agent": "code_quality_checker",
            "required": True,
            "timeout": 180
        },
        {
            "name": "security_scan",
            "agent": "security_scanner",
            "required": True,
            "timeout": 240
        }
    ],
    "failure_strategy": "stop_on_critical"
}
```

**自定义工具 - GitHub集成**：
```python
class GitHubPRFetcher:
    """获取PR的文件变更和元数据"""

    async def fetch_pr_files(self, pr_url: str) -> dict:
        # 使用gh CLI或GitHub API获取PR信息
        files_changed = await self._get_changed_files(pr_url)
        diff = await self._get_diff(pr_url)
        return {
            "files": files_changed,
            "diff": diff,
            "metadata": {...}
        }
```

**输出示例**：
```markdown
# PR Review Report: #1234

## Architecture Review ✅
- Design patterns: Well-structured MVC pattern
- Dependencies: No circular dependencies detected
- Recommendation: LGTM

## Code Quality ⚠️
- Complexity: 3 functions exceed complexity threshold
- Style: 12 linting issues found
- Recommendation: Address high-complexity functions

## Security Scan ✅
- No critical vulnerabilities found
- 1 low-severity warning (input validation)

## Performance Impact 🔍
- Estimated overhead: <2%
- Memory usage: Within acceptable range

## Test Coverage ❌
- Current coverage: 72% (target: 80%)
- Missing tests: UserService.updateProfile()
```

---

## 示例 3: 营销文案优化 (Critic-Actor)

### 业务场景

AI辅助营销内容创作与优化，生成高质量营销文案。

### 功能特性

**核心功能**：
- **初稿文案生成** - 基于产品和目标受众
- **多维度评估** - SEO、吸引力、品牌一致性、转化率潜力
- **迭代优化循环** - 根据反馈持续改进
- **A/B测试变体生成** - 生成多个版本供测试

**定制化特性**：
- 品牌指南集成
- 评分权重配置
- 质量阈值设定
- 内容类型模板（广告/博客/邮件/社交媒体）

### 架构设计

```
Iteration Loop (max 3 rounds):
    Actor (Content Writer)
        ↓ [generates content]
    Critic (Content Evaluator)
        ↓ [provides feedback]
    [if score < threshold] → Actor revises
    [if score >= threshold] → Done
```

### 技术实现要点

**评估指标**：
```python
class ContentEvaluator:
    """多维度内容评估"""

    def evaluate(self, content: str, brand_guide: dict) -> dict:
        scores = {
            "seo_score": self._evaluate_seo(content),
            "engagement_score": self._evaluate_engagement(content),
            "brand_alignment": self._check_brand_alignment(content, brand_guide),
            "conversion_potential": self._estimate_conversion(content),
            "readability": self._calculate_readability(content)
        }

        # 加权总分
        weights = {"seo": 0.2, "engagement": 0.3, "brand": 0.2,
                   "conversion": 0.2, "readability": 0.1}
        total_score = sum(scores[k] * weights[k.split("_")[0]]
                         for k in scores.keys())

        return {"scores": scores, "total": total_score}
```

**品牌指南示例** (brand_guide.yaml):
```yaml
brand_name: "TechFlow AI"
tone_of_voice:
  - "Professional yet approachable"
  - "Innovative and forward-thinking"
  - "Customer-focused"

prohibited_words:
  - "cheap"
  - "revolutionary" # overused

preferred_phrases:
  - "cutting-edge"
  - "user-centric"
  - "seamless integration"

target_audience: "B2B SaaS decision makers"
```

**输出示例**：
```
=== Content Generation Report ===

Original Brief:
- Product: AI-powered project management tool
- Target: Software development teams
- Goal: Drive free trial signups

--- Round 1 ---
Generated Content: [...]
Evaluation:
- SEO Score: 72/100
- Engagement: 65/100
- Brand Alignment: 88/100
- Total: 74/100 ❌ (threshold: 80)

Feedback: Improve engagement hooks and SEO keywords

--- Round 2 ---
Revised Content: [...]
Evaluation:
- Total: 82/100 ✅

Final Content:
[Optimized marketing copy...]

A/B Test Variants:
- Variant A (Focus: ROI)
- Variant B (Focus: Ease of use)
- Variant C (Focus: Integration)
```

---

## 示例 4: 企业IT支持平台 (Specialist Pool)

### 业务场景

智能IT技术支持路由系统，将问题自动分配给合适的专家代理。

### 功能特性

**核心功能**：
- **问题智能分类** - 分析问题属于哪个技术领域
- **专家自动路由** - 路由到网络/数据库/安全/云计算专家
- **并行专家协作** - 跨领域问题多专家协同
- **知识库集成** - 检索历史解决方案

**定制化特性**：
- 动态专家注册
- 关键词路由算法
- 优先级调度
- 专家负载均衡

### 架构设计

```
Lead Agent (Support Router)
    ├─> Routing Logic
    │   ├─> Network Specialist (网络问题)
    │   ├─> Database Specialist (数据库问题)
    │   ├─> Security Specialist (安全问题)
    │   └─> Cloud Specialist (云服务问题)
    └─> Response Aggregator
```

### 技术实现要点

**路由算法**：
```python
class SpecialistRouter:
    """基于关键词和规则的专家路由"""

    def __init__(self):
        self.specialist_keywords = {
            "network": ["vpn", "firewall", "dns", "router", "bandwidth"],
            "database": ["sql", "query", "backup", "replication", "index"],
            "security": ["breach", "malware", "encryption", "vulnerability"],
            "cloud": ["aws", "azure", "s3", "lambda", "kubernetes"]
        }

    def route(self, ticket: dict) -> list[str]:
        """返回应处理此问题的专家列表"""
        text = f"{ticket['title']} {ticket['description']}".lower()

        matched_specialists = []
        for specialist, keywords in self.specialist_keywords.items():
            if any(kw in text for kw in keywords):
                matched_specialists.append(specialist)

        # 默认路由到通用专家
        return matched_specialists or ["general_it"]
```

**动态专家注册**：
```python
# 运行时添加新专家
session.architecture.add_specialist(
    name="kubernetes_specialist",
    description="Expert in Kubernetes orchestration and troubleshooting",
    keywords=["kubernetes", "k8s", "pod", "deployment", "helm"],
    tools=["WebSearch", "Bash", "Read"],
    prompt="You are a Kubernetes expert..."
)
```

**配置示例** (config.yaml):
```yaml
specialists:
  network:
    keywords: ["vpn", "firewall", "dns", "network", "connectivity"]
    priority: high
    tools: ["WebSearch", "Bash"]

  database:
    keywords: ["sql", "database", "query", "postgresql", "mysql"]
    priority: high
    tools: ["WebSearch", "Bash", "Read"]

routing:
  strategy: "best_match"  # or "multi_specialist"
  max_specialists_per_ticket: 2
  fallback_specialist: "general_it"
```

---

## 示例 5: 技术选型决策支持 (Debate)

### 业务场景

技术架构决策辅助系统，通过正反辩论帮助团队做出明智的技术选择。

### 功能特性

**核心功能**：
- **正方论证** - 支持特定方案的优势分析
- **反方论证** - 挑战方案并提出替代方案
- **多轮深度辩论** - 3轮辩论深入探讨
- **专家评委裁决** - 综合分析给出建议

**定制化特性**：
- 决策模板（技术选型/架构变更/供应商选择）
- 评估维度配置
- 多评委投票机制
- 风险分析报告

### 架构设计

```
Round 1: Initial Arguments
    Proponent → supports Option A
    Opponent → challenges Option A, proposes Option B

Round 2: Rebuttal
    Proponent → addresses criticisms
    Opponent → counters arguments

Round 3: Deep Dive
    Proponent → final arguments
    Opponent → final arguments

Judge → analyzes all arguments → recommendation
```

### 技术实现要点

**辩论主题模板**：
```python
DECISION_TEMPLATES = {
    "tech_stack": {
        "question": "Should we migrate from {current} to {proposed}?",
        "evaluation_criteria": [
            "Development velocity",
            "Performance",
            "Cost",
            "Learning curve",
            "Community support",
            "Long-term maintainability"
        ]
    },
    "architecture": {
        "question": "Should we adopt {architecture_pattern}?",
        "evaluation_criteria": [
            "Scalability",
            "Complexity",
            "Team familiarity",
            "Migration effort",
            "Operational overhead"
        ]
    }
}
```

**评委评分系统**：
```python
class DebateJudge:
    """评估辩论并给出决策建议"""

    def evaluate(self, debate_transcript: list[dict]) -> dict:
        # 分析论点强度
        proponent_points = self._extract_arguments(debate_transcript, "proponent")
        opponent_points = self._extract_arguments(debate_transcript, "opponent")

        # 评分
        scores = {
            "proponent": self._score_arguments(proponent_points),
            "opponent": self._score_arguments(opponent_points)
        }

        # 风险评估
        risks = self._identify_risks(debate_transcript)

        # 生成建议
        recommendation = self._generate_recommendation(scores, risks)

        return {
            "scores": scores,
            "risks": risks,
            "recommendation": recommendation,
            "confidence": self._calculate_confidence(scores)
        }
```

**输出示例**：
```markdown
# Technical Decision: Migrate to GraphQL?

## Debate Summary

### Round 1: Opening Arguments

**Proponent (GraphQL)**
- Eliminates over-fetching and under-fetching
- Strongly typed schema
- Better developer experience with introspection
- Single endpoint simplifies API management

**Opponent (REST)**
- Team has 5 years REST experience
- Existing infrastructure optimized for REST
- GraphQL adds complexity (N+1 queries, caching)
- Learning curve impacts velocity

### Round 2: Rebuttals
[...]

### Round 3: Deep Dive
[...]

## Judge's Analysis

**Scores:**
- Proponent: 72/100
- Opponent: 68/100

**Key Risks Identified:**
- ⚠️ HIGH: Team learning curve (3-6 months ramp-up)
- ⚠️ MEDIUM: N+1 query performance issues
- ⚠️ LOW: Migration complexity

**Recommendation:**
Adopt GraphQL with **phased approach**:
1. Start with new microservices (low risk)
2. Build team expertise over 6 months
3. Migrate critical APIs after proven success
4. Maintain REST for legacy systems

**Confidence:** 75%
```

---

## 示例 6: 智能代码调试助手 (Reflexion)

### 业务场景

AI驱动的自适应调试系统，通过执行-反思-改进循环解决复杂bug。

### 功能特性

**核心功能**：
- **调试策略执行** - 尝试不同调试方法
- **结果反思分析** - 分析每次尝试的效果
- **策略动态调整** - 根据反馈改进方法
- **根因定位** - 最终确定bug原因

**定制化特性**：
- 调试策略库（日志分析、断点追踪、状态检查）
- 成功模式学习
- 失败模式识别
- 修复建议生成

### 架构设计

```
Iteration Loop (max 5 attempts):
    Actor (Debugger)
        ↓ [tries debugging strategy]
    Reflector (Analyzer)
        ↓ [evaluates effectiveness]
    [update strategy based on reflection]
    [if bug found] → Generate fix
    [if not found] → Try new strategy
```

### 技术实现要点

**调试策略库**：
```python
DEBUG_STRATEGIES = {
    "log_analysis": {
        "description": "Analyze application logs for errors",
        "tools": ["Read", "Grep"],
        "effectiveness": 0.7  # historical success rate
    },
    "trace_execution": {
        "description": "Trace code execution path",
        "tools": ["Bash", "Read"],
        "effectiveness": 0.8
    },
    "state_inspection": {
        "description": "Inspect variable states at breakpoints",
        "tools": ["Bash", "Read"],
        "effectiveness": 0.6
    },
    "dependency_check": {
        "description": "Verify dependency versions and compatibility",
        "tools": ["Bash", "Read"],
        "effectiveness": 0.5
    }
}
```

**反思机制**：
```python
class DebuggingReflector:
    """分析调试尝试的效果"""

    def reflect(self, strategy: str, result: dict, bug_description: str) -> dict:
        """
        评估调试策略是否有效

        Returns:
            {
                "progress": float,  # 0-1, how close to solution
                "insights": list[str],  # new insights gained
                "next_strategy": str,  # recommended next step
                "confidence": float  # confidence in current hypothesis
            }
        """
        # 检查是否找到错误迹象
        error_indicators = self._check_error_indicators(result)

        # 评估进展
        progress = self._evaluate_progress(error_indicators, bug_description)

        # 提取洞察
        insights = self._extract_insights(result, error_indicators)

        # 推荐下一步
        next_strategy = self._recommend_next_strategy(
            current=strategy,
            progress=progress,
            insights=insights
        )

        return {
            "progress": progress,
            "insights": insights,
            "next_strategy": next_strategy,
            "confidence": self._calculate_confidence(error_indicators)
        }
```

**输出示例**：
```
=== Debugging Session: API returns 500 error ===

Bug Description:
API endpoint /api/users returns 500 error intermittently

--- Attempt 1: Log Analysis ---
Strategy: Analyze application logs
Result: Found error "NoneType object has no attribute 'id'"
Reflection:
  - Progress: 40%
  - Insight: Error occurs in user authentication module
  - Confidence: 60%
Next Step: Trace execution in authentication code

--- Attempt 2: Trace Execution ---
Strategy: Trace code execution path
Result: Error occurs when user session is expired
Reflection:
  - Progress: 75%
  - Insight: Session expiration check returns None
  - Confidence: 85%
Next Step: Inspect session handling logic

--- Attempt 3: State Inspection ---
Strategy: Inspect variable states
Result: Found root cause!
  - session.get_user() returns None when session expired
  - Code doesn't handle None case

=== Root Cause Identified ===
File: src/auth/session.py:42
Issue: Missing null check after session.get_user()

Recommended Fix:
```python
user = session.get_user()
if user is None:
    raise AuthenticationError("Session expired")
return user.id
```

Confidence: 95%
```

---

## 示例 7: 大规模代码库分析 (MapReduce)

### 业务场景

技术债务全面诊断系统，分析大型代码库（500+ 文件）并生成优先级报告。

### 功能特性

**核心功能**：
- **代码库智能分片** - 按模块/文件/大小分片
- **并行静态分析** - 同时分析多个代码片段
- **问题聚合分类** - 按严重程度和类型分组
- **优先级排序报告** - 生成可操作的优化建议

**定制化特性**：
- 分片策略配置（文件数/代码行数/模块）
- 分析工具集成（pylint/bandit/radon）
- 聚合算法配置
- 可视化报告生成

### 架构设计

```
Map Phase (Parallel):
    Lead Agent → splits codebase into chunks
    ├─> Mapper 1 → analyzes chunk 1
    ├─> Mapper 2 → analyzes chunk 2
    ├─> Mapper 3 → analyzes chunk 3
    └─> Mapper N → analyzes chunk N

Reduce Phase:
    Reducer → aggregates all findings
    └─> generates prioritized report
```

### 技术实现要点

**分片策略**：
```python
class CodebaseSplitter:
    """智能代码库分片"""

    def split(self, codebase_path: Path, strategy: str, chunk_size: int) -> list[dict]:
        """
        分片策略：
        - by_files: 每chunk包含N个文件
        - by_modules: 按Python模块分组
        - by_size: 每chunk约M行代码
        """
        if strategy == "by_modules":
            return self._split_by_modules(codebase_path)
        elif strategy == "by_size":
            return self._split_by_size(codebase_path, chunk_size)
        else:  # by_files
            return self._split_by_files(codebase_path, chunk_size)

    def _split_by_modules(self, path: Path) -> list[dict]:
        """按Python包/模块分组"""
        chunks = []
        for module_dir in path.rglob("__init__.py"):
            module_files = list(module_dir.parent.glob("*.py"))
            chunks.append({
                "module": module_dir.parent.name,
                "files": module_files
            })
        return chunks
```

**并行分析**：
```python
# Map阶段：并行分析配置
mapper_agents = {
    f"mapper_{i}": AgentDefinitionConfig(
        name=f"Code Analyzer {i}",
        description=f"Analyze code chunk {i}",
        tools=["Read", "Bash", "Grep"],
        prompt=MAPPER_PROMPT
    )
    for i in range(num_chunks)
}
```

**分析工具集成**：
```python
class CodeAnalyzer:
    """集成多个静态分析工具"""

    async def analyze_chunk(self, files: list[Path]) -> dict:
        results = {}

        # Pylint - 代码质量
        results["quality"] = await self._run_pylint(files)

        # Bandit - 安全漏洞
        results["security"] = await self._run_bandit(files)

        # Radon - 复杂度分析
        results["complexity"] = await self._run_radon(files)

        # Custom rules
        results["custom"] = await self._run_custom_checks(files)

        return results
```

**聚合与优先级排序**：
```python
class IssueAggregator:
    """聚合并优先级排序问题"""

    def aggregate(self, mapper_results: list[dict]) -> dict:
        # 合并所有发现
        all_issues = []
        for result in mapper_results:
            all_issues.extend(result["issues"])

        # 按类型分组
        issues_by_type = self._group_by_type(all_issues)

        # 按严重程度分组
        issues_by_severity = self._group_by_severity(all_issues)

        # 计算优先级分数
        prioritized = self._calculate_priority(all_issues)

        # 生成统计
        statistics = self._generate_statistics(all_issues)

        return {
            "total_issues": len(all_issues),
            "by_type": issues_by_type,
            "by_severity": issues_by_severity,
            "top_priority": prioritized[:20],
            "statistics": statistics
        }

    def _calculate_priority(self, issues: list[dict]) -> list[dict]:
        """优先级 = severity * frequency * impact"""
        for issue in issues:
            issue["priority_score"] = (
                issue["severity"] * 0.4 +
                issue["frequency"] * 0.3 +
                issue["impact"] * 0.3
            )
        return sorted(issues, key=lambda x: x["priority_score"], reverse=True)
```

**输出示例**：
```markdown
# Codebase Analysis Report

## Executive Summary
- Total Files Analyzed: 523
- Total Issues Found: 1,247
- Critical Issues: 23
- High Priority: 156
- Medium Priority: 487
- Low Priority: 581

## Top Priority Issues

### 1. Security: SQL Injection Risk [CRITICAL]
- File: `src/database/queries.py:45`
- Description: User input directly interpolated in SQL query
- Impact: HIGH
- Recommendation: Use parameterized queries

### 2. Performance: N+1 Query Pattern [HIGH]
- Files: 8 occurrences
- Description: Loop executes database query on each iteration
- Impact: MEDIUM
- Recommendation: Use bulk queries or eager loading

### 3. Code Quality: High Complexity [HIGH]
- File: `src/core/processor.py:123`
- Complexity: 28 (threshold: 10)
- Impact: MEDIUM
- Recommendation: Refactor into smaller functions

## Issue Distribution

### By Type
- Security: 45 issues
- Performance: 123 issues
- Code Quality: 567 issues
- Maintainability: 312 issues
- Documentation: 200 issues

### By Severity
- Critical: 23 (fix immediately)
- High: 156 (fix within sprint)
- Medium: 487 (backlog)
- Low: 581 (optional)

## Module Breakdown

### Module: `authentication` (健康度: 72/100)
- Issues: 34
- Main concerns: Security vulnerabilities

### Module: `api` (健康度: 65/100)
- Issues: 89
- Main concerns: Error handling, input validation

### Module: `database` (健康度: 58/100)
- Issues: 123
- Main concerns: Query optimization, connection pooling

## Recommendations
1. **Immediate**: Fix 23 critical security issues
2. **This Sprint**: Address 156 high-priority issues
3. **Next Quarter**: Reduce technical debt by 40%
4. **Long-term**: Establish code quality gates in CI/CD
```

---

## 共性设计模式

### 1. 配置文件标准

所有示例使用统一的YAML配置格式：

```yaml
# config.yaml 标准结构
architecture: "<architecture_name>"

# 架构特定配置
<architecture_specific_config>

# 通用配置
models:
  lead: "sonnet"
  agents: "haiku"

output:
  directory: "outputs/"
  format: "json"  # or "pdf", "markdown"

logging:
  level: "INFO"
  file: "logs/session.log"

plugins:
  - "cost_tracker"
  - "retry_handler"
```

### 2. 错误处理模式

```python
async def main():
    session = None
    try:
        # 初始化
        session = init_session(config)

        # 执行
        result = await session.run(query)

        # 保存结果
        save_results(result)

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        print("Please check your config.yaml file")
        sys.exit(1)

    except APIError as e:
        logger.error(f"API error: {e}")
        print("API request failed. Please check your API key and connection")
        sys.exit(2)

    except Exception as e:
        logger.exception("Unexpected error")
        print(f"An error occurred: {e}")
        sys.exit(3)

    finally:
        if session:
            await session.teardown()
            print(f"Session saved to: {session.session_dir}")
```

### 3. 进度指示器模式

```python
from rich.progress import Progress, SpinnerColumn, TextColumn

async def process_with_progress(items: list):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    ) as progress:

        task = progress.add_task("Processing...", total=len(items))

        for item in items:
            progress.update(task, description=f"Processing {item}...")
            await process_item(item)
            progress.advance(task)
```

### 4. 结果保存模式

```python
class ResultSaver:
    """统一的结果保存接口"""

    def save(self, result: dict, format: str, output_path: Path):
        if format == "json":
            self._save_json(result, output_path)
        elif format == "pdf":
            self._save_pdf(result, output_path)
        elif format == "markdown":
            self._save_markdown(result, output_path)

        logger.info(f"Results saved to {output_path}")
```

---

## 测试策略

### 单元测试

每个示例包含单元测试：

```python
# tests/test_main.py
@pytest.mark.asyncio
async def test_config_loading():
    """测试配置文件加载"""
    config = load_config("config.yaml")
    assert config["architecture"] == "research"

@pytest.mark.asyncio
async def test_result_parsing():
    """测试结果解析"""
    mock_result = {...}
    parsed = parse_result(mock_result)
    assert "summary" in parsed
```

### 集成测试

```python
# tests/test_integration.py
@pytest.mark.asyncio
async def test_end_to_end():
    """端到端测试（使用mock）"""
    with patch("claude_agent_framework.core.session.AgentSession") as mock:
        result = await run_example(config)
        assert result["status"] == "completed"
```

---

## 文档要求

每个示例必须包含：

### README_CN.md

```markdown
# 示例名称

## 功能概述
[简要描述]

## 快速开始

### 安装
pip install -e ".[all]"

### 配置
[配置说明]

### 运行
python main.py

## 输出示例
[展示输出]

## 定制化
[如何定制]

## 常见问题
[FAQ]
```

### docs/ARCHITECTURE_CN.md

```markdown
# 架构设计

## 架构图
[Mermaid图或ASCII图]

## Agent职责
[每个agent的说明]

## 数据流
[数据如何在agents间流动]

## 设计决策
[为何这样设计]
```

---

## 下一步行动

1. 创建 `examples/production/` 目录结构
2. 实现共享工具模块 `common/utils.py`
3. 依次实现7个示例：
   - 01_competitive_intelligence (Research)
   - 02_pr_code_review (Pipeline)
   - 03_marketing_content (Critic-Actor)
   - 04_it_support (Specialist Pool)
   - 05_tech_decision (Debate)
   - 06_code_debugger (Reflexion)
   - 07_codebase_analysis (MapReduce)

每个示例完成后进行git提交。
