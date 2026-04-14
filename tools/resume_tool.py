"""Local resume-reading utilities for Agent 1 (Profile Parser)."""

from __future__ import annotations

from pathlib import Path

from PyPDF2 import PdfReader


def resume_reader_tool(file_path: str) -> str:
	"""Read a local PDF resume and return extracted text.

	Args:
		file_path: Absolute or relative path to a local PDF file.

	Returns:
		The concatenated plain text extracted from all PDF pages.

	Raises:
		FileNotFoundError: If the file does not exist.
		ValueError: If the file is not a PDF or contains no extractable text.
		OSError: If the file cannot be read due to an I/O issue.
	"""
	path = Path(file_path)
	if not path.exists():
		raise FileNotFoundError(f"Resume file was not found: {file_path}")

	if path.suffix.lower() != ".pdf":
		raise ValueError("resume_reader_tool currently supports PDF files only.")

	reader = PdfReader(str(path))
	page_texts: list[str] = []
	for page in reader.pages:
		page_texts.append(page.extract_text() or "")

	combined_text = "\n".join(page_texts).strip()
	if not combined_text:
		raise ValueError(f"No extractable text found in PDF: {file_path}")

	return combined_text
