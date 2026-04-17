"""Agent 3: Tech Evaluator node implementation."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, NotRequired, TypedDict

from tools.question_tool import QuestionBankError, QuestionBankTool, QuestionRecord


LOGGER = logging.getLogger(__name__)


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

	try:
		all_records: list[QuestionRecord] = tool.load_question_bank()
		catalog: list[str] = [record["skill"] for record in all_records]
		required_skills: list[str] = _extract_required_skills(
			job_description=job_description,
			explicit_required=explicit_required,
			available_skill_catalog=catalog,
		)

		matched_skills: list[str] = [skill for skill in required_skills if skill in found_skills]
		missing_skills: list[str] = [skill for skill in required_skills if skill not in found_skills]

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
			f"Matched {len(matched_skills)} of {len(required_skills)} required skills. "
			f"Missing: {', '.join(missing_skills) if missing_skills else 'none'}. "
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
	except QuestionBankError as error:
		LOGGER.exception("Agent 3 failed while loading/fetching question bank")
		return {
			"skill_gaps": {
				"required_skills": [],
				"found_skills": found_skills,
				"matched_skills": [],
				"missing_skills": [],
			},
			"evaluation_questions": [],
			"evaluation_summary": "Evaluator failed to prepare technical questions.",
			"evaluation_errors": [str(error)],
		}

