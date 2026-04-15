"""
SalaryBenchmarkTool: Fetches salary and demand data for skills from a local JSON dataset.

This tool is used by Agent 2 (Market Scout) to retrieve market salary ranges,
average compensation, and demand indicators for each detected skill.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Resolve data file path relative to this file's location
DATA_PATH: Path = Path(__file__).parent.parent / "data" / "salary_benchmarks.json"


@tool
def salary_benchmark_tool(skills: List[str]) -> Dict[str, Any]:
    """Fetch salary ranges, average compensation, and demand indicators for each skill.

    Looks up each skill in the local salary benchmarks JSON dataset. For skills
    not found in the dataset, returns a default entry with null values and
    'unknown' demand.

    Args:
        skills: List of skill names to benchmark (e.g. ["Python", "Docker"]).

    Returns:
        A dictionary mapping each skill name to its market data containing:
        - salary_range: [min, max] salary in USD, or None if unknown.
        - average: Average salary in USD, or None if unknown.
        - demand: One of "high", "emerging", "low", or "unknown".

    Raises:
        FileNotFoundError: If the salary benchmark data file is missing.
    """
    results: Dict[str, Any] = {}

    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            salary_data: Dict[str, Any] = json.load(f)
        logger.info("[SalaryBenchmarkTool] Loaded %d skills from dataset.", len(salary_data))
    except FileNotFoundError as e:
        logger.error("[SalaryBenchmarkTool] Data file not found at %s: %s", DATA_PATH, e)
        raise
    except json.JSONDecodeError as e:
        logger.error("[SalaryBenchmarkTool] Invalid JSON in data file: %s", e)
        raise

    for skill in skills:
        # Case-insensitive lookup: try exact match first, then case-insensitive
        if skill in salary_data:
            results[skill] = salary_data[skill]
            logger.info("[SalaryBenchmarkTool] Found data for skill: %s", skill)
        else:
            # Try case-insensitive match
            matched = False
            for key in salary_data:
                if key.lower() == skill.lower():
                    results[skill] = salary_data[key]
                    logger.info(
                        "[SalaryBenchmarkTool] Found data for skill '%s' (matched as '%s').",
                        skill, key
                    )
                    matched = True
                    break
            if not matched:
                results[skill] = {
                    "salary_range": None,
                    "average": None,
                    "demand": "unknown"
                }
                logger.warning("[SalaryBenchmarkTool] No data found for skill: %s", skill)

    logger.info("[SalaryBenchmarkTool] Benchmark results: %s", json.dumps(results, indent=2))
    return results
