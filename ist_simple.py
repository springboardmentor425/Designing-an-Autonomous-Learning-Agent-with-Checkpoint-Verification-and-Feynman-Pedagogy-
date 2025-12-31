import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GOOGLE_API_KEY)

while True:
    prompt = input("You: ").strip()
    if prompt.lower() in ["exit", "quit"]:
        break
    if not prompt:
        continue

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    print("Gemini:", response.text)
