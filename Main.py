import os
from langchain_google_genai import ChatGoogleGenerativeAI
import dotenv
dotenv.load_dotenv()



model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

result = model.invoke("What is date today?")

print(result.content)