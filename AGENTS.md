# AI Coding Rules: Multi-Agent Recruitment Swarm (MARS)

## 1. Core Infrastructure Constraints

- Local Only: Never use openai, anthropic, gemini, or other paid API libraries.
- Use `langchain_community.chat_models.ChatOllama` exclusively for any LLM interaction.
- Orchestration: Use LangGraph for agent interactions where required by the repository.
- Every agent must work with the shared project state and remain compatible with the existing graph design.
- State Management: Use the existing `TypedDict` named `AgentState` if already present in the repository.
- Do NOT lose previous agent data; always return only the state updates needed by Agent 4, without overwriting the entire state.

## 2. Python Coding Standards (Grading-Critical)

To ensure a high-quality submission:

- Strict Type Hinting: Every function signature must include type hints for all parameters and return values.
- Descriptive Docstrings: Use clear Google-style or Sphinx-style docstrings for every function, including Args, Returns, and Raises where relevant.
- Error Handling: Wrap risky operations such as file writing, tool usage, and optional LLM calls in try-except blocks with meaningful logging.
- Keep code beginner-friendly, readable, and modular.
- Do not add unnecessary complexity or abstractions.

## 3. Agent 4 (Recruitment Lead) Specific Logic

Since I am responsible for Agent 4, the AI must prioritize these responsibilities:

- Final Synthesis: Read the cumulative shared state produced by Agents 1, 2, and 3.
- Recommendation Logic: Generate a final hiring recommendation based only on the available evidence in the state.
- Do NOT invent missing information. If required information is missing, return `"Insufficient data"` with a short reason.
- Report Generation: Agent 4 must use `ReportGeneratorTool` from `tools/report_tool.py` to write the final summary into a formatted markdown or text report.
- Structured Output: Ensure the output written back to the state is structured and easy for integration.
- Recommendation labels must be exactly:
  - `Strong Hire`
  - `Proceed to Interview`
  - `Consider with Upskilling`
  - `Not Recommended`
  - `Insufficient data`

## 4. Observability & Logging

- Input/Output Tracing: Log the state fields received by Agent 4 and the final outputs it produces.
- Tool Logging: Log when the report tool is called and where the report is saved.
- Error Logging: Log exceptions clearly with enough detail for debugging.
- Do NOT generate hidden chain-of-thought or "think out loud" reasoning.
- Instead, provide only a short, concise recommendation reason suitable for debugging and review.

## 5. Testing Requirements

- Automated Validation: Create a corresponding pytest-based test file for Agent 4 in the `/tests` folder.
- Test Scenarios must include:
  - strong candidate
  - weak candidate
  - missing market data
  - insufficient data
  - successful report generation
- Tests must verify that Agent 4 returns structured output and does not crash on incomplete input.
- If an evaluation-style test is added, keep it local-only and compatible with Ollama.

## 6. Repository Safety Rules

- Do not modify unrelated agents.
- Do not modify unrelated tools.
- Do not change `README.md`.
- Do not rename folders or files unless explicitly required.
- Only work on Agent 4 related files such as:
  - `agents/lead_agent.py`
  - `tools/report_tool.py`
  - `tests/test_lead_agent.py`
  - optional sample input file if needed
- Keep all changes easy for the team leader to integrate into the main repository later.
