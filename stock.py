import requests
from twilio.rest import Client
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

STOCK_NAME = "TSLA"
COMPANY_NAME = "Tesla Inc"

STOCK_ENDPOINT = "https://www.alphavantage.co/query"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
STOCK_API_KEY = os.getenv("STOCK_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
RECEPIENT_PHONE_NUMBER = os.getenv("RECEPIENT_PHONE_NUMBER")

# Stock API parameters
stock_params = {
    "function": "TIME_SERIES_DAILY",
    "symbol": STOCK_NAME,
    "apikey": STOCK_API_KEY
}

# Fetch stock data
response = requests.get(STOCK_ENDPOINT, params=stock_params)
response.raise_for_status()
data = response.json()["Time Series (Daily)"]

# Extract relevant stock data
stock_data = [value for (key, value) in data.items()]
yesterdays_data = stock_data[0]
yesterdays_closing_price = yesterdays_data["4. close"]
print(yesterdays_closing_price)

day_before_yesterday_data = stock_data[1]
day_before_yesterdays_price = day_before_yesterday_data['4. close']
print(day_before_yesterdays_price)

# Calculate difference and percentage change
difference = (float(yesterdays_closing_price) - float(day_before_yesterdays_price))
up_down = "🔺" if difference > 0 else "🔻"

diff_percent = round((difference / float(yesterdays_closing_price)) * 100)
print(diff_percent)

# Initialize the articles list to avoid NameError
three_articles = []

# Only fetch news if the percentage change is significant
if abs(diff_percent) > 1:
    News_parameters = {
        "qInTitle": COMPANY_NAME,
        "apiKey": NEWS_API_KEY
    }

    # Fetch news articles
    news_response = requests.get(NEWS_ENDPOINT, params=News_parameters)
    news = news_response.json()["articles"]
    three_articles = news[:4]  # Get the top 3 or 4 articles

# Check if there are any articles to format and send
if three_articles:
    formatted_article = [
        f"{STOCK_NAME}: {up_down}{diff_percent}%\nHeadline: {article['title']} \nBrief: {article['description']}"
        for article in three_articles
    ]

    # Send each formatted article via Twilio
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    for article in formatted_article:
        message = client.messages.create(
            body=article,
            from_=TWILIO_PHONE_NUMBER,
            to=RECEPIENT_PHONE_NUMBER
        )
        print(f"Message sent: {message.sid}")
else:
    print("No significant stock price change or no news articles found.")

