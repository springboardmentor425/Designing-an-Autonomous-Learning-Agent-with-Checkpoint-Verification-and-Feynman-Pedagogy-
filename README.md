# 🧠 Deep Research From Scratch

A modular multi-agent research system built with **LangGraph**.

> Workflow: **Scope → Research → Write**

This project demonstrates structured research using agent orchestration, external tools, and multi-agent coordination.

---

## 🚀 Quick Start

### 🐳 Option 1: Docker (Recommended)

**Prerequisites**
- Docker
- Docker Compose

```bash
git clone https://github.com/springboardmentor425/Designing-an-Autonomous-Learning-Agent-with-Checkpoint-Verification-and-Feynman-Pedagogy---Group-2.git
cd deep_research_from_scratch
cp .env.example .env
```

Add API keys inside `.env`:

```env
TAVILY_API_KEY=your_key
GOOGLE_API_KEY=your_key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=deep_research_from_scratch
```

Run:

```bash
docker-compose build
docker-compose up -d
```

Access:
- Studio: https://smith.langchain.com/studio/?baseUrl=http://localhost:8000
- API Docs: http://localhost:8000/docs

Stop:
```bash
docker-compose down
```

---

### 💻 Option 2: Local Setup

**Requirements**
- Python 3.11+
- Node.js
- `uv` package manager

```bash
git clone https://github.com/langchain-ai/deep_research_from_scratch
cd deep_research_from_scratch
uv sync
touch .env
```

Add API keys to `.env`.

Run server:

```bash
uvx --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev --allow-blocking
```

Run notebooks:

```bash
uv run jupyter notebook
```

---

## 🏗 Architecture

The system follows a 3-phase pipeline:

1. **Scope** – Clarify and structure the research request  
2. **Research** – Iterative tool-based research  
3. **Write** – Generate final synthesized report  

---

## 📚 Tutorials

| Notebook | Purpose |
|----------|----------|
| `1_scoping.ipynb` | User clarification & brief generation |
| `2_research_agent.ipynb` | Tool-based research agent |
| `3_research_agent_mcp.ipynb` | MCP tool integration |
| `4_research_supervisor.ipynb` | Multi-agent coordination |
| `5_full_agent.ipynb` | Complete end-to-end system |

---

## 🎯 Key Concepts

- Structured outputs (Pydantic)
- ReAct & Supervisor agent patterns
- Async multi-agent orchestration
- MCP integration
- Complex state management in LangGraph

---

## 🧩 Tech Stack

- LangGraph
- LangChain
- Python 3.11
- Docker
- Tavily API
- MCP (Model Context Protocol)
- Google Gemini

---

## 📌 Outcome

A production-ready deep research system capable of handling complex, multi-layered research queries with intelligent scoping and coordinated execution.
