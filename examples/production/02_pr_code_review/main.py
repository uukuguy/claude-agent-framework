#!/usr/bin/env python3
"""
PR Code Review Pipeline.

Automated Pull Request code review using Pipeline architecture.
Demonstrates sequential stage processing with comprehensive analysis.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path to import common utilities
sys.path.insert(0, str(Path(__file__).parent.parent))

from common import (
    ConfigurationError,
    ExecutionError,
    ResultSaver,
    extract_message_content,
    load_yaml_config,
    setup_logging,
    validate_config,
)

from claude_agent_framework import create_session

logger = logging.getLogger(__name__)


async def run_pr_review(config: dict) -> dict:
    """
    Run PR code review pipeline.

    Args:
        config: Configuration dictionary

    Returns:
        Review results with stage-by-stage analysis

    Raises:
        ExecutionError: If review fails
    """
    try:
        # Extract configuration
        stages = config["stages"]
        pr_source = config["pr_source"]
        analysis_config = config.get("analysis", {})
        models = config.get("models", {})

        # Get PR changes
        pr_data = await _get_pr_changes(pr_source)

        logger.info(f"Starting PR review pipeline with {len(stages)} stages")
        logger.info(f"Analyzing {pr_data['files_changed']} files changed")

        # Build pipeline prompt
        prompt = _build_pipeline_prompt(stages, pr_data, analysis_config)

        # Initialize session with Pipeline architecture and business template
        session = create_session(
            "pipeline",
            model=models.get("lead", "sonnet"),
            business_template=config.get("business_template", "pr_code_review"),
            template_vars={
                "repository": config.get("repository", "Project Repository"),
                "pr_number": config.get("pr_number", ""),
                "review_focus": config.get("review_focus", ["Code Quality", "Security"]),
            },
            verbose=False,
        )

        # Run pipeline
        results = []
        async for msg in session.run(prompt):
            logger.info(f"Progress: {msg}")
            content = extract_message_content(msg)
            if content:
                results.append(content)

        # Teardown session
        await session.teardown()

        logger.info("PR review completed successfully")

        # Format results
        return {
            "title": "Pull Request Code Review Report",
            "summary": _generate_summary(stages, results),
            "pr_info": pr_data,
            "stages": _parse_stage_results(stages, results),
            "overall_status": _determine_overall_status(results),
            "recommendations": _extract_recommendations(results),
            "metadata": {
                "total_stages": len(stages),
                "files_changed": pr_data["files_changed"],
                "lines_added": pr_data["lines_added"],
                "lines_deleted": pr_data["lines_deleted"],
                "session_dir": str(session.session_dir) if session.session_dir else None,
            },
        }

    except Exception as e:
        logger.exception("Error during PR review")
        raise ExecutionError(f"PR review failed: {e}") from e


async def _get_pr_changes(pr_source: dict) -> dict:
    """
    Get PR changes from source.

    Args:
        pr_source: PR source configuration

    Returns:
        PR data dictionary
    """
    if "pr_url" in pr_source:
        # GitHub PR URL - would use gh CLI or API
        logger.info(f"Fetching PR from URL: {pr_source['pr_url']}")
        # For demo, return mock data
        return {
            "pr_url": pr_source["pr_url"],
            "files_changed": 15,
            "lines_added": 250,
            "lines_deleted": 80,
            "diff": "Mock diff content",
        }
    elif "local_path" in pr_source:
        # Local git repository
        logger.info(f"Analyzing local changes in: {pr_source['local_path']}")

        # Use git to get changes
        from subprocess import run

        try:
            # Get file stats
            result = run(
                ["git", "diff", "--shortstat", pr_source.get("base_branch", "main")],
                capture_output=True,
                text=True,
                cwd=pr_source["local_path"],
            )

            stats = result.stdout.strip()
            logger.info(f"Git stats: {stats}")

            # Parse stats (e.g., "15 files changed, 250 insertions(+), 80 deletions(-)")
            files_changed = 0
            lines_added = 0
            lines_deleted = 0

            if stats:
                parts = stats.split(",")
                if len(parts) >= 1 and "file" in parts[0]:
                    files_changed = int(parts[0].split()[0])
                if len(parts) >= 2 and "insertion" in parts[1]:
                    lines_added = int(parts[1].split()[0])
                if len(parts) >= 3 and "deletion" in parts[2]:
                    lines_deleted = int(parts[2].split()[0])

            # Get diff
            diff_result = run(
                ["git", "diff", pr_source.get("base_branch", "main")],
                capture_output=True,
                text=True,
                cwd=pr_source["local_path"],
            )

            return {
                "local_path": pr_source["local_path"],
                "base_branch": pr_source.get("base_branch", "main"),
                "files_changed": files_changed,
                "lines_added": lines_added,
                "lines_deleted": lines_deleted,
                "diff": diff_result.stdout[:5000],  # First 5000 chars
            }

        except Exception as e:
            logger.warning(f"Error getting git changes: {e}")
            # Return minimal data
            return {
                "local_path": pr_source["local_path"],
                "files_changed": 0,
                "lines_added": 0,
                "lines_deleted": 0,
                "diff": "",
            }
    else:
        raise ValueError("PR source must specify either 'pr_url' or 'local_path'")


def _build_pipeline_prompt(stages: list[dict], pr_data: dict, analysis_config: dict) -> str:
    """
    Build pipeline prompt.

    Note: Role instructions and workflow guidance are provided by the
    business template (pr_code_review). This function only generates
    the user task description.

    Args:
        stages: List of stage configurations
        pr_data: PR data
        analysis_config: Analysis configuration

    Returns:
        Formatted prompt string
    """
    stage_list = "\n".join(
        f"{i + 1}. **{stage['name']}**: {stage['description']}" for i, stage in enumerate(stages)
    )

    thresholds = "\n".join(
        f"- {key.replace('_', ' ').title()}: {value}" for key, value in analysis_config.items()
    )

    diff_summary = f"""
Files Changed: {pr_data["files_changed"]}
Lines Added: {pr_data["lines_added"]}
Lines Deleted: {pr_data["lines_deleted"]}
"""

    prompt = f"""Review the following Pull Request.

## PR Summary
{diff_summary}

## Review Stages
{stage_list}

## Quality Thresholds
{thresholds}

Deliver a comprehensive code review report with stage-by-stage analysis and recommendations.
"""

    return prompt


def _generate_summary(stages: list[dict], results: list[str]) -> str:
    """Generate review summary."""
    results_text = "\n".join(results)

    passed = results_text.count("✅")
    warnings = results_text.count("⚠️")
    failed = results_text.count("❌")

    return f"Completed {len(stages)} review stages: {passed} passed, {warnings} warnings, {failed} failed"


def _parse_stage_results(stages: list[dict], results: list[str]) -> list[dict]:
    """Parse results by stage."""
    # Simple parsing - in real implementation would be more sophisticated
    return [
        {
            "name": stage["name"],
            "description": stage["description"],
            "status": "completed",
        }
        for stage in stages
    ]


def _determine_overall_status(results: list[str]) -> str:
    """Determine overall review status."""
    results_text = "\n".join(results)

    if "❌ FAIL" in results_text:
        return "CHANGES_REQUESTED"
    elif "⚠️ WARNING" in results_text:
        return "APPROVED_WITH_COMMENTS"
    else:
        return "APPROVED"


def _extract_recommendations(results: list[str]) -> list[str]:
    """Extract recommendations from results."""
    # Simple extraction - in real implementation would parse structured output
    return [
        "Review all identified issues",
        "Address critical and high-priority items first",
        "Run tests after making changes",
        "Update documentation if needed",
    ]


async def main():
    """Main entry point."""
    try:
        # Load configuration
        config_path = Path(__file__).parent / "config.yaml"
        config = load_yaml_config(config_path)

        # Validate configuration
        validate_config(config, ["architecture", "stages", "pr_source", "output"])

        # Setup logging
        log_config = config.get("logging", {})
        setup_logging(
            level=log_config.get("level", "INFO"),
            log_file=Path(log_config.get("file")) if "file" in log_config else None,
        )

        logger.info("=" * 60)
        logger.info("PR Code Review Pipeline")
        logger.info("=" * 60)

        # Run review
        results = await run_pr_review(config)

        # Save results
        output_config = config["output"]
        saver = ResultSaver(output_config["directory"])

        output_path = saver.save(
            results,
            format=output_config.get("format", "json"),
            filename="pr_review_report",
        )

        print("\n✅ Review complete!")
        print(f"📊 Report saved to: {output_path}")

        # Print summary
        print("\n📈 Summary:")
        print(f"  - Overall Status: {results['overall_status']}")
        print(f"  - Files Changed: {results['metadata']['files_changed']}")
        print(f"  - Stages Completed: {results['metadata']['total_stages']}")
        if results["metadata"]["session_dir"]:
            print(f"  - Session logs: {results['metadata']['session_dir']}")

        print("\n💡 Top Recommendations:")
        for i, rec in enumerate(results["recommendations"][:3], 1):
            print(f"  {i}. {rec}")

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\n❌ Configuration Error: {e}")
        print("Please check your config.yaml file")
        sys.exit(1)

    except ExecutionError as e:
        logger.error(f"Execution error: {e}")
        print(f"\n❌ Execution Error: {e}")
        sys.exit(2)

    except Exception as e:
        logger.exception("Unexpected error")
        print(f"\n❌ Unexpected Error: {e}")
        sys.exit(3)


if __name__ == "__main__":
    asyncio.run(main())
