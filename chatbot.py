import requests
import json

MODEL = "llama3"
OLLAMA_URL = "http://localhost:11434/api/generate"

def chat_with_ai(prompt):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()

    data = response.json()
    return data["response"].strip()

print("🤖 Offline AI Chatbot Demo (FREE)")
print("Type 'exit' to quit")
print("-" * 40)

while True:
    user = input("You: ")
    if user.lower() in ["exit", "quit", "bye"]:
        print("Bot: Goodbye 👋")
        break

    reply = chat_with_ai(user)
    print("Bot:", reply)
