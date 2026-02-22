import os
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY not found. Check your .env file.")
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
class State(TypedDict):
    messages: Annotated[list, add_messages]
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

def chatbot_node(state: State):
    return {"messages": [llm.invoke(state["messages"]]}
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot_node)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()
if __name__ == "__main__":
    print("🤖 Gemini Chatbot is ready! Type 'quit' to exit.")
    current_state = {"messages": []}
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit"]:
            break
        current_state["messages"].append(("user", user_input))
        result = graph.invoke(current_state)
        ai_response = result["messages"][-1].content
        print(f"Gemini: {ai_response}")
        current_state = result
