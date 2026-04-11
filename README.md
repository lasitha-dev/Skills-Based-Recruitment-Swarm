# SE4010-CTSE Assignment 2: Multi-Agent Recruitment Swarm

## Project Overview
This project is a locally-hosted Multi-Agent System (MAS) developed for the **Sri Lanka Institute of Information Technology (SLIIT)**. The objective is to design, build, and deploy an autonomous "swarm" of agents that automates the multi-step recruitment and technical evaluation process. 

The system operates under strict **Zero-Cost and Local** constraints:
***LLM Engine**: Local Small Language Models (SLMs) via **Ollama**.
* **Orchestrator**: **LangGraph** for state management and routing.
* **Privacy**: No data is sent to the cloud; paid API keys are strictly prohibited.

---


## Team Members & Responsibilities
Each team member is responsible for a distinct agent, a custom Python tool, and an automated testing harness.

| Student Name | Agent Component | Custom Tool |
| :--- | :--- | :--- |
| **W.M.P.J. Wijenayake** | Agent 1: Profile Parser | `ResumeReaderTool` |
| **S.S Kumarasinghe** | Agent 2: Market Scout | `SalaryBenchmarkTool` |
| **A.L.M. Athulathmudali**  | **Agent 3: Tech Evaluator** | **`QuestionBankTool`** |
| **G.A. Sandaru** | Agent 4: Recruitment Lead | `ReportGeneratorTool` |

---

## File Structure
This repository is organized to ensure individual contribution proof and modular interaction.

```text
/recruitment-swarm
├── /agents               # Individual Agent Personas and System Prompts 
│   ├── parser_agent.py   # Student 1
│   ├── market_agent.py   # Student 2
│   ├── evaluator_agent.py# Student 3 
│   └── lead_agent.py     # Student 4
├── /tools                # Custom Python Tools with type hinting 
│   ├── resume_tool.py
│   ├── market_tool.py
│   ├── question_tool.py  # Evaluator tool for local question bank
│   └── report_tool.py
├── /data                 # Local data storage for zero-cost operation
│   ├── resume_samples/   # Local PDFs for ingestion
│   └── tech_questions.json # Local technical question bank
├── /tests                # Automated evaluation scripts 
│   ├── test_evaluator.py # LLM-as-a-Judge for Agent 3
│   └── test_harness.py   # Unified group testing script
├── main_graph.py         # LangGraph Orchestrator and State definitions 
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
