# Complete Windows Setup Guide

Here is the complete guide for a new user to run this project on Windows from scratch.

## 1. Prerequisites
- **Python 3.11+** installed.
- **Git** installed.

## 2. Install uv (Fast Python Package Installer)
Open **PowerShell** and run:

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Or via pip:
```bash
pip install uv
```

## 3. Clone the Repository
```powershell
git clone https://github.com/SaniyaNirmale/Infosys_springboard_Project.git
cd Infosys_springboard_Project
```

## 4. Configure Environment Variables
Create a `.env` file with your API keys (Groq, Tavily, OpenAI, etc.).

```powershell
copy .env.example .env
# Open .env and add your keys
```

## 5. Run the Project
The user has two options depending on what they want to do:

### Option A: Run the Backend Server (Recommended)
Use this command to run the LangGraph API server. This is the method currently used to run the project.

```powershell
uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev --host 0.0.0.0 --port 8000 --allow-blocking
```

**Note:** This will start the server at `http://localhost:8000`. Use the LangGraph Studio UI to interact with the agent.
