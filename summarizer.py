import argparse
from datetime import datetime, timedelta, timezone
import os
import requests

import google.generativeai as genai
import yfinance as yf
from dotenv import load_dotenv
from termcolor import colored

from db import Session, Summary


load_dotenv()
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
FINNHUB_COMPANY_NEWS_URL = os.getenv('FINNHUB_COMPANY_NEWS_URL')
FINNHUB_CRYPTO_NEWS_URL = os.getenv('FINNHUB_CRYPTO_NEWS_URL')
COINGECKO_API_URL = os.getenv('COINGECKO_API_URL')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# FIX: Initialize COINGECKO_COIN_LIST at the global scope
COINGECKO_COIN_LIST = None


def get_asset_name(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info.get('shortName', '').split()[0].lower()
    except Exception:
        return ''


def fetch_news(ticker, is_crypto=False):
    ticker_lower = ticker.lower()
    asset_name = get_asset_name(ticker)

    if is_crypto:
        params = {
            'category': 'crypto',
            'token': FINNHUB_API_KEY
        }
        response = requests.get(FINNHUB_CRYPTO_NEWS_URL, params=params)

        if response.status_code != 200:
            print(
                colored(
                    f"Finnhub Crypto News API error: {response.status_code} "
                    f"- {response.text}",
                    'red'
                )
            )
            return []

        data = response.json()
        relevant_articles = []

        for article in data:
            headline = article.get('headline', '').lower()
            summary = article.get('summary', '').lower()
            if (
                ticker_lower in headline or asset_name in headline or
                ticker_lower in summary or asset_name in summary
            ):
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
            print(
                colored(
                    f"Finnhub Company News API error: {response.status_code} "
                    f"- {response.text}",
                    'red'
                )
            )
            return []

        data = response.json()
        relevant_articles = []

        for article in data:
            headline = article.get('headline', '').lower()
            summary = article.get('summary', '').lower()
            if (
                ticker_lower in headline or asset_name in headline or
                ticker_lower in summary or asset_name in summary
            ):
                relevant_articles.append(article)
            if len(relevant_articles) == 3:
                break

        return relevant_articles


def get_coingecko_id(crypto):
    global COINGECKO_COIN_LIST
    if COINGECKO_COIN_LIST is None:
        try:
            print(colored("Fetching crypto ID list from CoinGecko...", "cyan"))
            resp = requests.get("https://api.coingecko.com/api/v3/coins/list")
            COINGECKO_COIN_LIST = resp.json()
        except Exception as e:
            print(
                colored(f"Error fetching CoinGecko coin list: {e}", "red")
            )
            return None

    crypto_lower = crypto.lower()
    for coin in COINGECKO_COIN_LIST:
        if (
            coin["id"].lower() == crypto_lower or
            coin["symbol"].lower() == crypto_lower or
            coin["name"].lower() == crypto_lower
        ):
            return coin["id"]
    return None


def fetch_crypto_price(crypto):
    crypto_id = get_coingecko_id(crypto)
    if not crypto_id:
        print(
            colored(
                f"Unable to find matching CoinGecko ID for '{crypto}'",
                'red'
            )
        )
        return None

    try:
        response = requests.get(
            COINGECKO_API_URL,
            params={'ids': crypto_id, 'vs_currencies': 'usd'}
        )
        data = response.json()
        price = data.get(crypto_id, {}).get('usd')
        return float(price) if price is not None else None
    except Exception as e:
        print(
            colored(f"Error fetching crypto price for {crypto}: {e}", 'red')
        )
        return None


def fetch_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        return float(stock.history(period='1d')['Close'].iloc[-1])
    except Exception:
        return None


def summarize_with_gemini(texts):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

    if isinstance(texts, str):
        texts = [texts]

    # Fixed the indentation of the prompt string
    prompt = """
You are a financial news summarizer.
Given the following news
articles, provide a concise summary,
overall sentiment (Positive/Negative/Neutral),
and a suggested action for a retail trader. Format:
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
    try:
        price_value = float(price)
    except (TypeError, ValueError):
        price_value = None

    if price_value is None:
        print(
            colored("Skipping database insert due to missing price.", "red")
        )
        return

    new_summary = Summary(
        ticker=ticker,
        summary=summary,
        price=price_value,
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
    parser = argparse.ArgumentParser(
        description='QuantBrief: AI Financial News Summarizer'
    )
    parser.add_argument('--ticker', type=str, help='Stock ticker symbol')
    parser.add_argument('--crypto', type=str, help='Cryptocurrency name')
    parser.add_argument('--history', action='store_true',
                        help='View summary history')
    args = parser.parse_args()

    if args.history:
        history = view_history_sqlalchemy()
        for record in history:
            print(
                colored(
                    f"[{record.ticker}] {record.sentiment}\n"
                    f"Summary: {record.summary}\n"
                    f"Price: ${record.price}\n"
                    f"Timestamp: {record.timestamp}",
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

        descriptions = [
            article.get('summary', '')
            for article in news if article.get('summary', '')
        ]

        print(
            colored(
                f"Number of articles being summarized: {len(descriptions)}",
                'magenta'
            )
        )

        if descriptions:
            print(colored("Summarizing, please wait...", 'yellow'))
            summary = summarize_with_gemini(descriptions)
        else:
            summary = summarize_with_gemini(
                f"No news found for {args.ticker}. Price is ${price}."
            )

        summary_lower = summary.lower()
        if "positive" in summary_lower:
            sentiment = "Positive"
        elif "negative" in summary_lower:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        store_summary_sqlalchemy(args.ticker, summary, price, sentiment)

        color = 'green' if sentiment == "Positive" else (
            'red' if sentiment == "Negative" else 'yellow'
        )
        # FIX: Added print for summary and formatted for PEP 8 compliance
        print(colored(f"[{args.ticker}] {sentiment}", color))
        print(colored(f"Summary: {summary}", color))
        print(colored(f"Price: ${price}", color))

    elif args.crypto:
        print(colored("Fetching price...", 'cyan'))
        price = fetch_crypto_price(args.crypto)

        print(colored("Fetching news...", 'cyan'))
        news = fetch_news(args.crypto, is_crypto=True)

        descriptions = [
            article.get('summary', '')
            for article in news if article.get('summary', '')
        ]

        print(
            colored(
                f"Number of articles being summarized: {len(descriptions)}",
                'magenta'
            )
        )

        if descriptions:
            print(colored("Summarizing, please wait...", 'yellow'))
            summary = summarize_with_gemini(descriptions)
        else:
            summary = summarize_with_gemini(
                f"Price of {args.crypto} is ${price}"
            )

        summary_lower = summary.lower()
        if "positive" in summary_lower:
            sentiment = "Positive"
        elif "negative" in summary_lower:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        store_summary_sqlalchemy(args.crypto, summary, price, sentiment)

        color = 'green' if sentiment == "Positive" else (
            'red' if sentiment == "Negative" else 'yellow'
        )
        print(
            colored(
                f"[{args.crypto}] {sentiment}\n"
                f"Summary: {summary}\n"
                f"Price: ${price}",
                color
            )
        )


if __name__ == '__main__':
    main()
