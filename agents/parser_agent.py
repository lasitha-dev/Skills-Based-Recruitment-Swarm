"""Agent 1: Profile Parser implementation."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
import re
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from tools.resume_tool import resume_reader_tool


LOGGER = logging.getLogger(__name__)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")


SYSTEM_PROMPT = """
You are Profile Parser, Agent 1 in a local recruitment swarm.
Your only task is to convert resume text into strict JSON.

Return exactly one JSON object with these keys:
- candidate_name: string
- skills: array of strings
- years_of_experience: number

Rules:
- Do not include explanations or markdown.
- If a field is unknown, use "" for candidate_name, [] for skills, and 0 for years_of_experience.
- Skills must be normalized, concise, and unique.
- If years_of_experience is not stated directly, estimate it from employment or project date ranges in the resume.
- Use the longest relevant continuous span or combined spans from work history to infer the most defensible whole number of years.
- Prefer explicit dates like "2022 - Present", "Jan 2023 - Dec 2024", or similar date ranges when calculating experience.
""".strip()


class ProfileData(TypedDict):
	"""Structured profile extracted from resume text."""

	candidate_name: str
	skills: list[str]
	years_of_experience: int


class GraphState(TypedDict, total=False):
	"""Shared state payload flowing through LangGraph."""

	file_path: str
	resume_text: str
	profile_data: ProfileData
	logs: list[str]
	error: str


def _extract_json_object(text: str) -> dict[str, Any]:
	"""Extract the first JSON object from a model response string."""
	stripped = text.strip()
	try:
		parsed = json.loads(stripped)
		if isinstance(parsed, dict):
			return parsed
	except json.JSONDecodeError:
		pass

	match = re.search(r"\{[\s\S]*\}", stripped)
	if not match:
		raise ValueError("No JSON object found in model output.")

	parsed_obj = json.loads(match.group(0))
	if not isinstance(parsed_obj, dict):
		raise ValueError("Model output JSON was not an object.")
	return parsed_obj


def _fallback_parse(resume_text: str) -> ProfileData:
	"""Fallback parser if JSON extraction from model output fails."""
	lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
	candidate_name = ""
	if lines:
		first_line = lines[0]
		if re.fullmatch(r"[A-Za-z][A-Za-z\s.'-]{1,80}", first_line):
			candidate_name = first_line

	skills_catalog = [
		"Python",
		"Java",
		"JavaScript",
		"TypeScript",
		"SQL",
		"AWS",
		"Docker",
		"Kubernetes",
		"React",
		"Node.js",
		"Git",
		"Machine Learning",
	]
	lower_text = resume_text.lower()
	skills = [skill for skill in skills_catalog if skill.lower() in lower_text]

	years = 0
	year_matches = re.findall(r"(\d{1,2})\+?\s+years?", lower_text)
	if year_matches:
		years = max(int(value) for value in year_matches)
	else:
		years = _infer_years_from_date_ranges(resume_text)

	return {
		"candidate_name": candidate_name,
		"skills": skills,
		"years_of_experience": years,
	}


def _parse_year(value: str) -> int | None:
	"""Extract a four-digit year from a date token."""
	matches = re.findall(r"(19|20)\d{2}", value)
	if not matches:
		return None
	full_match = re.search(r"(19|20)\d{2}", value)
	if not full_match:
		return None
	return int(full_match.group(0))


def _infer_years_from_date_ranges(text: str) -> int:
	"""Infer years of experience from visible date ranges in resume text."""
	current_year = datetime.now().year
	patterns = [
		r"(19\d{2}|20\d{2})\s*[-–—]\s*(present|current|now|19\d{2}|20\d{2})",
		r"([A-Za-z]{3,9}\s+\d{4}|\d{4})\s*[-–—]\s*(present|current|now|[A-Za-z]{3,9}\s+\d{4}|\d{4})",
	]

	spans: list[int] = []
	for pattern in patterns:
		for match in re.finditer(pattern, text, flags=re.IGNORECASE):
			segment = match.group(0)
			parts = re.split(r"[-–—]", segment)
			if len(parts) < 2:
				continue
			start_raw = parts[0].strip()
			end_raw = parts[1].strip().lower()

			start_year = _parse_year(start_raw)
			if start_year is None:
				continue

			if end_raw in {"present", "current", "now"}:
				end_year = current_year
			else:
				end_year = _parse_year(end_raw)
				if end_year is None:
					continue

			span = max(0, end_year - start_year)
			if span > 0:
				spans.append(span)

	if spans:
		return max(spans)
	return 0


def _normalize_profile(parsed: dict[str, Any]) -> ProfileData:
	"""Normalize model JSON into the strict profile schema."""
	candidate_name = parsed.get("candidate_name", "")
	if not isinstance(candidate_name, str):
		candidate_name = ""

	skills_raw = parsed.get("skills", [])
	skills: list[str] = []
	if isinstance(skills_raw, list):
		seen: set[str] = set()
		for item in skills_raw:
			if isinstance(item, str):
				token = item.strip()
				key = token.lower()
				if token and key not in seen:
					seen.add(key)
					skills.append(token)

	years_raw = parsed.get("years_of_experience", 0)
	years = 0
	if isinstance(years_raw, (int, float)):
		years = int(years_raw)
	elif isinstance(years_raw, str):
		digits = re.findall(r"\d+", years_raw)
		if digits:
			years = int(digits[0])

	return {
		"candidate_name": candidate_name.strip(),
		"skills": skills,
		"years_of_experience": max(0, years),
	}


def profile_parser_node(state: GraphState) -> dict[str, Any]:
	"""LangGraph node for Agent 1 profile parsing.

	Args:
		state: Shared state that must include `file_path`.

	Returns:
		A partial state update containing resume text, structured profile data,
		and observability logs.
	"""
	logs = list(state.get("logs", []))
	file_path = state.get("file_path", "")
	if not file_path:
		return {
			"error": "Missing required `file_path` in graph state.",
			"logs": logs + ["[ProfileParser] file_path was missing."],
		}

	logs.append(f"[ProfileParser] Reading resume from: {file_path}")
	try:
		resume_text = resume_reader_tool(file_path)
	except Exception as error:  # pragma: no cover - defensive path
		LOGGER.exception("Profile parser failed while reading resume")
		logs.append(f"[ProfileParser] Tool error: {error}")
		return {"error": str(error), "logs": logs}

	logs.append("[ProfileParser] Resume text extracted successfully.")
	llm = ChatOllama(model=OLLAMA_MODEL)
	user_prompt = (
		"Extract candidate_name, skills, and years_of_experience from this resume text:\n\n"
		f"{resume_text}"
	)

	profile: ProfileData
	try:
		response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)])
		parsed = _extract_json_object(str(response.content))
		profile = _normalize_profile(parsed)
		logs.append(f"[ProfileParser] Parsed structured profile using {OLLAMA_MODEL}.")
	except Exception as error:  # pragma: no cover - defensive path
		logs.append(f"[ProfileParser] LLM unavailable/invalid output; fallback used: {error}")
		profile = _fallback_parse(resume_text)

	return {
		"resume_text": resume_text,
		"profile_data": profile,
		"logs": logs,
	}
