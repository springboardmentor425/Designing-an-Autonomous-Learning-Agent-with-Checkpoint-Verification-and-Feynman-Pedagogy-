import os
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate


API_KEY = os.getenv("GEMINI_API_KEY")

model = ChatGoogleGenerativeAI(
    model="gemini-pro",  
    temperature=0.7,
    max_retries=1,
)

def generate_text(user_input):
    time.sleep(2)  
    response = model.invoke(user_input)
    return response.content

if __name__ == "__main__":
    prompt = "Write a one-sentence poem about the ocean."
    output = generate_text(prompt)

    print("Input:", prompt)
    print("Output:", output)

prompt_template = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{input}")
])

chain = prompt_template | model

time.sleep(2)
response = chain.invoke({"input": "Hello, how are you?"})
print(response.content)
