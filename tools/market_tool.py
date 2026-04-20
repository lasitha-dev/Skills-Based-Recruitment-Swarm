"""
SalaryBenchmarkTool: Fetches salary and demand data for skills.

Uses a hybrid approach:
  1. Primary: Local JSON dataset (fast, 220+ skills)
  2. Fallback: ChatOllama phi3 LLM estimation for unknown skills

This ensures that no skill ever returns "unknown" - the LLM fills the gaps
for any skill not in the local dataset.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import List, Dict, Any

from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama

logger = logging.getLogger(__name__)

# Resolve data file path relative to this file's location
DATA_PATH: Path = Path(__file__).parent.parent / "data" / "salary_benchmarks.json"

# System prompt for LLM fallback estimation
LLM_FALLBACK_PROMPT: str = """You are a salary data assistant. When given a tech skill, estimate its market data.

You MUST respond with ONLY a valid JSON object in this exact format (no markdown, no extra text):
{"salary_range": [min_salary, max_salary], "average": average_salary, "demand": "high" or "emerging" or "low"}

Rules:
- salary_range: two integers in USD (annual), e.g. [60000, 110000]
- average: single integer, must be between min and max
- demand: exactly one of "high", "emerging", or "low"
- Base your estimates on typical US tech industry salary data
- Respond with ONLY the JSON object, nothing else"""


def _parse_int_env(var_name: str, default_value: int, minimum: int) -> int:
    """Parse integer environment variables with a safe bounded fallback.

    Args:
        var_name: Name of the environment variable.
        default_value: Value used when env is missing or invalid.
        minimum: Minimum accepted value.

    Returns:
        Parsed integer value with lower bound enforcement.
    """
    raw_value = os.getenv(var_name, str(default_value))
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        logger.warning(
            "[SalaryBenchmarkTool] Invalid %s='%s'. Using default %s.",
            var_name,
            raw_value,
            default_value,
        )
        return default_value
    return max(minimum, parsed)


ENABLE_LLM_FALLBACK: bool = os.getenv("MARS_ENABLE_MARKET_LLM_FALLBACK", "false").lower() == "true"
MAX_LLM_FALLBACK_SKILLS: int = _parse_int_env("MARS_MAX_MARKET_LLM_FALLBACK_SKILLS", 2, 0)


def _load_salary_data() -> Dict[str, Any]:
    """Load the salary benchmarks from the local JSON file.

    Returns:
        Dictionary mapping skill names to their salary/demand data.

    Raises:
        FileNotFoundError: If the data file is missing.
        json.JSONDecodeError: If the data file contains invalid JSON.
    """
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)
    logger.info("[SalaryBenchmarkTool] Loaded %d skills from local dataset.", len(data))
    return data


def _lookup_skill(skill: str, salary_data: Dict[str, Any]) -> Dict[str, Any]:
    """Look up a single skill in the salary data with case-insensitive matching.

    Args:
        skill: The skill name to look up.
        salary_data: The loaded salary benchmark dictionary.

    Returns:
        The salary data for the skill, or None if not found.
    """
    # Exact match first
    if skill in salary_data:
        return salary_data[skill]

    # Case-insensitive match
    for key in salary_data:
        if key.lower() == skill.lower():
            return salary_data[key]

    return None


def _llm_fallback_estimate(skill: str) -> Dict[str, Any]:
    """Use ChatOllama phi3 to estimate salary data for an unknown skill.

    This is called when a skill is not found in the local JSON dataset.
    The LLM provides a reasonable estimate based on its training data.

    Args:
        skill: The skill name to estimate data for.

    Returns:
        Estimated salary data dict with salary_range, average, demand,
        and a flag indicating it was LLM-estimated.

    Raises:
        Exception: If the LLM call fails (caught by caller).
    """
    logger.info("[SalaryBenchmarkTool] Skill '%s' not in dataset. Using LLM fallback...", skill)

    llm = ChatOllama(
        model="phi3",
        temperature=0.2,
        base_url="http://localhost:11434",
        timeout=60,
    )

    messages = [
        SystemMessage(content=LLM_FALLBACK_PROMPT),
        HumanMessage(content=f"Estimate the salary data for this tech skill: {skill}")
    ]

    response = llm.invoke(messages)
    raw: str = response.content.strip()

    # Clean potential markdown wrapping
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    try:
        estimated: Dict[str, Any] = json.loads(raw)
        # Mark it as LLM-estimated so we know the source
        estimated["source"] = "llm_estimated"
        logger.info(
            "[SalaryBenchmarkTool] LLM estimated '%s': range=%s, avg=%s, demand=%s",
            skill, estimated.get("salary_range"), estimated.get("average"), estimated.get("demand")
        )
        return estimated
    except json.JSONDecodeError:
        logger.warning(
            "[SalaryBenchmarkTool] LLM returned unparseable response for '%s': %s",
            skill, raw[:200]
        )
        return {
            "salary_range": None,
            "average": None,
            "demand": "unknown",
            "source": "llm_failed"
        }


def _heuristic_fallback_estimate(skill: str) -> Dict[str, Any]:
    """Generate a deterministic estimate for unknown skills without LLM calls.

    Args:
        skill: Skill label that is missing from local benchmark data.

    Returns:
        Stable heuristic estimate payload.
    """
    normalized = skill.lower()

    high_demand_keywords = {
        "python", "java", "javascript", "typescript", "react", "node", "node.js",
        "aws", "docker", "kubernetes", "sql", "mongodb", "mysql", "cloud",
    }
    low_demand_keywords = {"excel", "word", "powerpoint", "typing", "data entry"}

    demand = "emerging"
    if any(keyword in normalized for keyword in high_demand_keywords):
        demand = "high"
    elif any(keyword in normalized for keyword in low_demand_keywords):
        demand = "low"

    if demand == "high":
        salary_range = [90000, 150000]
    elif demand == "low":
        salary_range = [45000, 85000]
    else:
        salary_range = [70000, 120000]

    average = int((salary_range[0] + salary_range[1]) / 2)

    logger.info(
        "[SalaryBenchmarkTool] Heuristic fallback for '%s': range=%s, avg=%s, demand=%s",
        skill,
        salary_range,
        average,
        demand,
    )

    return {
        "salary_range": salary_range,
        "average": average,
        "demand": demand,
        "source": "heuristic_fallback",
    }


def _resolve_unknown_skill(skill: str, llm_fallback_count: int) -> tuple[Dict[str, Any], int]:
    """Resolve market data for unknown skills with bounded optional LLM fallback.

    Args:
        skill: Unknown skill token.
        llm_fallback_count: Current count of used LLM fallback calls.

    Returns:
        Tuple of (resolved market payload, updated LLM fallback count).
    """
    if ENABLE_LLM_FALLBACK and llm_fallback_count < MAX_LLM_FALLBACK_SKILLS:
        try:
            llm_result = _llm_fallback_estimate(skill)
            return llm_result, llm_fallback_count + 1
        except Exception as error:
            logger.error("[SalaryBenchmarkTool] LLM fallback failed for '%s': %s", skill, error)

    return _heuristic_fallback_estimate(skill), llm_fallback_count


@tool
def salary_benchmark_tool(skills: List[str]) -> Dict[str, Any]:
    """Fetch salary ranges, average compensation, and demand indicators for each skill.

    Uses a hybrid approach:
    1. First checks the local JSON dataset (220+ skills, instant lookup).
    2. For any skill NOT found, falls back to ChatOllama phi3 for estimation.

    This ensures no skill ever returns 'unknown' - the LLM fills the gaps.

    Args:
        skills: List of skill names to benchmark (e.g. ["Python", "Docker"]).

    Returns:
        A dictionary mapping each skill name to its market data containing:
        - salary_range: [min, max] salary in USD, or None if estimation failed.
        - average: Average salary in USD, or None if estimation failed.
        - demand: One of "high", "emerging", "low", or "unknown".
        - source: "local_dataset" or "llm_estimated" or "llm_failed".

    Raises:
        FileNotFoundError: If the salary benchmark data file is missing.
    """
    results: Dict[str, Any] = {}

    # Load local dataset
    try:
        salary_data: Dict[str, Any] = _load_salary_data()
    except FileNotFoundError as e:
        logger.error("[SalaryBenchmarkTool] Data file not found at %s: %s", DATA_PATH, e)
        raise
    except json.JSONDecodeError as e:
        logger.error("[SalaryBenchmarkTool] Invalid JSON in data file: %s", e)
        raise

    llm_fallback_count = 0
    for skill in skills:
        cleaned_skill = re.sub(r"\s+", " ", skill).strip()
        if not cleaned_skill:
            continue

        # Step 1: Try local dataset
        local_result = _lookup_skill(cleaned_skill, salary_data)

        if local_result is not None:
            results[cleaned_skill] = {**local_result, "source": "local_dataset"}
            logger.info("[SalaryBenchmarkTool] Found '%s' in local dataset.", cleaned_skill)
        else:
            # Step 2: Resolve unknown skill with optional bounded LLM fallback.
            resolved, llm_fallback_count = _resolve_unknown_skill(cleaned_skill, llm_fallback_count)
            results[cleaned_skill] = resolved

    logger.info("[SalaryBenchmarkTool] Benchmark results for %d skills complete.", len(results))
    return results
