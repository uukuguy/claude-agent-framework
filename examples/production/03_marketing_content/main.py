"""Marketing Content Optimization Example.

This example demonstrates using the Critic-Actor architecture to create and
iteratively improve marketing content based on multi-dimensional evaluation.
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
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


async def run_content_optimization(config: dict) -> dict:
    """Run marketing content optimization using Critic-Actor architecture.

    Args:
        config: Configuration dictionary

    Returns:
        dict: Optimization result with content, scores, and history
    """
    content_config = config["content"]
    brand_config = config["brand"]
    evaluation_config = config["evaluation"]
    iteration_config = config["iteration"]
    models = config.get("models", {})

    logger.info("Starting marketing content optimization...")
    logger.info(f"Content type: {content_config['type']}")
    logger.info(f"Max iterations: {iteration_config['max_iterations']}")
    logger.info(f"Quality threshold: {iteration_config['quality_threshold']}")

    # Build critic-actor prompt
    prompt = _build_critic_actor_prompt(
        content_config, brand_config, evaluation_config, iteration_config
    )

    # Run critic-actor architecture with business template
    session = create_session(
        "critic_actor",
        model=models.get("lead", "sonnet"),
        business_template=config.get("business_template", "marketing_content"),
        template_vars={
            "brand_name": config.get("brand_name", "Brand Name"),
            "target_audience": config.get("target_audience", "Target Audience"),
            "content_type": config.get("content_type", "blog post"),
            "brand_voice": config.get("brand_voice", "professional"),
        },
        verbose=False,
    )

    results = []
    async for msg in session.run(prompt):
        logger.info(f"Progress: {msg}")
        content = extract_message_content(msg)
        if content:
            results.append(content)

    await session.teardown()

    # Parse results
    final_content, iterations, final_score = _parse_optimization_results(results)

    # Generate A/B variants if enabled
    variants = []
    if config.get("ab_testing", {}).get("enabled", False):
        num_variants = config["ab_testing"].get("num_variants", 2)
        logger.info(f"Generating {num_variants} A/B test variants...")
        variants = await _generate_ab_variants(
            final_content, content_config, brand_config, num_variants, models
        )

    # Build result
    result = {
        "title": "Marketing Content Optimization Report",
        "summary": _generate_summary(iterations, final_score, content_config),
        "content_type": content_config["type"],
        "final_content": final_content,
        "final_score": final_score,
        "iterations": iterations,
        "ab_variants": variants,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "num_iterations": len(iterations),
            "quality_threshold": iteration_config["quality_threshold"],
            "target_length": content_config.get("target_length", {}),
            "keywords": content_config.get("keywords", []),
        },
    }

    logger.info(f"✅ Optimization complete! Final score: {final_score}/100")
    logger.info(f"Iterations: {len(iterations)}")

    return result


def _build_critic_actor_prompt(
    content_config: dict,
    brand_config: dict,
    evaluation_config: dict,
    iteration_config: dict,
) -> str:
    """Build critic-actor prompt for content optimization.

    Note: Role instructions and workflow guidance are provided by the
    business template (marketing_content). This function only generates
    the user task description.

    Args:
        content_config: Content configuration
        brand_config: Brand guidelines
        evaluation_config: Evaluation criteria
        iteration_config: Iteration settings

    Returns:
        str: Formatted prompt
    """
    # Format evaluation criteria
    criteria_sections = []
    for category, details in evaluation_config.items():
        if category in ["seo", "engagement", "brand_consistency", "accuracy"]:
            weight = details["weight"]
            criteria = details["criteria"]
            criteria_list = "\n".join(f"  - {c}" for c in criteria)
            criteria_sections.append(
                f"**{category.replace('_', ' ').title()}** (Weight: {weight}%):\n{criteria_list}"
            )

    evaluation_text = "\n\n".join(criteria_sections)

    # Format brand guidelines
    brand_text = f"""
**Brand Voice**: {brand_config["voice"]}
**Tone Attributes**: {", ".join(brand_config["tone"])}
**Company Values**: {", ".join(brand_config["values"])}
**Prohibited Phrases**: {", ".join(brand_config.get("prohibited_phrases", []))}
"""

    # Format target length
    target_length = content_config.get("target_length", {})
    length_text = ""
    if target_length:
        min_words = target_length.get("min_words", "")
        max_words = target_length.get("max_words", "")
        if min_words and max_words:
            length_text = f"\n**Target Length**: {min_words}-{max_words} words"

    # Format keywords
    keywords = content_config.get("keywords", [])
    keywords_text = ""
    if keywords:
        keywords_text = f"\n**SEO Keywords**: {', '.join(keywords)}"

    prompt = f"""Optimize marketing content using iterative Critic-Actor pattern.

## Content Brief

**Content Type**: {content_config["type"]}
{length_text}
{keywords_text}

**Brief**:
{content_config["brief"]}

## Brand Guidelines
{brand_text}

## Evaluation Criteria
{evaluation_text}

## Iteration Settings
- Max iterations: {iteration_config["max_iterations"]}
- Quality threshold: {iteration_config["quality_threshold"]}
- Minimum improvement: {iteration_config.get("min_improvement", 5)}%

Deliver optimized content meeting the quality threshold.
"""

    return prompt


def _parse_optimization_results(results: list[str]) -> tuple[str, list[dict], float]:
    """Parse optimization results to extract content, iterations, and scores.

    Args:
        results: List of result messages

    Returns:
        tuple: (final_content, iterations_list, final_score)
    """
    full_text = "\n".join(results)

    # Extract iterations
    iterations = []
    iteration_blocks = full_text.split("=== ITERATION")

    for block in iteration_blocks[1:]:  # Skip first split
        if not block.strip():
            continue

        # Extract iteration number
        lines = block.split("\n")
        iteration_num = (
            int(lines[0].strip().split()[0]) if lines[0].strip() else len(iterations) + 1
        )

        # Extract content
        content_start = block.find("**Content**:")
        content_end = block.find("**Critic Evaluation**:")
        content = ""
        if content_start != -1 and content_end != -1:
            content = block[content_start + 12 : content_end].strip()

        # Extract overall score
        overall_score = 0.0
        score_match = block.find("**Overall Score**:")
        if score_match != -1:
            score_line = block[score_match:].split("\n")[0]
            # Extract number from "**Overall Score**: XX/100"
            try:
                score_str = score_line.split(":")[1].split("/")[0].strip()
                overall_score = float(score_str)
            except (IndexError, ValueError):
                pass

        # Extract individual scores
        scores = {}
        for dimension in ["SEO", "Engagement", "Brand Consistency", "Accuracy"]:
            dim_match = block.find(f"- {dimension}:")
            if dim_match != -1:
                dim_line = block[dim_match:].split("\n")[0]
                try:
                    score_str = dim_line.split(":")[1].split("/")[0].strip()
                    scores[dimension.lower().replace(" ", "_")] = float(score_str)
                except (IndexError, ValueError):
                    scores[dimension.lower().replace(" ", "_")] = 0.0

        iterations.append(
            {
                "iteration": iteration_num,
                "content": content,
                "overall_score": overall_score,
                "scores": scores,
            }
        )

    # Extract final content
    final_content = ""
    final_marker = full_text.find("=== FINAL CONTENT ===")
    if final_marker != -1:
        final_content = full_text[final_marker + 21 :].strip()
    elif iterations:
        final_content = iterations[-1]["content"]

    # Final score
    final_score = iterations[-1]["overall_score"] if iterations else 0.0

    return final_content, iterations, final_score


async def _generate_ab_variants(
    base_content: str,
    content_config: dict,
    brand_config: dict,
    num_variants: int,
    models: dict,
) -> list[dict]:
    """Generate A/B test variants with different angles.

    Args:
        base_content: Optimized base content
        content_config: Content configuration
        brand_config: Brand guidelines
        num_variants: Number of variants to generate
        models: Model configuration

    Returns:
        list: List of variant dictionaries
    """
    variants = []

    angles = [
        "Feature-focused (emphasize product capabilities)",
        "Benefit-focused (emphasize user outcomes)",
        "Problem-solution (start with pain points)",
        "Social proof (emphasize testimonials and adoption)",
    ]

    for i in range(min(num_variants, len(angles))):
        angle = angles[i]
        logger.info(f"Generating variant {i + 1} with angle: {angle}")

        prompt = f"""Generate a variant of this marketing content with a different angle.

**Original Content**:
{base_content}

**Variant Angle**: {angle}

**Brand Guidelines**:
- Voice: {brand_config["voice"]}
- Tone: {", ".join(brand_config["tone"])}

**Requirements**:
- Maintain the same key information and CTA
- Use the specified angle to differentiate
- Keep similar length
- Preserve brand voice and tone

Provide the variant content:
"""

        session = create_session("research", model=models.get("actor", "sonnet"), verbose=False)
        variant_text = []
        async for msg in session.run(prompt):
            variant_text.append(msg)
        await session.teardown()

        variants.append({"variant": i + 1, "angle": angle, "content": "\n".join(variant_text)})

    return variants


def _generate_summary(iterations: list[dict], final_score: float, content_config: dict) -> str:
    """Generate summary of optimization process.

    Args:
        iterations: List of iteration dictionaries
        final_score: Final overall score
        content_config: Content configuration

    Returns:
        str: Summary text
    """
    num_iterations = len(iterations)
    content_type = content_config["type"]

    if num_iterations == 0:
        return "No iterations completed"

    initial_score = iterations[0]["overall_score"]
    improvement = final_score - initial_score

    summary = f"""Optimized {content_type} through {num_iterations} iteration(s).
Initial score: {initial_score}/100
Final score: {final_score}/100
Improvement: +{improvement:.1f} points"""

    return summary


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Marketing Content Optimization")
    parser.add_argument("--config", type=str, default="config.yaml", help="Configuration file path")
    parser.add_argument(
        "--output-format",
        type=str,
        choices=["json", "markdown", "pdf"],
        help="Output format (overrides config)",
    )
    parser.add_argument("--output-file", type=str, help="Output file path (overrides config)")
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    try:
        # Load configuration
        config_path = Path(args.config)
        config = load_yaml_config(config_path)

        # Validate required fields
        required_fields = ["architecture", "content", "brand", "evaluation", "iteration", "output"]
        validate_config(config, required_fields)

        # Validate architecture
        if config["architecture"] != "critic_actor":
            raise ConfigurationError(
                f"Invalid architecture '{config['architecture']}'. Expected 'critic_actor'."
            )

        # Setup logging
        log_config = config.get("logging", {})
        log_level = args.log_level or log_config.get("level", "INFO")
        log_file = log_config.get("file")
        if log_file:
            log_file = Path(log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)

        setup_logging(level=log_level, log_file=log_file)

        # Run optimization
        result = asyncio.run(run_content_optimization(config))

        # Save result
        output_config = config["output"]
        output_dir = Path(output_config["directory"])
        output_format = args.output_format or output_config.get("format", "markdown")

        saver = ResultSaver(output_dir)
        output_file = args.output_file
        if output_file:
            output_file = Path(output_file).stem

        output_path = saver.save(result, format=output_format, filename=output_file)

        print("\n✅ Optimization complete!")
        print(f"📄 Output saved to: {output_path}")
        print(f"📊 Final score: {result['final_score']}/100")
        print(f"🔄 Iterations: {result['metadata']['num_iterations']}")

        if result.get("ab_variants"):
            print(f"🧪 Generated {len(result['ab_variants'])} A/B test variants")

    except ConfigurationError as e:
        print(f"❌ Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ExecutionError as e:
        print(f"❌ Execution Error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}", file=sys.stderr)
        logger.exception("Unexpected error occurred")
        sys.exit(3)


if __name__ == "__main__":
    main()
