"""
Scraper tests.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

import requests
import responses

from scrapers.stock_scraper import StockScraper
from scrapers.weather_scraper import WeatherScraper
from scrapers.exceptions import RequestError, ParsingError, RateLimitError


class TestStockScraper(unittest.TestCase):
    """
    Test the StockScraper class.
    """
    
    def setUp(self):
        """
        Set up test environment.
        """
        # Test configuration
        self.config = {
            'urls': [
                'https://finance.yahoo.com/quote/AAPL',
                'https://finance.yahoo.com/quote/MSFT',
            ],
            'selectors': {
                'price': "fin-streamer[data-field='regularMarketPrice']",
                'change': "fin-streamer[data-field='regularMarketChange']",
                'change_percent': "fin-streamer[data-field='regularMarketChangePercent']",
                'volume': "fin-streamer[data-field='regularMarketVolume']",
            },
            'headers': {
                'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        }
    
    @responses.activate
    def test_scrape_success(self):
        """
        Test successful scraping.
        """
        # Mock HTML response for AAPL
        aapl_html = """
        <html>
            <body>
                <fin-streamer data-field="regularMarketPrice">150.25</fin-streamer>
                <fin-streamer data-field="regularMarketChange">2.75</fin-streamer>
                <fin-streamer data-field="regularMarketChangePercent">1.85%</fin-streamer>
                <fin-streamer data-field="regularMarketVolume">65000000</fin-streamer>
            </body>
        </html>
        """
        
        # Mock HTML response for MSFT
        msft_html = """
        <html>
            <body>
                <fin-streamer data-field="regularMarketPrice">290.50</fin-streamer>
                <fin-streamer data-field="regularMarketChange">-1.25</fin-streamer>
                <fin-streamer data-field="regularMarketChangePercent">-0.43%</fin-streamer>
                <fin-streamer data-field="regularMarketVolume">32000000</fin-streamer>
            </body>
        </html>
        """
        
        # Add mock responses
        responses.add(
            responses.GET,
            'https://finance.yahoo.com/quote/AAPL',
            body=aapl_html,
            status=200,
            content_type='text/html'
        )
        responses.add(
            responses.GET,
            'https://finance.yahoo.com/quote/MSFT',
            body=msft_html,
            status=200,
            content_type='text/html'
        )
        
        # Create scraper
        scraper = StockScraper(self.config)
        
        # Run scraper
        results, errors = scraper.run()
        
        # Check results
        self.assertEqual(len(results), 2)
        self.assertEqual(len(errors), 0)
        
        # Check AAPL data
        aapl_data = next(item for item in results if item['symbol'] == 'AAPL')
        self.assertEqual(aapl_data['price'], 150.25)
        self.assertEqual(aapl_data['change'], 2.75)
        self.assertEqual(aapl_data['change_percent'], 1.85)
        self.assertEqual(aapl_data['volume'], 65000000)
        
        # Check MSFT data
        msft_data = next(item for item in results if item['symbol'] == 'MSFT')
        self.assertEqual(msft_data['price'], 290.50)
        self.assertEqual(msft_data['change'], -1.25)
        self.assertEqual(msft_data['change_percent'], -0.43)
        self.assertEqual(msft_data['volume'], 32000000)
    
    @responses.activate
    def test_scrape_error(self):
        """
        Test scraping error.
        """
        # Add mock responses
        responses.add(
            responses.GET,
            'https://finance.yahoo.com/quote/AAPL',
            status=404
        )
        responses.add(
            responses.GET,
            'https://finance.yahoo.com/quote/MSFT',
            body="Internal Server Error",
            status=500
        )
        
        # Create scraper
        scraper = StockScraper(self.config)
        
        # Run scraper
        results, errors = scraper.run()
        
        # Check results
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 2)
        
        # Check error types
        error_urls = [error['url'] for error in errors]
        self.assertIn('https://finance.yahoo.com/quote/AAPL', error_urls)
        self.assertIn('https://finance.yahoo.com/quote/MSFT', error_urls)
    
    @responses.activate
    def test_rate_limit(self):
        """
        Test rate limiting.
        """
        # Add mock responses
        responses.add(
            responses.GET,
            'https://finance.yahoo.com/quote/AAPL',
            status=429,
            headers={'Retry-After': '60'}
        )
        
        # Create scraper with only one retry
        scraper = StockScraper({**self.config, 'urls': ['https://finance.yahoo.com/quote/AAPL']})
        scraper.retry_attempts = 1
        
        # Run scraper
        results, errors = scraper.run()
        
        # Check results
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        
        # Check error type
        self.assertEqual(errors[0]['error_type'], 'RateLimitError')
    
    def test_extract_symbol(self):
        """
        Test symbol extraction from URL.
        """
        scraper = StockScraper(self.config)
        
        # Test standard URL
        symbol = scraper._extract_symbol_from_url('https://finance.yahoo.com/quote/AAPL')
        self.assertEqual(symbol, 'AAPL')
        
        # Test URL with additional path
        symbol = scraper._extract_symbol_from_url('https://finance.yahoo.com/quote/AAPL/history')
        self.assertEqual(symbol, 'AAPL')
        
        # Test URL with query string
        symbol = scraper._extract_symbol_from_url('https://finance.yahoo.com/quote/AAPL?p=AAPL')
        self.assertEqual(symbol, 'AAPL')
        
        # Test invalid URL
        symbol = scraper._extract_symbol_from_url('https://finance.yahoo.com/invalid')
        self.assertEqual(symbol, 'UNKNOWN')
    
    def test_parse_numeric_value(self):
        """
        Test numeric value parsing.
        """
        scraper = StockScraper(self.config)
        
        # Test standard number
        value = scraper._parse_numeric_value('123.45')
        self.assertEqual(value, 123.45)
        
        # Test number with plus sign
        value = scraper._parse_numeric_value('+2.75')
        self.assertEqual(value, 2.75)
        
        # Test negative number
        value = scraper._parse_numeric_value('-1.25')
        self.assertEqual(value, -1.25)
        
        # Test number with percentage
        value = scraper._parse_numeric_value('1.85%')
        self.assertEqual(value, 1.85)
        
        # Test number with parentheses (negative)
        value = scraper._parse_numeric_value('(0.43)')
        self.assertEqual(value, -0.43)
        
        # Test number with comma
        value = scraper._parse_numeric_value('65,000,000')
        self.assertEqual(value, 65000000)
        
        # Test empty value
        value = scraper._parse_numeric_value('')
        self.assertIsNone(value)
        
        # Test N/A value
        value = scraper._parse_numeric_value('N/A')
        self.assertIsNone(value)


class TestWeatherScraper(unittest.TestCase):
    """
    Test the WeatherScraper class.
    """
    
    def setUp(self):
        """
        Set up test environment.
        """
        # Test configuration
        self.config = {
            'base_url': 'https://api.openweathermap.org/data/2.5/weather',
            'cities': [
                {'name': 'New York', 'id': 5128581},
                {'name': 'Los Angeles', 'id': 5368361},
            ],
            'params': {
                'units': 'metric',
            },
            'api_key': 'test_api_key'
        }
        
        # Sample API response for New York
        self.ny_response = {
            "coord": {"lon": -74.0060, "lat": 40.7143},
            "weather": [
                {
                    "id": 804,
                    "main": "Clouds",
                    "description": "overcast clouds",
                    "icon": "04d"
                }
            ],
            "base": "stations",
            "main": {
                "temp": 22.5,
                "feels_like": 23.1,
                "temp_min": 20.2,
                "temp_max": 24.9,
                "pressure": 1013,
                "humidity": 65
            },
            "visibility": 10000,
            "wind": {
                "speed": 5.2,
                "deg": 180
            },
            "clouds": {
                "all": 75
            },
            "dt": 1631619600,
            "sys": {
                "type": 1,
                "id": 4610,
                "country": "US",
                "sunrise": 1631614455,
                "sunset": 1631659284
            },
            "timezone": -14400,
            "id": 5128581,
            "name": "New York",
            "cod": 200
        }
        
        # Sample API response for Los Angeles
        self.la_response = {
            "coord": {"lon": -118.2437, "lat": 34.0522},
            "weather": [
                {
                    "id": 800,
                    "main": "Clear",
                    "description": "clear sky",
                    "icon": "01d"
                }
            ],
            "base": "stations",
            "main": {
                "temp": 28.9,
                "feels_like": 29.3,
                "temp_min": 25.1,
                "temp_max": 32.2,
                "pressure": 1015,
                "humidity": 45
            },
            "visibility": 10000,
            "wind": {
                "speed": 3.1,
                "deg": 240
            },
            "clouds": {
                "all": 0
            },
            "dt": 1631619600,
            "sys": {
                "type": 1,
                "id": 3694,
                "country": "US",
                "sunrise": 1631622511,
                "sunset": 1631667267
            },
            "timezone": -25200,
            "id": 5368361,
            "name": "Los Angeles",
            "cod": 200
        }
    
    @responses.activate
    def test_scrape_success(self):
        """
        Test successful scraping.
        """
        # Add mock responses
        responses.add(
            responses.GET,
            'https://api.openweathermap.org/data/2.5/weather',
            json=self.ny_response,
            status=200,
            match=[
                responses.matchers.query_param_matcher({
                    'id': '5128581',
                    'appid': 'test_api_key',
                    'units': 'metric'
                })
            ]
        )
        responses.add(
            responses.GET,
            'https://api.openweathermap.org/data/2.5/weather',
            json=self.la_response,
            status=200,
            match=[
                responses.matchers.query_param_matcher({
                    'id': '5368361',
                    'appid': 'test_api_key',
                    'units': 'metric'
                })
            ]
        )
        
        # Create scraper
        scraper = WeatherScraper(self.config)
        
        # Run scraper
        results, errors = scraper.run()
        
        # Check results
        self.assertEqual(len(results), 2)
        self.assertEqual(len(errors), 0)
        
        # Check New York data
        ny_data = next(item for item in results if item['city_id'] == 5128581)
        self.assertEqual(ny_data['city_name'], 'New York')
        self.assertEqual(ny_data['temperature'], 22.5)
        self.assertEqual(ny_data['feels_like'], 23.1)
        self.assertEqual(ny_data['humidity'], 65)
        self.assertEqual(ny_data['weather_condition'], 'Clouds')
        
        # Check Los Angeles data
        la_data = next(item for item in results if item['city_id'] == 5368361)
        self.assertEqual(la_data['city_name'], 'Los Angeles')
        self.assertEqual(la_data['temperature'], 28.9)
        self.assertEqual(la_data['feels_like'], 29.3)
        self.assertEqual(la_data['humidity'], 45)
        self.assertEqual(la_data['weather_condition'], 'Clear')
    
    @responses.activate
    def test_api_error(self):
        """
        Test API error.
        """
        # Add mock response for API error
        responses.add(
            responses.GET,
            'https://api.openweathermap.org/data/2.5/weather',
            json={"cod": 401, "message": "Invalid API key"},
            status=401,
            match=[
                responses.matchers.query_param_matcher({
                    'id': '5128581',
                    'appid': 'test_api_key',
                    'units': 'metric'
                })
            ]
        )
        
        # Create scraper with only one city
        scraper = WeatherScraper({**self.config, 'cities': [{'name': 'New York', 'id': 5128581}]})
        
        # Run scraper
        results, errors = scraper.run()
        
        # Check results
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        
        # Check error
        self.assertEqual(errors[0]['city_name'], 'New York')
        self.assertEqual(errors[0]['error_type'], 'RequestError')
    
    @responses.activate
    def test_parse_weather_data(self):
        """
        Test weather data parsing.
        """
        # Create scraper
        scraper = WeatherScraper(self.config)
        
        # Parse New York data
        weather_data = scraper._parse_weather_data(self.ny_response, 'New York', 5128581)
        
        # Check parsed data
        self.assertEqual(weather_data['city_name'], 'New York')
        self.assertEqual(weather_data['city_id'], 5128581)
        self.assertEqual(weather_data['temperature'], 22.5)
        self.assertEqual(weather_data['feels_like'], 23.1)
        self.assertEqual(weather_data['humidity'], 65)
        self.assertEqual(weather_data['pressure'], 1013)
        self.assertEqual(weather_data['wind_speed'], 5.2)
        self.assertEqual(weather_data['wind_direction'], 180)
        self.assertEqual(weather_data['cloudiness'], 75)
        self.assertEqual(weather_data['weather_condition'], 'Clouds')
        self.assertEqual(weather_data['weather_description'], 'overcast clouds')
        self.assertEqual(weather_data['weather_icon'], '04d')
        self.assertEqual(weather_data['timezone_offset'], -14400)
        
        # Check datetime fields
        self.assertIsInstance(weather_data['timestamp'], datetime)
        self.assertIsInstance(weather_data['sunrise'], datetime)
        self.assertIsInstance(weather_data['sunset'], datetime)


if __name__ == '__main__':
    unittest.main()