"""Focused tests for Agent 3 QuestionBankTool behavior."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from agents.evaluator_agent import evaluate_candidate
from main_graph import tech_evaluator_agent
from tools.question_tool import QuestionBankError, QuestionBankTool


def _default_question_bank_path() -> Path:
	"""Builds the canonical local path to the seeded question bank."""
	return Path(__file__).resolve().parents[1] / "data" / "tech_questions.json"


def test_load_question_bank_success() -> None:
	"""Tool should load and validate seeded local records."""
	tool = QuestionBankTool(_default_question_bank_path())

	records = tool.load_question_bank()

	assert len(records) >= 10
	assert all("skill" in record for record in records)
	assert all("difficulty" in record for record in records)
	assert all("question" in record for record in records)


def test_filter_by_skill() -> None:
	"""Tool should return only requested skills."""
	tool = QuestionBankTool(_default_question_bank_path())

	records = tool.fetch_questions(skills=["python"], top_k=10)

	assert records
	assert all(record["skill"] == "python" for record in records)


def test_filter_by_skill_and_difficulty() -> None:
	"""Tool should honor both skill and difficulty filters."""
	tool = QuestionBankTool(_default_question_bank_path())

	records = tool.fetch_questions(skills=["aws"], difficulty="hard", top_k=10)

	assert records
	assert all(record["skill"] == "aws" for record in records)
	assert all(record["difficulty"] == "hard" for record in records)


def test_no_match_returns_empty() -> None:
	"""Unknown skills should produce no results instead of raising."""
	tool = QuestionBankTool(_default_question_bank_path())

	records = tool.fetch_questions(skills=["fortran"], top_k=10)

	assert records == []


def test_invalid_schema_raises_controlled_error(tmp_path: Path) -> None:
	"""Malformed question-bank records should raise a clear domain error."""
	malformed_path = tmp_path / "bad_questions.json"
	malformed_payload = [
		{
			"skill": "python",
			"difficulty": "medium"
		}
	]
	malformed_path.write_text(json.dumps(malformed_payload), encoding="utf-8")

	tool = QuestionBankTool(malformed_path)

	with pytest.raises(QuestionBankError, match="Invalid question record"):
		tool.load_question_bank()


def test_evaluator_generates_gap_report_and_questions() -> None:
	"""Evaluator should detect gaps and fetch targeted medium questions."""
	tool = QuestionBankTool(_default_question_bank_path())
	state = {
		"job_description": "Need strong Python, AWS and SQL experience for backend platform work.",
		"found_skills": ["Python"],
	}

	update = evaluate_candidate(state=state, question_tool=tool, top_k=5)

	assert "skill_gaps" in update
	assert "evaluation_questions" in update
	assert "evaluation_summary" in update
	assert "python" in update["skill_gaps"]["matched_skills"]
	assert "aws" in update["skill_gaps"]["missing_skills"]
	assert "sql" in update["skill_gaps"]["missing_skills"]
	assert len(update["evaluation_questions"]) > 0


def test_evaluator_returns_empty_questions_when_no_missing_skills() -> None:
	"""Evaluator should not fetch questions when candidate matches all required skills."""
	tool = QuestionBankTool(_default_question_bank_path())
	state = {
		"required_skills": ["python", "aws"],
		"found_skills": ["python", "aws"],
	}

	update = evaluate_candidate(state=state, question_tool=tool, top_k=5)

	assert update["skill_gaps"]["missing_skills"] == []
	assert update["evaluation_questions"] == []


def test_evaluator_returns_controlled_error_for_bad_question_bank(tmp_path: Path) -> None:
	"""Evaluator should return structured error output if question bank is invalid."""
	bad_path = tmp_path / "bad_questions.json"
	bad_path.write_text("{not-json}", encoding="utf-8")
	tool = QuestionBankTool(bad_path)
	state = {
		"required_skills": ["python"],
		"found_skills": [],
	}

	update = evaluate_candidate(state=state, question_tool=tool, top_k=5)

	assert update["evaluation_questions"] == []
	assert "evaluation_errors" in update
	assert len(update["evaluation_errors"]) == 1


def test_tech_evaluator_agent_preserves_upstream_state() -> None:
	"""Graph node should preserve upstream fields while appending evaluator outputs."""
	state = {
		"candidate_name": "Jane Doe",
		"job_description": "Need Python, AWS, and SQL experience.",
		"found_skills": ["python"],
		"market_data": {"skills_analyzed": ["Python"]},
		"logs": ["[MarketScout] done"],
	}

	updated = tech_evaluator_agent(state)

	# Upstream fields remain intact.
	assert updated["candidate_name"] == "Jane Doe"
	assert updated["market_data"]["skills_analyzed"] == ["Python"]
	assert "[MarketScout] done" in updated["logs"]

	# Agent 3 outputs are added.
	assert "evaluation_results" in updated
	assert "questions" in updated
	assert isinstance(updated["questions"], list)


def test_tech_evaluator_agent_handles_evaluation_exception() -> None:
	"""Graph node should return structured fallback output on evaluator failure."""
	state = {
		"job_description": "Need Python",
		"found_skills": ["python"],
		"logs": [],
	}

	with patch("main_graph.evaluate_candidate", side_effect=RuntimeError("boom")):
		updated = tech_evaluator_agent(state)

	assert "evaluation_results" in updated
	assert updated["questions"] == []
	assert updated["evaluation_results"]["evaluation_errors"] == ["boom"]

