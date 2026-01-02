import os
from langchain_google_genai import ChatGoogleGenerativeAI
import dotenv
dotenv.load_dotenv()


model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

result = model.invoke("Explain Feynman Technique in simple words.")

print(result.content)