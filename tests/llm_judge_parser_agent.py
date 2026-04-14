"""Simple LLM-as-a-Judge evaluation script for Agent 1 (Profile Parser)."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from main_graph import run_parser


JUDGE_SYSTEM_PROMPT = """
You are a strict evaluator for a resume parsing agent.
Assess only these criteria:
1) JSON format validity
2) Required fields exist: candidate_name (string), skills (array), years_of_experience (number)
3) Extracted content appears consistent with resume text

Respond as JSON with keys:
- verdict: PASS or FAIL
- score: integer from 0 to 100
- reasons: array of short strings
""".strip()


def _basic_schema_check(profile_data: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    if not isinstance(profile_data.get("candidate_name", ""), str):
        reasons.append("candidate_name is not a string")
    if not isinstance(profile_data.get("skills", []), list):
        reasons.append("skills is not a list")
    if not isinstance(profile_data.get("years_of_experience", 0), int):
        reasons.append("years_of_experience is not an integer")

    return (len(reasons) == 0, reasons)


def run_judge(file_path: str) -> int:
    """Execute parser + LLM judge flow and return process exit code."""
    result = run_parser(file_path)

    if "error" in result:
        print(json.dumps({"verdict": "FAIL", "score": 0, "reasons": [result["error"]]}, indent=2))
        return 1

    profile_data = result.get("profile_data", {})
    ok, schema_reasons = _basic_schema_check(profile_data)
    if not ok:
        print(json.dumps({"verdict": "FAIL", "score": 0, "reasons": schema_reasons}, indent=2))
        return 1

    judge_model = ChatOllama(model="llama3")
    judge_input = {
        "resume_text": result.get("resume_text", ""),
        "profile_data": profile_data,
    }

    judge_response = judge_model.invoke(
        [
            SystemMessage(content=JUDGE_SYSTEM_PROMPT),
            HumanMessage(content=json.dumps(judge_input, indent=2)),
        ]
    )

    print("Parser Output:")
    print(json.dumps(profile_data, indent=2))
    print("\nLLM Judge Assessment:")
    print(str(judge_response.content))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM-as-a-Judge for Agent 1 Profile Parser.")
    parser.add_argument("file_path", help="Path to local PDF resume file.")
    args = parser.parse_args()
    code = run_judge(args.file_path)
    sys.exit(code)


if __name__ == "__main__":
    main()
