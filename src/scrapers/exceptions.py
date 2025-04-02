"""
Scraper exceptions module.
Custom exceptions for scraping errors.
"""


class ScraperError(Exception):
    """
    Base exception for all scraper errors.
    """
    pass


class RequestError(ScraperError):
    """
    Exception for request errors.
    """
    pass


class ParsingError(ScraperError):
    """
    Exception for HTML/XML parsing errors.
    """
    pass


class RateLimitError(RequestError):
    """
    Exception for rate limiting errors.
    """
    pass


class DataValidationError(ScraperError):
    """
    Exception for data validation errors.
    """
    pass


class ConfigurationError(ScraperError):
    """
    Exception for configuration errors.
    """
    pass


# For direct execution
if __name__ == '__main__':
    # Test exceptions
    try:
        raise RequestError("Failed to request URL: Connection refused")
    except ScraperError as e:
        print(f"Caught error: {type(e).__name__} - {e}")
    
    try:
        raise ParsingError("Failed to parse HTML: Invalid selector")
    except ScraperError as e:
        print(f"Caught error: {type(e).__name__} - {e}")
    
    try:
        raise RateLimitError("Rate limited by API. Retry after 60 seconds.")
    except ScraperError as e:
        print(f"Caught error: {type(e).__name__} - {e}")
    
    try:
        raise DataValidationError("Invalid stock price value: 'N/A'")
    except ScraperError as e:
        print(f"Caught error: {type(e).__name__} - {e}")
        
    try:
        raise ConfigurationError("Missing required configuration: 'api_key'")
    except ScraperError as e:
        print(f"Caught error: {type(e).__name__} - {e}")
    
    print("Exception tests completed successfully!")