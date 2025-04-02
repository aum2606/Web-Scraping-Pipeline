"""
Configuration loader module.
Loads configuration from YAML config files and environment variables.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

class ConfigLoader:
    """
    Configuration loader class that handles loading and merging configuration
    from different sources
    """

    def __init__(self,config_path:str = None):
        """
        Initialize the config loader
        Args:
            config_path: Path to the configuration YAML file. If None, defaults to 'config/settings.yaml'.
        """

        #load enviroment variables from .env files
        load_dotenv()

        #set default config path if not provided
        if config_path is None:
            base_dir = Path(__file__).resolve().parent.parent
            config_path = base_dir / 'config' / 'settings.yaml'
        
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self)-> Dict[str,Any]:
        """
        Load configuration from YAML file
        Returns:
            dict: Merged configuration
        """
        try:
            with open(self.config_path,'r') as config_file:
                config = yaml.safe_load(config_file)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found at {self.config_path}")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing YAML file: {e}")

    def get_database_config(self)->Dict[str,Any]:
        """
        Get database configuration,with enviroment variables overriding YAML settings

        Returns:
            Dict containing databse configuration
        """        
        db_config = self.config.get('database',{})

        #override with enviroment variables if present
        db_config = self.config.get('database', {})
        
        # Override with environment variables if present
        db_config.update({
            'host': os.getenv('DB_HOST', db_config.get('host', 'localhost')),
            'port': int(os.getenv('DB_PORT', db_config.get('port', 5432))),
            'name': os.getenv('DB_NAME', db_config.get('name', 'scraper_db')),
            'user': os.getenv('DB_USER', db_config.get('user', 'postgres')),
            'password': os.getenv('DB_PASSWORD', db_config.get('password', '')),
        })
        
        return db_config

    def get_stock_scraper_config(self) -> Dict[str, Any]:
        """
        Get stock scraper configuration.
        
        Returns:
            Dict containing stock scraper configuration.
        """
        return self.config.get('stock_scraper', {})


    def get_weather_scraper_config(self) -> Dict[str, Any]:
        """
        Get weather scraper configuration.
        
        Returns:
            Dict containing weather scraper configuration.
        """
        weather_config = self.config.get('weather_scraper', {})
        
        # Add API key from environment
        weather_config['api_key'] = os.getenv('WEATHER_API_KEY', '')
        
        return weather_config
    

    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging configuration.
        
        Returns:
            Dict containing logging configuration.
        """
        log_config = self.config.get('logging', {})
        
        # Override with environment variable if present
        log_level = os.getenv('LOG_LEVEL')
        if log_level:
            log_config['level'] = log_level
        
        return log_config



# For direct execution
if __name__ == '__main__':
    # Test the config loader
    try:
        config_loader = ConfigLoader()
        print("Database config:", config_loader.get_database_config())
        print("Stock scraper config:", config_loader.get_stock_scraper_config())
        print("Weather scraper config:", config_loader.get_weather_scraper_config())
        print("Logging config:", config_loader.get_logging_config())
        print("Configuration loaded successfully!")
    except Exception as e:
        print(f"Error loading configuration: {e}")