#!/usr/bin/env python3
"""
Competitive Intelligence Analysis System.

Automated competitor research and analysis using Research architecture.
Demonstrates parallel data gathering, analysis, and report generation.
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
    load_yaml_config,
    setup_logging,
    validate_config,
)

from claude_agent_framework import init

logger = logging.getLogger(__name__)


async def run_competitive_intelligence(config: dict) -> dict:
    """
    Run competitive intelligence analysis.

    Args:
        config: Configuration dictionary

    Returns:
        Analysis results

    Raises:
        ExecutionError: If analysis fails
    """
    try:
        # Extract configuration
        competitors = config["competitors"]
        analysis_dimensions = config["analysis_dimensions"]
        models = config.get("models", {})

        # Build analysis prompt
        prompt = _build_analysis_prompt(competitors, analysis_dimensions)

        logger.info(f"Starting competitive intelligence analysis for {len(competitors)} competitors")

        # Initialize session with Research architecture
        session = init(
            "research",
            model=models.get("lead", "sonnet"),
            verbose=False,
        )

        # Run analysis
        results = []
        async for msg in session.run(prompt):
            logger.info(f"Progress: {msg}")
            results.append(msg)

        # Teardown session
        await session.teardown()

        logger.info("Analysis completed successfully")

        # Format results
        return {
            "title": "Competitive Intelligence Analysis Report",
            "summary": f"Analyzed {len(competitors)} competitors across {len(analysis_dimensions)} dimensions",
            "competitors": [c["name"] for c in competitors],
            "dimensions": analysis_dimensions,
            "content": "\n\n".join(results),
            "metadata": {
                "total_competitors": len(competitors),
                "total_dimensions": len(analysis_dimensions),
                "session_dir": str(session.session_dir) if session.session_dir else None,
            },
        }

    except Exception as e:
        logger.exception("Error during competitive intelligence analysis")
        raise ExecutionError(f"Analysis failed: {e}") from e


def _build_analysis_prompt(competitors: list[dict], dimensions: list[str]) -> str:
    """
    Build analysis prompt for the research architecture.

    Args:
        competitors: List of competitor configurations
        dimensions: Analysis dimensions

    Returns:
        Formatted prompt string
    """
    competitor_list = "\n".join(
        f"- {c['name']}: {c['website']}\n  Focus: {', '.join(c.get('focus_areas', ['General analysis']))}"
        for c in competitors
    )

    dimension_list = "\n".join(f"- {dim}" for dim in dimensions)

    prompt = f"""Conduct a comprehensive competitive intelligence analysis of the following competitors:

{competitor_list}

Analyze each competitor across these dimensions:
{dimension_list}

For each competitor:
1. Research their latest offerings and updates
2. Analyze their strengths and weaknesses
3. Identify market positioning
4. Compare pricing strategies
5. Assess customer satisfaction

Provide a detailed comparative analysis and generate insights about:
- Market trends
- Competitive advantages
- Potential opportunities and threats
- Strategic recommendations

Use WebSearch to gather current information and ensure all data is up-to-date.
"""

    return prompt


async def main():
    """Main entry point."""
    try:
        # Load configuration
        config_path = Path(__file__).parent / "config.yaml"
        config = load_yaml_config(config_path)

        # Validate configuration
        validate_config(config, ["architecture", "competitors", "analysis_dimensions", "output"])

        # Setup logging
        log_config = config.get("logging", {})
        setup_logging(
            level=log_config.get("level", "INFO"),
            log_file=Path(log_config.get("file")) if "file" in log_config else None,
        )

        logger.info("=" * 60)
        logger.info("Competitive Intelligence Analysis System")
        logger.info("=" * 60)

        # Run analysis
        results = await run_competitive_intelligence(config)

        # Save results
        output_config = config["output"]
        saver = ResultSaver(output_config["directory"])

        output_path = saver.save(
            results,
            format=output_config.get("format", "json"),
            filename="competitive_intelligence_report",
        )

        print(f"\n✅ Analysis complete!")
        print(f"📊 Report saved to: {output_path}")

        # Print summary
        print(f"\n📈 Summary:")
        print(f"  - Competitors analyzed: {len(results['competitors'])}")
        print(f"  - Analysis dimensions: {len(results['dimensions'])}")
        if results["metadata"]["session_dir"]:
            print(f"  - Session logs: {results['metadata']['session_dir']}")

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
