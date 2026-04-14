"""
AgentState definition for shared state management between agents in MARS.
"""
from typing import List, Dict, Any, TypedDict, Optional

class AgentState(TypedDict, total=False):
    found_skills: List[str]  # Skills extracted by Agent 1
    market_data: Dict[str, Any]  # Market data and trends from Agent 2
    logs: List[str]  # Log entries for observability
    structured_profile: Optional[Dict[str, Any]]  # Optional: structured profile from Agent 1
    # Add more fields as needed for future agents
