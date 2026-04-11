"""Focused tests for Agent 3 QuestionBankTool behavior."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

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

