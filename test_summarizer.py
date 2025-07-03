import unittest
from unittest.mock import patch, MagicMock
from summarizer import get_asset_name, fetch_stock_price, fetch_crypto_price, fetch_news

class TestSummarizer(unittest.TestCase):
    #Fake Data via patch and magicmok
    @patch('summarizer.yf.Ticker')
    def test_get_asset_name(self, mock_ticker):
        mock_ticker.return_value.info = {'shortName': 'Apple Inc.'}
        result = get_asset_name('AAPL')
        self.assertEqual(result, 'apple')

    @patch('summarizer.yf.Ticker')
    def test_fetch_stock_price(self, mock_ticker):
        mock_instance = MagicMock()
        mock_instance.history.return_value = {'Close': [123.45]}
        mock_ticker.return_value = mock_instance
        price = fetch_stock_price('AAPL')
        self.assertEqual(price, 123.45)

    @patch('summarizer.requests.get')
    def test_fetch_crypto_price(self, mock_get):
        mock_get.return_value.json.return_value = {'bitcoin': {'usd': 34000.50}}
        price = fetch_crypto_price('bitcoin')
        self.assertEqual(price, 34000.50)

    @patch('summarizer.requests.get')
    @patch('summarizer.get_asset_name')
    def test_fetch_news_crypto(self, mock_get_asset_name, mock_get):
        mock_get_asset_name.return_value = 'ethereum'
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {
                'headline': 'Ethereum upgrade released', #Mock data
                'summary': 'ETH 2.0 brings more scalability.', #Mock data
            },
            {
                'headline': 'Bitcoin spikes again', #Mock data
                'summary': 'But this is unrelated to ETH.', #Mock data
            }
        ]
        news = fetch_news('ETH', is_crypto=True)
        self.assertEqual(len(news), 1)  #1 article situation

if __name__ == '__main__':
    unittest.main()
