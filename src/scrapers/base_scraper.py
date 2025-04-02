"""
Base scraper module.
Abstract base class for all scrapers.
"""

import logging
import time
import random
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import requests
from requests.exceptions import RequestException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .exceptions import ScraperError, RequestError, RateLimitError

#setup logger
logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """
    Abstract base class for all scrapers
    """

    def __init__(
        self,
        scraper_config: Dict[str, Any],
        user_agent: Optional[str] = None,
        proxies: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        retry_attempts: int = 3,
        min_delay: float = 1.0,
        max_delay: float = 5.0,
    ):
        """
        Initialize the base scraper.
        
        Args:
            scraper_config: Configuration for the scraper.
            user_agent: User agent string to use for requests.
            proxies: Dictionary of proxies to use for requests.
            timeout: Request timeout in seconds.
            retry_attempts: Number of retry attempts for failed requests.
            min_delay: Minimum delay between requests in seconds.
            max_delay: Maximum delay between requests in seconds.
        """
        self.config = scraper_config
        self.session = requests.Session()

        #self default headers
        if user_agent:
            self.session.headers.update({'User-Agent': user_agent})
        else:
            #use a realistic user agent if none provided
            default_ua = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
            self.session.headers.update({'User-Agent': default_ua})

        #set proxies if provided
        if proxies:
            self.session.proxies.update(proxies)

        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.min_delay = min_delay
        self.max_delay = max_delay

        #store start time and result for logging
        self.start_time = None
        self.results = []
        self.errors = []

    @retry(
        retry=retry_if_exception_type((RequestError,RateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1,min=2,max=30),
        reraise=True
    )
    def make_request(
        self,
        url:str,
        method:str = "GET",
        params:Optional[Dict[str,Any]]=None,
        data:Optional[Dict[str,Any]]=None,
        headers:Optional[Dict[str,str]]=None,
        cookies:Optional[Dict[str,str]]=None,
    )->requests.Response:
        """
        Make an HTTP request with error handling and retries.
        
        Args:
            url: URL to request.
            method: HTTP method to use ('GET', 'POST', etc.).
            params: URL parameters to include.
            data: Data to include in the request body.
            headers: Additional headers to include.
            cookies: Cookies to include.
            
        Returns:
            Response object.
            
        Raises:
            RequestError: If the request fails.
            RateLimitError: If rate limited by the server.
        """
        # Add jitter to reduce the chance of being detected as a bot
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                headers=headers,
                cookies=cookies,
                timeout=self.timeout
            )
            
            # Check for rate limiting
            if response.status_code == 429:
                # Extract retry-after header if present
                retry_after = response.headers.get('Retry-After')
                wait_time = int(retry_after) if retry_after and retry_after.isdigit() else 60
                
                logger.warning(f"Rate limited. Waiting {wait_time} seconds before retrying.")
                raise RateLimitError(f"Rate limited by {url}. Retry after {wait_time} seconds.")
            
            # Raise an exception for 4XX and 5XX status codes
            response.raise_for_status()
            
            return response
            
        except RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            raise RequestError(f"Failed to request {url}: {e}")
        
    @abstractmethod
    def scrape(self)->Tuple[List[Dict[str,Any]],List[Dict[str,Any]]]:
        """
        Scrape data from configured source.

        Returns:
            Tuple containing two lists:
            - First list contains dictionaries of scraped data.
            - Second list contains dictionaries of errors that occurred during scraping.
        """
        pass

    def run(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Run the scraper and return the results.
        
        Returns:
            Tuple containing:
                - List of dictionaries with scraped data
                - List of dictionaries with error information
        """
        self.start_time = datetime.now()
        self.results = []
        self.errors = []

        try:
            logger.info(f"Starting {self.__class__.__name__} scraper")
            results, errors = self.scrape()
            self.results = results
            self.errors = errors
            
            logger.info(f"Completed {self.__class__.__name__} scraper with {len(results)} results and {len(errors)} errors")
            return results, errors
            
        except ScraperError as e:
            logger.error(f"Scraper error: {e}")
            error_info = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'timestamp': datetime.utcnow()
            }
            self.errors.append(error_info)
            return [], self.errors
            
        except Exception as e:
            logger.exception(f"Unexpected error in {self.__class__.__name__} scraper: {e}")
            error_info = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'timestamp': datetime.utcnow()
            }
            self.errors.append(error_info)
            return [], self.errors

    def close(self):
        """
        Clean up resources used by the scraper.
        """
        self.session.close()
        logger.debug(f"Closed {self.__class__.__name__} scraper session")

