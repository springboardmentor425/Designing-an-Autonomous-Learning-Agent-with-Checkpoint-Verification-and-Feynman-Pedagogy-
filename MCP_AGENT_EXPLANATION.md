# Research Agent MCP - Explanation and Issues

## Summary

The **research_agent_mcp** is working as designed - it's **NOT broken**. However, it may not be doing what you expect.

## What is research_agent_mcp?

The `research_agent_mcp` is a **file-based research agent** that demonstrates how to use the **Model Context Protocol (MCP)** to access local files. It's designed to:

1. ✅ Read files from the `src/deep_research_from_scratch/files/` directory
2. ✅ Use MCP filesystem server to access local documents
3. ✅ Summarize and compress information from existing files
4. ❌ **NOT** do web searches
5. ❌ **NOT** save new reports (it only compresses research)

## The "Flip Flop" Issue Explained

When you asked the MCP agent about "flip flop", here's what happened:

1. The MCP agent looked in the `files/` directory
2. It found these existing reports:
   - `report_58ef21dc-4572-4543-b123-695aeb86eb03.md` (about Virtual Assistants)
   - `report_e787e240-38f6-42dc-9e57-b70c8336d8a2.md` (about Coffee Shops)
   - `coffee_shops_sf.md`
3. Since it's designed to work with **local files only**, it read these files and summarized them
4. It gave you a summary of those reports instead of doing new web research about flip flops

## Why This Happens

The MCP agent uses this prompt (from `prompts.py` line 202):

```
You are a research assistant conducting research on the user's input topic using local files.
Your job is to use file system tools to gather information from local research files.
```

It has access to:
- `list_allowed_directories` - See what directories you can access
- `list_directory` - List files in directories
- `read_file` - Read individual files
- `read_multiple_files` - Read multiple files at once
- `search_files` - Find files containing specific content

**It does NOT have access to web search tools like Tavily.**

## Which Agent Should You Use?

### For Web Research + Saving Reports: Use `research_agent_full`
- ✅ Does web searches using Tavily
- ✅ Saves reports to `files/` directory
- ✅ Complete workflow: clarify → research → write → save
- ✅ Best for new research topics

### For Local File Research: Use `research_agent_mcp`
- ✅ Reads existing files in `files/` directory
- ✅ Demonstrates MCP integration
- ✅ Good for analyzing existing documents
- ❌ Does NOT do web searches
- ❌ Does NOT save new reports

### For Simple Web Research: Use `research_agent`
- ✅ Does web searches using Tavily
- ✅ Compresses research findings
- ❌ Does NOT save reports to files

## How to Use research_agent_full

1. **Start the LangGraph server** (already running):
   ```bash
   uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev --allow-blocking
   ```

2. **Access LangGraph Studio**:
   - Go to: https://smith.langchain.com/studio/?baseUrl=http://localhost:8000
   - Select the `research_agent_full` graph

3. **Ask your question**:
   - Example: "Research flip flops - types, materials, and popular brands"
   - The agent will:
     - Clarify your request if needed
     - Do web research using Tavily
     - Generate a comprehensive report
     - **Save the report to `src/deep_research_from_scratch/files/report_<uuid>.md`**

4. **Find your report**:
   - Check the `src/deep_research_from_scratch/files/` directory
   - Look for `report_<uuid>.md` files

## File Saving Locations

Only `research_agent_full` saves reports. Here's the code (from `research_agent_full.py` lines 61-87):

```python
async def save_report_to_file(state: AgentState):
    """Save the final report to a file in the 'files' directory."""
    final_report = state.get("final_report", "")
    
    # Get the directory where this module is located
    module_dir = os.path.dirname(os.path.abspath(__file__))
    files_dir = os.path.join(module_dir, "files")
    
    # Create the files directory if it doesn't exist
    os.makedirs(files_dir, exist_ok=True)
    
    # Generate a unique filename using UUID
    report_id = str(uuid.uuid4())
    filename = f"report_{report_id}.md"
    filepath = os.path.join(files_dir, filename)
    
    # Save the report
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_report)
    
    return {
        "messages": [f"Report saved to: {filepath}"],
    }
```

Reports are saved to:
```
e:\Infosys\Internship_stuff\GitHub_infosys_2\Designing-an-Autonomous-Learning-Agent-with-Checkpoint-Verification-and-Feynman-Pedagogy---Group-2-main\src\deep_research_from_scratch\files\report_<uuid>.md
```

## Conclusion

**No bugs found!** The system is working as designed:

- ✅ `research_agent_mcp` correctly reads local files (not web search)
- ✅ `research_agent_full` correctly does web research and saves reports
- ✅ Reports are saved to the correct location

**Recommendation**: Use `research_agent_full` for your flip flop research to get web-based research with saved reports.
