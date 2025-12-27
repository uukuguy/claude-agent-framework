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
    extract_message_content,
    load_yaml_config,
    setup_logging,
    validate_config,
)

from claude_agent_framework import create_session
from claude_agent_framework.core.roles import AgentInstanceConfig

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

        logger.info(
            f"Starting competitive intelligence analysis for {len(competitors)} competitors"
        )

        # Determine prompt mode and configure session accordingly
        prompt_mode = config.get("prompt_mode", "templates")
        prompts_dir = Path(__file__).parent / "prompts" / prompt_mode

        # Template variables for prompt customization
        template_vars = {
            "company_name": config.get("company_name", "Our Company"),
            "industry": config.get("industry", "Technology"),
        }

        logger.info(f"Using prompt mode: {prompt_mode}")

        # Build agent instances based on competitors
        agent_instances = _build_agent_instances(config, models)
        logger.info(
            f"Created {len(agent_instances)} agent instances for {len(competitors)} competitors"
        )

        if prompt_mode == "templates":
            # Templates mode: local overrides + framework business_template fallback
            session = create_session(
                "research",
                model=models.get("lead", "sonnet"),
                agent_instances=agent_instances,
                business_template=config.get("business_template", "competitive_intelligence"),
                prompts_dir=prompts_dir if prompts_dir.exists() else None,
                template_vars=template_vars,
                verbose=False,
            )
        else:
            # Skills mode: use local prompts only (no business_template fallback)
            if not prompts_dir.exists():
                raise ExecutionError(
                    f"Skills mode requires prompts directory: {prompts_dir}"
                )
            session = create_session(
                "research",
                model=models.get("lead", "sonnet"),
                agent_instances=agent_instances,
                prompts_dir=prompts_dir,
                template_vars=template_vars,
                verbose=False,
            )

        # Run analysis
        results = []
        async for msg in session.run(prompt):
            logger.info(f"Progress: {msg}")
            # Extract string content from message objects
            content = extract_message_content(msg)
            if content:
                results.append(content)

        # Teardown session
        await session.teardown()

        logger.info("Analysis completed successfully")

        # Format results
        return {
            "title": "Competitive Intelligence Analysis Report",
            "summary": f"Analyzed {len(competitors)} competitors across {len(analysis_dimensions)} dimensions",
            "competitors": [c["name"] for c in competitors],
            "dimensions": analysis_dimensions,
            "content": "\n\n".join(results) if results else "No content generated",
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

    Note: Role instructions and workflow guidance are provided by either:
    - Templates mode: business template (competitive_intelligence) with optional local overrides
    - Skills mode: local prompts that guide agents to use Skills for methodology

    This function only generates the user task description.

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

    prompt = f"""Analyze the following competitors:

{competitor_list}

Analysis dimensions:
{dimension_list}

Deliver a comprehensive competitive intelligence report with comparative analysis and strategic recommendations.
"""

    return prompt


def _build_agent_instances(config: dict, models: dict) -> list[AgentInstanceConfig]:
    """
    Build agent instances based on competitors configuration.

    Creates one researcher worker per competitor for parallel research,
    plus optional processor and required synthesizer.

    Args:
        config: Configuration dictionary with competitors list
        models: Model configuration

    Returns:
        List of AgentInstanceConfig instances
    """
    agent_model = models.get("agents", "haiku")
    competitors = config.get("competitors", [])

    agent_instances = []

    # Worker 角色: 每个 competitor 创建一个专属 researcher
    for competitor in competitors:
        name = competitor["name"].lower().replace(" ", "_")
        agent_instances.append(
            AgentInstanceConfig(
                name=f"researcher_{name}",
                role="worker",
                description=f"Research {competitor['name']} ({competitor['website']})",
                tools=["Write", "Read"],
                prompt_file="researcher.txt",
                model=agent_model,
                metadata={"competitor": competitor},
            )
        )

    # Processor 角色: 数据分析师（可选，0-1）
    if config.get("output", {}).get("include_charts", False):
        agent_instances.append(
            AgentInstanceConfig(
                name="data_analyst",
                role="processor",
                description="Analyze research data and generate visualizations",
                tools=["Glob", "Bash"],
                prompt_file="data_analyst.txt",
                model=agent_model,
            )
        )

    # Synthesizer 角色: 报告撰写者（必须恰好 1 个）
    agent_instances.append(
        AgentInstanceConfig(
            name="report_writer",
            role="synthesizer",
            description="Generate comprehensive competitive intelligence report",
            tools=["Read", "Glob"],
            prompt_file="report_writer.txt",
            model=agent_model,
        )
    )

    return agent_instances


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

        print("\n✅ Analysis complete!")
        print(f"📊 Report saved to: {output_path}")

        # Print summary
        print("\n📈 Summary:")
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
