"""
Unit tests for Agent 2 (Market Scout) and SalaryBenchmarkTool.

Tests cover:
- SalaryBenchmarkTool: known skills, unknown skills, empty input, case-insensitive matching.
- Market Scout Agent: full agent execution with skills, no skills, and unknown skills.
"""

import unittest
import json
import logging
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

from agents.state import AgentState
from tools.market_tool import salary_benchmark_tool

# Configure logging for test visibility
logging.basicConfig(level=logging.INFO)


# ═══════════════════════════════════════════════════════════════════════════════
# SalaryBenchmarkTool Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSalaryBenchmarkTool(unittest.TestCase):
    """Unit tests for the SalaryBenchmarkTool."""

    def test_known_skill(self) -> None:
        """Test that a known skill returns correct salary data and demand."""
        result: Dict[str, Any] = salary_benchmark_tool.invoke({"skills": ["Python"]})
        self.assertIn("Python", result)
        self.assertEqual(result["Python"]["demand"], "high")
        self.assertIsInstance(result["Python"]["salary_range"], list)
        self.assertEqual(len(result["Python"]["salary_range"]), 2)
        self.assertIsInstance(result["Python"]["average"], int)

    @patch("tools.market_tool.ChatOllama")
    def test_unknown_skill(self, mock_ollama_class: MagicMock) -> None:
        """Test that an unknown skill returns LLM estimated values."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content=json.dumps({
            "salary_range": [10000, 20000],
            "average": 15000,
            "demand": "emerging"
        }))
        mock_ollama_class.return_value = mock_llm

        result: Dict[str, Any] = salary_benchmark_tool.invoke({"skills": ["NonExistentSkill"]})
        self.assertIn("NonExistentSkill", result)
        self.assertEqual(result["NonExistentSkill"]["demand"], "emerging")
        self.assertEqual(result["NonExistentSkill"]["source"], "llm_estimated")

    @patch("tools.market_tool.ChatOllama")
    def test_multiple_skills(self, mock_ollama_class: MagicMock) -> None:
        """Test benchmarking multiple skills at once, covering all demand categories."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content=json.dumps({
            "salary_range": [10000, 20000],
            "average": 15000,
            "demand": "emerging"
        }))
        mock_ollama_class.return_value = mock_llm

        skills: List[str] = ["Python", "Go", "Cobol", "NonExistentSkill"]
        result: Dict[str, Any] = salary_benchmark_tool.invoke({"skills": skills})

        self.assertEqual(len(result), 4)
        self.assertEqual(result["Python"]["demand"], "high")
        self.assertEqual(result["Go"]["demand"], "emerging")
        self.assertEqual(result["Cobol"]["demand"], "low")
        self.assertEqual(result["NonExistentSkill"]["demand"], "emerging")

    def test_empty_input(self) -> None:
        """Test that empty skill list returns empty result."""
        result: Dict[str, Any] = salary_benchmark_tool.invoke({"skills": []})
        self.assertEqual(result, {})

    def test_salary_range_values(self) -> None:
        """Test that salary range min < max and average is within range."""
        result: Dict[str, Any] = salary_benchmark_tool.invoke({"skills": ["Python"]})
        salary_range = result["Python"]["salary_range"]
        average = result["Python"]["average"]

        self.assertLess(salary_range[0], salary_range[1])
        self.assertGreaterEqual(average, salary_range[0])
        self.assertLessEqual(average, salary_range[1])

    def test_case_insensitive_matching(self) -> None:
        """Test that skill lookup works regardless of case."""
        result: Dict[str, Any] = salary_benchmark_tool.invoke({"skills": ["python"]})
        self.assertIn("python", result)
        self.assertEqual(result["python"]["demand"], "high")


# ═══════════════════════════════════════════════════════════════════════════════
# Market Scout Agent Tests (with LLM mocked)
# ═══════════════════════════════════════════════════════════════════════════════

class TestMarketScoutAgent(unittest.TestCase):
    """Unit tests for the Market Scout agent node.

    LLM calls are mocked to avoid requiring a running Ollama instance
    during automated testing.
    """

    def _mock_llm_response(self) -> str:
        """Create a mock LLM response for testing.

        Returns:
            JSON string matching the expected LLM output format.
        """
        return json.dumps({
            "skill_analyses": [
                {"skill": "Python", "category": "high-demand",
                 "insight": "Python is widely used."},
                {"skill": "Go", "category": "emerging",
                 "insight": "Go is rising in popularity."}
            ],
            "top_skills": ["Python"],
            "market_summary": "Strong profile with Python expertise.",
            "recommended_salary_range": {"min": 80000, "max": 120000},
            "reasoning": "Python is high-demand, Go is emerging."
        })

    @patch("agents.market_agent.ChatOllama")
    def test_agent_with_skills(self, mock_ollama_class: MagicMock) -> None:
        """Test full agent execution with valid skills."""
        # Setup mock LLM
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content=self._mock_llm_response())
        mock_ollama_class.return_value = mock_llm

        from agents.market_agent import market_scout_agent

        state: AgentState = {"found_skills": ["Python", "Go"], "logs": []}
        updated_state: AgentState = market_scout_agent(state)

        # Verify market_data structure
        self.assertIn("market_data", updated_state)
        market_data = updated_state["market_data"]
        self.assertIn("benchmark_data", market_data)
        self.assertIn("trends", market_data)
        self.assertIn("llm_analysis", market_data)
        self.assertIn("skills_analyzed", market_data)

        # Verify benchmark data
        self.assertIn("Python", market_data["benchmark_data"])
        self.assertIn("Go", market_data["benchmark_data"])

        # Verify trends
        self.assertEqual(market_data["trends"]["Python"], "high-demand")
        self.assertEqual(market_data["trends"]["Go"], "emerging")

        # Verify LLM was called
        mock_llm.invoke.assert_called_once()

        # Verify logs
        self.assertTrue(any("MarketScout" in log for log in updated_state["logs"]))

    @patch("agents.market_agent.ChatOllama")
    def test_agent_with_no_skills(self, mock_ollama_class: MagicMock) -> None:
        """Test agent behavior when no skills are provided."""
        from agents.market_agent import market_scout_agent

        state: AgentState = {"found_skills": [], "logs": []}
        updated_state: AgentState = market_scout_agent(state)

        # Should still have market_data key but empty
        self.assertIn("market_data", updated_state)
        self.assertEqual(updated_state["market_data"]["benchmark_data"], {})
        self.assertEqual(updated_state["market_data"]["skills_analyzed"], [])
        self.assertTrue(any("No skills found" in log for log in updated_state["logs"]))

        # LLM should NOT have been called
        mock_ollama_class.assert_not_called()

    @patch("tools.market_tool.ChatOllama")
    @patch("agents.market_agent.ChatOllama")
    def test_agent_with_unknown_skill(self, mock_agent_ollama: MagicMock, mock_tool_ollama: MagicMock) -> None:
        """Test agent with a skill not in the benchmark dataset falls back to LLM estimation."""
        mock_tool_llm = MagicMock()
        mock_tool_llm.invoke.return_value = MagicMock(content=json.dumps({
            "salary_range": [50000, 60000],
            "average": 55000,
            "demand": "emerging"
        }))
        mock_tool_ollama.return_value = mock_tool_llm

        mock_agent_llm = MagicMock()
        mock_agent_llm.invoke.return_value = MagicMock(content=json.dumps({
            "skill_analyses": [
                {"skill": "UnknownSkill", "category": "emerging",
                 "insight": "LLM estimated dataset."}
            ],
            "top_skills": [],
            "market_summary": "Insufficient data.",
            "recommended_salary_range": {"min": 0, "max": 0},
            "reasoning": "Estimated."
        }))
        mock_agent_ollama.return_value = mock_agent_llm

        from agents.market_agent import market_scout_agent

        state: AgentState = {"found_skills": ["UnknownSkill"], "logs": []}
        updated_state: AgentState = market_scout_agent(state)

        benchmark = updated_state["market_data"]["benchmark_data"]
        self.assertEqual(benchmark["UnknownSkill"]["demand"], "emerging")
        self.assertEqual(updated_state["market_data"]["trends"]["UnknownSkill"], "emerging")

    @patch("agents.market_agent.ChatOllama")
    def test_agent_preserves_existing_state(self, mock_ollama_class: MagicMock) -> None:
        """Test that Agent 2 does not overwrite state fields from other agents."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content=self._mock_llm_response())
        mock_ollama_class.return_value = mock_llm

        from agents.market_agent import market_scout_agent

        state: AgentState = {
            "found_skills": ["Python"],
            "candidate_name": "Test Candidate",
            "structured_profile": {"name": "Test", "experience": 5},
            "logs": ["[Agent1] Previous log entry"],
        }
        updated_state: AgentState = market_scout_agent(state)

        # Verify other agent fields are preserved
        self.assertEqual(updated_state["candidate_name"], "Test Candidate")
        self.assertEqual(updated_state["structured_profile"]["name"], "Test")

        # Verify previous logs are preserved
        self.assertIn("[Agent1] Previous log entry", updated_state["logs"])

    @patch("agents.market_agent.ChatOllama")
    def test_agent_output_json_serializable(self, mock_ollama_class: MagicMock) -> None:
        """Test that the entire agent output is JSON-serializable for Agent 3."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content=self._mock_llm_response())
        mock_ollama_class.return_value = mock_llm

        from agents.market_agent import market_scout_agent

        state: AgentState = {"found_skills": ["Python", "Docker"], "logs": []}
        updated_state: AgentState = market_scout_agent(state)

        # This should not raise — output must be JSON serializable
        try:
            json.dumps(updated_state, default=str)
        except TypeError as e:
            self.fail(f"Agent output is not JSON serializable: {e}")


if __name__ == "__main__":
    unittest.main()
