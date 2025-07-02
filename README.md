# QuantBrief - AI Financial News Summarizer

**QuantBrief** is a command-line application that summarizes recent financial news from the last 7 days using AI. It fetches real-time data for stocks and cryptocurrencies, summarizes up to 3 relevant articles using Google Gemini, and stores insights with sentiment and price data in a local database using SQLAlchemy.

---

## Table of Contents

* [General Info](#general-info)
* [Technologies](#technologies)
* [Setup](#setup)
* [Usage](#usage)

---

## General Info

QuantBrief helps beginner investors and traders stay informed by providing short, AI-generated summaries of financial news for a given stock or crypto asset. It also tracks prices and sentiment for historical insight.

---

## Technologies

Project is created with:

- Python
- [Finnhub API](https://finnhub.io)
- [Google Gemini](https://ai.google.dev/)
- [Coingecko API](https://www.coingecko.com/)
- SQLAlchemy
- YFinance
- Termcolor
- dotenv

---

## Setup

1. Clone the repository

2. Create and activate a virtual enviroment(avoids version conflicts):
'''
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
'''

3. Install dependencies:
'''
pip install -r requirements.txt
'''

4. Create a .env file in the root directory and fill FinnHub and Gemini portion with your API information:
'''
FINNHUB_API_KEY=your_finnhub_key
GEMINI_API_KEY=your_gemini_key
FINNHUB_COMPANY_NEWS_URL=https://finnhub.io/api/v1/company-news
FINNHUB_CRYPTO_NEWS_URL=https://finnhub.io/api/v1/news
COINGECKO_API_URL=https://api.coingecko.com/api/v3/simple/price
'''

---

## Usage
'''
Get Stock Summary: python3 summarizer.py --ticker MSFT

Get Crypto Summary: python3 summarizer.py --crypto BTC

View Summary History: python3 summarizer.py --history
'''
