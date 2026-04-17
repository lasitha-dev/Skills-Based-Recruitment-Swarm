"""
Agent 2: Market Scout — LangGraph Node with ChatOllama (phi3) Integration.

This agent consumes skills extracted by Agent 1 (Profile Parser), fetches
salary benchmarks using the SalaryBenchmarkTool, and then uses a local LLM
(phi3 via Ollama) to perform chain-of-thought trend analysis. The structured
output is placed in the shared AgentState for Agent 3 (Tech Evaluator).
"""

import json
import logging
import os
from typing import Dict, Any, List

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama

from agents.state import AgentState
from tools.market_tool import salary_benchmark_tool

logger = logging.getLogger(__name__)
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "phi3")

# ── Market Scout system prompt (defines the agent persona) ──────────────────
MARKET_SCOUT_SYSTEM_PROMPT: str = """You are the Market Scout agent in a multi-agent recruitment system.
Your role is to analyze salary benchmark data and market demand for candidate skills.

You will receive a JSON object containing salary ranges, averages, and demand indicators for each skill.

Your task:
1. Analyze each skill's market position (high-demand, emerging, or low-demand).
2. Identify the candidate's strongest market advantages (skills with highest demand and salary).
3. Identify any skills that may be declining or niche.
4. Provide a brief overall market assessment of the candidate's skill portfolio.
5. Suggest a recommended salary range based on the combined skill set.

IMPORTANT: Respond ONLY with a valid JSON object in this exact format (no markdown, no extra text):
{
    "skill_analyses": [
        {
            "skill": "<skill name>",
            "category": "high-demand" | "emerging" | "low-demand" | "unknown",
            "insight": "<one sentence about this skill's market position>"
        }
    ],
    "top_skills": ["<top 3 most valuable skills>"],
    "market_summary": "<2-3 sentence overall assessment>",
    "recommended_salary_range": {"min": <number>, "max": <number>},
    "reasoning": "<your chain-of-thought reasoning explaining how you arrived at this analysis>"
}
"""


def _invoke_llm_analysis(
    market_data: Dict[str, Any],
    skills: List[str]
) -> Dict[str, Any]:
    """Invoke ChatOllama to perform chain-of-thought trend analysis.

    Sends the raw salary benchmark data to the local LLM and asks it to
    reason about trends, market position, and provide structured insights.

    Args:
        market_data: Raw salary benchmark data from the SalaryBenchmarkTool.
        skills: List of skill names being analyzed.

    Returns:
        A dictionary containing the LLM's structured analysis including
        skill_analyses, top_skills, market_summary, recommended_salary_range,
        and reasoning (chain-of-thought).

    Raises:
        Exception: If the LLM invocation fails or returns unparseable output.
    """
    llm = ChatOllama(
        model=OLLAMA_MODEL,
        temperature=0.3,
        base_url="http://localhost:11434"
    )

    human_prompt = f"""Analyze the following market data for a job candidate's skills.

Skills being evaluated: {json.dumps(skills)}

Salary benchmark data:
{json.dumps(market_data, indent=2)}

Provide your analysis as a JSON object following the exact format specified in your instructions."""

    logger.info("[MarketScout] Sending data to %s LLM for analysis...", OLLAMA_MODEL)
    logger.info("[MarketScout] LLM Input — Skills: %s", skills)

    messages = [
        SystemMessage(content=MARKET_SCOUT_SYSTEM_PROMPT),
        HumanMessage(content=human_prompt)
    ]

    response = llm.invoke(messages)
    raw_response: str = response.content
    logger.info("[MarketScout] Raw LLM response:\n%s", raw_response)

    # Parse the LLM response as JSON
    try:
        # Try to extract JSON from the response (handle potential markdown wrapping)
        cleaned = raw_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        llm_analysis: Dict[str, Any] = json.loads(cleaned)
        logger.info("[MarketScout] Successfully parsed LLM analysis.")
        return llm_analysis
    except json.JSONDecodeError as e:
        logger.warning(
            "[MarketScout] Failed to parse LLM response as JSON: %s. "
            "Using raw response as reasoning.",
            e
        )
        # Fallback: return the raw response as the reasoning
        return {
            "skill_analyses": [],
            "top_skills": [],
            "market_summary": "LLM analysis could not be parsed. See reasoning for raw output.",
            "recommended_salary_range": {"min": 0, "max": 0},
            "reasoning": raw_response
        }


def _classify_demand(demand: str) -> str:
    """Classify a demand indicator into a standardized trend category.

    Args:
        demand: Raw demand string from the salary benchmark data.

    Returns:
        One of 'high-demand', 'emerging', 'low-demand', or 'unknown'.
    """
    demand_map: Dict[str, str] = {
        "high": "high-demand",
        "emerging": "emerging",
        "low": "low-demand",
    }
    return demand_map.get(demand, "unknown")


def market_scout_agent(state: AgentState) -> AgentState:
    """Agent 2 (Market Scout): LangGraph node that analyzes market demand for candidate skills.

    This agent performs three steps:
    1. Reads skills from the shared state (produced by Agent 1).
    2. Fetches salary benchmarks using the SalaryBenchmarkTool (local JSON lookup).
    3. Invokes ChatOllama for chain-of-thought trend analysis.

    The output is structured as JSON so Agent 3 (Tech Evaluator) can parse it.

    Args:
        state: The shared AgentState containing found_skills and other agent outputs.

    Returns:
        Updated AgentState with market_data populated and logs appended.
        Never overwrites existing state fields from other agents.
    """
    logger.info("[MarketScout] ===========================================")
    logger.info("[MarketScout] Agent 2 (Market Scout) invoked.")
    logger.info("[MarketScout] Received state keys: %s", list(state.keys()))

    # Preserve existing logs, never overwrite
    logs: List[str] = list(state.get("logs", []))
    logs.append(f"[MarketScout] Agent invoked. State keys: {list(state.keys())}")

    # ── Step 1: Skill Intake ────────────────────────────────────────────────
    skills: List[str] = state.get("found_skills", [])

    if not skills:
        logs.append("[MarketScout] No skills found in state. Skipping market analysis.")
        logger.warning("[MarketScout] No skills found in state. Returning early.")
        return {
            **state,
            "market_data": {
                "benchmark_data": {},
                "trends": {},
                "llm_analysis": {},
                "skills_analyzed": []
            },
            "logs": logs,
        }

    logs.append(f"[MarketScout] Skills received from Agent 1: {skills}")
    logger.info("[MarketScout] Skills to analyze: %s", skills)

    # ── Step 2: Market Benchmarking (SalaryBenchmarkTool) ───────────────────
    benchmark_data: Dict[str, Any] = {}
    try:
        benchmark_data = salary_benchmark_tool.invoke({"skills": skills})
        logs.append(f"[MarketScout] SalaryBenchmarkTool returned data for {len(benchmark_data)} skills.")
        logger.info("[MarketScout] Benchmark data fetched for %d skills.", len(benchmark_data))
    except FileNotFoundError:
        logs.append("[MarketScout] ERROR: Salary benchmark data file not found.")
        logger.error("[MarketScout] Salary benchmark data file not found.")
        benchmark_data = {
            skill: {"salary_range": None, "average": None, "demand": "unknown"}
            for skill in skills
        }
    except Exception as e:
        logs.append(f"[MarketScout] ERROR fetching market data: {e}")
        logger.error("[MarketScout] Unexpected error fetching market data: %s", e)
        benchmark_data = {
            skill: {"salary_range": None, "average": None, "demand": "error"}
            for skill in skills
        }

    # ── Step 3: Trend Classification (rule-based) ───────────────────────────
    trends: Dict[str, str] = {}
    for skill, data in benchmark_data.items():
        demand = data.get("demand", "unknown") if isinstance(data, dict) else "unknown"
        trend = _classify_demand(demand)
        trends[skill] = trend
        logs.append(f"[MarketScout] Skill '{skill}' classified as '{trend}' (demand: {demand})")
        logger.info("[MarketScout] %s -> %s", skill, trend)

    # ── Step 4: LLM Chain-of-Thought Analysis (ChatOllama) ──────────────────
    llm_analysis: Dict[str, Any] = {}
    try:
        llm_analysis = _invoke_llm_analysis(benchmark_data, skills)
        logs.append(f"[MarketScout] LLM ({OLLAMA_MODEL}) analysis complete.")
        logs.append(f"[MarketScout] LLM reasoning: {llm_analysis.get('reasoning', 'N/A')}")
        logger.info("[MarketScout] LLM analysis completed successfully.")
    except Exception as e:
        logs.append(f"[MarketScout] ERROR during LLM analysis: {e}")
        logger.error("[MarketScout] LLM analysis failed: %s", e)
        llm_analysis = {
            "skill_analyses": [],
            "top_skills": [],
            "market_summary": f"LLM analysis failed: {e}",
            "recommended_salary_range": {"min": 0, "max": 0},
            "reasoning": f"Error: {e}"
        }

    # ── Step 5: Structure Output for Agent 3 ────────────────────────────────
    market_output: Dict[str, Any] = {
        "benchmark_data": benchmark_data,
        "trends": trends,
        "llm_analysis": llm_analysis,
        "skills_analyzed": skills,
    }

    logs.append(f"[MarketScout] Final output structured with {len(skills)} skills analyzed.")
    logger.info("[MarketScout] Agent 2 complete. Output keys: %s", list(market_output.keys()))
    logger.info("[MarketScout] ===========================================")

    # Return updated state without overwriting other agent fields
    return {
        **state,
        "market_data": market_output,
        "logs": logs,
    }
