"""Unified group testing harness for the LangGraph swarm."""

from __future__ import annotations

from main_graph import build_graph


def test_graph_wires_evaluator_node() -> None:
	"""The compiled graph should run end-to-end and include evaluator outputs."""
	app = build_graph()

	result = app.invoke(
		{
			"job_description": "Need strong Python, AWS and SQL experience for backend platform work.",
			"found_skills": ["Python"],
			"required_skills": ["python", "aws", "sql"],
		}
	)

	assert "skill_gaps" in result
	assert "evaluation_questions" in result
	assert "evaluation_summary" in result
	assert "aws" in result["skill_gaps"]["missing_skills"]
	assert "sql" in result["skill_gaps"]["missing_skills"]

