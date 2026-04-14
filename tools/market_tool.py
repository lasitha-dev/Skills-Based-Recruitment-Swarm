"""
SalaryBenchmarkTool: Fetches salary and demand data for skills from a local JSON file.
"""

import json
import logging
from typing import List, Dict, Any

def SalaryBenchmarkTool(skills: List[str]) -> Dict[str, Any]:
	"""
	Fetch salary ranges, average compensation, and demand indicators for each skill.

	Args:
		skills (List[str]): List of skill names to benchmark.

	Returns:
		Dict[str, Any]: Mapping of skill to market data (salary, average, demand).

	Raises:
		FileNotFoundError: If the salary benchmark data file is missing.
		Exception: For other unexpected errors.
	"""
	data_path = "data/salary_benchmarks.json"
	results = {}
	try:
		with open(data_path, "r", encoding="utf-8") as f:
			salary_data = json.load(f)
		for skill in skills:
			if skill in salary_data:
				results[skill] = salary_data[skill]
			else:
				results[skill] = {"salary_range": None, "average": None, "demand": "unknown"}
				logging.warning(f"[SalaryBenchmarkTool] No data for skill: {skill}")
		logging.info(f"[SalaryBenchmarkTool] Results: {results}")
		return results
	except FileNotFoundError as e:
		logging.error(f"[SalaryBenchmarkTool] Data file not found: {e}")
		raise
	except Exception as e:
		logging.error(f"[SalaryBenchmarkTool] Unexpected error: {e}")
		raise
