"""Agent 3: Tech Evaluator node implementation."""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, NotRequired, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from tools.question_tool import QuestionBankError, QuestionBankTool, QuestionRecord


LOGGER = logging.getLogger(__name__)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3")

EVALUATOR_SYSTEM_PROMPT = """
You are an expert technical lead. Your role is to identify the 'Skill Gaps' between a candidate's profile and a target Job Description. You must use the provided market data to weigh the importance of these gaps.

Your output must strictly be a valid JSON object with the following keys:
- required_skills: A list of strings representing the skills required by the job description.
- found_skills: A list of strings representing the skills found in the candidate's profile.
- matched_skills: A list of strings representing the skills that match between the required and found skills.
- missing_skills: A list of strings representing the skills required but missing from the candidate's profile, keeping only standard technology names.
- weighted_gap_summary: A concise string summarizing the most critical missing skills, heavily factored by the provided market data, emphasizing emerging and high-demand skills.

Constraints:
- Respond ONLY with valid JSON.
- Do not output any conversational text or markdown formatting outside the JSON block.
- Base your missing_skills solely on identifying the difference between the required_skills (derived primarily from the job description) and found_skills.
"""

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

class SkillGapReport(TypedDict):
	"""Structured evaluator output for skill-gap analysis."""

	required_skills: list[str]
	found_skills: list[str]
	matched_skills: list[str]
	missing_skills: list[str]


class EvaluatorState(TypedDict, total=False):
	"""Minimal state contract consumed/updated by Agent 3."""

	job_description: str
	found_skills: list[str]
	required_skills: list[str]
	market_data: dict[str, Any]
	skill_gaps: SkillGapReport
	evaluation_questions: list[QuestionRecord]
	evaluation_summary: str
	evaluation_errors: NotRequired[list[str]]


def _default_question_bank_path() -> Path:
	"""Returns the canonical local question-bank path."""
	return Path(__file__).resolve().parents[1] / "data" / "tech_questions.json"


def _dedupe_lower(values: list[str]) -> list[str]:
	"""Normalizes list values to lower-case unique tokens preserving order."""
	seen: set[str] = set()
	normalized: list[str] = []
	for value in values:
		token: str = value.strip().lower()
		if token and token not in seen:
			seen.add(token)
			normalized.append(token)
	return normalized


def _extract_required_skills(
	job_description: str,
	explicit_required: list[str],
	available_skill_catalog: list[str],
) -> list[str]:
	"""Builds the required-skill set from explicit state and JD keyword matching.

	Args:
		job_description: Raw job description text.
		explicit_required: Required skills provided directly in state.
		available_skill_catalog: Known skills available in question bank.

	Returns:
		A normalized list of required skills.
	"""
	required: list[str] = _dedupe_lower(explicit_required)
	jd_text: str = job_description.lower()

	for skill in _dedupe_lower(available_skill_catalog):
		pattern: str = r"\b" + re.escape(skill) + r"\b"
		if re.search(pattern, jd_text):
			required.append(skill)

	return _dedupe_lower(required)


def evaluate_candidate(
	state: EvaluatorState,
	question_tool: QuestionBankTool | None = None,
	top_k: int = 5,
) -> dict[str, Any]:
	"""Evaluates candidate skills and returns structured Agent 3 state updates.

	Args:
		state: Shared workflow state from previous nodes.
		question_tool: Optional injected tool (useful for testing).
		top_k: Maximum total number of technical questions to return.

	Returns:
		Partial state update containing `skill_gaps`, `evaluation_questions`, and
		`evaluation_summary`. The caller should merge this into the global state.
	"""
	LOGGER.info(
		"Agent 3 input payload",
		extra={
			"job_description_length": len(state.get("job_description", "")),
			"found_skills_count": len(state.get("found_skills", [])),
			"required_skills_count": len(state.get("required_skills", [])),
		},
	)

	tool: QuestionBankTool = question_tool or QuestionBankTool(_default_question_bank_path())

	found_skills: list[str] = _dedupe_lower(state.get("found_skills", []))
	explicit_required: list[str] = state.get("required_skills", [])
	job_description: str = state.get("job_description", "")
	market_data: dict[str, Any] = state.get("market_data", {})

	try:
		# Use LLM with market data to identify gaps and prioritize them
		llm = ChatOllama(model=OLLAMA_MODEL, temperature=0.1)

		prompt = (
			f"Job Description: {job_description}\n"
			f"Explicit Required Skills: {', '.join(explicit_required)}\n"
			f"Candidate Found Skills: {', '.join(found_skills)}\n"
			f"Market Data Insights:\n{json.dumps(market_data, indent=2)}\n\n"
			"Please output the valid JSON object with the required keys."
		)

		messages = [
			SystemMessage(content=EVALUATOR_SYSTEM_PROMPT),
			HumanMessage(content=prompt),
		]

		LOGGER.info("Agent 3 invoking LLM for gap analysis")
		response = llm.invoke(messages)
		
		# Parse JSON response
		llm_json = _extract_json_object(response.content)

		required_skills: list[str] = _dedupe_lower(llm_json.get("required_skills", []))
		matched_skills: list[str] = _dedupe_lower(llm_json.get("matched_skills", []))
		missing_skills: list[str] = _dedupe_lower(llm_json.get("missing_skills", []))
		llm_summary: str = llm_json.get("weighted_gap_summary", "No summary provided.")

		LOGGER.info(
			"Agent 3 reasoning",
			extra={
				"required_skills": required_skills,
				"matched_skills": matched_skills,
				"missing_skills": missing_skills,
			},
		)

		questions: list[QuestionRecord] = []
		if missing_skills:
			per_skill_quota: int = max(1, top_k // len(missing_skills))
			for missing_skill in missing_skills:
				questions.extend(
					tool.fetch_questions(
						skills=[missing_skill],
						difficulty="medium",
						top_k=per_skill_quota,
					)
				)

		questions = questions[:top_k]

		summary: str = (
			f"{llm_summary} "
			f"Prepared {len(questions)} targeted interview questions."
		)

		gap_report: SkillGapReport = {
			"required_skills": required_skills,
			"found_skills": found_skills,
			"matched_skills": matched_skills,
			"missing_skills": missing_skills,
		}

		return {
			"skill_gaps": gap_report,
			"evaluation_questions": questions,
			"evaluation_summary": summary,
		}
	except Exception as error:
		LOGGER.exception("Agent 3 failed during gap analysis or fetching questions")
		return {
			"skill_gaps": {
				"required_skills": [],
				"found_skills": found_skills,
				"matched_skills": [],
				"missing_skills": [],
			},
			"evaluation_questions": [],
			"evaluation_summary": "Evaluator failed unexpectedly.",
			"evaluation_errors": [str(error)],
		}

