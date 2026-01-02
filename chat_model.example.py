import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# 1. Configuration
os.environ["GOOGLE_API_KEY"] = "your-api-key"

llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    temperature=1.0,
    max_output_tokens=500
)

# 3. Hard-coded Message
query = [HumanMessage(content="write about india in short")]

# 4. Invoke and Print
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
