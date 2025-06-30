import os
import argparse
from termcolor import colored
import requests
import yfinance as yf
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv


load_dotenv()


FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
COINGECKO_API_URL = 'https://api.coingecko.com/api/v3/simple/price'
FINNHUB_COMPANY_NEWS_URL = 'https://finnhub.io/api/v1/company-news'
FINNHUB_CRYPTO_NEWS_URL = 'https://finnhub.io/api/v1/news'

# replace with DB later
db_records = []

def store_summary(ticker, summary, price, sentiment):
    #Save summary record to db
    record = {
        'ticker': ticker,
        'summary': summary,
        'price': price,
        'sentiment': sentiment,
        'timestamp': datetime.now(timezone.utc)
    }
    db_records.append(record)
    print(colored("Saved record.", 'blue'))

def view_history():
    #Print stored summaries
    if not db_records:
        print(colored("No stored records.", 'yellow'))
    for rec in reversed(db_records):
        print(colored(
            f"[{rec['ticker']}] {rec['sentiment']}\nSummary: {rec['summary']}\nPrice: ${rec['price']}\nTime: {rec['timestamp']}",
            'cyan'))

def fetch_news(ticker, is_crypto=False):
    #Fetch recent news articles for ticker or crypto
    ticker_lower = ticker.lower()
    try:
        if is_crypto:
            params = {'category': 'crypto', 'token': FINNHUB_API_KEY}
            response = requests.get(FINNHUB_CRYPTO_NEWS_URL, params=params)
        else:
            today = datetime.now(timezone.utc).date()
            week_ago = today - timedelta(days=7)
            params = {
                'symbol': ticker.upper(),
                'from': week_ago.isoformat(),
                'to': today.isoformat(),
                'token': FINNHUB_API_KEY
            }
            response = requests.get(FINNHUB_COMPANY_NEWS_URL, params=params)

        response.raise_for_status()
        data = response.json()

        filtered = []
        for article in data:
            combined = (article.get('headline', '') + article.get('summary', '')).lower()
            if ticker_lower in combined:
                filtered.append(article)
            if len(filtered) >= 3:
                break
        return filtered
    except Exception as e:
        print(colored(f"Error fetching news: {e}", 'red'))
        return []

def fetch_crypto_price(crypto):
    #Get current price for a cryptocurrency
    try:
        response = requests.get(COINGECKO_API_URL, params={'ids': crypto, 'vs_currencies': 'usd'})
        response.raise_for_status()
        return response.json().get(crypto, {}).get('usd', 'N/A')
    except Exception as e:
        print(colored(f"Error fetching crypto price: {e}", 'red'))
        return 'N/A'

def fetch_stock_price(ticker):
    #Get current stock price
    try:
        stock = yf.Ticker(ticker)
        return stock.history(period='1d')['Close'].iloc[-1]
    except Exception as e:
        print(colored(f"Error fetching stock price: {e}", 'red'))
        return 'N/A'

def summarize(texts):
   # Use Gemini to summarize
   return 


