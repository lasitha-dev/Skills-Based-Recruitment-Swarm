"""
LangGraph orchestrator for the MARS (Multi-Agent Recruitment Swarm) system.

Pipeline:
    START -> profile_parser -> market_scout -> tech_evaluator -> recruitment_lead -> END
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from langgraph.graph import END, START, StateGraph

from agents.evaluator_agent import evaluate_candidate
from agents.market_agent import market_scout_agent
from agents.parser_agent import GraphState, profile_parser_agent, profile_parser_node
from agents.state import AgentState

# Configure logging for the entire pipeline (stdout to avoid PowerShell stderr issues)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def tech_evaluator_agent(state: AgentState) -> AgentState:
    """Agent 3 (Tech Evaluator) integration node.

    Consumes upstream outputs from Agent 1/2 and writes evaluator outputs back
    into shared state without overwriting previous fields.
    """
    logs = list(state.get("logs", []))
    logs.append(f"[TechEvaluator] Agent invoked. State keys: {list(state.keys())}")

    evaluator_input: dict[str, Any] = {
        "job_description": state.get("job_description", ""),
        "found_skills": state.get("found_skills", []),
        "required_skills": state.get("required_skills", []),
    }

    logger.info("[TechEvaluator] Running gap analysis for %d skills.", len(evaluator_input["found_skills"]))

    try:
        evaluator_update = evaluate_candidate(evaluator_input)
    except Exception as error:
        logger.error("[TechEvaluator] Evaluation failed: %s", error)
        logs.append(f"[TechEvaluator] ERROR during evaluation: {error}")
        return {
            **state,
            "evaluation_results": {
                "skill_gaps": {
                    "required_skills": [],
                    "found_skills": evaluator_input["found_skills"],
                    "matched_skills": [],
                    "missing_skills": [],
                },
                "evaluation_summary": "Evaluator failed unexpectedly.",
                "evaluation_errors": [str(error)],
            },
            "questions": [],
            "logs": logs,
        }

    evaluation_results = {
        "skill_gaps": evaluator_update.get("skill_gaps", {}),
        "evaluation_summary": evaluator_update.get("evaluation_summary", ""),
        "evaluation_errors": evaluator_update.get("evaluation_errors", []),
    }
    questions = evaluator_update.get("evaluation_questions", [])

    logs.append(
        "[TechEvaluator] Completed. Missing skills: "
        f"{evaluation_results.get('skill_gaps', {}).get('missing_skills', [])}. "
        f"Questions generated: {len(questions)}"
    )

    return {
        **state,
        "evaluation_results": evaluation_results,
        "questions": questions,
        "logs": logs,
    }


def recruitment_lead_stub(state: AgentState) -> AgentState:
    """Stub for Agent 4 (Recruitment Lead)."""
    logs = list(state.get("logs", []))
    logs.append("[RecruitmentLead] (STUB) Agent 4 placeholder - passing through.")
    logger.info("[RecruitmentLead] (STUB) Passing through.")
    return {**state, "logs": logs}


def build_mars_graph() -> Any:
    """Build and compile the MARS state graph."""
    graph = StateGraph(AgentState)

    graph.add_node("profile_parser", profile_parser_agent)
    graph.add_node("market_scout", market_scout_agent)
    graph.add_node("tech_evaluator", tech_evaluator_agent)
    graph.add_node("recruitment_lead", recruitment_lead_stub)

    graph.add_edge(START, "profile_parser")
    graph.add_edge("profile_parser", "market_scout")
    graph.add_edge("market_scout", "tech_evaluator")
    graph.add_edge("tech_evaluator", "recruitment_lead")
    graph.add_edge("recruitment_lead", END)

    logger.info(
        "[MARS] State graph built: START -> profile_parser -> market_scout "
        "-> tech_evaluator -> recruitment_lead -> END"
    )

    return graph.compile()


def build_graph() -> Any:
    """Compatibility wrapper for callers expecting build_graph()."""
    return build_mars_graph()


def run_parser(file_path: str) -> GraphState:
    """Run Agent 1 parser standalone for direct validation scripts."""
    parser_graph = StateGraph(GraphState)
    parser_graph.add_node("profile_parser", profile_parser_node)
    parser_graph.add_edge(START, "profile_parser")
    parser_graph.add_edge("profile_parser", END)
    app = parser_graph.compile()
    return app.invoke({"file_path": file_path, "logs": []})


def run_mars_pipeline(initial_state: AgentState) -> AgentState:
    """Run the full MARS pipeline with the given initial state."""
    logger.info("[MARS] ==================================================")
    logger.info("[MARS] Starting MARS pipeline...")
    logger.info(
        "[MARS] Initial state: %s",
        json.dumps({k: v for k, v in initial_state.items() if k != "logs"}, indent=2, default=str),
    )

    compiled_graph = build_mars_graph()
    final_state: AgentState = compiled_graph.invoke(initial_state)

    logger.info("[MARS] Pipeline completed successfully.")
    logger.info("[MARS] Final state keys: %s", list(final_state.keys()))
    return final_state


if __name__ == "__main__":
    test_state: AgentState = {
        "candidate_name": "John Doe",
        "job_description": "Need Python, AWS, SQL, and Docker for backend platform work.",
        "found_skills": ["Python", "Docker", "React"],
        "logs": [],
    }

    final_state = run_mars_pipeline(test_state)
    print(json.dumps(final_state, indent=2, default=str))
