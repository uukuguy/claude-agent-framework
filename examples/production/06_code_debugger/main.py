"""Code Debugger using Reflexion Architecture.

Provides intelligent debugging through execute-reflect-improve loop:
- Execute debugging strategies
- Reflect on results and failures
- Improve strategy based on learnings
- Iterate until root cause found

Uses the Reflexion architecture from Claude Agent Framework.
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
    """Raised when debugging execution fails."""

    pass


def _confidence_to_score(confidence: str) -> float:
    """Convert confidence string to numeric score.

    Args:
        confidence: Confidence level (High, Medium, Low, Unknown)

    Returns:
        float: Numeric score between 0.0 and 1.0
    """
    confidence_map = {
        "high": 1.0,
        "medium": 0.6,
        "low": 0.3,
        "unknown": 0.0,
    }
    return confidence_map.get(confidence.lower(), 0.0)


async def run_code_debugger(
    config: dict,
    bug_description: str,
    context: dict,
) -> dict:
    """Run code debugging using Reflexion architecture.

    Args:
        config: Configuration dict from config.yaml
        bug_description: Description of the bug
        context: Context including error message, file paths, reproduction steps

    Returns:
        dict: Debugging result with root cause, fix, and validation
    """
    # Validate configuration
    required_fields = ["architecture", "debugging", "reflexion_config", "strategies"]
    validate_config(config, required_fields)

    # Validate architecture type
    if config["architecture"] != "reflexion":
        raise ConfigurationError(
            f"Invalid architecture: {config['architecture']}. Must be 'reflexion'"
        )

    # Validate reflexion_config structure
    reflexion_config = config["reflexion_config"]
    required_roles = ["executor", "reflector", "improver"]
    for role in required_roles:
        if role not in reflexion_config:
            raise ConfigurationError(f"Missing reflexion_config.{role}")
        if "name" not in reflexion_config[role]:
            raise ConfigurationError(f"Missing reflexion_config.{role}.name")
        if "role" not in reflexion_config[role]:
            raise ConfigurationError(f"Missing reflexion_config.{role}.role")

    # Extract configuration
    debugging_config = config["debugging"]
    strategies = config["strategies"]
    bug_categories = config.get("bug_categories", {})
    root_cause_framework = config.get("root_cause_analysis", {})
    models = config.get("models", {})
    advanced = config.get("advanced", {})

    # Build reflexion prompt
    prompt = _build_reflexion_prompt(
        bug_description,
        context,
        debugging_config,
        reflexion_config,
        strategies,
        bug_categories,
        root_cause_framework,
        advanced,
    )

    # Initialize reflexion session with business template
    try:
        session = create_session(
            "reflexion",
            model=models.get("lead", "sonnet"),
            business_template=config.get("business_template", "code_debugger"),
            template_vars={
                "codebase": config.get("codebase", "Application Codebase"),
                "language": config.get("language", "Python"),
                "bug_description": bug_description,
            },
            verbose=False,
        )
    except Exception as e:
        raise ExecutionError(f"Failed to initialize reflexion session: {e}")

    # Run reflexion loop
    results = []
    try:
        async for msg in session.run(prompt):
            content = extract_message_content(msg)
            if content:
                results.append(content)
    except Exception as e:
        raise ExecutionError(f"Reflexion execution failed: {e}")
    finally:
        await session.teardown()

    # Parse debugging results
    debugging_timeline = _parse_debugging_timeline(results)
    root_cause = _extract_root_cause(results)
    proposed_fix = _extract_proposed_fix(results)
    failed_attempts = _extract_failed_attempts(results)
    learnings = _extract_learnings(results)
    prevention_recommendations = _extract_prevention_recommendations(results)

    # Build result structure
    result = {
        "debug_session_id": str(uuid.uuid4()),
        "title": f"Debug Session: {bug_description[:100]}",
        "summary": _generate_summary(bug_description, root_cause, debugging_timeline),
        "bug": {
            "description": bug_description,
            "error_message": context.get("error_message", ""),
            "file_path": context.get("file_path", ""),
            "category": _categorize_bug(bug_description, context, bug_categories),
            "context": context,
        },
        "debugging_timeline": debugging_timeline,
        "root_cause": root_cause,
        "proposed_fix": proposed_fix,
        "failed_attempts": failed_attempts,
        "learnings": learnings,
        "prevention_recommendations": prevention_recommendations,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "iterations": len(debugging_timeline),
            "max_iterations": debugging_config.get("max_iterations", 5),
            "success": _confidence_to_score(root_cause.get("confidence", "Unknown"))
            >= debugging_config.get("success_threshold", 0.9),
            "config": {
                "strategies_used": list(strategies.keys()),
                "models": models,
            },
        },
    }

    return result


def _build_reflexion_prompt(
    bug_description: str,
    context: dict,
    debugging_config: dict,
    reflexion_config: dict,
    strategies: dict,
    bug_categories: dict,
    root_cause_framework: dict,
    advanced: dict,
) -> str:
    """Build reflexion debugging prompt.

    Note: Role instructions and workflow guidance are provided by the
    business template (code_debugger). This function only generates
    the user task description.

    Args:
        bug_description: Bug description
        context: Bug context (error message, file path, etc.)
        debugging_config: Debugging configuration
        reflexion_config: Reflexion loop configuration
        strategies: Available debugging strategies
        bug_categories: Bug categorization patterns
        root_cause_framework: Root cause analysis framework
        advanced: Advanced options

    Returns:
        str: User task description for debugging
    """
    # Extract context
    error_message = context.get("error_message", "")
    file_path = context.get("file_path", "")
    reproduction_steps = context.get("reproduction_steps", [])
    expected_behavior = context.get("expected_behavior", "")
    actual_behavior = context.get("actual_behavior", "")
    code_snippet = context.get("code_snippet", "")

    # Build strategies description
    strategies_desc = []
    for strategy_name, strategy_config in strategies.items():
        desc = strategy_config.get("description", "")
        priority = strategy_config.get("priority", 0)
        strategies_desc.append(f"- **{strategy_name}** (Priority {priority}): {desc}")

    strategies_text = "\n".join(strategies_desc)

    # Build root cause categories
    categories = root_cause_framework.get("categories", [])
    categories_desc = []
    for category in categories:
        name = category.get("name", "")
        indicators = category.get("indicators", [])
        categories_desc.append(f"- **{name}**: {', '.join(indicators)}")

    categories_text = "\n".join(categories_desc)

    # Build advanced options
    advanced_options = []
    if advanced.get("enable_static_analysis"):
        advanced_options.append("- Static analysis enabled")
    if advanced.get("enable_llm_debugging"):
        advanced_options.append("- LLM debugging enabled")
    if advanced.get("verbose_logging"):
        advanced_options.append("- Verbose logging enabled")
    advanced_text = "\n".join(advanced_options) if advanced_options else "None"

    prompt = f"""# Code Debugging Task

## Bug Description

{bug_description}

## Bug Context

**Error Message**:
```
{error_message if error_message else "No error message provided"}
```

**File Path**: {file_path if file_path else "Not specified"}

**Code Snippet**:
```python
{code_snippet if code_snippet else "No code snippet provided"}
```

**Expected Behavior**: {expected_behavior if expected_behavior else "Not specified"}

**Actual Behavior**: {actual_behavior if actual_behavior else "Not specified"}

**Reproduction Steps**:
{chr(10).join(f"{i + 1}. {step}" for i, step in enumerate(reproduction_steps)) if reproduction_steps else "Not provided"}

## Debugging Configuration

Maximum iterations: {debugging_config.get("max_iterations", 5)}
Success threshold: {debugging_config.get("success_threshold", 0.9)}

## Available Debugging Strategies

{strategies_text}

## Root Cause Categories

{categories_text}

## Advanced Options

{advanced_text}

Debug this issue using the reflexion loop to systematically find and fix the root cause.
"""

    return prompt


def _categorize_bug(bug_description: str, context: dict, bug_categories: dict) -> str:
    """Categorize bug based on description and context.

    Args:
        bug_description: Bug description
        context: Bug context
        bug_categories: Bug category patterns

    Returns:
        str: Bug category
    """
    error_message = context.get("error_message", "").lower()
    description_lower = bug_description.lower()

    for category, config in bug_categories.items():
        patterns = config.get("patterns", [])
        for pattern in patterns:
            if pattern.lower() in error_message or pattern.lower() in description_lower:
                return category

    return "unknown"


def _parse_debugging_timeline(results: list[str]) -> list[dict]:
    """Parse debugging timeline from reflexion results.

    Args:
        results: Raw reflexion output

    Returns:
        list[dict]: Timeline of debugging iterations
    """
    full_text = "\n".join(results)

    timeline = []

    # Extract iterations
    iterations = []
    current_iteration = None

    for line in full_text.split("\n"):
        if line.startswith("### Iteration"):
            if current_iteration:
                iterations.append(current_iteration)
            current_iteration = {"iteration": line, "content": []}
        elif current_iteration is not None:
            current_iteration["content"].append(line)

    if current_iteration:
        iterations.append(current_iteration)

    # Parse each iteration
    for idx, iteration_data in enumerate(iterations):
        iteration_text = "\n".join(iteration_data["content"])

        # Extract executor, reflector, improver sections
        executor_text = ""
        reflector_text = ""
        improver_text = ""

        if "**[Executor]**" in iteration_text:
            parts = iteration_text.split("**[Executor]**")
            if len(parts) > 1:
                executor_part = parts[1].split("**[Reflector]**")[0]
                executor_text = executor_part.strip()

        if "**[Reflector]**" in iteration_text:
            parts = iteration_text.split("**[Reflector]**")
            if len(parts) > 1:
                reflector_part = parts[1].split("**[Improver]**")[0]
                reflector_text = reflector_part.strip()

        if "**[Improver]**" in iteration_text:
            parts = iteration_text.split("**[Improver]**")
            if len(parts) > 1:
                improver_text = parts[1].strip()

        timeline.append(
            {
                "iteration": idx + 1,
                "executor": executor_text,
                "reflector": reflector_text,
                "improver": improver_text,
            }
        )

    return timeline


def _extract_root_cause(results: list[str]) -> dict:
    """Extract root cause from debugging results.

    Args:
        results: Raw reflexion output

    Returns:
        dict: Root cause details
    """
    full_text = "\n".join(results)

    root_cause = {
        "category": "Unknown",
        "description": "",
        "confidence": "Unknown",
        "evidence": [],
    }

    if "**Root Cause Identified**" in full_text:
        cause_start = full_text.index("**Root Cause Identified**")
        cause_section = full_text[cause_start : cause_start + 1500]

        # Extract category
        if "Category:" in cause_section:
            category_line = cause_section.split("Category:")[1].split("\n")[0]
            root_cause["category"] = category_line.strip()

        # Extract description
        if "Description:" in cause_section:
            desc_start = cause_section.index("Description:")
            desc_end = cause_section.find("Why it causes", desc_start)
            if desc_end == -1:
                desc_end = cause_section.find("Confidence:", desc_start)
            if desc_end == -1:
                desc_end = len(cause_section)
            description = cause_section[desc_start:desc_end]
            root_cause["description"] = description.replace("Description:", "").strip()

        # Extract confidence
        if "Confidence:" in cause_section:
            conf_line = cause_section.split("Confidence:")[1].split("\n")[0]
            root_cause["confidence"] = conf_line.strip()

        # Extract evidence
        if "Evidence:" in cause_section:
            evidence_start = cause_section.index("Evidence:")
            evidence_section = cause_section[evidence_start : evidence_start + 500]
            lines = evidence_section.split("\n")
            for line in lines:
                if line.strip().startswith(("1.", "2.", "3.", "4.", "5.")):
                    evidence_text = line.strip()[3:].strip()
                    root_cause["evidence"].append(evidence_text)

    return root_cause


def _extract_proposed_fix(results: list[str]) -> dict:
    """Extract proposed fix from debugging results.

    Args:
        results: Raw reflexion output

    Returns:
        dict: Proposed fix details
    """
    full_text = "\n".join(results)

    proposed_fix = {
        "file_path": None,
        "before_code": None,
        "after_code": None,
        "explanation": "",
        "alternatives": [],
    }

    if "**Proposed Fix**" in full_text:
        fix_start = full_text.index("**Proposed Fix**")
        fix_section = full_text[fix_start : fix_start + 2000]

        # Extract file path
        if "# File:" in fix_section:
            file_line = fix_section.split("# File:")[1].split("\n")[0]
            proposed_fix["file_path"] = file_line.strip()

        # Extract before/after code
        if "# Before" in fix_section and "# After" in fix_section:
            # Extract before code
            before_start = fix_section.find("# Before")
            after_marker = fix_section.find("# After", before_start)
            if after_marker != -1:
                before_section = fix_section[before_start:after_marker]
                # Skip the "# Before (problematic code):" line
                lines = before_section.split("\n")[1:]
                # Stop at empty lines or comment markers
                code_lines = []
                for line in lines:
                    if not line.strip() or line.strip().startswith("# After"):
                        break
                    code_lines.append(line)
                proposed_fix["before_code"] = "\n".join(code_lines).strip()

            # Extract after code
            after_start = fix_section.find("# After")
            expl_marker = fix_section.find("# Explanation:", after_start)
            if expl_marker == -1:
                expl_marker = fix_section.find("```", after_start + 10)  # Find closing ```
            if expl_marker != -1:
                after_section = fix_section[after_start:expl_marker]
                # Skip the "# After (fixed code):" line
                lines = after_section.split("\n")[1:]
                # Stop at empty lines, explanation, or closing ```
                code_lines = []
                for line in lines:
                    if line.strip().startswith("# Explanation") or line.strip() == "```":
                        break
                    code_lines.append(line)
                proposed_fix["after_code"] = "\n".join(code_lines).strip()

        # Extract explanation
        if "# Explanation:" in fix_section:
            expl_start = fix_section.index("# Explanation:")
            expl_end = fix_section.find("Alternative approaches", expl_start)
            if expl_end == -1:
                expl_end = fix_section.find("**Fix Validation**", expl_start)
            if expl_end == -1:
                expl_end = len(fix_section)
            explanation = fix_section[expl_start:expl_end]
            proposed_fix["explanation"] = explanation.replace("# Explanation:", "").strip()

    return proposed_fix


def _extract_failed_attempts(results: list[str]) -> list[dict]:
    """Extract failed debugging attempts.

    Args:
        results: Raw reflexion output

    Returns:
        list[dict]: Failed attempts with reasons
    """
    full_text = "\n".join(results)

    failed_attempts = []

    if "**Failed Attempts Summary**" in full_text:
        summary_start = full_text.index("**Failed Attempts Summary**")
        summary_section = full_text[summary_start : summary_start + 1000]

        lines = summary_section.split("\n")
        for line in lines:
            if line.strip().startswith("Iteration"):
                # Parse: "Iteration 1: Tried X - Failed because Y"
                parts = line.split(":")
                if len(parts) >= 2:
                    iteration_part = parts[0].strip()
                    detail_part = ":".join(parts[1:])

                    if " - Failed because " in detail_part:
                        tried_part, reason_part = detail_part.split(" - Failed because ")
                        failed_attempts.append(
                            {
                                "iteration": iteration_part,
                                "strategy": tried_part.replace("Tried", "").strip(),
                                "reason": reason_part.strip(),
                            }
                        )

    return failed_attempts


def _extract_learnings(results: list[str]) -> list[str]:
    """Extract key learnings from debugging session.

    Args:
        results: Raw reflexion output

    Returns:
        list[str]: Key learnings
    """
    full_text = "\n".join(results)

    learnings = []

    if "Key learnings:" in full_text:
        learnings_start = full_text.index("Key learnings:")
        learnings_section = full_text[learnings_start : learnings_start + 500]

        lines = learnings_section.split("\n")
        for line in lines:
            if line.strip().startswith(("1.", "2.", "3.", "4.", "5.")):
                learning_text = line.strip()[3:].strip()
                learnings.append(learning_text)

    return learnings if learnings else ["No explicit learnings documented"]


def _extract_prevention_recommendations(results: list[str]) -> list[str]:
    """Extract prevention recommendations.

    Args:
        results: Raw reflexion output

    Returns:
        list[str]: Prevention recommendations
    """
    full_text = "\n".join(results)

    recommendations = []

    if "**Prevention Recommendations**" in full_text:
        prev_start = full_text.index("**Prevention Recommendations**")
        prev_section = full_text[prev_start : prev_start + 800]

        lines = prev_section.split("\n")
        for line in lines:
            if line.strip().startswith(("1.", "2.", "3.", "4.", "5.")):
                rec_text = line.strip()[3:].strip()
                recommendations.append(rec_text)

    return recommendations if recommendations else ["No prevention recommendations provided"]


def _generate_summary(
    bug_description: str, root_cause: dict, debugging_timeline: list[dict]
) -> str:
    """Generate executive summary.

    Args:
        bug_description: Bug description
        root_cause: Root cause dict
        debugging_timeline: Debugging iterations

    Returns:
        str: Summary text
    """
    iterations = len(debugging_timeline)
    category = root_cause.get("category", "Unknown")
    confidence = root_cause.get("confidence", "Low")

    return f"Debugged: {bug_description[:100]}. Root cause: {category}. Confidence: {confidence}. Iterations: {iterations}."


async def main():
    """Main entry point for code debugger CLI."""
    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    config = load_yaml_config(config_path)

    # Example bug
    bug_description = "AttributeError: 'NoneType' object has no attribute 'get'"

    context = {
        "error_message": """
Traceback (most recent call last):
  File "app.py", line 45, in process_user_data
    user_email = user.get('email')
AttributeError: 'NoneType' object has no attribute 'get'
        """,
        "file_path": "app.py",
        "code_snippet": """
def process_user_data(user_id):
    user = fetch_user(user_id)
    user_email = user.get('email')  # Line 45 - Error occurs here
    send_notification(user_email)
    return user
        """,
        "reproduction_steps": [
            "Call process_user_data(999) with non-existent user ID",
            "fetch_user returns None for invalid ID",
            "Attempt to call .get() on None raises AttributeError",
        ],
        "expected_behavior": "Should handle missing user gracefully",
        "actual_behavior": "Crashes with AttributeError",
    }

    # Run debugging
    print(f"Debugging: {bug_description}\n")

    result = await run_code_debugger(config, bug_description, context)

    print(f"Debug Session ID: {result['debug_session_id']}")
    print(f"Root Cause: {result['root_cause']['category']}")
    print(f"Confidence: {result['root_cause']['confidence']}")
    print(f"Iterations: {result['metadata']['iterations']}")
    print(f"\nSummary: {result['summary']}")

    # Save result
    output_config = config.get("output", {})
    saver = ResultSaver(output_config.get("directory", "outputs/debug_sessions"))
    output_path = saver.save(result, format=output_config.get("format", "json"))

    print(f"\nFull debugging report saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
