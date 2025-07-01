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
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

    if isinstance(texts, str):
        texts = [texts]

    prompt = """
    You are a financial news summarizer. Given the following news articles, provide a concise summary, overall sentiment (Positive/Negative/Neutral), and a suggested action for a retail trader. Format:
    Summary: ...
    Sentiment: ...
    Actions: ...
    
    Articles: 
    """

    for i, t in enumerate(texts):
        prompt += f"Article {i+1}: {t}\n"
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Summary unavailable. Error: {e}"

def main():
    parser = argparse.ArgumentParser(description="Crypto & Stock News Summarizer")
    parser.add_argument('--ticker', type=str, help='Stock ticker symbol')
    parser.add_argument('--crypto', type=str, help ='Cryptocurrency name')
    parser.add_argument('--history', action='store_true', help='View summary history')
    args = parser.parse_args()

    if args.history:
        #replace with real db later
        view_history()
        return
    
    elif args.ticker:
        print(colored("Fetching news...", 'cyan'))
        news = fetch_news(args.ticker, is_crypto = False)

        print(colored("Fetching price...", 'cyan'))
        price = fetch_stock_price(args.ticker)

        if not news:
            print(colored(f"No news found for {args.ticker}.", "yellow"))
            return
        
        descriptions = []
        for articles in news:
            summary_text = article.get('summary', '')
            if summary_text:
                descriptions.append(summary_text)
        
        print(colored(f"Number of articles being summarized: {len(descriptions)}", 'magenta'))

        if descriptions:
            print(colored("Summarizing, please wait...", 'yellow'))
            summary = summarize(descriptions)
        else:
            summary = summarize(f"No news summaries found for {args.ticker}. Price is ${price}.")

        if "positive" in summary.lower():
            sentiment = "Postiive"
        
        elif "negative" in summary.lower():
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        #replace with real db summary
        store_summary(args.ticker, summary, price, sentiment)

        color = 'green' if sentiment == "Positive" else 'red' if sentiment == "Negative" else 'yellow'
        print(colored(f"[{args.ticker}] {sentiment}\nSummary: {summary}\nPrice: ${price}", color))
    
    elif args.crypto:
        print(colored("Fetching price...", 'cyan'))
        price = fetch_crypto_price(args.crypto)

        print(colored("Fetching news...", 'cyan'))
        news = fetch_news(args.crypto, is_crypto=True)

        if not news:
            print(colored(f"No news found for {args.crypto}.", "yellow"))
            return

        descriptions = []
        for articles in news:
            summary_text = article.get('summary', '')
            if summary_text:
                descriptions.append(summary_text)

        print(colored(f"Number of articles being summarized: {len(descriptions)}", 'magenta'))

        if descriptions:
            print(colored("Summarizing, please wait...", 'yellow'))
            summary = summarize(descriptions)
        else:
            summary = summarize(f"No news summaries found for {args.crypto}. Price is ${price}.")

        if "positive" in summary.lower():
            sentiment = "Positive"

        elif "negative" in summary.lower():
            sentiment = "Negative"

        else:
            sentiment = "Neutral"

        #replace with real db summary
        store_summary(args.crypto, summary, price, sentiment)
    
        color = 'green' if sentiment == "Positive" else 'red' if sentiment == "Negative" else 'yellow'
        print(colored(f"[{args.crypto}] {sentiment}\nSummary: {summary}\nPrice: ${price}", color))






 


