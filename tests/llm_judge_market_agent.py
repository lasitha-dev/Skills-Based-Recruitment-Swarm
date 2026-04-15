"""
LLM-as-a-Judge validation script for Agent 2 (Market Scout).

Uses ChatOllama (phi3) to independently evaluate whether Agent 2's output
is technically accurate, well-structured, and follows the Market Scout persona.

This script requires:
- Ollama installed and running locally
- phi3 model pulled (ollama pull phi3)

Usage:
    python tests/llm_judge_market_agent.py
"""

import json
import logging
import os
import sys
from typing import Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama

# Add parent directory to path for imports
sys.path.insert(0, ".")

from agents.market_agent import market_scout_agent
from agents.state import AgentState

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "phi3")

# ── Judge system prompt ─────────────────────────────────────────────────────

JUDGE_SYSTEM_PROMPT: str = """You are an expert evaluator reviewing the output of an AI agent in a multi-agent recruitment system.

You must evaluate the agent's output based on these criteria:

1. TECHNICAL ACCURACY: Is the market/salary data plausible and reasonable?
2. STRUCTURE: Is the output well-structured JSON that downstream agents can parse?
3. PERSONA ADHERENCE: Does the output match the "Market Scout" persona (focused on salary data, demand trends, and market insights)?
4. COMPLETENESS: Does the output cover all input skills with appropriate analysis?
5. REASONING: Is the chain-of-thought reasoning logical and transparent?

Respond with a JSON object in this exact format:
{
    "verdict": "PASS" or "FAIL",
    "score": <number from 1-10>,
    "technical_accuracy": "<assessment>",
    "structure": "<assessment>",
    "persona_adherence": "<assessment>",
    "completeness": "<assessment>",
    "reasoning_quality": "<assessment>",
    "improvements": ["<suggestion 1>", "<suggestion 2>"],
    "overall_assessment": "<2-3 sentence summary>"
}
"""


def run_ollama_judge(
    agent_output: Dict[str, Any],
    input_skills: list,
    persona: str = "Market Scout"
) -> Dict[str, Any]:
    """Call ChatOllama to judge the output of Agent 2.

    Uses a separate LLM invocation to independently evaluate whether
    Agent 2's output meets quality criteria for accuracy, structure,
    and persona adherence.

    Args:
        agent_output: The market_data output from Agent 2 (market_scout_agent).
        input_skills: The list of skills that were provided as input.
        persona: The expected agent persona name.

    Returns:
        A dictionary containing the LLM judge's assessment with verdict,
        score, and detailed criteria evaluations.

    Raises:
        Exception: If the LLM invocation fails.
    """
    llm = ChatOllama(
        model=OLLAMA_MODEL,
        temperature=0.2,
        base_url="http://localhost:11434"
    )

    human_prompt: str = f"""Evaluate the following output from the "{persona}" agent.

INPUT SKILLS PROVIDED: {json.dumps(input_skills)}

AGENT OUTPUT (JSON):
{json.dumps(agent_output, indent=2, default=str)}

Assess this output against all criteria and provide your verdict as JSON."""

    logger.info("[LLM-Judge] Sending agent output to %s for evaluation...", OLLAMA_MODEL)

    messages = [
        SystemMessage(content=JUDGE_SYSTEM_PROMPT),
        HumanMessage(content=human_prompt),
    ]

    try:
        response = llm.invoke(messages)
        raw_response: str = response.content
        logger.info("[LLM-Judge] Raw judge response:\n%s", raw_response)

        # Parse the response
        cleaned = raw_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            assessment: Dict[str, Any] = json.loads(cleaned)
            return assessment
        except json.JSONDecodeError:
            logger.warning("[LLM-Judge] Could not parse response as JSON.")
            return {
                "verdict": "INCONCLUSIVE",
                "score": 0,
                "overall_assessment": raw_response,
                "improvements": ["Judge response was not valid JSON"],
            }

    except Exception as e:
        logger.error("[LLM-Judge] Failed to invoke LLM judge: %s", e)
        return {
            "verdict": "ERROR",
            "score": 0,
            "overall_assessment": f"Judge invocation failed: {e}",
            "improvements": [],
        }


def main() -> None:
    """Run the LLM-as-a-Judge validation for Agent 2.

    Executes Agent 2 with test data, then sends the output to a separate
    LLM call for independent quality evaluation.
    """
    print("\n" + "=" * 60)
    print("  LLM-as-a-Judge — Agent 2 (Market Scout) Validation")
    print("=" * 60 + "\n")

    # Step 1: Run Agent 2 with test data
    test_skills = ["Python", "Docker", "Machine Learning", "Go", "Cobol"]
    test_state: AgentState = {
        "candidate_name": "Test Candidate",
        "found_skills": test_skills,
        "logs": [],
    }

    print("📋 Input skills:", test_skills)
    print("\n🔄 Running Agent 2 (Market Scout)...\n")

    try:
        output_state: AgentState = market_scout_agent(test_state)
        market_data: Dict[str, Any] = output_state.get("market_data", {})
    except Exception as e:
        print(f"❌ Agent 2 execution failed: {e}")
        logger.error("Agent 2 execution failed: %s", e)
        return

    print("✅ Agent 2 completed. Output preview:")
    print(json.dumps(market_data, indent=2, default=str)[:500] + "...\n")

    # Step 2: Send output to LLM Judge
    print("🧑‍⚖️ Running LLM-as-a-Judge evaluation...\n")

    assessment: Dict[str, Any] = run_ollama_judge(
        agent_output=market_data,
        input_skills=test_skills,
    )

    # Step 3: Display results
    print("=" * 60)
    print("  JUDGE ASSESSMENT")
    print("=" * 60)
    print(json.dumps(assessment, indent=2, default=str))

    verdict = assessment.get("verdict", "UNKNOWN")
    score = assessment.get("score", "N/A")
    print(f"\n{'✅' if verdict == 'PASS' else '❌'} Verdict: {verdict}")
    print(f"📊 Score: {score}/10")

    if assessment.get("improvements"):
        print("\n💡 Suggested Improvements:")
        for improvement in assessment["improvements"]:
            print(f"   • {improvement}")


if __name__ == "__main__":
    main()
