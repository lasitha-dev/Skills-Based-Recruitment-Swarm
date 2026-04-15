📜 AI Coding Rules: Multi-Agent Recruitment Swarm (MARS)

1. Core Infrastructure Constraints

    Local Only: Never use openai, anthropic, or other paid API libraries. Use langchain_community.chat_models.ChatOllama exclusively.

    Orchestration: Use LangGraph for all agent interactions. Every agent must be a "node" in a state graph.

    State Management: Use a TypedDict named AgentState. Do NOT lose previous agent data; always return an update to the existing state, never overwrite it entirely.

2. Python Coding Standards (Grading-Critical)

To ensure a 90-100% "Excellent" grade on tools and agents:

    Strict Type Hinting: Every function signature must have type hints for all arguments and the return value.

        Good: def process_skills(skills: List[str]) -> Dict[str, int]:

    Descriptive Docstrings: Use Google or Sphinx style docstrings for every function, explaining Args, Returns, and Raises.

    Error Handling: Wrap all tool calls and LLM invocations in try-except blocks with meaningful logging.

3. Agent 2 (Market Scout) Specific Logic

Since I am responsible for Agent 2, the AI must prioritize these reasoning steps:

    Skill Intake: Read the found_skills or structured_profile from the shared state produced by Agent 1.

    Market Benchmarking: Use the SalaryBenchmarkTool to retrieve salary ranges, average compensation, and demand indicators for each detected skill.

    Trend Analysis: Identify which candidate skills are high-demand, emerging, or low-demand based on the dataset or API response.

    Sanitization: Ensure the output to the state is structured (JSON) so the next agent (Tech Evaluator) can parse it easily.

4. Observability & Logging

    Input/Output Tracing: Every time an agent receives state or a tool is called, print or log the specific payload.

    Reasoning Logs: Ensure the agent "thinks out loud" (Chain of Thought) before returning its final answer to help with the "Observability" requirement.

5. Testing Requirements

    Automated Validation: For every agent node, generate a corresponding test in the /tests folder.

    LLM-as-a-Judge: Create a test script that uses a separate Ollama call to evaluate if the agent's output is technically accurate and follows the persona.