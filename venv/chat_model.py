import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

os.environ["GOOGLE_API_KEY"] = "AIzaSyBKmXhZCOnsDnZvOvVev7eVmlX8EgKnZcA"

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",  # or "gemini-2.0", "gemini-3.0-pro", etc.
    temperature=0.7,  # Gemini 3.0+ defaults to 1.0
    #thinking_level="low",
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
)

def generate_text(user_input):
    response = model.invoke(user_input)
    return response.content

if __name__ == "__main__":
    prompt = "Write a one-sentence poem about the ocean."
    output = generate_text(prompt)
    
    print(f"Input: {prompt}")
    print(f"Output: {output}")



prompt_template = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant"),
    ("human", "{input}")
])

chain = prompt_template | model

response = chain.invoke({"input": "Hello, how are you?"})
print(response.content)