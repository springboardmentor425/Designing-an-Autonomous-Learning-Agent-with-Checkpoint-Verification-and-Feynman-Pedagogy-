import os
from langchain.chat_models import init_chat_model
from langchain_google_genai import ChatGoogleGenerativeAI
import dotenv
dotenv.load_dotenv()

model=init_chat_model("google_genai:models/gemini-2.5-flash")

result=model.invoke([{"role":"user", "content": "write a poem about Rain."}])
print(result.content)