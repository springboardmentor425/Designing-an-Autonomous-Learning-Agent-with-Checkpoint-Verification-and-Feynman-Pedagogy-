import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate


load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")


model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
)


prompt_template = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant. Answer clearly."),
    ("human", "{input}")
])

chain = prompt_template | model


print("Gemini Chatbot (type 'quit' to stop)\n")

while True:
    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit"]:
        print("Chat ended.")
        break

    response = chain.invoke({"input": user_input})
    print(f"AI: {response.content}\n")