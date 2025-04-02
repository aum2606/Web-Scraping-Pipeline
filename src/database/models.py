"""
Database models module.
Defines the data schema using SQLAlchemy ORM.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class StockPrice(Base):
    """
    Stock price data model.
    """
    __tablename__ = 'stock_prices'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False, index=True)
    price = Column(Float, nullable=False)
    change = Column(Float)
    change_percent = Column(Float)
    volume = Column(Integer)
    scrape_url = Column(String(255))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<StockPrice(symbol='{self.symbol}', price={self.price}, timestamp='{self.timestamp}')>"


class WeatherData(Base):
    """
    Weather data model.
    """
    __tablename__ = 'weather_data'
    
    id = Column(Integer, primary_key=True)
    city_name = Column(String(100), nullable=False, index=True)
    city_id = Column(Integer, nullable=False, index=True)
    temperature = Column(Float, nullable=False)
    feels_like = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Integer)
    cloudiness = Column(Float)
    weather_condition = Column(String(100))
    weather_description = Column(Text)
    weather_icon = Column(String(20))
    rain_1h = Column(Float)
    snow_1h = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    sunrise = Column(DateTime)
    sunset = Column(DateTime)
    timezone_offset = Column(Integer)
    
    def __repr__(self):
        return f"<WeatherData(city='{self.city_name}', temp={self.temperature}, timestamp='{self.timestamp}')>"


class ScraperLog(Base):
    """
    Scraper log data model to keep track of scraper runs.
    """
    __tablename__ = 'scraper_logs'
    
    id = Column(Integer, primary_key=True)
    scraper_type = Column(String(50), nullable=False, index=True)
    target = Column(String(100), nullable=False, index=True)
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime)
    success = Column(Boolean, default=False)
    records_scraped = Column(Integer, default=0)
    error_message = Column(Text)
    
    def __repr__(self):
        return f"<ScraperLog(type='{self.scraper_type}', target='{self.target}', success={self.success})>"


# For direct execution
if __name__ == '__main__':
    from sqlalchemy import create_engine
    
    # Create an in-memory SQLite database for testing
    engine = create_engine('sqlite:///:memory:')
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    print("Tables created successfully:")
    for table in Base.metadata.tables:
        print(f" - {table}")