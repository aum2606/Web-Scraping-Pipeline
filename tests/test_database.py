"""
Database tests.
"""

import unittest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from database.models import Base, StockPrice, WeatherData, ScraperLog
from database.storage_manager import StorageManager


class TestDatabaseModels(unittest.TestCase):
    """
    Test database models.
    """
    
    def setUp(self):
        """
        Set up test database.
        """
        # Create an in-memory SQLite database for testing
        self.engine = create_engine('sqlite:///:memory:')
        
        # Create all tables
        Base.metadata.create_all(self.engine)
        
        # Create a session
        self.session = sessionmaker(bind=self.engine)()
    
    def tearDown(self):
        """
        Tear down test database.
        """
        self.session.close()
    
    def test_stock_price_model(self):
        """
        Test StockPrice model.
        """
        # Create a stock price
        stock = StockPrice(
            symbol='AAPL',
            price=150.25,
            change=2.75,
            change_percent=1.85,
            volume=65000000,
            scrape_url='https://finance.yahoo.com/quote/AAPL',
            timestamp=datetime.utcnow()
        )
        
        # Add to session
        self.session.add(stock)
        self.session.commit()
        
        # Query for the stock
        queried_stock = self.session.query(StockPrice).filter_by(symbol='AAPL').first()
        
        # Check values
        self.assertEqual(queried_stock.symbol, 'AAPL')
        self.assertEqual(queried_stock.price, 150.25)
        self.assertEqual(queried_stock.change, 2.75)
        self.assertEqual(queried_stock.change_percent, 1.85)
        self.assertEqual(queried_stock.volume, 65000000)
        self.assertEqual(queried_stock.scrape_url, 'https://finance.yahoo.com/quote/AAPL')
    
    def test_weather_data_model(self):
        """
        Test WeatherData model.
        """
        # Create a weather data
        weather = WeatherData(
            city_name='New York',
            city_id=5128581,
            temperature=22.5,
            feels_like=23.1,
            humidity=65.0,
            pressure=1013.0,
            wind_speed=5.2,
            wind_direction=180,
            cloudiness=75.0,
            weather_condition='Clouds',
            weather_description='broken clouds',
            weather_icon='04d',
            timestamp=datetime.utcnow()
        )
        
        # Add to session
        self.session.add(weather)
        self.session.commit()
        
        # Query for the weather
        queried_weather = self.session.query(WeatherData).filter_by(city_id=5128581).first()
        
        # Check values
        self.assertEqual(queried_weather.city_name, 'New York')
        self.assertEqual(queried_weather.city_id, 5128581)
        self.assertEqual(queried_weather.temperature, 22.5)
        self.assertEqual(queried_weather.feels_like, 23.1)
        self.assertEqual(queried_weather.humidity, 65.0)
        self.assertEqual(queried_weather.weather_condition, 'Clouds')
    
    def test_scraper_log_model(self):
        """
        Test ScraperLog model.
        """
        # Create a scraper log
        log = ScraperLog(
            scraper_type='stock',
            target='yahoo_finance',
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            success=True,
            records_scraped=10
        )
        
        # Add to session
        self.session.add(log)
        self.session.commit()
        
        # Query for the log
        queried_log = self.session.query(ScraperLog).filter_by(scraper_type='stock').first()
        
        # Check values
        self.assertEqual(queried_log.scraper_type, 'stock')
        self.assertEqual(queried_log.target, 'yahoo_finance')
        self.assertEqual(queried_log.success, True)
        self.assertEqual(queried_log.records_scraped, 10)


class TestStorageManager(unittest.TestCase):
    """
    Test storage manager.
    """
    
    def setUp(self):
        """
        Set up test database and storage manager.
        """
        # Create an in-memory SQLite database for testing
        self.engine = create_engine('sqlite:///:memory:')
        
        # Create all tables
        Base.metadata.create_all(self.engine)
        
        # Create a session factory
        session_factory = sessionmaker(bind=self.engine)
        self.Session = session_factory
        
        # Create storage manager
        self.storage_manager = StorageManager({'batch_size': 10})
        
        # Monkey patch the Session attribute in the storage manager
        # This is a bit of a hack, but it allows us to use an in-memory database for testing
        import src.database.connection
        src.database.connection.Session = session_factory
    
    def tearDown(self):
        """
        Tear down test database.
        """
        pass
    
    def test_save_stock_data(self):
        """
        Test saving stock data.
        """
        # Create sample stock data
        stock_data = [
            {
                'symbol': 'AAPL',
                'price': 150.25,
                'change': 2.75,
                'change_percent': 1.85,
                'volume': 65000000,
                'scrape_url': 'https://finance.yahoo.com/quote/AAPL',
                'timestamp': datetime.utcnow()
            },
            {
                'symbol': 'MSFT',
                'price': 290.50,
                'change': -1.25,
                'change_percent': -0.43,
                'volume': 32000000,
                'scrape_url': 'https://finance.yahoo.com/quote/MSFT',
                'timestamp': datetime.utcnow()
            }
        ]
        
        # Save stock data
        saved_count = self.storage_manager.save_stock_data(stock_data)
        
        # Check that all records were saved
        self.assertEqual(saved_count, 2)
        
        # Query for the stocks
        session = self.Session()
        aapl = session.query(StockPrice).filter_by(symbol='AAPL').first()
        msft = session.query(StockPrice).filter_by(symbol='MSFT').first()
        session.close()
        
        # Check values
        self.assertEqual(aapl.price, 150.25)
        self.assertEqual(msft.price, 290.50)
    
    def test_save_weather_data(self):
        """
        Test saving weather data.
        """
        # Create sample weather data
        weather_data = [
            {
                'city_name': 'New York',
                'city_id': 5128581,
                'temperature': 22.5,
                'feels_like': 23.1,
                'humidity': 65.0,
                'pressure': 1013.0,
                'timestamp': datetime.utcnow()
            }
        ]
        
        # Save weather data
        saved_count = self.storage_manager.save_weather_data(weather_data)
        
        # Check that all records were saved
        self.assertEqual(saved_count, 1)
        
        # Query for the weather
        session = self.Session()
        ny = session.query(WeatherData).filter_by(city_id=5128581).first()
        session.close()
        
        # Check values
        self.assertEqual(ny.city_name, 'New York')
        self.assertEqual(ny.temperature, 22.5)
    
    def test_log_scraper_run(self):
        """
        Test logging scraper run.
        """
        # Log a scraper run
        log_id = self.storage_manager.log_scraper_run(
            'test',
            'test_target',
            datetime.utcnow(),
            True,
            10
        )
        
        # Check that log was created
        self.assertIsNotNone(log_id)
        
        # Query for the log
        session = self.Session()
        log = session.query(ScraperLog).filter_by(id=log_id).first()
        session.close()
        
        # Check values
        self.assertEqual(log.scraper_type, 'test')
        self.assertEqual(log.target, 'test_target')
        self.assertEqual(log.success, True)
        self.assertEqual(log.records_scraped, 10)


if __name__ == '__main__':
    unittest.main()