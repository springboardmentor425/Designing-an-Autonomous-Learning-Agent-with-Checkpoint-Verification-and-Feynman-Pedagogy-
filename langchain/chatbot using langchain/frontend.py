import streamlit as st
from chat_model import get_response

st.title("💬Chatbot using langchain")
st.caption("Ask anything — powered by Gemini")


query=st.chat_input("Say something")

if query:
    #user input
    with st.chat_message("human"):
        st.write(f"{query}")

    #bot response
    with st.chat_message("ai") :  
        response=get_response(query)
        st.write(response)