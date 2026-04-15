"""LangGraph orchestrator for the recruitment swarm."""

from __future__ import annotations

import argparse
import json
import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from agents.evaluator_agent import EvaluatorState, evaluate_candidate


LOGGER = logging.getLogger(__name__)


class AgentState(EvaluatorState, total=False):
	"""Shared state passed between the swarm nodes.

	The state is intentionally cumulative so each agent can append to the same
	payload without erasing prior work.
	"""

	resume_path: str
	parsed_resume: dict[str, Any]
	salary_data: dict[str, Any]
	report_path: str


def parser_node(state: AgentState) -> dict[str, Any]:
	"""Pass-through placeholder for Agent 1 until the parser is implemented."""
	LOGGER.info("Parser node received state", extra={"keys": list(state.keys())})
	return {}


def market_node(state: AgentState) -> dict[str, Any]:
	"""Pass-through placeholder for Agent 2 until the market scout is implemented."""
	LOGGER.info("Market node received state", extra={"keys": list(state.keys())})
	return {}


def evaluator_node(state: AgentState) -> dict[str, Any]:
	"""Runs Agent 3 gap analysis and question selection."""
	LOGGER.info("Evaluator node received state", extra={"keys": list(state.keys())})
	return evaluate_candidate(state)


def lead_node(state: AgentState) -> dict[str, Any]:
	"""Pass-through placeholder for Agent 4 until the report generator is implemented."""
	LOGGER.info("Lead node received state", extra={"keys": list(state.keys())})
	return {}


def build_graph() -> Any:
	"""Builds the LangGraph workflow for the recruitment swarm.

	Returns:
		A compiled LangGraph application ready to invoke with an AgentState.
	"""
	graph: StateGraph[AgentState] = StateGraph(AgentState)
	graph.add_node("parser", parser_node)
	graph.add_node("market", market_node)
	graph.add_node("evaluator", evaluator_node)
	graph.add_node("lead", lead_node)

	graph.add_edge(START, "parser")
	graph.add_edge("parser", "market")
	graph.add_edge("market", "evaluator")
	graph.add_edge("evaluator", "lead")
	graph.add_edge("lead", END)

	return graph.compile()


def main() -> None:
	"""Runs the orchestrator or an interactive CLI demo."""
	parser = argparse.ArgumentParser(description="Run the recruitment swarm graph")
	parser.add_argument(
		"--interactive",
		action="store_true",
		help="Prompt for job description and skills in the terminal.",
	)
	arguments = parser.parse_args()

	app = build_graph()
	if arguments.interactive:
		job_description: str = input("Job description: ").strip()
		found_skills_input: str = input("Found skills (comma-separated): ").strip()
		required_skills_input: str = input("Required skills (comma-separated, optional): ").strip()
		sample_state: AgentState = {
			"job_description": job_description,
			"found_skills": [
				skill.strip()
				for skill in found_skills_input.split(",")
				if skill.strip()
			],
		}
		if required_skills_input:
			sample_state["required_skills"] = [
				skill.strip()
				for skill in required_skills_input.split(",")
				if skill.strip()
			]
	else:
		sample_state = {
			"job_description": "Need strong Python, AWS and SQL experience for backend platform work.",
			"found_skills": ["Python"],
			"required_skills": ["python", "aws", "sql"],
		}

	result: dict[str, Any] = app.invoke(sample_state)
	LOGGER.info("Graph run completed", extra={"keys": list(result.keys())})
	print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
	main()
