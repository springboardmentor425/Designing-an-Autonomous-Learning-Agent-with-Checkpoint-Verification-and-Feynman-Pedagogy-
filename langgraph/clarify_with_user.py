from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage


class State(TypedDict):
    messages: list
    needs_clarification: bool

llm = ChatGoogleGenerativeAI(model="gemini-3.0-flash-preview")



def analyzer(state: State):
    """Determines if the user's prompt is too vague."""
    prompt = f"Analyze this request: '{state['messages'][-1].content}'. Is it specific enough to act on? Respond with ONLY 'CLEAR' or 'UNCLEAR'."
    response = llm.invoke(prompt)
    
    return {"needs_clarification": "UNCLEAR" in response.content.upper()}

def clarify_node(state: State):
    """Gemini generates a clarification question."""
    last_msg = state['messages'][-1].content
    prompt = f"The user asked: '{last_msg}'. This is too vague. Ask a concise follow-up question to clarify their intent."
    response = llm.invoke(prompt)
    return {"messages": [response]}

def work(state: State):
    """The final task execution."""
    return {"messages": [AIMessage(content="Processing your clear request now!")]}



def check(state: State):
    if state["needs_clarification"]:
        return "clarify"
    return "work"



workflow = StateGraph(State)

workflow.add_node("analyzer", analyzer)
workflow.add_node("clarify", clarify_node)
workflow.add_node("work", work)

workflow.set_entry_point("analyzer")

workflow.add_conditional_edges(
    "analyzer",
    check,
    {
        "clarify": "clarify",
        "work": "work"
    }
)

workflow.add_edge("clarify", END)
workflow.add_edge("work", END)


memory = MemorySaver()
app = workflow.compile(checkpointer=memory, interrupt_before=["clarify"])
