"""
Stock scraper module.
Scrapes stock price data from Yahoo Finance.
"""

import logging
import re
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from bs4.element import Tag

from .base_scraper import BaseScraper
from .exceptions import ParsingError, ConfigurationError

# Setup logger
logger = logging.getLogger(__name__)

class StockScraper(BaseScraper):
    """
    Scraper for stock price data from Yahoo finance
    """
    def __init__(self, scraper_config: Dict[str, Any]):
        """
        Initialize the stock scraper.
        
        Args:
            scraper_config: Configuration for the stock scraper.
        """
        #validate configuration
        if 'urls' not in scraper_config:
            raise ConfigurationError("Stock scraper configuration must include 'urls")
        if 'selectors' not in scraper_config:
            raise ConfigurationError("Stock scraper configuration must include 'selectors'")

        #get user agent from config
        user_agent = scraper_config.get('headers',{}).get('User-Agent')

        super().__init__(scraper_config,user_agent=user_agent)

        #store selectors
        self.selectors = scraper_config['selectors']

    def _extract_symbol_from_url(self,url:str)->str:
        """
        Extract stock symbol from URL.

        Args:
            url: URL to extract symbol from.

        Returns:
            Stock symbol.
        """
        #extract symbol from URL pattern like https://finance.yahoo.com/quote/AAPL
        match = re.search(r"/quote/([A-Z0-9.-]+)", url)
        if match:
            return match.group(1)
        else:
            return "UNKNOWN"

    def _parse_numeric_value(self,value_text:str)->Optional[float]:
        """
        Parse numeric value from text.
        Args:
            value_text: Text to parse
        Returns:
            Parsed value as float, or None if parsing fails
        """
        if not value_text or value_text.strip() in ['N/A','-','']:
            return None
        
        # Remove characters like +, %, (, ), commas
        clean_text = re.sub(r'[+%(),]', '', value_text.strip())
        
        # Handle parentheses for negative numbers
        if clean_text.startswith('(') and clean_text.endswith(')'):
            clean_text = '-' + clean_text[1:-1]
        
        try:
            return float(clean_text)
        except ValueError:
            logger.warning(f"Failed to parse numeric value: {value_text}")
            return None
    

    def _parse_stock_data(self, html: str, url: str) -> Dict[str, Any]:
        """
        Parse stock data from HTML content.
        
        Args:
            html: HTML content from Yahoo Finance.
            url: URL that was scraped.
            
        Returns:
            Dictionary containing parsed stock data.
            
        Raises:
            ParsingError: If parsing fails.
        """
        try:
            soup = BeautifulSoup(html,'html.parser')

            #initialize result dictionary
            stock_data = {
                'symbol': self._extract_symbol_from_url(url),
                'scrape_url': url,
                'timestamp': datetime.utcnow()
            }
            #extract price data using selectors from config
            for field,selector in self.selectors.items():
                element = soup.select_one(selector)
                if element:
                    #get text value
                    value_text = element.get_text(strip=True)
                    #parse numeric value if possible
                    if field in ['price','change','change_percent','volume']:
                        parsed_value = self._parse_numeric_value(value_text)
                        stock_data[field] = parsed_value
                    else:
                        stock_data[field] = value_text
                else:
                    logger.warning(f"selector not found for {field}: {selector}")
                    stock_data[field] = None
            return stock_data
        
        except Exception as e:
            raise ParsingError(f"Error parsing stock data from {url}: {e}")
        
    def scrape(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Scrape stock price data from Yahoo Finance.
        
        Returns:
            Tuple containing:
                - List of dictionaries with stock data
                - List of dictionaries with error information
        """
        results = []
        errors = []
        for url in self.config['urls']:
            try:
                logger.info(f"Scraping stock data from {url}")

                #make request
                response = self.make_request(url)

                #parse stock data
                stock_data = self._parse_stock_data(response.text,url)

                #add to results
                results.append(stock_data)

                logger.info(f"Successfully scraped stock data from {url}")
            
            except Exception as e:
                logger.error(f"Error scraping stock data from {url}: {e}")

                #add to errors
                error_info = {
                    'url': url,
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'timestamp': datetime.utcnow()
                }
                errors.append(error_info)
        
        return results, errors


# For direct execution
if __name__ == '__main__':
    # import sys
    # import json
    
    # # Setup logging
    # logging.basicConfig(
    #     level=logging.INFO,
    #     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    # )
    
    # # Test configuration
    # test_config = {
    #     'urls': [
    #         'https://finance.yahoo.com/quote/AAPL',
    #         'https://finance.yahoo.com/quote/MSFT',
    #     ],
    #     'selectors': {
    #         'price': "fin-streamer[data-field='regularMarketPrice']",
    #         'change': "fin-streamer[data-field='regularMarketChange']",
    #         'change_percent': "fin-streamer[data-field='regularMarketChangePercent']",
    #         'volume': "fin-streamer[data-field='regularMarketVolume']",
    #     },
    #     'headers': {
    #         'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    #     }
    # }
    
    # try:
    #     # Create scraper
    #     scraper = StockScraper(test_config)
        
    #     # Run scraper
    #     results, errors = scraper.run()
        
    #     # Print results
    #     print(f"Scraped {len(results)} stocks:")
    #     for stock_data in results:
    #         print(f"  {stock_data['symbol']}: ${stock_data.get('price')} (Change: {stock_data.get('change')})")
        
    #     # Print errors
    #     if errors:
    #         print(f"Encountered {len(errors)} errors:")
    #         for error in errors:
    #             print(f"  {error['url']}: {error['error_type']} - {error['error_message']}")
        
    #     # Close scraper
    #     scraper.close()
        
    #     print("Stock scraper test completed successfully!")
        
    # except Exception as e:
    #     print(f"Error testing stock scraper: {e}")
    #     sys.exit(1)
    pass