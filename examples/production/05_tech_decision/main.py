"""Tech Decision Support System using Debate Architecture.

Provides structured debate for evaluating technical decisions including:
- Technology selection (React vs Vue, PostgreSQL vs MongoDB)
- Architecture changes (Monolith to Microservices)
- Build vs Buy decisions
- Vendor selection

Uses the Debate architecture from Claude Agent Framework.
"""

import asyncio
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add parent directories to path for common utilities
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from common import ResultSaver, load_yaml_config, validate_config

from claude_agent_framework import create_session


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""

    pass


class ExecutionError(Exception):
    """Raised when decision execution fails."""

    pass


async def run_tech_decision(
    config: dict,
    decision_question: str,
    context: dict,
) -> dict:
    """Run tech decision evaluation using Debate architecture.

    Args:
        config: Configuration dict from config.yaml
        decision_question: The technical decision to evaluate
        context: Context including options, requirements, constraints

    Returns:
        dict: Decision result with debate transcript, evaluation, and recommendation
    """
    # Validate configuration
    required_fields = ["architecture", "participants", "debate_config", "evaluation_criteria"]
    validate_config(config, required_fields)

    # Extract configuration
    participants_config = config["participants"]
    debate_config = config["debate_config"]
    evaluation_criteria = config["evaluation_criteria"]
    decision_config = config.get("decision", {})
    models = config.get("models", {})
    advanced = config.get("advanced", {})

    # Build debate prompt
    prompt = _build_debate_prompt(
        decision_question,
        context,
        participants_config,
        debate_config,
        evaluation_criteria,
        decision_config,
        advanced,
    )

    # Initialize debate session with business template
    try:
        session = create_session(
            "debate",
            model=models.get("lead", "sonnet"),
            business_template=config.get("business_template", "tech_decision"),
            template_vars={
                "decision_topic": config.get("decision_topic", "Technology Decision"),
                "organization": config.get("organization", "Organization"),
                "evaluation_criteria": config.get(
                    "evaluation_criteria", ["Technical Fit", "Cost", "Risk"]
                ),
            },
            verbose=False,
        )
    except Exception as e:
        raise ExecutionError(f"Failed to initialize debate session: {e}")

    # Run debate
    results = []
    try:
        async for msg in session.run(prompt):
            results.append(msg)
    except Exception as e:
        raise ExecutionError(f"Debate execution failed: {e}")
    finally:
        await session.teardown()

    # Parse debate results
    debate_transcript = _parse_debate_transcript(results)
    evaluation_scores = _extract_evaluation_scores(results, evaluation_criteria)
    final_recommendation = _extract_final_recommendation(results)
    risk_assessment = _extract_risk_assessment(results)
    implementation_roadmap = _extract_implementation_roadmap(results)

    # Build result structure
    result = {
        "decision_id": str(uuid.uuid4()),
        "title": f"Tech Decision: {decision_question}",
        "summary": _generate_summary(decision_question, final_recommendation, evaluation_scores),
        "decision": {
            "question": decision_question,
            "context": context,
            "decision_type": decision_config.get("decision_type", "technology_selection"),
        },
        "debate": {
            "rounds": debate_config.get("rounds", 3),
            "transcript": debate_transcript,
            "format": debate_config.get("format", "oxford_style"),
        },
        "evaluation": {
            "criteria": evaluation_criteria,
            "scores": evaluation_scores,
            "overall_score": _calculate_overall_score(evaluation_scores, evaluation_criteria),
        },
        "recommendation": final_recommendation,
        "risk_assessment": risk_assessment,
        "implementation_roadmap": implementation_roadmap,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "config": {
                "rounds": debate_config.get("rounds"),
                "participants": list(participants_config.keys()),
                "models": models,
            },
        },
    }

    return result


def _build_debate_prompt(
    decision_question: str,
    context: dict,
    participants_config: dict,
    debate_config: dict,
    evaluation_criteria: dict,
    decision_config: dict,
    advanced: dict,
) -> str:
    """Build comprehensive debate prompt.

    Note: Role instructions and workflow guidance are provided by the
    business template (tech_decision). This function only generates
    the user task description.

    Args:
        decision_question: The decision to evaluate
        context: Decision context (options, requirements, constraints)
        participants_config: Debate participants configuration
        debate_config: Debate structure and rules
        evaluation_criteria: Weighted evaluation criteria
        decision_config: Decision type and templates
        advanced: Advanced options (fact-checking, evidence requirements)

    Returns:
        str: Complete debate prompt
    """
    # Extract context
    options = context.get("options", [])
    requirements = context.get("requirements", [])
    constraints = context.get("constraints", {})
    current_situation = context.get("current_situation", "")

    # Build criteria description
    criteria_desc = []
    for criterion, config in evaluation_criteria.items():
        weight = config.get("weight", 0)
        sub_criteria = config.get("sub_criteria", [])
        criteria_desc.append(
            f"- **{criterion.replace('_', ' ').title()}** ({weight}%): " + ", ".join(sub_criteria)
        )

    criteria_text = "\n".join(criteria_desc)

    # Build debate structure
    rounds = debate_config.get("rounds", 3)

    prompt = f"""# Tech Decision Debate

## Decision Question

{decision_question}

## Current Situation

{current_situation if current_situation else "Not specified"}

## Options Being Evaluated

{chr(10).join(f"- **Option {i + 1}**: {opt}" for i, opt in enumerate(options))}

## Requirements

{chr(10).join(f"- {req}" for req in requirements)}

## Constraints

Budget: {constraints.get("budget", "Not specified")}
Timeline: {constraints.get("timeline", "Not specified")}
Team Size: {constraints.get("team_size", "Not specified")}
Existing Tech Stack: {constraints.get("tech_stack", "Not specified")}

## Debate Configuration

Rounds: {rounds}
Format: {debate_config.get("format", "oxford_style")}

## Evaluation Criteria (Weighted)

{criteria_text}

Conduct a structured debate and provide a final recommendation with implementation roadmap.
"""

    return prompt


def _parse_debate_transcript(results: list[str]) -> list[dict]:
    """Parse debate transcript into structured format.

    Args:
        results: Raw debate output from session.run()

    Returns:
        list[dict]: Structured debate rounds with speaker and content
    """
    full_text = "\n".join(results)

    transcript = []

    # Extract rounds
    rounds = []
    current_round = None

    for line in full_text.split("\n"):
        if line.startswith("### Round"):
            if current_round:
                rounds.append(current_round)
            current_round = {"round": line, "content": []}
        elif current_round is not None:
            current_round["content"].append(line)

    if current_round:
        rounds.append(current_round)

    # Parse each round
    for round_data in rounds:
        round_text = "\n".join(round_data["content"])

        # Extract proponent and opponent statements
        proponent_text = ""
        opponent_text = ""

        if "**[Proponent]**" in round_text:
            parts = round_text.split("**[Proponent]**")
            if len(parts) > 1:
                proponent_part = parts[1].split("**[Opponent]**")[0]
                proponent_text = proponent_part.strip()

        if "**[Opponent]**" in round_text:
            parts = round_text.split("**[Opponent]**")
            if len(parts) > 1:
                opponent_text = parts[1].strip()

        transcript.append(
            {
                "round": round_data["round"],
                "proponent": proponent_text,
                "opponent": opponent_text,
            }
        )

    return transcript


def _extract_evaluation_scores(results: list[str], evaluation_criteria: dict) -> dict[str, dict]:
    """Extract evaluation scores from debate results.

    Args:
        results: Raw debate output
        evaluation_criteria: Criteria configuration

    Returns:
        dict: Scores by criterion and option
    """
    full_text = "\n".join(results)

    scores = {}

    # Look for Evaluation Scorecard section
    if "### Evaluation Scorecard" in full_text:
        scorecard_start = full_text.index("### Evaluation Scorecard")
        scorecard_section = full_text[scorecard_start:]

        # Extract scores for each criterion
        for criterion in evaluation_criteria.keys():
            criterion_title = criterion.replace("_", " ").title()
            if criterion_title in scorecard_section:
                # Parse scores (simplified - in reality would need more robust parsing)
                scores[criterion] = {
                    "weight": evaluation_criteria[criterion].get("weight", 0),
                    "scores": {},  # Would extract actual scores here
                }

    return scores if scores else {"note": "Scores not found in standard format"}


def _extract_final_recommendation(results: list[str]) -> dict:
    """Extract final recommendation from judge.

    Args:
        results: Raw debate output

    Returns:
        dict: Recommendation details
    """
    full_text = "\n".join(results)

    recommendation = {
        "recommended_option": "Not determined",
        "justification": "",
        "strengths": [],
        "risks": [],
    }

    # Look for Final Recommendation section
    if "### Final Recommendation" in full_text:
        rec_start = full_text.index("### Final Recommendation")
        rec_section = full_text[rec_start : rec_start + 2000]  # Take next 2000 chars

        # Extract recommended option
        if "**Recommended Option**:" in rec_section:
            option_line = rec_section.split("**Recommended Option**:")[1].split("\n")[0]
            recommendation["recommended_option"] = option_line.strip()

        # Extract justification
        if "**Justification**:" in rec_section:
            just_start = rec_section.index("**Justification**:")
            just_end = rec_section.find("**Key Strengths**:", just_start)
            if just_end == -1:
                just_end = len(rec_section)
            justification = rec_section[just_start:just_end]
            recommendation["justification"] = justification.replace(
                "**Justification**:", ""
            ).strip()

    return recommendation


def _extract_risk_assessment(results: list[str]) -> list[dict]:
    """Extract risk assessment from results.

    Args:
        results: Raw debate output

    Returns:
        list[dict]: Identified risks with mitigation strategies
    """
    full_text = "\n".join(results)

    risks = []

    if "**Acknowledged Risks**:" in full_text:
        risks_start = full_text.index("**Acknowledged Risks**:")
        risks_section = full_text[risks_start : risks_start + 1000]

        # Extract numbered risks
        lines = risks_section.split("\n")
        for line in lines:
            if line.strip().startswith(("1.", "2.", "3.", "4.", "5.")):
                risk_text = line.strip()[3:].strip()  # Remove number
                risks.append({"risk": risk_text, "severity": "Medium", "mitigation": ""})

    return risks if risks else [{"risk": "No risks explicitly identified", "severity": "N/A"}]


def _extract_implementation_roadmap(results: list[str]) -> dict:
    """Extract implementation roadmap.

    Args:
        results: Raw debate output

    Returns:
        dict: Phased implementation plan
    """
    full_text = "\n".join(results)

    roadmap = {"phases": [], "success_metrics": []}

    if "**Implementation Roadmap**:" in full_text:
        roadmap_start = full_text.index("**Implementation Roadmap**:")
        roadmap_section = full_text[roadmap_start : roadmap_start + 2000]

        # Extract phases
        for phase_name in ["Phase 1", "Phase 2", "Phase 3"]:
            if phase_name in roadmap_section:
                phase_start = roadmap_section.index(phase_name)
                phase_end = roadmap_section.find("Phase", phase_start + 1)
                if phase_end == -1:
                    phase_end = roadmap_section.find("**Success Metrics**:", phase_start)
                if phase_end == -1:
                    phase_end = len(roadmap_section)

                phase_text = roadmap_section[phase_start:phase_end]
                actions = [
                    line.strip()[2:].strip()
                    for line in phase_text.split("\n")
                    if line.strip().startswith("-")
                ]

                roadmap["phases"].append({"phase": phase_name, "actions": actions})

    return roadmap


def _generate_summary(
    decision_question: str, final_recommendation: dict, evaluation_scores: dict
) -> str:
    """Generate executive summary.

    Args:
        decision_question: The decision question
        final_recommendation: Final recommendation dict
        evaluation_scores: Evaluation scores

    Returns:
        str: Concise summary
    """
    recommended = final_recommendation.get("recommended_option", "Not determined")
    justification = final_recommendation.get("justification", "")

    # Truncate justification to first sentence
    if justification:
        first_sentence = justification.split(".")[0] + "."
    else:
        first_sentence = "Decision evaluated through structured debate."

    return f"Evaluated: {decision_question}. Recommendation: {recommended}. {first_sentence}"


def _calculate_overall_score(evaluation_scores: dict, evaluation_criteria: dict) -> float:
    """Calculate weighted overall score.

    Args:
        evaluation_scores: Scores by criterion
        evaluation_criteria: Criteria weights

    Returns:
        float: Overall weighted score (0-100)
    """
    # Simplified - would calculate actual weighted average
    return 0.0


async def main():
    """Main entry point for tech decision CLI."""
    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    config = load_yaml_config(config_path)

    # Example decision
    decision_question = "Should we migrate from REST API to GraphQL?"

    context = {
        "options": [
            "Migrate entire API to GraphQL",
            "Hybrid approach (GraphQL for new, REST for existing)",
            "Stay with REST and enhance with better documentation",
        ],
        "requirements": [
            "Reduce number of API calls from mobile app",
            "Improve developer experience",
            "Maintain backward compatibility",
            "Support real-time updates",
        ],
        "constraints": {
            "budget": "$50,000",
            "timeline": "6 months",
            "team_size": "5 backend engineers",
            "tech_stack": "Node.js, PostgreSQL, React Native mobile app",
        },
        "current_situation": """
        Our REST API has 150+ endpoints. Mobile app makes 20+ API calls to render a single screen.
        Team experienced with REST but no GraphQL experience.
        Customers complain about slow mobile app performance.
        """,
    }

    # Run decision process
    print(f"Evaluating decision: {decision_question}\n")

    result = await run_tech_decision(config, decision_question, context)

    print(f"Decision ID: {result['decision_id']}")
    print(f"Recommendation: {result['recommendation']['recommended_option']}")
    print(f"\nSummary: {result['summary']}")

    # Save result
    output_config = config.get("output", {})
    saver = ResultSaver(output_config.get("directory", "outputs/tech_decisions"))
    output_path = saver.save(result, format=output_config.get("format", "json"))

    print(f"\nFull decision report saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
