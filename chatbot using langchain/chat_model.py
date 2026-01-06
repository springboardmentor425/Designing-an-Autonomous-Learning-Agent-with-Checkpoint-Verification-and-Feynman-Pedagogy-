import os
import dotenv
dotenv.load_dotenv("venv/.env")
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage


api=os.environ.get("GOOGLE_API_KEY")


llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    temperature=1.0,
    max_output_tokens=500
)


query = [HumanMessage(content="what is langchain and how it is useful for building chatbot applications?")]


print("--- Response from (Gemini 3 Flash) ---")
try:
    response = llm.invoke(query)
    content=response.content
    if isinstance(content, list):
        msg_text = "".join([part['text'] for part in content if 'text' in part])
        print(msg_text)
    elif isinstance(content, str):
        print(content)

except Exception as e:
    print(f"Error: {e}")
