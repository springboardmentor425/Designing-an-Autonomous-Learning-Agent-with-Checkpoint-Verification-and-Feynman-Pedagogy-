# MCP Research Agent File Search Issue - FIXED

## Problem Summary

When using the `research_agent_mcp` in LangSmith Studio and asking questions like "what is MCP server?", the agent was reporting "No matches found" even though relevant report files existed in the `src/deep_research_from_scratch/files/` directory.

## Root Cause

The MCP filesystem server's `search_files` tool searches for **exact text matches**. When you ask "what is MCP server?", it searches for that exact phrase in file contents. If the phrase doesn't appear exactly as written, the search returns no results.

**Example:**
- Query: "what is MCP server?"
- Existing file: `report_ce494a99-ce5a-46b0-812a-9f26a1f6191c.md` (contains "Introduction to MCP Server")
- Problem: The search tool might not find this file because it's looking for exact phrase matches

## Solution Implemented

Modified the `research_agent_prompt_with_mcp` in `src/deep_research_from_scratch/prompts.py` to:

1. **Always list files first** - Instructs the agent to use `list_directory` FIRST to see ALL available files
2. **Don't rely solely on search** - Warns that `search_files` may miss relevant files
3. **Read files based on filenames** - Encourages reading files with relevant-looking names
4. **Fallback strategy** - If search returns "No matches found", list all files and read promising ones

### Key Changes:
```python
# Before: Generic instruction to "explore available files"
2. **Explore available files** - Use list_allowed_directories and list_directory to understand what's available

# After: Explicit instruction to ALWAYS list files first
2. **ALWAYS START by listing files** - Use list_allowed_directories and list_directory FIRST to see ALL available files
```

Added warning:
```python
**IMPORTANT**: If search_files returns "No matches found", don't give up! List all files and read ones with relevant-looking names.
```

## How to Test

1. **Server is running** at: http://localhost:8000
2. **Open LangSmith Studio**: https://smith.langchain.com/studio/?baseUrl=http://localhost:8000
3. **Select**: `research_agent_mcp` graph
4. **Test input**:
   ```json
   {
     "researcher_messages": [
       {
         "role": "user",
         "content": "what is MCP server?"
       }
     ]
   }
   ```
5. **Expected behavior**: 
   - Agent will first list all files in the directory
   - Agent will identify `report_ce494a99-ce5a-46b0-812a-9f26a1f6191c.md` as relevant
   - Agent will read this file and provide information about MCP servers

## Files in the Directory

Current reports available:
- `coffee_shops_sf.md`
- `report_58ef21dc-4572-4543-b123-695aeb86eb03.md`
- `report_6cccef4a-b3f2-4e1c-ba54-955b1ab8754d.md` (about Perceptron)
- `report_85785809-0547-4c7e-a5eb-0893c80c12f8.md`
- `report_ce494a99-ce5a-46b0-812a-9f26a1f6191c.md` (**about MCP Server** ✓)
- `report_e787e240-38f6-42dc-9e57-b70c8336d8a2.md`
- `test_report_7e9446db-49cb-4729-abf2-15b33b46b0d5.md`

## Additional Notes

- The MCP filesystem server is correctly configured to access: `src/deep_research_from_scratch/files/`
- File saving works correctly (verified with test script)
- The issue was purely in the agent's search strategy, not the MCP configuration
