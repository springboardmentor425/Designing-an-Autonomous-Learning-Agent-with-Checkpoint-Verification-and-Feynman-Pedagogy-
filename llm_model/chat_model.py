import os
import dotenv
import requests
from langchain.tools import tool
from tavily import TavilyClient

dotenv.load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
CURRENCY_API_KEY = os.getenv("CURRENCY_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY missing")
if not NEWS_API_KEY:
    raise ValueError("NEWS_API_KEY missing")
if not CURRENCY_API_KEY:
    raise ValueError("CURRENCY_API_KEY missing")


#WEB SEARCH
@tool
def web_search(query: str) -> str:
    """Search the web and return top result"""

    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    response = tavily_client.search(query=query, max_results=1)

    return response["results"][0]["content"]


#NEWS TOOL
@tool
def get_news(topic: str) -> str:
    """Get latest news using NewsAPI"""

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": topic,
        "apiKey": NEWS_API_KEY,
        "pageSize": 1
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return "Could not fetch news"

    data = response.json()
    article = data["articles"][0]

    return f"Latest news on {topic}: {article['title']}"


#currency tool
@tool
def convert_currency(from_currency: str, to_currency: str, amount: float) -> str:
    """Convert currency using ExchangeRate API"""

    url = f"https://v6.exchangerate-api.com/v6/{CURRENCY_API_KEY}/pair/{from_currency}/{to_currency}/{amount}"
    response = requests.get(url)

    if response.status_code != 200:
        return "Currency conversion failed"

    data = response.json()
    return f"{amount} {from_currency} = {data['conversion_result']} {to_currency}"


if __name__ == "__main__":

    print("\n--- WEB SEARCH ---")
    print(web_search.invoke({"query": "Tesla stock price today"}))

    print("\n--- NEWS ---")
    print(get_news.invoke({"topic": "Artificial Intelligence"}))

    print("\n--- CURRENCY ---")
    print(convert_currency.invoke({
        "from_currency": "USD",
        "to_currency": "INR",
        "amount": 100
    }))
