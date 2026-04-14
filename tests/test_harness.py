from agents.market_agent import market_scout_agent
from agents.state import AgentState

class TestMarketScoutAgent(unittest.TestCase):
	def test_agent_with_skills(self):
		state: AgentState = {"found_skills": ["Python", "Go"], "logs": []}
		updated_state = market_scout_agent(state)
		self.assertIn("market_data", updated_state)
		self.assertIn("Python", updated_state["market_data"]["market_data"])
		self.assertEqual(updated_state["market_data"]["trends"]["Go"], "emerging")
		self.assertTrue(any("Market data fetched" in log for log in updated_state["logs"]))

	def test_agent_with_no_skills(self):
		state: AgentState = {"found_skills": [], "logs": []}
		updated_state = market_scout_agent(state)
		self.assertNotIn("market_data", updated_state)
		self.assertTrue(any("No skills found" in log for log in updated_state["logs"]))

	def test_agent_with_unknown_skill(self):
		state: AgentState = {"found_skills": ["UnknownSkill"], "logs": []}
		updated_state = market_scout_agent(state)
		self.assertEqual(updated_state["market_data"]["market_data"]["UnknownSkill"]["demand"], "unknown")
		self.assertEqual(updated_state["market_data"]["trends"]["UnknownSkill"], "unknown")
"""
Unit tests for SalaryBenchmarkTool (Agent 2: Market Scout)
"""

import unittest
from tools.market_tool import SalaryBenchmarkTool

class TestSalaryBenchmarkTool(unittest.TestCase):
	def test_known_skill(self):
		result = SalaryBenchmarkTool(["Python"])
		self.assertIn("Python", result)
		self.assertEqual(result["Python"]["demand"], "high")
		self.assertIsInstance(result["Python"]["salary_range"], list)

	def test_unknown_skill(self):
		result = SalaryBenchmarkTool(["Fortran"])
		self.assertIn("Fortran", result)
		self.assertEqual(result["Fortran"]["demand"], "unknown")
		self.assertIsNone(result["Fortran"]["salary_range"])

	def test_multiple_skills(self):
		result = SalaryBenchmarkTool(["Python", "Go", "Cobol", "UnknownSkill"])
		self.assertEqual(result["Python"]["demand"], "high")
		self.assertEqual(result["Go"]["demand"], "emerging")
		self.assertEqual(result["Cobol"]["demand"], "low")
		self.assertEqual(result["UnknownSkill"]["demand"], "unknown")

	def test_empty_input(self):
		result = SalaryBenchmarkTool([])
		self.assertEqual(result, {})

if __name__ == "__main__":
	unittest.main()
