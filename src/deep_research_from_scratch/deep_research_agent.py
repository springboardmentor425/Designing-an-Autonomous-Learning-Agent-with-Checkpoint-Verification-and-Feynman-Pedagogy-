
"""
Full Multi-Agent Research System

This module integrates all components of the research system:
- User clarification and scoping
- Research brief generation  
- Multi-agent research coordination
- Final report generation

The system orchestrates the complete research workflow from initial user
input through final report delivery.
"""

import os
import uuid
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

from deep_research_from_scratch.utils import get_today_str
from deep_research_from_scratch.prompts import final_report_generation_prompt
from deep_research_from_scratch.state_scope import AgentState, AgentInputState
from deep_research_from_scratch.research_agent_scope import clarify_with_user, write_research_brief
from deep_research_from_scratch.multi_agent_supervisor import supervisor_agent

# ===== Config =====

from langchain.chat_models import init_chat_model
writer_model = init_chat_model("groq:llama-3.3-70b-versatile")

# ===== FINAL REPORT GENERATION =====

from deep_research_from_scratch.state_scope import AgentState

async def final_report_generation(state: AgentState):
    """
    Final report generation node.

    Synthesizes all research findings into a comprehensive final report
    """

    notes = state.get("notes", [])

    findings = "\n".join(notes)

    final_report_prompt = final_report_generation_prompt.format(
        research_brief=state.get("research_brief", ""),
        findings=findings,
        date=get_today_str()
    )

    final_report = await writer_model.ainvoke([HumanMessage(content=final_report_prompt)])

    return {
        "final_report": final_report.content, 
        "messages": ["Here is the final report: " + final_report.content],
    }

# ===== SAVE REPORT TO FILE =====

async def save_report_to_file(state: AgentState):
    """
    Save the final report to a file in the 'files' directory.
    
    Uses UUID to generate a unique filename for each report.
    Uses asyncio.to_thread to avoid blocking the async event loop.
    """
    import asyncio
    final_report = state.get("final_report", "")
    
    # Get the directory where this module is located
    module_dir = os.path.dirname(os.path.abspath(__file__))
    files_dir = os.path.join(module_dir, "files")
    
    # Generate a unique filename using UUID
    report_id = str(uuid.uuid4())
    filename = f"report_{report_id}.md"
    filepath = os.path.join(files_dir, filename)
    
    # Use asyncio.to_thread to avoid blocking the async event loop
    def write_file():
        os.makedirs(files_dir, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(final_report)
    
    await asyncio.to_thread(write_file)
    
    return {
        "messages": [f"Report saved to: {filepath}"],
    }

# ===== GRAPH CONSTRUCTION =====
# Build the overall workflow
deep_researcher_builder = StateGraph(AgentState, input_schema=AgentInputState)

# Add workflow nodes
deep_researcher_builder.add_node("clarify_with_user", clarify_with_user)
deep_researcher_builder.add_node("write_research_brief", write_research_brief)
deep_researcher_builder.add_node("supervisor_subgraph", supervisor_agent)
deep_researcher_builder.add_node("final_report_generation", final_report_generation)
deep_researcher_builder.add_node("save_report_to_file", save_report_to_file)

# Add workflow edges
deep_researcher_builder.add_edge(START, "clarify_with_user")
deep_researcher_builder.add_edge("write_research_brief", "supervisor_subgraph")
deep_researcher_builder.add_edge("supervisor_subgraph", "final_report_generation")
deep_researcher_builder.add_edge("final_report_generation", "save_report_to_file")
deep_researcher_builder.add_edge("save_report_to_file", END)

# Compile the full workflow
deep_researcher = deep_researcher_builder.compile()






