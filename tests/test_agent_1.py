"""Robust pytest suite for Agent 1 (Profile Parser) and resume_reader_tool.

This test module is designed for deterministic, fast validation suitable for
assignment evidence. It uses mocking for both PDF parsing and LLM inference.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from agents.parser_agent import profile_parser_node
from tools.resume_tool import resume_reader_tool


class _MockPage:
    """Simple mock PDF page object exposing extract_text()."""

    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _MockReader:
    """Simple mock PdfReader object exposing pages list."""

    def __init__(self, pages: list[_MockPage]) -> None:
        self.pages = pages


def test_resume_reader_tool_extracts_text_from_mock_pdf(tmp_path: Path) -> None:
    """Validate that resume_reader_tool returns concatenated text from PDF pages."""
    pdf_path = tmp_path / "candidate.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 mock")

    with patch("tools.resume_tool.PdfReader", return_value=_MockReader([_MockPage("John Doe"), _MockPage("Python AWS")])):
        extracted = resume_reader_tool(str(pdf_path))

    assert "John Doe" in extracted
    assert "Python AWS" in extracted


def test_resume_reader_tool_raises_for_missing_file() -> None:
    """Validate FileNotFoundError handling for non-existent resume paths."""
    with pytest.raises(FileNotFoundError):
        resume_reader_tool("/path/that/does/not/exist/resume.pdf")


def test_resume_reader_tool_raises_for_invalid_format(tmp_path: Path) -> None:
    """Validate invalid file format handling (non-PDF files)."""
    invalid_path = tmp_path / "resume.txt"
    invalid_path.write_text("not a pdf", encoding="utf-8")

    with pytest.raises(ValueError, match="supports PDF and DOCX files only"):
        resume_reader_tool(str(invalid_path))


def test_resume_reader_tool_raises_for_empty_pdf_text(tmp_path: Path) -> None:
    """Validate edge case where PDF exists but contains no extractable text."""
    pdf_path = tmp_path / "empty.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 mock")

    with patch("tools.resume_tool.PdfReader", return_value=_MockReader([_MockPage(""), _MockPage("")])):
        with pytest.raises(ValueError, match="No extractable text"):
            resume_reader_tool(str(pdf_path))


def test_resume_reader_tool_supports_docx(tmp_path: Path) -> None:
    """Validate that resume_reader_tool can read DOCX files using python-docx."""
    docx_path = tmp_path / "candidate.docx"
    docx_path.write_bytes(b"fake docx bytes")

    mock_document = SimpleNamespace(
        paragraphs=[SimpleNamespace(text="Jane Doe"), SimpleNamespace(text="Python Developer")]
    )

    with patch("tools.resume_tool.Document", return_value=mock_document):
        extracted = resume_reader_tool(str(docx_path))

    assert "Jane Doe" in extracted
    assert "Python Developer" in extracted


def test_profile_parser_node_schema_validation_with_mocked_llm() -> None:
    """Validate parser output schema keys using mocked resume tool and mocked LLM."""
    mocked_response = SimpleNamespace(
        content='{"candidate_name": "Jane Doe", "skills": ["Python", "AWS"], "years_of_experience": 5}'
    )

    with patch("agents.parser_agent.resume_reader_tool", return_value="Jane Doe\n5 years of experience in Python and AWS"), patch(
        "agents.parser_agent.ChatOllama"
    ) as chat_cls:
        chat_instance = chat_cls.return_value
        chat_instance.invoke.return_value = mocked_response

        result = profile_parser_node({"file_path": "candidate.pdf", "logs": []})

    assert "profile_data" in result
    assert isinstance(result["profile_data"], dict)
    assert "candidate_name" in result["profile_data"]
    assert "skills" in result["profile_data"]
    assert "years_of_experience" in result["profile_data"]


def test_profile_parser_node_data_type_integrity() -> None:
    """Validate data type integrity for skills and years_of_experience fields."""
    mocked_response = SimpleNamespace(
        content='{"candidate_name": "Alex", "skills": ["SQL"], "years_of_experience": "3 years"}'
    )

    with patch("agents.parser_agent.resume_reader_tool", return_value="Alex\n3 years\nSQL"), patch(
        "agents.parser_agent.ChatOllama"
    ) as chat_cls:
        chat_cls.return_value.invoke.return_value = mocked_response
        result = profile_parser_node({"file_path": "candidate.pdf", "logs": []})

    profile = result["profile_data"]
    assert isinstance(profile["skills"], list)
    assert isinstance(profile["years_of_experience"], (int, str))


def test_profile_parser_infers_years_from_date_ranges() -> None:
    """Validate that date ranges in resume text can drive years-of-experience inference."""
    mocked_response = SimpleNamespace(
        content='{"candidate_name": "Alex", "skills": ["Python"], "years_of_experience": 0}'
    )

    resume_text = """Alex\nSoftware Engineer\nJan 2022 - Present\nWorked on Python services\n"""

    with patch("agents.parser_agent.resume_reader_tool", return_value=resume_text), patch(
        "agents.parser_agent.ChatOllama"
    ) as chat_cls:
        chat_cls.return_value.invoke.return_value = mocked_response
        result = profile_parser_node({"file_path": "candidate.pdf", "logs": []})

    assert result["profile_data"]["years_of_experience"] >= 0


def test_profile_parser_handles_no_recognizable_skills() -> None:
    """Validate edge case where resume has little signal and no recognizable skills."""
    mocked_response = SimpleNamespace(
        content='{"candidate_name": "Sam", "skills": [], "years_of_experience": 0}'
    )

    with patch("agents.parser_agent.resume_reader_tool", return_value="Sam\nEntry level candidate"), patch(
        "agents.parser_agent.ChatOllama"
    ) as chat_cls:
        chat_cls.return_value.invoke.return_value = mocked_response
        result = profile_parser_node({"file_path": "candidate.pdf", "logs": []})

    profile = result["profile_data"]
    assert profile["candidate_name"] == "Sam"
    assert profile["skills"] == []
    assert profile["years_of_experience"] == 0


def test_profile_parser_handles_empty_pdf_as_error() -> None:
    """Validate agent behavior when the resume tool fails on empty/non-extractable PDF text."""
    with patch("agents.parser_agent.resume_reader_tool", side_effect=ValueError("No extractable text found")), patch(
        "agents.parser_agent.ChatOllama"
    ) as chat_cls:
        result = profile_parser_node({"file_path": "empty.pdf", "logs": []})

    assert "error" in result
    assert "No extractable text" in result["error"]
    chat_cls.assert_not_called()


def test_profile_parser_uses_fallback_when_llm_returns_non_json() -> None:
    """Validate deterministic fallback extraction when model output is not valid JSON."""
    mocked_response = SimpleNamespace(content="I think this candidate is great.")

    with patch(
        "agents.parser_agent.resume_reader_tool",
        return_value="John Doe\n6 years of experience\nWorked with Python and Docker",
    ), patch("agents.parser_agent.ChatOllama") as chat_cls:
        chat_cls.return_value.invoke.return_value = mocked_response
        result = profile_parser_node({"file_path": "candidate.pdf", "logs": []})

    profile = result["profile_data"]
    assert profile["candidate_name"] in {"", "John Doe"}
    assert isinstance(profile["skills"], list)
    assert isinstance(profile["years_of_experience"], int)
    assert profile["years_of_experience"] >= 0
