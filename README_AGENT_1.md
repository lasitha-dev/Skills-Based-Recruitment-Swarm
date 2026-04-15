# Agent 1 Run Guide (Profile Parser)

This guide explains how to run Agent 1 locally and view the output in the terminal.

You can use separate terminals for Ollama and the agent, but every terminal that runs the Python code must either:

1. activate the same virtual environment with `source .venv/bin/activate`, or
2. call the venv interpreter directly with `.venv/bin/python3`.

## Quick Run (same commands that worked)

Use this exact sequence if you want the shortest reliable path:

```bash
cd /Users/pramodwijenayake/Desktop/Skills-Based-Recruitment-Swarm
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 main_graph.py "/Users/pramodwijenayake/Desktop/CV/PRAMOD WIJENAYAKE V1.6.pdf"
```

If the parser runs successfully, it prints JSON to the terminal.

## 1. Go to the project folder

```bash
cd /Users/pramodwijenayake/Desktop/Skills-Based-Recruitment-Swarm
```

## 2. Create and activate virtual environment (first time only)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Note: In new terminal tabs/windows, activate `.venv` again before running commands.

## 4. Ensure Ollama is running and model is available

Start Ollama service:

```bash
ollama serve
```

If terminal says address already in use, Ollama is already running.

This terminal can stay separate from your Python terminal.

Check installed models:

```bash
ollama list
```

If `llama3:8b` is missing:

```bash
ollama pull llama3:8b
```

Optional (force model selection):

```bash
export OLLAMA_MODEL=llama3:8b
```

## 5. Run Agent 1 with a local resume (PDF or DOCX)

```bash
python3 main_graph.py "/Users/pramodwijenayake/Desktop/CV/PRAMOD WIJENAYAKE V1.6.pdf"
```

DOCX example:

```bash
python3 main_graph.py "/Users/pramodwijenayake/Desktop/CV/v6doc.docx"
```

Important: Use `python3` (not `python`) on this Mac.

If you prefer not to activate the venv, use this exact command instead:

```bash
.venv/bin/python3 main_graph.py "/Users/pramodwijenayake/Desktop/CV/PRAMOD WIJENAYAKE V1.6.pdf"
```

DOCX variant with direct venv interpreter:

```bash
.venv/bin/python3 main_graph.py "/Users/pramodwijenayake/Desktop/CV/v6doc.docx"
```

## 6. Expected terminal output

You will get JSON with these fields:

- `file_path`
- `resume_text`
- `profile_data`
  - `candidate_name`
  - `skills` (list)
  - `years_of_experience`
- `logs`

Supported input formats:

- `.pdf`
- `.docx`

## 7. Run LLM-as-a-Judge validation

```bash
PYTHONPATH=. python3 tests/llm_judge_parser_agent.py "/Users/pramodwijenayake/Desktop/CV/PRAMOD WIJENAYAKE V1.6.pdf"
```

DOCX example:

```bash
PYTHONPATH=. python3 tests/llm_judge_parser_agent.py "/Users/pramodwijenayake/Desktop/CV/v6doc.docx"
```

If you run this in a fresh terminal, activate the venv first:

```bash
source .venv/bin/activate
```

Or use the venv interpreter directly:

```bash
PYTHONPATH=. .venv/bin/python3 tests/llm_judge_parser_agent.py "/Users/pramodwijenayake/Desktop/CV/PRAMOD WIJENAYAKE V1.6.pdf"
```

DOCX variant with direct venv interpreter:

```bash
PYTHONPATH=. .venv/bin/python3 tests/llm_judge_parser_agent.py "/Users/pramodwijenayake/Desktop/CV/v6doc.docx"
```

The script prints:

- Parser output JSON
- LLM judge verdict (`PASS` or `FAIL`), score, and reasons

## 8. Run deterministic pytest suite for Agent 1

```bash
python3 -m pytest tests/test_agent_1.py
```

## Troubleshooting

- `zsh: command not found: python`:
  - Use `python3` in all commands.

- `ModuleNotFoundError: No module named langgraph`:
  - Activate venv and install dependencies in that same shell:
  - `source .venv/bin/activate`
  - `python3 -m pip install -r requirements.txt`

- `ModuleNotFoundError: No module named main_graph`:
  - Run judge command with `PYTHONPATH=.` exactly as shown above.

- `Connection refused` or Ollama errors:
  - Start service with `ollama serve`.
  - Confirm model with `ollama list`.

- `No extractable text found in PDF`:
  - Use a text-based PDF (not scanned image PDF), or OCR it first.

- `No extractable text found in DOCX`:
  - Ensure the DOCX has real paragraph text (not image-only content).

- `externally-managed-environment` during pip install:
  - Use virtual environment and install inside `.venv`.
