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
│   ├── question_tool.py 
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
```

## 🚀 Setup & Installation Guide

Follow these steps to set up and run the project on your local machine.

---

### 1️⃣ Prerequisites

Ensure you have the following installed:

- **Python 3.9+** – Required to run the application.  
  🔗 https://www.python.org/downloads/

- **Ollama** – Essential for running the LLM locally.  
  🔗 https://ollama.com/

- **Git** – Required for cloning the repository.  
  🔗 https://git-scm.com/downloads

You can verify the installations using:

```bash
python --version
git --version
ollama --version

```
## 2️⃣ Prepare the LLM Engine

Open your terminal and pull the models required for the agents:

```bash
# Pull the primary model
ollama pull llama3:8b

# Optional: Pull a smaller model for faster testing on lower hardware
ollama pull phi3

```

## 3️⃣ Repository and Environment Setup

Clone the project and create a virtual environment to manage dependencies.

```bash
# Clone the repository
git clone <your-repository-url>
cd recruitment-swarm

# Create a virtual environment
python -m venv venv
```
🔹 Activate the Virtual Environment

```bash
# On Windows
venv\Scripts\activate
```
```bash
# On macOS/Linux
source venv/bin/activate
```
🔹 Install Required Packages

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 4️⃣ Configure Local Data

Ensure your local data files are in place so the agents can use their tools:

📄 Place sample resumes (PDF/DOCX) in:
```bash
/data/resume_samples/
```
📋 Ensure the following file contains a valid list of interview questions:
```bash
/data/tech_questions.json
```

## 5️⃣ Running the Swarm
Once the environment is ready and Ollama is serving the models, run the main orchestration script:
```bash
python main_graph.py
```

## 6️⃣ Running Tests

To verify that individual components and tools are working correctly:
```bash
# Run the full test suite
python -m pytest tests/
```
