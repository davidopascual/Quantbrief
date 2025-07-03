import unittest
from unittest.mock import patch, MagicMock
import pandas as pd  # Needed for DataFrame mock

from summarizer import get_asset_name, fetch_stock_price, \
    fetch_crypto_price, fetch_news


class TestSummarizer(unittest.TestCase):
    @patch('summarizer.yf.Ticker')
    def test_get_asset_name(self, mock_ticker):
        mock_ticker.return_value.info = {'shortName': 'Apple Inc.'}
        result = get_asset_name('AAPL')
        self.assertEqual(result, 'apple')

    @patch('summarizer.yf.Ticker')
    def test_fetch_stock_price(self, mock_ticker):
        mock_instance = MagicMock()
        # Return a DataFrame with a 'Close' column
        mock_instance.history.return_value = pd.DataFrame({'Close': [123.45]})
        mock_ticker.return_value = mock_instance
        price = fetch_stock_price('AAPL')
        self.assertEqual(price, 123.45)

    @patch('summarizer.requests.get')
    @patch('summarizer.COINGECKO_COIN_LIST', None)
    def test_fetch_crypto_price(self, mock_get):
        mock_get.return_value.json.side_effect = [
            # This mocks the CoinGecko coin list
            {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
            {"id": "ethereum", "symbol": "eth", "name": "Ethereum"}
        ], \
            {   # This mocks the actual price response
                "bitcoin": {"usd": 34000.50}
            }
        price = fetch_crypto_price('bitcoin')
        self.assertEqual(price, 34000.50)

    @patch('summarizer.requests.get')
    @patch('summarizer.get_asset_name')
    def test_fetch_news_crypto(self, mock_get_asset_name, mock_get):
        mock_get_asset_name.return_value = 'ethereum'
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {
                'headline': 'Ethereum upgrade released',
                'summary': 'ETH 2.0 brings more scalability.',
            },
            {
                'headline': 'Bitcoin spikes again',
                'summary': 'BTC rises on ETF speculation.',
            }
        ]
        news = fetch_news('ETH', is_crypto=True)
        # Only the first article should match 'ETH' or 'ethereum'
        self.assertEqual(len(news), 1)


if __name__ == '__main__':
    unittest.main()
