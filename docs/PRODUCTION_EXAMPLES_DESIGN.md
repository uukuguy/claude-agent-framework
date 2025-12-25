# Production Examples Design Document

This document details the design, features, and implementation of 7 production-grade examples for Claude Agent Framework.

## Overview

Each example demonstrates an architecture pattern in a real business scenario, including:

- ✅ **Complete Runnable Code** - Main program, config files, custom components
- ✅ **Error Handling** - Try/except wrappers, friendly error messages, fallback logic
- ✅ **Logging** - Structured logs, progress indicators, debug information
- ✅ **Test Coverage** - Unit tests, integration tests, end-to-end tests
- ✅ **Complete Documentation** - Usage guide, architecture docs, customization guide

## Example Directory Structure

```
examples/production/
├── README.md                        # Overview (EN)
├── README_CN.md                     # Overview (CN)
├── common/                          # Shared utilities
│   ├── __init__.py
│   ├── utils.py                     # Common utility functions
│   └── templates/                   # Shared templates
│
├── 01_competitive_intelligence/     # Research example
│   ├── __init__.py
│   ├── README.md                    # Example docs (EN)
│   ├── README_CN.md                 # Example docs (CN)
│   ├── main.py                      # Main entry point
│   ├── config.yaml                  # Configuration file
│   ├── prompts/                     # Custom prompts
│   ├── plugins/                     # Custom plugins
│   ├── tests/                       # Tests
│   └── docs/                        # Detailed documentation
│
└── [Other examples follow same structure]
```

---

## Example 1: Competitive Intelligence System (Research)

### Business Scenario

Automated competitive intelligence gathering and analysis system for SaaS companies to understand competitive landscape.

### Features

**Core Functionality**:
- **Parallel Competitor Research** - Simultaneously research multiple competitors (AWS, Azure, Google Cloud, etc.)
- **Multi-Channel Data Collection** - Official websites, social media, user reviews, industry news
- **Automated Analysis** - Generate comparison analysis and visualization charts
- **Structured Reports** - Output PDF competitive analysis reports

**Customization Features**:
- Custom analysis dimensions (features, pricing, market share, tech stack)
- Industry-specific data source configuration
- SWOT analysis templates
- Trend tracking and historical comparison

### Architecture Design

```
Lead Agent (Research Orchestrator)
    ├─> Industry Researcher (research industry trends)
    ├─> Competitor Analyst 1 (research competitor A)
    ├─> Competitor Analyst 2 (research competitor B)
    ├─> Competitor Analyst 3 (research competitor C)
    └─> Report Generator (generate final report)
```

### Technical Implementation

**Custom Agents**:
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

**Custom Plugin - Data Validation**:
```python
class CompetitorDataValidator(BasePlugin):
    """Validate completeness of collected competitor data"""

    async def on_agent_complete(self, agent_type, result, context):
        if agent_type == "competitor_analyst":
            # Validate required fields
            required_fields = ["company_name", "products", "pricing", "features"]
            missing = [f for f in required_fields if f not in result]
            if missing:
                logger.warning(f"Missing fields: {missing}")
```

**Configuration Example** (config.yaml):
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

### Output Example

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

## Example 2: PR Code Review Pipeline (Pipeline)

### Business Scenario

Automated GitHub Pull Request code review with multi-dimensional quality analysis.

### Features

**Core Functionality**:
- **Architecture Review** - Analyze design patterns, dependencies
- **Code Quality Check** - Style, complexity, maintainability
- **Security Scan** - SAST analysis (SQL injection, XSS, etc.)
- **Performance Benchmark** - Performance impact assessment
- **Test Coverage Validation** - Ensure adequate test coverage

**Customization Features**:
- Optional stage configuration (skip certain checks)
- Inter-stage data transformation
- Failure strategy (stop vs continue)
- Structured review reports

### Architecture Design

```
Lead Agent (Review Coordinator)
    ├─> Stage 1: Architecture Reviewer
    ├─> Stage 2: Code Quality Checker
    ├─> Stage 3: Security Scanner
    ├─> Stage 4: Performance Analyzer
    └─> Stage 5: Test Coverage Validator
```

### Technical Implementation

**Pipeline Configuration**:
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

**Custom Tool - GitHub Integration**:
```python
class GitHubPRFetcher:
    """Fetch PR file changes and metadata"""

    async def fetch_pr_files(self, pr_url: str) -> dict:
        # Use gh CLI or GitHub API to get PR info
        files_changed = await self._get_changed_files(pr_url)
        diff = await self._get_diff(pr_url)
        return {
            "files": files_changed,
            "diff": diff,
            "metadata": {...}
        }
```

**Output Example**:
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

## Example 3: Marketing Content Optimization (Critic-Actor)

### Business Scenario

AI-assisted marketing content creation and optimization to generate high-quality marketing copy.

### Features

**Core Functionality**:
- **Draft Generation** - Based on product and target audience
- **Multi-Dimensional Evaluation** - SEO, engagement, brand consistency, conversion potential
- **Iterative Optimization** - Continuous improvement based on feedback
- **A/B Test Variants** - Generate multiple versions for testing

**Customization Features**:
- Brand guideline integration
- Scoring weight configuration
- Quality threshold settings
- Content type templates (ads/blog/email/social media)

### Architecture Design

```
Iteration Loop (max 3 rounds):
    Actor (Content Writer)
        ↓ [generates content]
    Critic (Content Evaluator)
        ↓ [provides feedback]
    [if score < threshold] → Actor revises
    [if score >= threshold] → Done
```

### Technical Implementation

**Evaluation Metrics**:
```python
class ContentEvaluator:
    """Multi-dimensional content evaluation"""

    def evaluate(self, content: str, brand_guide: dict) -> dict:
        scores = {
            "seo_score": self._evaluate_seo(content),
            "engagement_score": self._evaluate_engagement(content),
            "brand_alignment": self._check_brand_alignment(content, brand_guide),
            "conversion_potential": self._estimate_conversion(content),
            "readability": self._calculate_readability(content)
        }

        # Weighted total score
        weights = {"seo": 0.2, "engagement": 0.3, "brand": 0.2,
                   "conversion": 0.2, "readability": 0.1}
        total_score = sum(scores[k] * weights[k.split("_")[0]]
                         for k in scores.keys())

        return {"scores": scores, "total": total_score}
```

**Brand Guide Example** (brand_guide.yaml):
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

---

## Example 4: Enterprise IT Support Platform (Specialist Pool)

### Business Scenario

Intelligent IT support routing system that automatically assigns issues to appropriate expert agents.

### Features

**Core Functionality**:
- **Intelligent Classification** - Analyze which technical domain the issue belongs to
- **Automatic Expert Routing** - Route to network/database/security/cloud specialists
- **Parallel Expert Collaboration** - Multiple experts collaborate on cross-domain issues
- **Knowledge Base Integration** - Retrieve historical solutions

**Customization Features**:
- Dynamic specialist registration
- Keyword routing algorithm
- Priority scheduling
- Specialist load balancing

### Architecture Design

```
Lead Agent (Support Router)
    ├─> Routing Logic
    │   ├─> Network Specialist (network issues)
    │   ├─> Database Specialist (database issues)
    │   ├─> Security Specialist (security issues)
    │   └─> Cloud Specialist (cloud service issues)
    └─> Response Aggregator
```

---

## Example 5: Technical Decision Support (Debate)

### Business Scenario

Technical architecture decision support through pro-con debate to help teams make informed technical choices.

### Features

**Core Functionality**:
- **Proponent Arguments** - Analyze advantages of specific approach
- **Opponent Challenges** - Challenge approach and propose alternatives
- **Multi-Round Debate** - 3 rounds of in-depth discussion
- **Expert Judge Decision** - Comprehensive analysis and recommendation

**Customization Features**:
- Decision templates (tech stack/architecture change/vendor selection)
- Evaluation criteria configuration
- Multi-judge voting mechanism
- Risk analysis reports

### Architecture Design

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

---

## Example 6: Intelligent Code Debugger (Reflexion)

### Business Scenario

AI-driven adaptive debugging system solving complex bugs through execute-reflect-improve cycles.

### Features

**Core Functionality**:
- **Debug Strategy Execution** - Try different debugging methods
- **Result Reflection** - Analyze effectiveness of each attempt
- **Dynamic Strategy Adjustment** - Improve methods based on feedback
- **Root Cause Identification** - Ultimately determine bug cause

**Customization Features**:
- Debug strategy library (log analysis, breakpoint tracing, state inspection)
- Success pattern learning
- Failure pattern recognition
- Fix suggestion generation

### Architecture Design

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

---

## Example 7: Large-Scale Codebase Analysis (MapReduce)

### Business Scenario

Comprehensive technical debt diagnosis system analyzing large codebases (500+ files) with prioritized reports.

### Features

**Core Functionality**:
- **Intelligent Codebase Partitioning** - Split by module/file/size
- **Parallel Static Analysis** - Analyze multiple code segments simultaneously
- **Issue Aggregation and Classification** - Group by severity and type
- **Prioritized Reports** - Generate actionable optimization recommendations

**Customization Features**:
- Partitioning strategy configuration (file count/lines of code/module)
- Analysis tool integration (pylint/bandit/radon)
- Aggregation algorithm configuration
- Visualization report generation

### Architecture Design

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

---

## Common Design Patterns

### 1. Configuration File Standard

All examples use unified YAML configuration format:

```yaml
# config.yaml standard structure
architecture: "<architecture_name>"

# Architecture-specific configuration
<architecture_specific_config>

# Common configuration
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

### 2. Error Handling Pattern

```python
async def main():
    session = None
    try:
        # Initialize
        session = init_session(config)

        # Execute
        result = await session.run(query)

        # Save results
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

### 3. Progress Indicator Pattern

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

### 4. Result Saving Pattern

```python
class ResultSaver:
    """Unified result saving interface"""

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

## Testing Strategy

### Unit Tests

Each example includes unit tests:

```python
# tests/test_main.py
@pytest.mark.asyncio
async def test_config_loading():
    """Test configuration file loading"""
    config = load_config("config.yaml")
    assert config["architecture"] == "research"

@pytest.mark.asyncio
async def test_result_parsing():
    """Test result parsing"""
    mock_result = {...}
    parsed = parse_result(mock_result)
    assert "summary" in parsed
```

### Integration Tests

```python
# tests/test_integration.py
@pytest.mark.asyncio
async def test_end_to_end():
    """End-to-end test (using mocks)"""
    with patch("claude_agent_framework.core.session.AgentSession") as mock:
        result = await run_example(config)
        assert result["status"] == "completed"
```

---

## Documentation Requirements

Each example must include:

### README.md

```markdown
# Example Name

## Overview
[Brief description]

## Quick Start

### Installation
pip install -e ".[all]"

### Configuration
[Configuration instructions]

### Run
python main.py

## Output Example
[Show output]

## Customization
[How to customize]

## FAQ
[Frequently asked questions]
```

### docs/ARCHITECTURE.md

```markdown
# Architecture Design

## Architecture Diagram
[Mermaid diagram or ASCII diagram]

## Agent Responsibilities
[Description of each agent]

## Data Flow
[How data flows between agents]

## Design Decisions
[Why designed this way]
```

---

## Next Steps

1. Create `examples/production/` directory structure
2. Implement shared utility module `common/utils.py`
3. Implement 7 examples sequentially:
   - 01_competitive_intelligence (Research)
   - 02_pr_code_review (Pipeline)
   - 03_marketing_content (Critic-Actor)
   - 04_it_support (Specialist Pool)
   - 05_tech_decision (Debate)
   - 06_code_debugger (Reflexion)
   - 07_codebase_analysis (MapReduce)

Git commit after each example is completed.
