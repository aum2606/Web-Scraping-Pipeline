"""
Weather scraper module.
Scrapes weather data from OpenWeatherMap API.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from .base_scraper import BaseScraper
from .exceptions import ConfigurationError, RequestError

# Setup logger
logger = logging.getLogger(__name__)

class WeatherScraper(BaseScraper):
    """
    Scraper for weather data from OpenWeatherMap API.
    """
    def __init__(self, scraper_config: Dict[str, Any]):
        """
        Initialize the weather scraper.

        Args:
            scraper_config: Configuration for the weather scraper.
        """
        #validate configuration
        if 'base_url' not in scraper_config:
            raise ConfigurationError("Weather scraper configuration must include 'base_url'")
        if 'cities' not in scraper_config:
            raise ConfigurationError("Weather scraper configuration must include 'cities'")
        if 'api_key' not in scraper_config:
            raise ConfigurationError("Weather scraper configuration must include 'api_key'")
        
        super().__init__(scraper_config)

        #staore API Key
        self.api_key = scraper_config['api_key']
        self.base_url = scraper_config['base_url']
        self.cities = scraper_config['cities']
        self.params = scraper_config.get('params',{})

        #store API key
        self.api_key = scraper_config['api_key']
        self.base_url = scraper_config['base_url']
        self.cities = scraper_config['cities']
        self.params = scraper_config.get('params',{})

    def _parse_weather_data(self, data: Dict[str, Any], city_name: str, city_id: int) -> Dict[str, Any]:
        """
        Parse weather data from API response.
        
        Args:
            data: Weather data from API response.
            city_name: Name of the city.
            city_id: ID of the city.
            
        Returns:
            Dictionary containing parsed weather data.
        """
        # Extract timezone offset
        timezone_offset = data.get('timezone', 0)
        
        # Extract main weather data
        main_data = data.get('main', {})
        
        # Extract wind data
        wind_data = data.get('wind', {})
        
        # Extract clouds data
        clouds_data = data.get('clouds', {})
        
        # Extract weather conditions
        weather_conditions = data.get('weather', [{}])[0] if data.get('weather') else {}
        
        # Extract rain data
        rain_data = data.get('rain', {})
        
        # Extract snow data
        snow_data = data.get('snow', {})
        
        # Extract sys data for sunrise/sunset
        sys_data = data.get('sys', {})
        
        # Convert sunrise/sunset timestamps to datetime objects
        sunrise = None
        sunset = None
        
        if 'sunrise' in sys_data:
            sunrise = datetime.utcfromtimestamp(sys_data['sunrise'])
        
        if 'sunset' in sys_data:
            sunset = datetime.utcfromtimestamp(sys_data['sunset'])
        
        # Create weather data dictionary
        weather_data = {
            'city_name': city_name,
            'city_id': city_id,
            'temperature': main_data.get('temp'),
            'feels_like': main_data.get('feels_like'),
            'humidity': main_data.get('humidity'),
            'pressure': main_data.get('pressure'),
            'wind_speed': wind_data.get('speed'),
            'wind_direction': wind_data.get('deg'),
            'cloudiness': clouds_data.get('all'),
            'weather_condition': weather_conditions.get('main'),
            'weather_description': weather_conditions.get('description'),
            'weather_icon': weather_conditions.get('icon'),
            'rain_1h': rain_data.get('1h'),
            'snow_1h': snow_data.get('1h'),
            'timestamp': datetime.utcnow(),
            'sunrise': sunrise,
            'sunset': sunset,
            'timezone_offset': timezone_offset
        }
        
        return weather_data
    
    def scrape(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Scrape weather data from OpenWeatherMap API.
        
        Returns:
            Tuple containing:
                - List of dictionaries with weather data
                - List of dictionaries with error information
        """
        results = []
        errors = []

        for city in self.cities:
            city_name = city['name']
            city_id = city['id']

            try:
                logger.info(f"Scrapping weather data for {city_name}")

                #prepare API parameters
                params = self.params.copy()
                params.update({
                    'id':city_id,
                    'appid':self.api_key
                })

                #make request
                response = self.make_request(self.base_url,params=params)

                #Parse JSON response
                weather_json = response.json()

                #check for API error
                if 'cod' in weather_json and weather_json['cod'] != 200:
                    error_msg = weather_json.get('message','Unknown API error')
                    raise RequestError(f"API request failed for {city_name}: {error_msg}")
            
                #parse weather data
                weather_data = self._parse_weather_data(weather_json,city_name,city_id)

                #add to results
                results.append(weather_data)

                logger.info(f"Successfully scraped weather data for {city_name}")
            
            except Exception as e:
                logger.error(f"Error scraping weather data for {city_name}: {e}")

                #add to errors
                error_info = {
                    'city_name': city_name,
                    'city_id': city_id,
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'timestamp': datetime.utcnow()
                }
                errors.append(error_info)
                    
        return results, errors


# For direct execution
if __name__ == '__main__':
    # import sys
    # import os
    # from dotenv import load_dotenv
    
    # # Load environment variables
    # load_dotenv()
    
    # # Setup logging
    # logging.basicConfig(
    #     level=logging.INFO,
    #     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    # )
    
    # # Get API key from environment
    # api_key = os.getenv('WEATHER_API_KEY')
    # if not api_key:
    #     print("Error: WEATHER_API_KEY environment variable not set")
    #     sys.exit(1)
    
    # # Test configuration
    # test_config = {
    #     'base_url': 'https://api.openweathermap.org/data/2.5/weather',
    #     'cities': [
    #         {'name': 'New York', 'id': 5128581},
    #         {'name': 'Los Angeles', 'id': 5368361},
    #     ],
    #     'params': {
    #         'units': 'metric',
    #     },
    #     'api_key': api_key
    # }
    
    # try:
    #     # Create scraper
    #     scraper = WeatherScraper(test_config)
        
    #     # Run scraper
    #     results, errors = scraper.run()
        
    #     # Print results
    #     print(f"Scraped weather data for {len(results)} cities:")
    #     for weather_data in results:
    #         print(f"  {weather_data['city_name']}: {weather_data.get('temperature')}°C, {weather_data.get('weather_condition')}")
        
    #     # Print errors
    #     if errors:
    #         print(f"Encountered {len(errors)} errors:")
    #         for error in errors:
    #             print(f"  {error['city_name']}: {error['error_type']} - {error['error_message']}")
        
    #     # Close scraper
    #     scraper.close()
        
    #     print("Weather scraper test completed successfully!")
        
    # except Exception as e:
    #     print(f"Error testing weather scraper: {e}")
    #     sys.exit(1)
    pass