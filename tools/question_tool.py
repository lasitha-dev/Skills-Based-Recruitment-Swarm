"""Question bank loading and retrieval utilities for Agent 3."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Literal, Sequence, TypedDict


LOGGER = logging.getLogger(__name__)


Difficulty = Literal["easy", "medium", "hard"]


class QuestionRecord(TypedDict):
	"""Schema for a single technical question-bank entry."""

	skill: str
	difficulty: Difficulty
	question: str
	tags: list[str]


class QuestionBankError(Exception):
	"""Raised when the question bank cannot be loaded or queried."""


class QuestionBankTool:
	"""Provides deterministic question retrieval for skill-gap evaluation.

	The tool reads a local JSON question bank and filters records by skill and
	optional difficulty. It never generates questions itself.

	Args:
		question_bank_path: Path to the local JSON file.
	"""

	def __init__(self, question_bank_path: str | Path) -> None:
		self.question_bank_path: Path = Path(question_bank_path)

	def load_question_bank(self) -> list[QuestionRecord]:
		"""Loads and validates the local question bank.

		Returns:
			A validated list of question records.

		Raises:
			QuestionBankError: If file read, JSON parse, or schema validation fails.
		"""
		LOGGER.info("Loading question bank", extra={"path": str(self.question_bank_path)})

		try:
			raw_text: str = self.question_bank_path.read_text(encoding="utf-8")
		except OSError as error:
			raise QuestionBankError(
				f"Failed to read question bank file: {self.question_bank_path}"
			) from error

		try:
			payload: object = json.loads(raw_text)
		except json.JSONDecodeError as error:
			raise QuestionBankError(
				f"Invalid JSON in question bank file: {self.question_bank_path}"
			) from error

		if not isinstance(payload, list):
			raise QuestionBankError("Question bank JSON root must be a list of records.")

		validated_records: list[QuestionRecord] = []
		for index, raw_record in enumerate(payload):
			validated_records.append(self._validate_record(raw_record, index))

		LOGGER.info("Question bank loaded", extra={"count": len(validated_records)})
		return validated_records

	def fetch_questions(
		self,
		skills: Sequence[str],
		difficulty: Difficulty | None = None,
		top_k: int = 5,
	) -> list[QuestionRecord]:
		"""Fetches deterministic question matches for the requested skills.

		Args:
			skills: Candidate gap skills to query.
			difficulty: Optional difficulty filter (easy, medium, hard).
			top_k: Maximum number of records to return.

		Returns:
			A list of filtered and sorted question records.

		Raises:
			QuestionBankError: If input validation fails or load fails.
		"""
		if top_k <= 0:
			raise QuestionBankError("top_k must be a positive integer.")

		normalized_skills: set[str] = {
			skill.strip().lower() for skill in skills if skill and skill.strip()
		}
		if not normalized_skills:
			return []

		if difficulty is not None and difficulty not in {"easy", "medium", "hard"}:
			raise QuestionBankError("difficulty must be one of: easy, medium, hard.")

		records: list[QuestionRecord] = self.load_question_bank()
		filtered: list[QuestionRecord] = []

		for record in records:
			skill_match: bool = record["skill"].strip().lower() in normalized_skills
			difficulty_match: bool = difficulty is None or record["difficulty"] == difficulty
			if skill_match and difficulty_match:
				filtered.append(record)

		filtered.sort(key=lambda item: (item["skill"], item["difficulty"], item["question"]))
		return filtered[:top_k]

	def _validate_record(self, raw_record: object, index: int) -> QuestionRecord:
		"""Validates and normalizes one record from the JSON payload.

		Args:
			raw_record: Raw JSON object.
			index: Record index for error reporting.

		Returns:
			A validated record with normalized values.

		Raises:
			QuestionBankError: If the record does not match the expected schema.
		"""
		if not isinstance(raw_record, dict):
			raise QuestionBankError(
				f"Invalid question record at index {index}: expected an object."
			)

		skill: object = raw_record.get("skill")
		difficulty: object = raw_record.get("difficulty")
		question: object = raw_record.get("question")
		tags: object = raw_record.get("tags", [])

		if not isinstance(skill, str) or not skill.strip():
			raise QuestionBankError(
				f"Invalid question record at index {index}: 'skill' must be a non-empty string."
			)
		if difficulty not in {"easy", "medium", "hard"}:
			raise QuestionBankError(
				f"Invalid question record at index {index}: 'difficulty' must be easy, medium, or hard."
			)
		if not isinstance(question, str) or not question.strip():
			raise QuestionBankError(
				f"Invalid question record at index {index}: 'question' must be a non-empty string."
			)
		if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
			raise QuestionBankError(
				f"Invalid question record at index {index}: 'tags' must be a list of strings."
			)

		normalized_record: QuestionRecord = {
			"skill": skill.strip().lower(),
			"difficulty": difficulty,
			"question": question.strip(),
			"tags": [tag.strip().lower() for tag in tags if tag.strip()],
		}
		return normalized_record

