"""
Agent 2: Market Scout
Scaffold for LangGraph node with state handling and logging.
"""


from typing import Dict, Any
from agents.state import AgentState
import logging
from tools.market_tool import SalaryBenchmarkTool

def market_scout_agent(state: AgentState) -> AgentState:
	"""
	Agent 2 (Market Scout): Consumes skills from Agent 1, fetches market data, and updates state.

	Args:
		state (AgentState): The shared state containing skills and other agent outputs.

	Returns:
		AgentState: Updated state with market data and logs.
	"""
	logging.info(f"[MarketScout] Received state: {state}")
	logs = state.get('logs', [])
	logs.append(f"[MarketScout] Input state: {state}")

	# Extract skills from state
	skills = state.get('found_skills') or []
	if not skills:
		logs.append("[MarketScout] No skills found in state. Skipping market analysis.")
		state['logs'] = logs
		return state

	# Fetch market data using SalaryBenchmarkTool
	try:
		market_data = SalaryBenchmarkTool(skills)
		logs.append(f"[MarketScout] Market data fetched for skills: {skills}")
	except Exception as e:
		logs.append(f"[MarketScout] Error fetching market data: {e}")
		market_data = {skill: {"salary_range": None, "average": None, "demand": "error"} for skill in skills}

	# Trend analysis: classify demand
	trends = {}
	for skill, data in market_data.items():
		demand = data.get("demand", "unknown")
		if demand == "high":
			trend = "high-demand"
		elif demand == "emerging":
			trend = "emerging"
		elif demand == "low":
			trend = "low-demand"
		else:
			trend = "unknown"
		trends[skill] = trend
		logs.append(f"[MarketScout] Skill '{skill}' classified as '{trend}' (demand: {demand})")

	# Structure output for Agent 3
	output = {
		"market_data": market_data,
		"trends": trends
	}
	state['market_data'] = output
	state['logs'] = logs
	logging.info(f"[MarketScout] Updated state: {state}")
	return state
