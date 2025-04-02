"""
Scrapers package initialization.
"""

from .base_scraper import BaseScraper
from .stock_scraper import StockScraper
from .weather_scraper import WeatherScraper
from .exceptions import (
    ScraperError,
    RequestError,
    ParsingError,
    RateLimitError
)

__all__ = [
    'BaseScraper',
    'StockScraper',
    'WeatherScraper',
    'ScraperError',
    'RequestError',
    'ParsingError',
    'RateLimitError',
]