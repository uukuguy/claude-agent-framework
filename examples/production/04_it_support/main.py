"""IT Support Platform Example.

This example demonstrates using the Specialist Pool architecture to route
technical support issues to appropriate specialist agents based on keywords
and domain expertise.
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
    load_yaml_config,
    setup_logging,
    validate_config,
)

from claude_agent_framework import create_session

logger = logging.getLogger(__name__)


async def run_it_support(config: dict, issue_title: str, issue_description: str) -> dict:
    """Run IT support issue resolution using Specialist Pool architecture.

    Args:
        config: Configuration dictionary
        issue_title: Issue title
        issue_description: Detailed issue description

    Returns:
        dict: Support resolution result
    """
    specialists_config = config["specialists"]
    routing_config = config["routing"]
    categorization_config = config.get("categorization", {})
    response_template = config.get("response_template", {})
    models = config.get("models", {})

    logger.info(f"Processing IT support issue: {issue_title}")

    # Categorize urgency
    urgency, sla_hours = _categorize_urgency(issue_title, issue_description, categorization_config)
    logger.info(f"Issue urgency: {urgency} (SLA: {sla_hours}h)")

    # Route to appropriate specialists
    selected_specialists = _route_to_specialists(
        issue_title, issue_description, specialists_config, routing_config
    )

    if not selected_specialists:
        logger.warning("No specialists matched. Using fallback.")
        selected_specialists = [_get_fallback_specialist(specialists_config)]

    logger.info(
        f"Routed to {len(selected_specialists)} specialist(s): {[s['name'] for s in selected_specialists]}"
    )

    # Build specialist pool prompt
    prompt = _build_specialist_pool_prompt(
        issue_title,
        issue_description,
        selected_specialists,
        urgency,
        sla_hours,
        response_template,
    )

    # Run specialist pool architecture
    session = create_session("specialist_pool", model=models.get("lead", "sonnet"), verbose=False)

    results = []
    async for msg in session.run(prompt):
        logger.info(f"Progress: {msg}")
        results.append(msg)

    await session.teardown()

    # Parse specialist responses
    specialist_responses = _parse_specialist_responses(results, selected_specialists)

    # Generate consolidated solution (pass results too for extraction)
    consolidated_solution = _consolidate_solutions(specialist_responses, results)

    # Build result
    result = {
        "title": f"IT Support Resolution: {issue_title}",
        "summary": _generate_summary(urgency, selected_specialists, consolidated_solution),
        "issue": {
            "title": issue_title,
            "description": issue_description,
            "urgency": urgency,
            "sla_hours": sla_hours,
        },
        "routing": {
            "specialists": [s["name"] for s in selected_specialists],
            "routing_strategy": routing_config.get("strategy", "keyword_match"),
        },
        "specialist_responses": specialist_responses,
        "consolidated_solution": consolidated_solution,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "num_specialists": len(selected_specialists),
            "urgency": urgency,
            "sla_hours": sla_hours,
        },
    }

    logger.info("✅ Support resolution complete!")
    logger.info(f"Specialists consulted: {len(selected_specialists)}")

    return result


def _categorize_urgency(
    title: str, description: str, categorization_config: dict
) -> tuple[str, int]:
    """Categorize issue urgency based on keywords.

    Args:
        title: Issue title
        description: Issue description
        categorization_config: Categorization configuration

    Returns:
        tuple: (urgency_level, sla_hours)
    """
    text = f"{title} {description}".lower()

    urgency_levels = categorization_config.get("urgency_levels", [])

    for level in urgency_levels:
        keywords = level.get("keywords", [])
        if any(keyword.lower() in text for keyword in keywords):
            return level["name"], level["sla_hours"]

    # Default to medium
    return "medium", 24


def _route_to_specialists(
    title: str, description: str, specialists_config: list[dict], routing_config: dict
) -> list[dict]:
    """Route issue to appropriate specialists based on keywords.

    Args:
        title: Issue title
        description: Issue description
        specialists_config: List of specialist configurations
        routing_config: Routing configuration

    Returns:
        list: Selected specialists
    """
    text = f"{title} {description}".lower()
    min_matches = routing_config.get("min_keyword_matches", 1)
    allow_multiple = routing_config.get("allow_multiple", True)
    max_specialists = routing_config.get("max_specialists", 3)

    # Calculate match scores for each specialist
    specialist_scores = []

    for specialist in specialists_config:
        # Skip fallback specialist (has lowest priority)
        if specialist.get("priority", 5) >= 5:
            continue

        keywords = specialist.get("keywords", [])
        matches = sum(1 for keyword in keywords if keyword.lower() in text)

        if matches >= min_matches:
            specialist_scores.append(
                {
                    "specialist": specialist,
                    "matches": matches,
                    "priority": specialist.get("priority", 5),
                }
            )

    # Sort by matches (descending) then priority (ascending)
    specialist_scores.sort(key=lambda x: (-x["matches"], x["priority"]))

    # Select specialists
    if not allow_multiple:
        selected = specialist_scores[:1]
    else:
        selected = specialist_scores[:max_specialists]

    return [item["specialist"] for item in selected]


def _get_fallback_specialist(specialists_config: list[dict]) -> dict:
    """Get fallback specialist (lowest priority).

    Args:
        specialists_config: List of specialist configurations

    Returns:
        dict: Fallback specialist
    """
    fallback = None
    lowest_priority = 0

    for specialist in specialists_config:
        priority = specialist.get("priority", 5)
        if priority >= lowest_priority:
            lowest_priority = priority
            fallback = specialist

    return fallback or specialists_config[0]


def _build_specialist_pool_prompt(
    title: str,
    description: str,
    specialists: list[dict],
    urgency: str,
    sla_hours: int,
    response_template: dict,
) -> str:
    """Build specialist pool prompt for issue resolution.

    Args:
        title: Issue title
        description: Issue description
        specialists: Selected specialists
        urgency: Urgency level
        sla_hours: SLA hours
        response_template: Response template configuration

    Returns:
        str: Formatted prompt
    """
    # Format specialist list
    specialist_list = "\n".join(
        f"- **{spec['name']}**: {spec['description']}" for spec in specialists
    )

    # Response requirements
    requirements = []
    if response_template.get("include_diagnosis", True):
        requirements.append("Root cause diagnosis")
    if response_template.get("include_steps", True):
        requirements.append("Step-by-step resolution steps")
    if response_template.get("include_prevention", True):
        requirements.append("Prevention recommendations")
    if response_template.get("include_escalation", False):
        requirements.append("Escalation criteria")

    requirements_text = "\n".join(f"- {req}" for req in requirements)

    prompt = f"""Resolve an IT support issue using specialist expertise.

## Issue Details

**Title**: {title}

**Description**:
{description}

**Urgency**: {urgency.upper()} (SLA: {sla_hours} hours)

## Available Specialists

{specialist_list}

## Instructions

Each specialist should analyze the issue from their domain perspective and provide:

{requirements_text}

**Output Format**:

For each specialist, provide:

```
### [Specialist Name]

**Analysis**:
[Domain-specific analysis of the issue]

**Root Cause**:
[Likely root cause from this specialist's perspective]

**Resolution Steps**:
1. [Specific actionable step]
2. [Another step]
...

**Prevention**:
[Recommendations to prevent recurrence]

**Confidence**: [High/Medium/Low]
```

After all specialists have provided input, provide:

```
### Consolidated Solution

**Primary Root Cause**:
[Most likely root cause based on all specialist input]

**Recommended Action Plan**:
1. [Immediate action]
2. [Follow-up action]
...

**Expected Resolution Time**: [Estimate]

**Risk Assessment**: [Any risks to be aware of]
```

Begin the specialist analysis now.
"""

    return prompt


def _parse_specialist_responses(results: list[str], specialists: list[dict]) -> list[dict]:
    """Parse specialist responses from results.

    Args:
        results: List of result messages
        specialists: List of specialists

    Returns:
        list: Parsed specialist responses
    """
    full_text = "\n".join(results)
    responses = []

    for specialist in specialists:
        name = specialist["name"]

        # Find specialist section
        marker = f"### {name}"
        start = full_text.find(marker)

        if start == -1:
            # Try alternative format
            marker = f"**{name}**"
            start = full_text.find(marker)

        if start != -1:
            # Extract until next specialist or consolidated solution
            end = len(full_text)
            for other_spec in specialists:
                if other_spec["name"] != name:
                    other_marker = f"### {other_spec['name']}"
                    other_pos = full_text.find(other_marker, start + 1)
                    if other_pos != -1 and other_pos < end:
                        end = other_pos

            # Also check for consolidated solution
            consol_marker = "### Consolidated Solution"
            consol_pos = full_text.find(consol_marker, start + 1)
            if consol_pos != -1 and consol_pos < end:
                end = consol_pos

            response_text = full_text[start:end].strip()

            # Extract confidence if present
            confidence = "Medium"
            if "Confidence**: High" in response_text or "Confidence: High" in response_text:
                confidence = "High"
            elif "Confidence**: Low" in response_text or "Confidence: Low" in response_text:
                confidence = "Low"

            responses.append(
                {
                    "specialist": name,
                    "response": response_text,
                    "confidence": confidence,
                }
            )

    return responses


def _consolidate_solutions(specialist_responses: list[dict], results: list[str]) -> str:
    """Extract consolidated solution from responses.

    Args:
        specialist_responses: List of specialist responses
        results: Original result messages

    Returns:
        str: Consolidated solution text
    """
    # First, try to find in the full results text
    all_results_text = "\n".join(results)
    marker = "### Consolidated Solution"
    start = all_results_text.find(marker)
    if start != -1:
        return all_results_text[start:].strip()

    # Look for consolidated solution in specialist responses
    for response in specialist_responses:
        text = response.get("response", "")
        if "Consolidated Solution" in text:
            start = text.find(marker)
            if start != -1:
                return text[start:].strip()

    return "Consolidated solution not generated. Please review individual specialist responses."


def _generate_summary(urgency: str, specialists: list[dict], consolidated_solution: str) -> str:
    """Generate summary of support resolution.

    Args:
        urgency: Urgency level
        specialists: List of specialists consulted
        consolidated_solution: Consolidated solution

    Returns:
        str: Summary text
    """
    num_specialists = len(specialists)
    specialist_names = ", ".join(s["name"] for s in specialists)

    summary = f"""IT support issue resolved with {urgency} urgency.
Consulted {num_specialists} specialist(s): {specialist_names}.
Consolidated solution provided with actionable steps."""

    return summary


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="IT Support Platform")
    parser.add_argument("--config", type=str, default="config.yaml", help="Configuration file path")
    parser.add_argument("--title", type=str, help="Issue title")
    parser.add_argument("--description", type=str, help="Issue description")
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
    parser.add_argument(
        "--use-example",
        type=int,
        help="Use example issue from config (0-based index)",
    )

    args = parser.parse_args()

    try:
        # Load configuration
        config_path = Path(args.config)
        config = load_yaml_config(config_path)

        # Validate required fields
        required_fields = ["architecture", "specialists", "routing", "output"]
        validate_config(config, required_fields)

        # Validate architecture
        if config["architecture"] != "specialist_pool":
            raise ConfigurationError(
                f"Invalid architecture '{config['architecture']}'. Expected 'specialist_pool'."
            )

        # Setup logging
        log_config = config.get("logging", {})
        log_level = args.log_level or log_config.get("level", "INFO")
        log_file = log_config.get("file")
        if log_file:
            log_file = Path(log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)

        setup_logging(level=log_level, log_file=log_file)

        # Get issue details
        if args.use_example is not None:
            example_issues = config.get("example_issues", [])
            if 0 <= args.use_example < len(example_issues):
                example = example_issues[args.use_example]
                issue_title = example["title"]
                issue_description = example["description"]
                logger.info(f"Using example issue #{args.use_example}: {issue_title}")
            else:
                raise ConfigurationError(
                    f"Example index {args.use_example} out of range (0-{len(example_issues) - 1})"
                )
        elif args.title and args.description:
            issue_title = args.title
            issue_description = args.description
        else:
            # Use first example if no input provided
            example_issues = config.get("example_issues", [])
            if example_issues:
                example = example_issues[0]
                issue_title = example["title"]
                issue_description = example["description"]
                logger.info(f"Using default example: {issue_title}")
            else:
                raise ConfigurationError(
                    "No issue provided. Use --title and --description, or --use-example"
                )

        # Run IT support
        result = asyncio.run(run_it_support(config, issue_title, issue_description))

        # Save result
        output_config = config["output"]
        output_dir = Path(output_config["directory"])
        output_format = args.output_format or output_config.get("format", "markdown")

        saver = ResultSaver(output_dir)
        output_file = args.output_file
        if output_file:
            output_file = Path(output_file).stem

        output_path = saver.save(result, format=output_format, filename=output_file)

        print("\n✅ IT support resolution complete!")
        print(f"📄 Output saved to: {output_path}")
        print(f"🔧 Specialists consulted: {result['metadata']['num_specialists']}")
        print(f"⚡ Urgency: {result['metadata']['urgency'].upper()}")
        print(f"⏰ SLA: {result['metadata']['sla_hours']} hours")

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
