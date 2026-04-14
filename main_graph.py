"""LangGraph orchestrator for local recruitment swarm (Agent 1 ready)."""

from __future__ import annotations

import argparse
import json
from typing import Any

from langgraph.graph import END, START, StateGraph

from agents.parser_agent import GraphState, profile_parser_node


def build_graph() -> Any:
	"""Build and compile a minimal graph with Profile Parser as first node."""
	graph: StateGraph[GraphState] = StateGraph(GraphState)
	graph.add_node("profile_parser", profile_parser_node)
	graph.add_edge(START, "profile_parser")
	graph.add_edge("profile_parser", END)
	return graph.compile()


def run_parser(file_path: str) -> GraphState:
	"""Run Agent 1 from a local resume path and return final graph state."""
	app = build_graph()
	initial_state: GraphState = {"file_path": file_path, "logs": []}
	return app.invoke(initial_state)


def main() -> None:
	"""CLI entrypoint for local Agent 1 execution."""
	parser = argparse.ArgumentParser(description="Run Agent 1 (Profile Parser) on a local PDF resume.")
	parser.add_argument("file_path", help="Path to a local PDF resume file.")
	args = parser.parse_args()

	result = run_parser(args.file_path)
	print(json.dumps(result, indent=2))


if __name__ == "__main__":
	main()
