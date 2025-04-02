"""
Data validation module.
Validates and cleans scraped data before storage.
"""

import logging
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator, ValidationError

# Setup logger
logger = logging.getLogger(__name__)


class StockDataModel(BaseModel):
    """
    Pydantic model for stock data validation.
    """
    symbol: str
    price: float
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    scrape_url: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v
    
    @validator('symbol')
    def symbol_must_be_valid(cls, v):
        if not v or len(v) > 10:
            raise ValueError('Symbol must be non-empty and <= 10 characters')
        return v


class WeatherDataModel(BaseModel):
    """
    Pydantic model for weather data validation.
    """
    city_name: str
    city_id: int
    temperature: float
    feels_like: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[int] = None
    cloudiness: Optional[float] = None
    weather_condition: Optional[str] = None
    weather_description: Optional[str] = None
    weather_icon: Optional[str] = None
    rain_1h: Optional[float] = None
    snow_1h: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sunrise: Optional[datetime] = None
    sunset: Optional[datetime] = None
    timezone_offset: Optional[int] = None
    
    @validator('temperature')
    def temperature_must_be_in_range(cls, v):
        # Reasonable range check for temperatures in Celsius
        if v < -100 or v > 100:
            raise ValueError('Temperature must be between -100 and 100 Celsius')
        return v
    
    @validator('city_name')
    def city_name_must_be_valid(cls, v):
        if not v or len(v) > 100:
            raise ValueError('City name must be non-empty and <= 100 characters')
        return v


class DataValidator:
    """
    Validator class for scraped data.
    """
    
    def __init__(self):
        """
        Initialize the data validator.
        """
        self.validation_models = {
            'stock': StockDataModel,
            'weather': WeatherDataModel
        }
    
    def validate_stock_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate stock data.
        
        Args:
            data: List of stock data dictionaries.
            
        Returns:
            List of validated and cleaned stock data dictionaries.
        """
        return self._validate_data(data, 'stock')
    
    def validate_weather_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate weather data.
        
        Args:
            data: List of weather data dictionaries.
            
        Returns:
            List of validated and cleaned weather data dictionaries.
        """
        return self._validate_data(data, 'weather')
    
    def _validate_data(self, data: List[Dict[str, Any]], data_type: str) -> List[Dict[str, Any]]:
        """
        Generic method to validate data using the appropriate model.
        
        Args:
            data: List of data dictionaries.
            data_type: Type of data ('stock' or 'weather').
            
        Returns:
            List of validated and cleaned data dictionaries.
        """
        if not data:
            return []
        
        if data_type not in self.validation_models:
            raise ValueError(f"Unknown data type: {data_type}")
        
        model = self.validation_models[data_type]
        validated_data = []
        
        for item in data:
            try:
                # Validate using the model
                validated_item = model(**item)
                
                # Convert back to dictionary
                validated_data.append(validated_item.dict())
                
            except ValidationError as e:
                # Log validation error
                logger.warning(f"Validation error for {data_type} data: {e}")
                
                # We could also choose to include invalid data with a flag,
                # but for now we'll just skip it
                continue
        
        return validated_data


# For direct execution
if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create validator
    validator = DataValidator()
    
    # Test with valid stock data
    valid_stock_data = [
        {
            'symbol': 'AAPL',
            'price': 150.25,
            'change': 2.75,
            'change_percent': 1.85,
            'volume': 65000000,
            'scrape_url': 'https://finance.yahoo.com/quote/AAPL',
            'timestamp': datetime.utcnow()
        }
    ]
    
    # Test with invalid stock data
    invalid_stock_data = [
        {
            'symbol': 'AAPL',
            'price': -10.0,  # Invalid negative price
            'scrape_url': 'https://finance.yahoo.com/quote/AAPL'
        }
    ]
    
    # Test with valid weather data
    valid_weather_data = [
        {
            'city_name': 'New York',
            'city_id': 5128581,
            'temperature': 22.5,
            'feels_like': 23.1,
            'humidity': 65.0,
            'timestamp': datetime.utcnow()
        }
    ]
    
    # Test with invalid weather data
    invalid_weather_data = [
        {
            'city_name': 'New York',
            'city_id': 5128581,
            'temperature': 150.0,  # Invalid temperature
            'timestamp': datetime.utcnow()
        }
    ]
    
    # Validate data
    validated_stock = validator.validate_stock_data(valid_stock_data)
    invalid_stock = validator.validate_stock_data(invalid_stock_data)
    
    validated_weather = validator.validate_weather_data(valid_weather_data)
    invalid_weather = validator.validate_weather_data(invalid_weather_data)
    
    # Print results
    print(f"Valid stock data: {len(validated_stock)} of {len(valid_stock_data)} passed validation")
    print(f"Invalid stock data: {len(invalid_stock)} of {len(invalid_stock_data)} passed validation")
    
    print(f"Valid weather data: {len(validated_weather)} of {len(valid_weather_data)} passed validation")
    print(f"Invalid weather data: {len(invalid_weather)} of {len(invalid_weather_data)} passed validation")
    
    print("Data validator tests completed successfully!")