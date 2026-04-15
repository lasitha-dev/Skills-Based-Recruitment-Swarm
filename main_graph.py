"""
LangGraph orchestrator for the MARS (Multi-Agent Recruitment Swarm) system.

Uses LangGraph StateGraph to define the agent pipeline as a proper state machine.
Each agent is a node that reads from and writes to the shared AgentState.

Pipeline: START → Agent 1 (Profile Parser) → Agent 2 (Market Scout)
               → Agent 3 (Tech Evaluator) → Agent 4 (Recruitment Lead) → END
"""

import logging
import json
from typing import Dict, Any

from langgraph.graph import StateGraph, START, END

from agents.state import AgentState
from agents.parser_agent import profile_parser_agent, GraphState, profile_parser_node
from agents.market_agent import market_scout_agent

import sys

# Configure logging for the entire pipeline (stdout to avoid PowerShell stderr issues)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


# ── Stub nodes for agents not yet implemented by teammates ──────────────────


def tech_evaluator_stub(state: AgentState) -> AgentState:
    """Stub for Agent 3 (Tech Evaluator) — placeholder until teammate integrates.

    In the real system, this agent would generate technical interview questions
    based on the market data from Agent 2.

    Args:
        state: The shared AgentState.

    Returns:
        The state unchanged.
    """
    logs = list(state.get("logs", []))
    logs.append("[TechEvaluator] (STUB) Agent 3 placeholder — passing through.")
    logger.info("[TechEvaluator] (STUB) Passing through. Market data present: %s",
                "market_data" in state)
    return {**state, "logs": logs}


def recruitment_lead_stub(state: AgentState) -> AgentState:
    """Stub for Agent 4 (Recruitment Lead) — placeholder until teammate integrates.

    In the real system, this agent would compile the final recruitment report.

    Args:
        state: The shared AgentState.

    Returns:
        The state unchanged.
    """
    logs = list(state.get("logs", []))
    logs.append("[RecruitmentLead] (STUB) Agent 4 placeholder — passing through.")
    logger.info("[RecruitmentLead] (STUB) Passing through.")
    return {**state, "logs": logs}


# ── Build the LangGraph State Machine ──────────────────────────────────────

def build_mars_graph() -> StateGraph:
    """Build and compile the MARS agent pipeline as a LangGraph StateGraph.

    Creates a state machine with the following flow:
        START → profile_parser → market_scout → tech_evaluator → recruitment_lead → END

    Returns:
        A compiled LangGraph StateGraph ready to be invoked.
    """
    graph = StateGraph(AgentState)

    # Add agent nodes
    graph.add_node("profile_parser", profile_parser_agent)
    graph.add_node("market_scout", market_scout_agent)
    graph.add_node("tech_evaluator", tech_evaluator_stub)
    graph.add_node("recruitment_lead", recruitment_lead_stub)

    # Define the edges (sequential pipeline)
    graph.add_edge(START, "profile_parser")
    graph.add_edge("profile_parser", "market_scout")
    graph.add_edge("market_scout", "tech_evaluator")
    graph.add_edge("tech_evaluator", "recruitment_lead")
    graph.add_edge("recruitment_lead", END)

    logger.info("[MARS] State graph built: START -> profile_parser -> market_scout "
                "-> tech_evaluator -> recruitment_lead -> END")

    return graph.compile()


def run_parser(file_path: str) -> GraphState:
    """Run Agent 1 parser standalone for direct validation scripts.

    Args:
        file_path: Path to a local resume file.

    Returns:
        GraphState output produced by Agent 1 parser node.
    """
    parser_graph = StateGraph(GraphState)
    parser_graph.add_node("profile_parser", profile_parser_node)
    parser_graph.add_edge(START, "profile_parser")
    parser_graph.add_edge("profile_parser", END)
    app = parser_graph.compile()
    return app.invoke({"file_path": file_path, "logs": []})


def run_mars_pipeline(initial_state: AgentState) -> AgentState:
    """Run the full MARS pipeline with the given initial state.

    Builds the LangGraph state machine, invokes it with the initial state,
    and returns the final state after all agents have processed.

    Args:
        initial_state: The initial AgentState (typically containing found_skills
                       from a resume or test data).

    Returns:
        The final AgentState after all agents have run.

    Raises:
        Exception: If any agent node fails during execution.
    """
    logger.info("[MARS] ==================================================")
    logger.info("[MARS] Starting MARS pipeline...")
    logger.info("[MARS] Initial state: %s", json.dumps(
        {k: v for k, v in initial_state.items() if k != "logs"},
        indent=2, default=str
    ))

    compiled_graph = build_mars_graph()

    try:
        final_state: AgentState = compiled_graph.invoke(initial_state)
        logger.info("[MARS] Pipeline completed successfully.")
        logger.info("[MARS] Final state keys: %s", list(final_state.keys()))
        return final_state
    except Exception as e:
        logger.error("[MARS] Pipeline execution failed: %s", e)
        raise


if __name__ == "__main__":
    # Example: run pipeline with test data (or pre-populated skills if no resume path)
    test_state: AgentState = {
        "candidate_name": "John Doe",
        "found_skills": ["Python", "Docker", "Machine Learning", "React", "Cobol"],
        "logs": [],
    }

    print("\n" + "=" * 60)
    print("  MARS — Multi-Agent Recruitment Swarm")
    print("  Running pipeline with test candidate...")
    print("=" * 60 + "\n")
    sys.stdout.flush()

    final_state = run_mars_pipeline(test_state)

    print("\n" + "=" * 60)
    print("  PIPELINE RESULTS")
    print("=" * 60)
    sys.stdout.flush()

    # Print market data summary
    market_data = final_state.get("market_data", {})

    print("\n[TRENDS]")
    for skill, trend in market_data.get("trends", {}).items():
        print(f"  {skill}: {trend}")

    print("\n[BENCHMARK DATA]")
    for skill, data in market_data.get("benchmark_data", {}).items():
        if isinstance(data, dict):
            sr = data.get("salary_range", "N/A")
            avg = data.get("average", "N/A")
            demand = data.get("demand", "N/A")
            print(f"  {skill}: salary_range={sr}, average=${avg}, demand={demand}")
    sys.stdout.flush()

    # Print LLM analysis summary
    llm_analysis = market_data.get("llm_analysis", {})
    if llm_analysis:
        print("\n[LLM ANALYSIS SUMMARY]")
        print(f"  Market Summary: {llm_analysis.get('market_summary', 'N/A')}")
        print(f"  Top Skills: {llm_analysis.get('top_skills', [])}")
        rec = llm_analysis.get("recommended_salary_range", {})
        print(f"  Recommended Salary: ${rec.get('min', 0):,} - ${rec.get('max', 0):,}")
        print(f"\n  Chain-of-Thought Reasoning:")
        reasoning = llm_analysis.get("reasoning", "N/A")
        print(f"  {reasoning[:500]}{'...' if len(str(reasoning)) > 500 else ''}")
    sys.stdout.flush()

    # Print logs
    print("\n[AGENT LOGS]")
    for log_entry in final_state.get("logs", []):
        # Skip very long log entries (e.g. full LLM reasoning embedded in logs)
        display = log_entry if len(log_entry) < 200 else log_entry[:200] + "..."
        print(f"  {display}")
    sys.stdout.flush()
