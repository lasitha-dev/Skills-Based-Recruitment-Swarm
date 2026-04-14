"""
LLM-as-a-Judge script for Agent 2 (Market Scout) output validation.
Uses a local Ollama model to assess technical accuracy and persona adherence.
"""
import subprocess
import json

def run_ollama_judge(agent_output: dict, persona: str = "Market Scout") -> str:
    """
    Calls Ollama locally to judge the output of Agent 2.

    Args:
        agent_output (dict): The output from Agent 2 (market_scout_agent).
        persona (str): The expected agent persona.

    Returns:
        str: LLM's assessment of the output.
    """
    prompt = f"""
You are an expert evaluator. Judge the following output from an agent in a multi-agent recruitment system.

Persona: {persona}
Output (JSON):
{json.dumps(agent_output, indent=2)}

Criteria:
- Is the market data technically accurate and plausible?
- Is the output well-structured and parseable by downstream agents?
- Does the output and reasoning match the Market Scout persona (salary/demand focus, clear trend analysis)?
- Any errors or improvements?

Respond with a short assessment and a pass/fail verdict.
"""
    # Call Ollama locally (assumes 'ollama run' is available and a suitable model is installed)
    result = subprocess.run([
        "ollama", "run", "phi3", "--prompt", prompt
    ], capture_output=True, text=True)
    return result.stdout

if __name__ == "__main__":
    # Example usage: run after an integration test
    from agents.market_agent import market_scout_agent
    from agents.state import AgentState
    test_state: AgentState = {"found_skills": ["Python", "Go"], "logs": []}
    output = market_scout_agent(test_state)
    assessment = run_ollama_judge(output["market_data"])
    print("LLM-as-a-Judge Assessment:\n", assessment)
