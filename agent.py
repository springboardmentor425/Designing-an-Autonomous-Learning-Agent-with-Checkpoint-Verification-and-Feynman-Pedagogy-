import dotenv

dotenv.load_dotenv()
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage


class SimpleAIAgent:
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.6
        )

    def run(self, query: str) -> str:
        message = HumanMessage(content=query)
        response = self.model.invoke([message])
        return response.content


if __name__ == "__main__":
    agent = SimpleAIAgent()
    user_query = input("Ask the AI agent: ")
    print("\nAI Agent Response:")
    print(agent.run(user_query))
