
"""Multi-agent supervisor for coordinating research across multiple specialized agents.

This module implements a supervisor pattern where:
1. A supervisor agent coordinates research activities and delegates tasks
2. Multiple researcher agents work on specific sub-topics independently
3. Results are aggregated and compressed for final reporting

The supervisor uses parallel research execution to improve efficiency while
maintaining isolated context windows for each research topic.
"""

import asyncio

from typing_extensions import Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    HumanMessage, 
    BaseMessage, 
    SystemMessage, 
    ToolMessage,
    filter_messages
)
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from deep_research_from_scratch.prompts import lead_researcher_prompt
from deep_research_from_scratch.research_agent import researcher_agent
from deep_research_from_scratch.state_multi_agent_supervisor import (
    SupervisorState, 
    ConductResearch, 
    ResearchComplete
)
from deep_research_from_scratch.utils import get_today_str, think_tool
from deep_research_from_scratch.retry_utils import ainvoke_with_retry

def get_notes_from_tool_calls(messages: list[BaseMessage]) -> list[str]:
    # Manually filter for ToolMessage to avoid potential type issues with filter_messages
    notes = []
    for msg in messages:
        if isinstance(msg, ToolMessage):
             # Skip error messages or empty content
            if msg.content and "Error synthesizing" not in str(msg.content):
                notes.append(str(msg.content))
    
    # Debug print
    print(f"Extracted {len(notes)} research notes from history.")
    return notes

# Ensure async compatibility for Jupyter environments
try:
    import nest_asyncio
    # Only apply if running in Jupyter/IPython environment
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            nest_asyncio.apply()
    except ImportError:
        pass  # Not in Jupyter, no need for nest_asyncio
except ImportError:
    pass  # nest_asyncio not available, proceed without it


# ===== CONFIGURATION =====

supervisor_tools = [ConductResearch, ResearchComplete, think_tool]
supervisor_model = init_chat_model("groq:mixtral-8x7b-32768")
supervisor_model_with_tools = supervisor_model.bind_tools(supervisor_tools)

# System constants
# Maximum number of tool call iterations for individual researcher agents
# This prevents infinite loops and controls research depth per topic
# Maximum number of tool call iterations for individual researcher agents
# This prevents infinite loops and controls research depth per topic
max_researcher_iterations = 2 # Calls to think_tool + ConductResearch

# Maximum number of concurrent research agents the supervisor can launch
# This is passed to the lead_researcher_prompt to limit parallel research tasks
max_concurrent_researchers = 1

# ===== SUPERVISOR NODES =====

async def supervisor(state: SupervisorState) -> Command[Literal["supervisor_tools"]]:
    """Coordinate research activities.

    Analyzes the research brief and current progress to decide:
    - What research topics need investigation
    - Whether to conduct parallel research
    - When research is complete

    Args:
        state: Current supervisor state with messages and research progress

    Returns:
        Command to proceed to supervisor_tools node with updated state
    """
    supervisor_messages = state.get("supervisor_messages", [])

    # Prepare system message with current date and constraints
    system_message = lead_researcher_prompt.format(
        date=get_today_str(), 
        max_concurrent_research_units=max_concurrent_researchers,
        max_researcher_iterations=max_researcher_iterations
    )
    # Trim history to last 6 messages to stay under Groq's 6000 TPM limit
    trimmed_messages = supervisor_messages[-6:] if len(supervisor_messages) > 6 else supervisor_messages
    messages = [SystemMessage(content=system_message)] + trimmed_messages

    # Make decision about next research steps
    response = await ainvoke_with_retry(supervisor_model_with_tools, messages)

    # Find the user's latest request to update research_brief
    latest_request = None
    if supervisor_messages:
        for msg in reversed(supervisor_messages):
            if isinstance(msg, HumanMessage):
                latest_request = msg.content
                break
    
    updates = {
        "supervisor_messages": [response],
        "research_iterations": state.get("research_iterations", 0) + 1
    }
    
    if latest_request:
        updates["research_brief"] = latest_request

    return Command(
        goto="supervisor_tools",
        update=updates
    )

async def supervisor_tools(state: SupervisorState) -> Command[Literal["supervisor", "__end__"]]:
    """Execute supervisor decisions - either conduct research or end the process.

    Handles:
    - Executing think_tool calls for strategic reflection
    - Launching parallel research agents for different topics
    - Aggregating research results
    - Determining when research is complete

    Args:
        state: Current supervisor state with messages and iteration count

    Returns:
        Command to continue supervision, end process, or handle errors
    """
    supervisor_messages = state.get("supervisor_messages", [])
    research_iterations = state.get("research_iterations", 0)
    most_recent_message = supervisor_messages[-1]

    # Initialize variables for single return pattern
    tool_messages = []
    all_raw_notes = []
    next_step = "supervisor"  # Default next step
    should_end = False

    # Separate tool calls
    tool_calls = most_recent_message.tool_calls or []
    conduct_research_calls = [t for t in tool_calls if t["name"] == "ConductResearch"]
    think_tool_calls = [t for t in tool_calls if t["name"] == "think_tool"]
    research_complete_calls = [t for t in tool_calls if t["name"] == "ResearchComplete"]

    # --- 1. HANDLE THINKING (Always run if present) ---
    for tool_call in think_tool_calls:
        try:
            observation = think_tool.invoke(tool_call["args"])
            tool_messages.append(
                ToolMessage(
                    content=observation, 
                    name=tool_call["name"], 
                    tool_call_id=tool_call["id"]
                )
            )
        except Exception as e:
            print(f"Error in think_tool: {e}")

    # --- 2. LOGIC FOR NEXT STEP ---
    
    # CASE A: Conduct Research (Priority)
    if conduct_research_calls:
        should_end = False
        next_step = "supervisor"
        
        try:
            # Launch parallel research agents with retry logic
            async def execute_research_with_retry(tool_call, max_retries=2):
                for attempt in range(max_retries):
                    try:
                        return await researcher_agent.ainvoke({
                            "researcher_messages": [
                                HumanMessage(content=tool_call["args"]["research_topic"])
                            ],
                            "research_topic": tool_call["args"]["research_topic"]
                        })
                    except Exception as e:
                        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "rate_limit" in str(e).lower():
                            if attempt < max_retries - 1:
                                wait_time = (2 ** attempt) + 2  # 3s, 4s, 6s...
                                print(f"Rate limited during research execution. Retrying in {wait_time}s...")
                                await asyncio.sleep(wait_time)
                            else:
                                print(f"Research failed after {max_retries} attempts due to rate limits.")
                                return {"compressed_research": f"Error: Research failed due to rate limits: {str(e)}", "raw_notes": []}
                        else:
                            print(f"Research error (non-rate-limit): {e}")
                            return {"compressed_research": f"Error: Research failed: {str(e)}", "raw_notes": []}
                return {"compressed_research": "Error: Unknown failure", "raw_notes": []}

            coros = [
                execute_research_with_retry(tool_call)
                for tool_call in conduct_research_calls
            ]

            # Wait for all research to complete
            tool_results = await asyncio.gather(*coros)

            # Format research results
            research_tool_messages = [
                ToolMessage(
                    # Truncate to 1500 chars to stay under Groq's 6000 TPM limit
                    content=result.get("compressed_research", "Error synthesizing research report")[:1500],
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"]
                ) for result, tool_call in zip(tool_results, conduct_research_calls)
            ]

            tool_messages.extend(research_tool_messages)

            # Aggregate raw notes
            all_raw_notes = [
                "\n".join(result.get("raw_notes", [])) 
                for result in tool_results
            ]
            
        except Exception as e:
            print(f"Error executing research: {e}")
            # If research fails, we should probably tell the supervisor
            tool_messages.append(ToolMessage(content=f"Error executing research: {str(e)}", tool_call_id=conduct_research_calls[0]["id"], name="ConductResearch"))

    # CASE B: Research Complete
    elif research_complete_calls:
        # Prevent premature completion (Lazy Agent Check)
        # If we are in the first few iterations and have NO notes, we shouldn't complete.
        previous_notes = get_notes_from_tool_calls(supervisor_messages)
        if research_iterations <= 2 and not previous_notes:
             print("Premature completion detected. Forcing retry.")
             return Command(
                goto="supervisor",
                update={
                    "supervisor_messages": [
                        HumanMessage(content="You cannot call ResearchComplete yet because you haven't conducted any research. You MUST call ConductResearch first.")
                    ],
                    "research_iterations": 0
                }
            )
        
        should_end = True
        next_step = END
        # Handle the tool call validly by appending a message (optional but good practice)
        tool_messages.append(ToolMessage(content="Research completion acknowledged.", name="ResearchComplete", tool_call_id=research_complete_calls[0]["id"]))

    # CASE C: No Major Actions (or just thinking)
    else:
        # Lazy Agent Check (No tools at all on first turn)
        if research_iterations <= 2 and not think_tool_calls:
            print("Lazy agent detected (no tools on first turn). Forcing retry.")
            return Command(
                goto="supervisor",
                update={
                    "supervisor_messages": [
                        HumanMessage(content="You MUST call the ConductResearch tool to investigate this topic. Do not answer directly. Start research now.")
                    ],
                    "research_iterations": 0
                }
            )
        
        # Just thinking or exceeded limits?
        if research_iterations >= max_researcher_iterations:
             should_end = True
             next_step = END
        else:
             should_end = False
             next_step = "supervisor"

    # Single return point with appropriate state updates
    if should_end:
        return Command(
            goto=next_step,
            update={
                "notes": get_notes_from_tool_calls(supervisor_messages),
                "research_brief": state.get("research_brief", "")
            }
        )
    else:
        return Command(
            goto=next_step,
            update={
                "supervisor_messages": tool_messages,
                "raw_notes": all_raw_notes
            }
        )

# ===== GRAPH CONSTRUCTION =====

# Build supervisor graph
supervisor_builder = StateGraph(SupervisorState)
supervisor_builder.add_node("supervisor", supervisor)
supervisor_builder.add_node("supervisor_tools", supervisor_tools)
supervisor_builder.add_edge(START, "supervisor")
supervisor_agent = supervisor_builder.compile()





