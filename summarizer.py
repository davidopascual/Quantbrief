import argparse
from termcolor import colored
import yfinance as yf
import requests
import google.generativeai as genai
from datetime import datetime, timedelta, timezone
from db import Session, Summary
import os 
from dotenv import load_dotenv

load_dotenv()
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
FINNHUB_COMPANY_NEWS_URL = os.getenv('FINNHUB_COMPANY_NEWS_URL')
FINNHUB_CRYPTO_NEWS_URL = os.getenv('FINNHUB_CRYPTO_NEWS_URL')
COINGECKO_API_URL = os.getenv('COINGECKO_API_URL')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')


def fetch_news(ticker, is_crypto=False):
    ticker_lower = ticker.lower()
    if is_crypto:
        params = {
            'category': 'crypto',
            'token': FINNHUB_API_KEY
        }
        response = requests.get(FINNHUB_CRYPTO_NEWS_URL, params=params)

        if response.status_code != 200:
            print(colored(f"Finnhub Crypto News API error: {response.status_code} - {response.text}", 'red'))
            return []

        data = response.json()
        relevant_articles = []

        for article in data:
            combined_text = article.get('headline', '').lower() + article.get('summary', '').lower()
            if ticker_lower in combined_text:
                if (article.get('headline', '').lower().find(ticker_lower) < 100 or
                        article.get('summary', '').lower().find(ticker_lower) < 100):
                    relevant_articles.append(article)
            if len(relevant_articles) == 3:
                break

        return relevant_articles

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

        if response.status_code != 200:
            print(colored(f"Finnhub Company News API error: {response.status_code} - {response.text}", 'red'))
            return []

        data = response.json()
        relevant_articles = []

        for article in data:
            combined_text = article.get('headline', '').lower() + article.get('summary', '').lower()
            if ticker_lower in combined_text:
                if (article.get('headline', '').lower().find(ticker_lower) < 100 or
                        article.get('summary', '').lower().find(ticker_lower) < 100):
                    relevant_articles.append(article)
            if len(relevant_articles) == 3:
                break

        return relevant_articles


def fetch_crypto_price(crypto):
    response = requests.get(COINGECKO_API_URL, params={'ids': crypto, 'vs_currencies': 'usd'})
    return response.json().get(crypto, {}).get('usd', 'N/A')


def fetch_stock_price(ticker):
    stock = yf.Ticker(ticker)
    return stock.history(period='1d')['Close'].iloc[-1]


def summarize_with_gemini(texts):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

    if isinstance(texts, str):
        texts = [texts]

    prompt = """
You are a financial news summarizer. Given the following news articles, provide a concise summary, overall sentiment (Positive/Negative/Neutral), and a suggested action for a retail trader. Format:
Summary: ...
Sentiment: ...
Action: ...

Articles:
"""

    for i, t in enumerate(texts):
        prompt += f"Article {i + 1}: {t}\n"

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Summary unavailable. Error: {e}"


def store_summary_sqlalchemy(ticker, summary, price, sentiment):
    session = Session()
    new_summary = Summary(
        ticker=ticker,
        summary=summary,
        price=price,
        sentiment=sentiment,
        timestamp=datetime.now(timezone.utc)
    )
    session.add(new_summary)
    session.commit()
    session.close()


def view_history_sqlalchemy():
    session = Session()
    records = session.query(Summary).order_by(Summary.timestamp.desc()).all()
    session.close()
    return records


def main():
    parser = argparse.ArgumentParser(description='QuantBrief: AI Financial News Summarizer')
    parser.add_argument('--ticker', type=str, help='Stock ticker symbol')
    parser.add_argument('--crypto', type=str, help='Cryptocurrency name')
    parser.add_argument('--history', action='store_true', help='View summary history')
    args = parser.parse_args()

    if args.history:
        history = view_history_sqlalchemy()
        for record in history:
            print(
                colored(
                    f"[{record.ticker}] {record.sentiment}\nSummary: {record.summary}\nPrice: ${record.price}\nTimestamp: {record.timestamp}",
                    'cyan'
                )
            )

    elif args.ticker:
        print(colored("Fetching news...", 'cyan'))
        news = fetch_news(args.ticker, is_crypto=False)

        print(colored("Fetching price...", 'cyan'))
        price = fetch_stock_price(args.ticker)

        if not news:
            print(colored(f"No news found for {args.ticker}.", 'yellow'))
            return

        descriptions = []
        for article in news:
            summary_text = article.get('summary', '')
            if summary_text:
                descriptions.append(summary_text)

        print(colored(f"Number of articles being summarized: {len(descriptions)}", 'magenta'))

        if descriptions:
            print(colored("Summarizing, please wait...", 'yellow'))
            summary = summarize_with_gemini(descriptions)
        else:
            summary = summarize_with_gemini(f"No news summaries found for {args.ticker}. Price is ${price}.")

        if "Positive" in summary:
            sentiment = "Positive"
        elif "Negative" in summary:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        store_summary_sqlalchemy(args.ticker, summary, price, sentiment)

        color = 'green' if sentiment == "Positive" else ('red' if sentiment == "Negative" else 'yellow')
        print(colored(f"[{args.ticker}] {sentiment}\nSummary: {summary}\nPrice: ${price}", color))

    elif args.crypto:
        print(colored("Fetching price...", 'cyan'))
        price = fetch_crypto_price(args.crypto)

        print(colored("Fetching news...", 'cyan'))
        news = fetch_news(args.crypto, is_crypto=True)

        descriptions = []
        for article in news:
            summary_text = article.get('summary', '')
            if summary_text:
                descriptions.append(summary_text)

        print(colored(f"Number of articles being summarized: {len(descriptions)}", 'magenta'))

        if descriptions:
            print(colored("Summarizing, please wait...", 'yellow'))
            summary = summarize_with_gemini(descriptions)
        else:
            summary = summarize_with_gemini(f"Price of {args.crypto} is ${price}")

        summary_lower = summary.lower()
        if "positive" in summary_lower:
            sentiment = "Positive"
        elif "negative" in summary_lower:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        store_summary_sqlalchemy(args.crypto, summary, price, sentiment)

        color = 'green' if sentiment == "Positive" else ('red' if sentiment == "Negative" else 'yellow')
        print(colored(f"[{args.crypto}] {sentiment}\nSummary: {summary}\nPrice: ${price}", color))


if __name__ == '__main__':
    main()