import os
import requests
import yfinance as yf
from twilio.rest import Client
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import google.generativeai as genai

# Load environment variables
load_dotenv()

# API keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
STOCK_API_KEY = os.getenv("STOCK_API_KEY")  # For US stocks (Alpha Vantage)
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
RECEPIENT_PHONE_NUMBER = os.getenv("RECEPIENT_PHONE_NUMBER")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

def ask_gemini(prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()

# Step 1: Get stock info
know_ticker = input("Do you know the stock ticker? (yes/no): ").strip().lower()
if know_ticker == "yes":
    STOCK_NAME = input("Enter stock ticker (e.g., TSLA, AAPL, ZOMATO.NS): ").upper()
    COMPANY_NAME = input(f"Enter full company name for {STOCK_NAME}: ")

    # Auto append .NS for Indian stocks if not present
    if len(STOCK_NAME) > 0 and "." not in STOCK_NAME:
        add_suffix = input("Is this an Indian stock? (yes/no): ").strip().lower()
        if add_suffix == "yes":
            STOCK_NAME += ".NS"

else:
    search_choice = input("Do you want me to search it using AI? (yes/no): ").strip().lower()
    if search_choice == "yes":
        company_query = input("Enter company name or description: ")
        gemini_reply = ask_gemini(
            f"What is the official stock ticker for {company_query}? Reply with only the ticker and full company name."
        )
        print("\nGemini suggests:\n", gemini_reply)
        STOCK_NAME = input("\nEnter the stock ticker you want to track: ").upper()
        COMPANY_NAME = input(f"Enter full company name for {STOCK_NAME}: ")

        if len(STOCK_NAME) > 0 and "." not in STOCK_NAME:
            add_suffix = input("Is this an Indian stock? (yes/no): ").strip().lower()
            if add_suffix == "yes":
                STOCK_NAME += ".NS"
    else:
        print("Can't proceed without a stock ticker.")
        exit()

threshold = float(input("Enter % change threshold for alerts (e.g., 1.5): "))
hours = int(input("Enter news time window in hours (e.g., 2): "))

NEWS_ENDPOINT = "https://newsapi.org/v2/everything"

# Step 2: Fetch stock data
if STOCK_NAME.endswith(".NS") or STOCK_NAME.endswith(".BO"):  # Indian stocks
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)
    data = yf.download(STOCK_NAME, start=start_date, end=end_date, interval="1d", auto_adjust=False)

    if data.empty:
        print("No data found for this ticker.")
        exit()

    latest_close = float(data['Close'].iloc[-1].item())
    prev_close = float(data['Close'].iloc[-2].item())

else:  # US or global stocks
    STOCK_ENDPOINT = "https://www.alphavantage.co/query"
    stock_params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": STOCK_NAME,
        "apikey": STOCK_API_KEY
    }
    response = requests.get(STOCK_ENDPOINT, params=stock_params)
    response.raise_for_status()
    stock_json = response.json()

    if "Time Series (Daily)" not in stock_json:
        print("Error fetching stock data. Possibly wrong ticker or API limit reached.")
        exit()

    data = list(stock_json["Time Series (Daily)"].values())
    latest_close = float(data[0]["4. close"])
    prev_close = float(data[1]["4. close"])

# Step 3: Calculate change
difference = latest_close - prev_close
up_down = "🔺" if difference > 0 else "🔻"
diff_percent = round((difference / prev_close) * 100, 2)

print(f"{STOCK_NAME} moved {up_down}{diff_percent}% (from {prev_close} to {latest_close})")

# Step 4: Fetch news if threshold exceeded
three_articles = []
if abs(diff_percent) > threshold:
    from_time = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    News_parameters = {
        "qInTitle": f"{COMPANY_NAME} OR {STOCK_NAME.split('.')[0]}",
        "from": from_time,
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY
    }
    news_response = requests.get(NEWS_ENDPOINT, params=News_parameters)
    news = news_response.json().get("articles", [])
    three_articles = news[:3]

# Step 5: Send alerts
if three_articles:
    formatted_articles = [
        f"{STOCK_NAME}: {up_down}{diff_percent}%\nHeadline: {article['title']} \nBrief: {article['description']}"
        for article in three_articles
    ]
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    for article in formatted_articles:
        message = client.messages.create(
            body=article,
            from_=TWILIO_PHONE_NUMBER,
            to=RECEPIENT_PHONE_NUMBER
        )
        print(f"Message sent: {message.sid}")
else:
    print("No significant stock price change or no recent news found.")


# import requests
# from twilio.rest import Client
# from dotenv import load_dotenv
# import os

# # Load environment variables from .env file
# load_dotenv()

# STOCK_NAME = "TSLA"
# COMPANY_NAME = "Tesla Inc"

# STOCK_ENDPOINT = "https://www.alphavantage.co/query"
# NEWS_ENDPOINT = "https://newsapi.org/v2/everything"

# NEWS_API_KEY = os.getenv("NEWS_API_KEY")
# STOCK_API_KEY = os.getenv("STOCK_API_KEY")
# TWILIO_SID = os.getenv("TWILIO_SID")
# TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
# TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
# RECEPIENT_PHONE_NUMBER = os.getenv("RECEPIENT_PHONE_NUMBER")

# # Stock API parameters
# stock_params = {
#     "function": "TIME_SERIES_DAILY",
#     "symbol": STOCK_NAME,
#     "apikey": STOCK_API_KEY
# }

# # Fetch stock data
# response = requests.get(STOCK_ENDPOINT, params=stock_params)
# response.raise_for_status()
# data = response.json()["Time Series (Daily)"]

# # Extract relevant stock data
# stock_data = [value for (key, value) in data.items()]
# yesterdays_data = stock_data[0]
# yesterdays_closing_price = yesterdays_data["4. close"]
# print(yesterdays_closing_price)

# day_before_yesterday_data = stock_data[1]
# day_before_yesterdays_price = day_before_yesterday_data['4. close']
# print(day_before_yesterdays_price)

# # Calculate difference and percentage change
# difference = (float(yesterdays_closing_price) - float(day_before_yesterdays_price))
# up_down = "🔺" if difference > 0 else "🔻"

# diff_percent = round((difference / float(yesterdays_closing_price)) * 100)
# print(diff_percent)

# # Initialize the articles list to avoid NameError
# three_articles = []

# # Only fetch news if the percentage change is significant
# if abs(diff_percent) > 1:
#     News_parameters = {
#         "qInTitle": COMPANY_NAME,
#         "apiKey": NEWS_API_KEY
#     }

#     # Fetch news articles
#     news_response = requests.get(NEWS_ENDPOINT, params=News_parameters)
#     news = news_response.json()["articles"]
#     three_articles = news[:4]  # Get the top 3 or 4 articles

# # Check if there are any articles to format and send
# if three_articles:
#     formatted_article = [
#         f"{STOCK_NAME}: {up_down}{diff_percent}%\nHeadline: {article['title']} \nBrief: {article['description']}"
#         for article in three_articles
#     ]

#     # Send each formatted article via Twilio
#     client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
#     for article in formatted_article:
#         message = client.messages.create(
#             body=article,
#             from_=TWILIO_PHONE_NUMBER,
#             to=RECEPIENT_PHONE_NUMBER
#         )
#         print(f"Message sent: {message.sid}")
# else:
#     print("No significant stock price change or no news articles found.")
