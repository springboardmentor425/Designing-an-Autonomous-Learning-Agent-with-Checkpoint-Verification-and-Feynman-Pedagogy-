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

def get_response(user_text: str) -> str:
    query = [HumanMessage(content=user_text)]
    try:
        response = llm.invoke(query)
        content=response.content
        if isinstance(content, list):
            return "".join([part['text'] for part in content if 'text' in part])
            return content
        elif isinstance(content, str):
            return content

    except Exception as e:
        return e 