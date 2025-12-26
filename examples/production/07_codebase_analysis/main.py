"""Codebase Analysis using MapReduce Architecture.

Performs large-scale static analysis of codebases:
- Map: Parallel analysis of code chunks
- Reduce: Aggregate and prioritize findings
- Comprehensive reporting with metrics and recommendations

Uses the MapReduce architecture from Claude Agent Framework.
"""

import asyncio
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Add parent directories to path for common utilities
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from common import ResultSaver, extract_message_content, load_yaml_config, validate_config

from claude_agent_framework import create_session


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""

    pass


class ExecutionError(Exception):
    """Raised when analysis execution fails."""

    pass


async def run_codebase_analysis(
    config: dict,
    codebase_path: str,
    options: dict = None,
) -> dict:
    """Run codebase analysis using MapReduce architecture.

    Args:
        config: Configuration dict from config.yaml
        codebase_path: Path to codebase root directory
        options: Optional runtime options (filters, focus areas)

    Returns:
        dict: Analysis results with issues, metrics, and recommendations
    """
    # Validate configuration
    required_fields = ["architecture", "analysis", "mapreduce_config", "analysis_types"]
    validate_config(config, required_fields)

    # Validate architecture type
    if config["architecture"] != "mapreduce":
        raise ConfigurationError(
            f"Invalid architecture: {config['architecture']}. Must be 'mapreduce'"
        )

    # Validate mapreduce_config structure
    mapreduce_config = config["mapreduce_config"]
    required_roles = ["mapper", "reducer", "coordinator"]
    for role in required_roles:
        if role not in mapreduce_config:
            raise ConfigurationError(f"Missing mapreduce_config.{role}")
        if "name" not in mapreduce_config[role]:
            raise ConfigurationError(f"Missing mapreduce_config.{role}.name")
        if "role" not in mapreduce_config[role]:
            raise ConfigurationError(f"Missing mapreduce_config.{role}.role")

    # Extract configuration
    analysis_config = config["analysis"]
    analysis_types = config["analysis_types"]
    chunking_strategies = config.get("chunking_strategies", {})
    aggregation_rules = config.get("aggregation_rules", {})
    output_config = config.get("output_config", {})
    models = config.get("models", {})
    advanced = config.get("advanced", {})
    options = options or {}

    # Build mapreduce prompt
    prompt = _build_mapreduce_prompt(
        codebase_path,
        analysis_config,
        mapreduce_config,
        analysis_types,
        chunking_strategies,
        aggregation_rules,
        output_config,
        advanced,
        options,
    )

    # Initialize mapreduce session with business template
    try:
        session = create_session(
            "mapreduce",
            model=models.get("coordinator", "sonnet"),
            business_template=config.get("business_template", "codebase_analysis"),
            template_vars={
                "codebase": config.get("codebase", "Project Codebase"),
                "analysis_focus": config.get(
                    "analysis_focus", ["Code Quality", "Security", "Performance"]
                ),
                "file_patterns": config.get("file_patterns", "**/*.py"),
            },
            verbose=False,
        )
    except Exception as e:
        raise ExecutionError(f"Failed to initialize mapreduce session: {e}")

    # Run mapreduce analysis
    results = []
    try:
        async for msg in session.run(prompt):
            content = extract_message_content(msg)
            if content:
                results.append(content)
    except Exception as e:
        raise ExecutionError(f"MapReduce execution failed: {e}")
    finally:
        await session.teardown()

    # Parse analysis results
    chunks_analyzed = _extract_chunks_analyzed(results)
    issues_found = _extract_issues(results)
    metrics = _extract_metrics(results)
    module_health = _extract_module_health(results)
    trends = _extract_trends(results)
    recommendations = _extract_recommendations(results)

    # Calculate overall scores
    overall_score = _calculate_overall_score(metrics, module_health)
    issue_summary = _summarize_issues(issues_found)

    # Build result structure
    result = {
        "analysis_id": str(uuid.uuid4()),
        "title": f"Codebase Analysis: {Path(codebase_path).name}",
        "summary": _generate_summary(issue_summary, overall_score, chunks_analyzed),
        "codebase": {
            "path": codebase_path,
            "files_analyzed": metrics.get("total_files", 0),
            "lines_of_code": metrics.get("total_lines", 0),
            "languages": metrics.get("languages", []),
        },
        "execution": {
            "chunks_analyzed": chunks_analyzed,
            "parallel_mappers": len(chunks_analyzed),
            "chunking_strategy": options.get("chunking_strategy", "by_module"),
        },
        "issues": {
            "total": len(issues_found),
            "by_severity": issue_summary,
            "critical": [i for i in issues_found if i.get("severity") == "critical"],
            "high": [i for i in issues_found if i.get("severity") == "high"],
            "medium": [i for i in issues_found if i.get("severity") == "medium"],
            "low": [i for i in issues_found if i.get("severity") == "low"],
            "all_issues": issues_found,
        },
        "metrics": metrics,
        "module_health": module_health,
        "trends": trends,
        "recommendations": recommendations,
        "scores": {
            "overall": overall_score,
            "quality": metrics.get("quality_score", 0),
            "security": metrics.get("security_score", 0),
            "maintainability": metrics.get("maintainability_score", 0),
            "test_coverage": metrics.get("test_coverage", 0),
        },
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "analysis_config": {
                "types_enabled": [t for t, cfg in analysis_types.items() if cfg.get("enabled")],
                "parallel_mappers": analysis_config.get("max_parallel_mappers", 10),
                "chunk_size": analysis_config.get("chunk_size", 50),
            },
            "models": models,
        },
    }

    return result


def _build_mapreduce_prompt(
    codebase_path: str,
    analysis_config: dict,
    mapreduce_config: dict,
    analysis_types: dict,
    chunking_strategies: dict,
    aggregation_rules: dict,
    output_config: dict,
    advanced: dict,
    options: dict,
) -> str:
    """Build mapreduce analysis prompt.

    Note: Role instructions and workflow guidance are provided by the
    business template (codebase_analysis). This function only generates
    the user task description.

    Args:
        codebase_path: Path to codebase
        analysis_config: Analysis configuration
        mapreduce_config: MapReduce role definitions
        analysis_types: Types of analysis to perform
        chunking_strategies: Available chunking strategies
        aggregation_rules: Rules for aggregating results
        output_config: Output formatting config
        advanced: Advanced options
        options: Runtime options

    Returns:
        str: User task description for codebase analysis
    """
    # Extract enabled analysis types
    enabled_analyses = []
    for analysis_type, type_config in analysis_types.items():
        if type_config.get("enabled", True):
            priority = type_config.get("priority", 2)
            checks = type_config.get("checks", [])
            enabled_analyses.append(
                f"- **{analysis_type.replace('_', ' ').title()}** (Priority {priority}): {', '.join(checks)}"
            )

    analyses_text = "\n".join(enabled_analyses)

    # Extract chunking strategy
    chunking_strategy = options.get("chunking_strategy", "by_module")
    strategy_info = chunking_strategies.get(chunking_strategy, {})

    # Extract filters
    exclude_paths = advanced.get("filters", {}).get("exclude_paths", [])
    include_extensions = advanced.get("filters", {}).get("include_extensions", [])

    # Build deduplication and prioritization info
    dedup_config = aggregation_rules.get("deduplication", {})
    priority_criteria = aggregation_rules.get("prioritization", {}).get("criteria", {})

    prompt = f"""# Codebase Analysis Task

## Analysis Target

**Codebase Path**: {codebase_path}

**Analysis Scope**:
- Include extensions: {", ".join(include_extensions) if include_extensions else "All"}
- Exclude paths: {", ".join(exclude_paths) if exclude_paths else "None"}
- Minimum confidence: {analysis_config.get("min_confidence", 0.7)}

## Analysis Configuration

Maximum parallel mappers: {analysis_config.get("max_parallel_mappers", 10)}
Target chunk size: {analysis_config.get("chunk_size", 50)} files per chunk
Aggregation strategy: {analysis_config.get("aggregation_strategy", "weighted")}

## Chunking Strategy

**Selected Strategy**: {chunking_strategy}
{strategy_info.get("description", "")}

**Benefits**:
{chr(10).join(f"- {b}" for b in strategy_info.get("benefits", [])) if strategy_info.get("benefits") else "- Efficient code analysis"}

## Analysis Types

{analyses_text}

## Aggregation Rules

**Deduplication**:
- Similarity threshold: {dedup_config.get("similarity_threshold", 0.85)}
- Merge strategy: {dedup_config.get("merge_strategy", "highest_severity")}

**Prioritization Criteria**:
{chr(10).join(f"- {k}: {v * 100}%" for k, v in priority_criteria.items()) if priority_criteria else "- Default prioritization"}

Analyze the codebase using MapReduce pattern to efficiently identify issues and generate recommendations.
"""

    return prompt


def _extract_chunks_analyzed(results: list[str]) -> list[dict]:
    """Extract chunk analysis information.

    Args:
        results: Raw mapreduce output

    Returns:
        list[dict]: Chunk information
    """
    chunks = []
    full_text = "\n".join(results)

    # Look for "Chunk N Analysis" patterns
    import re

    chunk_pattern = r"\*\*Chunk (\d+) Analysis\*\*.*?Files: \[([^\]]+)\]"
    matches = re.finditer(chunk_pattern, full_text, re.DOTALL)

    for match in matches:
        chunk_num = int(match.group(1))
        files_str = match.group(2)
        files = [f.strip().strip("'\"") for f in files_str.split(",")]

        chunks.append(
            {
                "chunk_id": chunk_num,
                "files": files,
                "file_count": len(files),
            }
        )

    # If no chunks found, create a default single chunk
    if not chunks:
        chunks.append(
            {
                "chunk_id": 1,
                "files": ["[Analyzed files]"],
                "file_count": 0,
            }
        )

    return chunks


def _extract_issues(results: list[str]) -> list[dict]:
    """Extract all issues from analysis results.

    Args:
        results: Raw mapreduce output

    Returns:
        list[dict]: Issues with severity, type, location
    """
    issues = []
    full_text = "\n".join(results)

    # Look for issues in various formats
    # Format 1: - [Severity] [Type] in [file]:[line] - [Description]
    import re

    issue_pattern1 = (
        r"-\s*\[(critical|high|medium|low)\]\s*\[(\w+)\]\s*in\s+([^:]+):(\d+)\s*-\s*(.+?)(?:\n|$)"
    )
    matches = re.finditer(issue_pattern1, full_text, re.IGNORECASE | re.MULTILINE)

    for match in matches:
        severity = match.group(1).lower()
        issue_type = match.group(2)
        file_path = match.group(3).strip()
        line_number = int(match.group(4))
        description = match.group(5).strip()

        issues.append(
            {
                "severity": severity,
                "type": issue_type,
                "file": file_path,
                "line": line_number,
                "description": description,
                "confidence": "Medium",  # Default
                "fix_effort": "Medium",  # Default
            }
        )

    # Format 2: Top issues list
    # 1. [Issue description] in [file]:[line]
    top_issue_pattern = r"\d+\.\s*(.+?)\s+in\s+([^:]+):(\d+)"
    matches = re.finditer(top_issue_pattern, full_text, re.MULTILINE)

    seen = set()
    for match in matches:
        description = match.group(1).strip()
        file_path = match.group(2).strip()
        line_number = int(match.group(3))

        # Avoid duplicates
        key = (description, file_path, line_number)
        if key in seen:
            continue
        seen.add(key)

        # Try to extract severity from context
        severity = "medium"
        if "critical" in description.lower() or "security" in description.lower():
            severity = "critical"
        elif "high" in description.lower() or "performance" in description.lower():
            severity = "high"

        issues.append(
            {
                "severity": severity,
                "type": "code_quality",
                "file": file_path,
                "line": line_number,
                "description": description,
                "confidence": "High",
                "fix_effort": "Medium",
            }
        )

    return issues


def _extract_metrics(results: list[str]) -> dict:
    """Extract code metrics from analysis.

    Args:
        results: Raw mapreduce output

    Returns:
        dict: Code metrics
    """
    full_text = "\n".join(results)

    metrics = {
        "total_files": 0,
        "total_lines": 0,
        "average_complexity": 0,
        "max_complexity": 0,
        "test_coverage": 0,
        "quality_score": 0,
        "security_score": 0,
        "maintainability_score": 0,
        "languages": [],
    }

    import re

    # Extract metrics
    patterns = {
        "total_files": r"Total files analyzed:\s*(\d+)",
        "total_lines": r"Total lines of code:\s*(\d+)",
        "average_complexity": r"Average complexity:\s*([\d.]+)",
        "test_coverage": r"Test coverage:\s*([\d.]+)%?",
        "quality_score": r"Quality score:\s*([\d.]+)",
        "security_score": r"Security score:\s*([\d.]+)",
        "maintainability_score": r"Maintainability score:\s*([\d.]+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            value = match.group(1)
            metrics[key] = float(value) if "." in value else int(value)

    return metrics


def _extract_module_health(results: list[str]) -> list[dict]:
    """Extract per-module health scores.

    Args:
        results: Raw mapreduce output

    Returns:
        list[dict]: Module health information
    """
    modules = []
    full_text = "\n".join(results)

    # Look for "Module Health" section
    if "**Module Health**" in full_text:
        module_section_start = full_text.index("**Module Health**")
        module_section = full_text[module_section_start : module_section_start + 2000]

        import re

        # Format: - [Module name]: [score]/100
        module_pattern = r"-\s*([^:]+):\s*(\d+)/100"
        matches = re.finditer(module_pattern, module_section)

        for match in matches:
            module_name = match.group(1).strip()
            score = int(match.group(2))

            modules.append(
                {
                    "name": module_name,
                    "score": score,
                    "status": (
                        "healthy"
                        if score >= 80
                        else "needs_attention"
                        if score >= 60
                        else "critical"
                    ),
                }
            )

    return modules


def _extract_trends(results: list[str]) -> dict:
    """Extract trend information.

    Args:
        results: Raw mapreduce output

    Returns:
        dict: Trend data
    """
    full_text = "\n".join(results)

    trends = {
        "new_issues": 0,
        "resolved_issues": 0,
        "net_change": 0,
    }

    import re

    patterns = {
        "new_issues": r"New issues introduced:\s*(\d+)",
        "resolved_issues": r"Issues resolved:\s*(\d+)",
        "net_change": r"Net change:\s*([+-]?\d+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            value = match.group(1)
            trends[key] = int(value.replace("+", "").replace("-", ""))
            if "-" in value:
                trends[key] = -trends[key]

    return trends


def _extract_recommendations(results: list[str]) -> list[dict]:
    """Extract prioritized recommendations.

    Args:
        results: Raw mapreduce output

    Returns:
        list[dict]: Recommendations with priority and effort
    """
    recommendations = []
    full_text = "\n".join(results)

    # Look for recommendations section
    if "**Top Recommendations**" in full_text or "**Recommendations**" in full_text:
        import re

        # Format: N. [Priority] [Action]
        rec_pattern = (
            r"\d+\.\s*(?:\[Priority \d+\]\s*)?(.+?)(?:\n\s+Reason:|Effort:|Impact:|\d+\.|$)"
        )
        matches = re.finditer(rec_pattern, full_text, re.DOTALL)

        for match in matches:
            action = match.group(1).strip()
            if action and len(action) > 10:  # Filter out noise
                recommendations.append(
                    {
                        "action": action,
                        "priority": "high",
                        "effort": "medium",
                        "impact": "high",
                    }
                )

    return recommendations[:10]  # Top 10


def _calculate_overall_score(metrics: dict, module_health: list[dict]) -> int:
    """Calculate overall codebase health score.

    Args:
        metrics: Code metrics
        module_health: Per-module health scores

    Returns:
        int: Overall score 0-100
    """
    # Weighted average of various scores
    quality = metrics.get("quality_score", 70)
    security = metrics.get("security_score", 70)
    maintainability = metrics.get("maintainability_score", 70)
    coverage = metrics.get("test_coverage", 0)

    # Module health average
    module_avg = 70
    if module_health:
        module_avg = sum(m["score"] for m in module_health) / len(module_health)

    # Weighted calculation
    overall = (
        quality * 0.25 + security * 0.3 + maintainability * 0.2 + coverage * 0.15 + module_avg * 0.1
    )

    return int(overall)


def _summarize_issues(issues: list[dict]) -> dict:
    """Summarize issues by severity.

    Args:
        issues: List of all issues

    Returns:
        dict: Count by severity
    """
    summary = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    for issue in issues:
        severity = issue.get("severity", "medium").lower()
        if severity in summary:
            summary[severity] += 1

    return summary


def _generate_summary(issue_summary: dict, overall_score: int, chunks: list) -> str:
    """Generate executive summary.

    Args:
        issue_summary: Issue counts by severity
        overall_score: Overall health score
        chunks: Analyzed chunks

    Returns:
        str: Executive summary
    """
    total_issues = sum(issue_summary.values())
    critical = issue_summary.get("critical", 0)
    high = issue_summary.get("high", 0)

    status = (
        "healthy"
        if overall_score >= 80
        else "needs attention"
        if overall_score >= 60
        else "critical"
    )

    summary = (
        f"Analyzed {len(chunks)} chunks with overall health score of {overall_score}/100 ({status}). "
        f"Found {total_issues} total issues: {critical} critical, {high} high priority. "
    )

    if critical > 0:
        summary += f"Immediate action required on {critical} critical security/quality issues."
    elif high > 0:
        summary += f"Should address {high} high-priority issues in next sprint."
    else:
        summary += "No critical issues found. Focus on continuous improvement."

    return summary


async def main():
    """Example usage."""
    config = load_yaml_config("config.yaml")

    # Example: Analyze current directory
    codebase_path = str(Path(__file__).parent.parent.parent)

    options = {
        "chunking_strategy": "by_module",
        "focus_areas": ["security", "code_quality"],
    }

    result = await run_codebase_analysis(config, codebase_path, options)

    print(f"\n{'=' * 60}")
    print(f"ANALYSIS: {result['title']}")
    print(f"{'=' * 60}")
    print(f"\n📊 Summary: {result['summary']}")
    print(f"\n🎯 Overall Score: {result['scores']['overall']}/100")
    print(f"\n⚠️  Issues Found: {result['issues']['total']}")
    print(f"   - Critical: {len(result['issues']['critical'])}")
    print(f"   - High: {len(result['issues']['high'])}")
    print(f"   - Medium: {len(result['issues']['medium'])}")
    print(f"   - Low: {len(result['issues']['low'])}")

    # Save results
    saver = ResultSaver()
    saver.save(result, "codebase_analysis")


if __name__ == "__main__":
    asyncio.run(main())
