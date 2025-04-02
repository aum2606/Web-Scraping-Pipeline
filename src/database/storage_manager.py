"""
Storage manager module.
Handles data insertion, updates, and schema creation.
"""

import logging
from typing import List, Dict, Any, Type, Optional
from datetime import datetime
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect, text
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from .connection import Session
from .models import Base, StockPrice, WeatherData, ScraperLog

# Setup logger
logger = logging.getLogger(__name__)

class StorageManager:
    """
    Storage manager class that handles databse operations
    """

    def __init__(self,db_config:Dict[str,Any]):
        """
        Initialize the storage manager
        Args:
            db_config: Databse configuration dictionary
        """
        self.db_config = db_config
        self.batch_size = db_config.get('batch_size',100)
        self.retry_attempts = db_config.get('retry_attempts',3)
        self.retry_delay = db_config.get('retry_delay',5)

        
    def create_tables(self,engine):
        """
        Create all databse defined in models
        Args:
            engine: SQLAlchemy engine instance
        """
        try:
            Base.metadata.create_all(engine)
            logger.info("All tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error creating tables: {e}")
            raise

    @retry(
        retry=retry_if_exception_type(SQLAlchemyError),
        stop=stop_after_attempt(3),
        wait=wait_fixed(5),
        reraise=True
    )
    def save_stock_data(self,stock_data:List[Dict[str,Any]])->int:
        """
        Save stock data to the databse
        Args:
            stock_data: List of dictionaries containing stock data
        Returns:
            Number of records inserted
        """        
        return self._save_data(StockPrice,stock_data)
    
    @retry(
        retry=retry_if_exception_type(SQLAlchemyError),
        stop=stop_after_attempt(3),
        wait=wait_fixed(5),
        reraise=True
    )
    def save_weather_data(self, weather_data: List[Dict[str, Any]]) -> int:
        """
        Save weather data to the database.
        
        Args:
            weather_data: List of dictionaries containing weather data.
            
        Returns:
            Number of records inserted.
        """
        return self._save_data(WeatherData, weather_data)

    def _save_data(self, model_class: Type[DeclarativeMeta], data_list: List[Dict[str, Any]]) -> int:
        """
        Generic method to save data to the database.
        
        Args:
            model_class: SQLAlchemy model class.
            data_list: List of dictionaries containing data.
            
        Returns:
            Number of records inserted.
        """
        if not data_list:
            logger.warning(f"No data to save for {model_class.__name__}")
            return 0
        
        session = Session()

        try:
            total_records = 0

            #process in batches to avoid large transaction
            for i in range(0,len(data_list),self.batch_size):
                batch = data_list[i:i + self.batch_size]
                model_objects = [model_class(**item) for item in batch]

                session.add_all(model_objects)
                session.commit()
                
                total_records += len(batch)
                logger.debug(f"Commited batch of {len(batch)} {model_class.__name__} records")

            logger.info(f"Successfully saved {total_records} {model_class.__name__} records")
            return total_records
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error saving {model_class.__name__}: {e}")
            raise
        finally:
            session.close()

    def log_scraper_run(
        self,
        scraper_type: str,
        target: str,
        start_time: Optional[datetime] = None,
        success: bool = False,
        records_scraped: int = 0,
        error_message: str = None
    ) -> int:
        """
        Log a scraper run to the database.
        
        Args:
            scraper_type: Type of scraper (e.g., 'stock', 'weather').
            target: Target being scraped (e.g., 'AAPL', 'New York').
            start_time: Start time of the scraper run.
            success: Whether the scraper run was successful.
            records_scraped: Number of records scraped.
            error_message: Error message if the scraper run failed.
            
        Returns:
            ID of the log entry.
        """
        session = Session()
        try:
            #if no start time provided, use current time
            if start_time is None:
                start_time = datetime.utcnow()

            #create log entry
            log_entry = ScraperLog(
                scraper_type=scraper_type,
                target=target,
                start_time=start_time,
                end_time=datetime.utcnow(),
                success=success,
                records_scraped=records_scraped,
                error_message=error_message
            )
            session.add(log_entry)
            session.commit()

            logger.info(f"Successfully logged scraper run for {scraper_type} on {target}")
            return log_entry.id
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error logging scraper run: {e}")
            return None
        finally:
            session.close()

    def execute_raw_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute a raw SQL query and return the results.
        
        Args:
            query: SQL query string.
            params: Query parameters.
            
        Returns:
            List of dictionaries containing query results.
        """
        session = Session()
        try:
            result = session.execute(text(query),params or {})

            #convert result to list of dictionaries
            columns = result.key()
            return [dict(zip(columns, row)) for row in result.fetchall()]
        except SQLAlchemyError as e:
            logger.error(f"Error executing raw query: {e}")
            raise
        finally:
            session.close()

            
    

     
# For direct execution
if __name__ == '__main__':
    import sys
    from sqlalchemy import create_engine
    from datetime import datetime, timedelta
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create an in-memory SQLite database for testing
    engine = create_engine('sqlite:///:memory:')
    
    # Create tables
    Base.metadata.create_all(engine)
    
    # Create a session factory
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.orm import scoped_session
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    
    # Create storage manager
    storage_manager = StorageManager({'batch_size': 10})
    
    # Test with sample data
    sample_stock_data = [
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
    
    sample_weather_data = [
        {
            'city_name': 'New York',
            'city_id': 5128581,
            'temperature': 22.5,
            'feels_like': 23.1,
            'humidity': 65.0,
            'pressure': 1013.0,
            'wind_speed': 5.2,
            'wind_direction': 180,
            'cloudiness': 75.0,
            'weather_condition': 'Clouds',
            'weather_description': 'broken clouds',
            'weather_icon': '04d',
            'timestamp': datetime.utcnow(),
            'sunrise': datetime.utcnow() - timedelta(hours=6),
            'sunset': datetime.utcnow() + timedelta(hours=6)
        }
    ]
    
    try:
        # Save sample data
        stock_count = storage_manager.save_stock_data(sample_stock_data)
        weather_count = storage_manager.save_weather_data(sample_weather_data)
        log_id = storage_manager.log_scraper_run('test', 'test', success=True, records_scraped=stock_count + weather_count)
        
        print(f"Inserted {stock_count} stock records and {weather_count} weather records")
        print(f"Created log entry with ID: {log_id}")
        
        # Query data
        result = storage_manager.execute_raw_query("SELECT * FROM stock_prices")
        print(f"Stock Prices: {result}")
        
        result = storage_manager.execute_raw_query("SELECT * FROM weather_data")
        print(f"Weather Data: {result}")
        
        result = storage_manager.execute_raw_query("SELECT * FROM scraper_logs")
        print(f"Scraper Logs: {result}")
        
        print("Storage manager tests completed successfully!")
        
    except Exception as e:
        print(f"Error testing storage manager: {e}")
        sys.exit(1)