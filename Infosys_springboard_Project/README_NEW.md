# Complete Windows Setup Guide

This guide will help you run the **Autonomous Learning Agent** project on Windows **without any errors**. Just follow these steps carefully.

---

## 1. Prerequisites

Before starting, make sure you have:
- **Python 3.11 or higher** installed ([Download here](https://www.python.org/downloads/))
- **Git** installed ([Download here](https://git-scm.com/downloads))

---

## 2. Install uv (Fast Python Package Installer)

Open **PowerShell** and run:

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Alternative:** If the above doesn't work, install via pip:
```bash
pip install uv
```

---

## 3. Clone the Repository

```powershell
git clone https://github.com/SaniyaNirmale/Infosys_springboard_Project.git
cd Infosys_springboard_Project
```

---

## 4. Configure Environment Variables

You need to create a `.env` file with your API keys. 

### Step 4.1: Copy the example file
```powershell
copy .env.example .env
```

### Step 4.2: Edit the `.env` file
Open the `.env` file in any text editor (Notepad, VS Code, etc.) and add your API keys:

```env
# Required for research agents with external search
TAVILY_API_KEY=your_tavily_api_key_here

# Required for Google Gemini models (primary model used)
GOOGLE_API_KEY=your_google_api_key_here

# Required for Groq models (used in research agent)
GROQ_API_KEY=your_groq_api_key_here

# Optional: For LangSmith evaluation and tracing
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=deep_research_from_scratch
```

**Where to get API keys:**
- **Tavily**: [https://tavily.com](https://tavily.com) (Sign up for free)
- **Google Gemini**: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- **Groq**: [https://console.groq.com/keys](https://console.groq.com/keys)
- **LangSmith** (Optional): [https://smith.langchain.com](https://smith.langchain.com)

---

## 5. Run the Project

Once you've set up the `.env` file, run this command to start the server:

```powershell
uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev --host 127.0.0.1 --port 8000 --allow-blocking
```

### What this command does:
- Installs all required dependencies automatically
- Starts the LangGraph API server
- Makes it accessible at `http://localhost:8000`

### Expected Output:
You should see output like:
```
Ready!
- API: http://localhost:8000
```

---

## 6. Access the Application

Once the server is running:
1. Open **LangGraph Studio** (download from [https://github.com/langchain-ai/langgraph-studio](https://github.com/langchain-ai/langgraph-studio))
2. Connect to `http://localhost:8000`
3. Start interacting with the autonomous learning agent!

---

## Troubleshooting

### Issue: "Python not found"
- Make sure Python 3.11+ is installed and added to your PATH
- Restart PowerShell after installing Python

### Issue: "uv not found"
- Close and reopen PowerShell after installing `uv`
- Or use the pip installation method: `pip install uv`

### Issue: "API key errors"
- Double-check that you've added your API keys to the `.env` file
- Make sure there are no extra spaces or quotes around the keys

---

## Notes
- All notebooks include automatic Windows compatibility fixes
- The `uvx` command handles all dependency installation automatically

**Need help?** Open an issue on GitHub: [https://github.com/SaniyaNirmale/Infosys_springboard_Project/issues](https://github.com/SaniyaNirmale/Infosys_springboard_Project/issues)
