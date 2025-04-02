"""
Main entry point for the web scraping pipeline application.
"""

import sys
import time
import logging
import schedule
from datetime import datetime
from typing import Dict, Any, List

from .config_loader import ConfigLoader
from .utils.logging_config import setup_logging
from .database.connection import get_engine, close_engine
from .database.storage_manager import StorageManager
from .database.models import Base
from .scrapers.stock_scraper import StockScraper
from .scrapers.weather_scraper import WeatherScraper
from .pipelines.validation import DataValidator


class ScraperApp:
    """
    Main scraper application class.
    """
    
    def __init__(self, skip_db=False):
        """
        Initialize the scraper application.
        
        Args:
            skip_db: If True, skip database initialization (for testing or when DB is unavailable)
        """
        # Load configuration
        self.config_loader = ConfigLoader()
        
        # Set up logging
        log_config = self.config_loader.get_logging_config()
        setup_logging(log_config)
        self.logger = logging.getLogger(__name__)
        
        self.db_initialized = False
        self.engine = None
        self.storage_manager = None
        
        if not skip_db:
            try:
                # Initialize database
                db_config = self.config_loader.get_database_config()
                self.engine = get_engine(db_config)
                
                # Create tables if they don't exist
                Base.metadata.create_all(self.engine)
                
                # Try to create storage manager
                try:
                    # Create storage manager
                    self.storage_manager = StorageManager(db_config)
                    
                    # Test the storage manager by calling a simple method
                    try:
                        # Just a simple test to make sure storage_manager's Session is working
                        self.storage_manager.execute_raw_query("SELECT 1")
                        self.db_initialized = True
                        self.logger.info("Database connection established and tested successfully")
                    except Exception as test_err:
                        self.logger.error(f"Failed to test storage manager: {test_err}")
                        self.logger.warning("Database connection succeeded but storage manager test failed")
                        self.storage_manager = None
                except Exception as sm_err:
                    self.logger.error(f"Failed to create storage manager: {sm_err}")
                    self.logger.warning("Running in DB-less mode. Data will not be persisted.")
            except Exception as e:
                self.logger.error(f"Failed to initialize database: {e}")
                self.logger.warning("Running in DB-less mode. Data will not be persisted.")
        else:
            self.logger.info("Database initialization skipped as requested")
        
        # Create data validator (doesn't require DB)
        self.validator = DataValidator()
        
        self.logger.info("Scraper application initialized")
    
    def run_stock_scraper(self):
        """
        Run the stock scraper.
        """
        try:
            self.logger.info("Starting stock scraper run")
            
            # Get stock scraper configuration
            stock_config = self.config_loader.get_stock_scraper_config()
            
            # Create and run stock scraper
            scraper = StockScraper(stock_config)
            start_time = datetime.utcnow()
            stock_data, errors = scraper.run()
            
            # Validate stock data
            validated_data = self.validator.validate_stock_data(stock_data)
            
            # Only attempt to save data if database is initialized and storage manager exists
            if self.db_initialized and self.storage_manager is not None:
                try:
                    # Log scraper run
                    success = len(errors) == 0
                    self.storage_manager.log_scraper_run(
                        'stock',
                        'yahoo_finance',
                        start_time,
                        success,
                        len(stock_data),
                        str(errors) if errors else None
                    )
                    
                    if validated_data:
                        # Save stock data to database
                        saved_count = self.storage_manager.save_stock_data(validated_data)
                        self.logger.info(f"Saved {saved_count} stock records to database")
                    else:
                        self.logger.warning("No valid stock data to save")
                except Exception as db_err:
                    self.logger.error(f"Database error: {db_err}")
                    self.logger.warning("Continuing in DB-less mode for this run")
                    self.db_initialized = False  # Mark as not initialized for future runs
                    
                    # Fall through to DB-less mode below
            
            # If we get here with db_initialized False (either initially or after an error),
            # just log the data without saving to DB
            if not self.db_initialized or self.storage_manager is None:
                self.logger.info(f"Scraped {len(stock_data)} stock records (not saved to database)")
                if validated_data:
                    for data in validated_data[:3]:  # Show first 3 records as sample
                        self.logger.info(f"Sample data: {data['symbol']} - ${data.get('price')} (Change: {data.get('change')})")
                    if len(validated_data) > 3:
                        self.logger.info(f"... and {len(validated_data) - 3} more records")
            
            # Close scraper
            scraper.close()
            
            self.logger.info("Completed stock scraper run")
            
        except Exception as e:
            self.logger.exception(f"Error running stock scraper: {e}")
    
    def run_weather_scraper(self):
        """
        Run the weather scraper.
        """
        try:
            self.logger.info("Starting weather scraper run")
            
            # Get weather scraper configuration
            weather_config = self.config_loader.get_weather_scraper_config()
            
            # Create and run weather scraper
            scraper = WeatherScraper(weather_config)
            start_time = datetime.utcnow()
            weather_data, errors = scraper.run()
            
            # Validate weather data
            validated_data = self.validator.validate_weather_data(weather_data)
            
            # Only attempt to save data if database is initialized and storage manager exists
            if self.db_initialized and self.storage_manager is not None:
                try:
                    # Log scraper run
                    success = len(errors) == 0
                    self.storage_manager.log_scraper_run(
                        'weather',
                        'openweathermap',
                        start_time,
                        success,
                        len(weather_data),
                        str(errors) if errors else None
                    )
                    
                    if validated_data:
                        # Save weather data to database
                        saved_count = self.storage_manager.save_weather_data(validated_data)
                        self.logger.info(f"Saved {saved_count} weather records to database")
                    else:
                        self.logger.warning("No valid weather data to save")
                except Exception as db_err:
                    self.logger.error(f"Database error: {db_err}")
                    self.logger.warning("Continuing in DB-less mode for this run")
                    self.db_initialized = False  # Mark as not initialized for future runs
                    
                    # Fall through to DB-less mode below
            
            # If we get here with db_initialized False (either initially or after an error),
            # just log the data without saving to DB
            if not self.db_initialized or self.storage_manager is None:
                self.logger.info(f"Scraped {len(weather_data)} weather records (not saved to database)")
                if validated_data:
                    for data in validated_data[:3]:  # Show first 3 records as sample
                        self.logger.info(f"Sample data: {data['city_name']} - {data.get('temperature')}°C, {data.get('weather_condition')}")
                    if len(validated_data) > 3:
                        self.logger.info(f"... and {len(validated_data) - 3} more records")
            
            # Close scraper
            scraper.close()
            
            self.logger.info("Completed weather scraper run")
            
        except Exception as e:
            self.logger.exception(f"Error running weather scraper: {e}")
    
    def schedule_scrapers(self):
        """
        Schedule scrapers to run at regular intervals.
        """
        # Get scraper configurations
        stock_config = self.config_loader.get_stock_scraper_config()
        weather_config = self.config_loader.get_weather_scraper_config()
        
        # Get intervals in seconds
        stock_interval = stock_config.get('interval_seconds', 3600)  # Default 1 hour
        weather_interval = weather_config.get('interval_seconds', 7200)  # Default 2 hours
        
        # Schedule stock scraper
        stock_minutes = max(1, stock_interval // 60)
        schedule.every(stock_minutes).minutes.do(self.run_stock_scraper)
        self.logger.info(f"Scheduled stock scraper to run every {stock_minutes} minutes")
        
        # Schedule weather scraper
        weather_minutes = max(1, weather_interval // 60)
        schedule.every(weather_minutes).minutes.do(self.run_weather_scraper)
        self.logger.info(f"Scheduled weather scraper to run every {weather_minutes} minutes")
    
    def run(self, run_immediately=True, use_scheduler=True):
        """
        Run the scraper application.
        
        Args:
            run_immediately: Whether to run scrapers immediately.
            use_scheduler: Whether to use the scheduler for recurring scraper runs.
        """
        try:
            self.logger.info("Starting scraper application")
            
            # Run scrapers immediately if requested
            if run_immediately:
                self.run_stock_scraper()
                self.run_weather_scraper()
            
            # Schedule scrapers if requested
            if use_scheduler:
                self.schedule_scrapers()
                
                # Run scheduler loop
                self.logger.info("Entering scheduler loop")
                while True:
                    schedule.run_pending()
                    time.sleep(1)
            
        except KeyboardInterrupt:
            self.logger.info("Scraper application stopped by user")
        except Exception as e:
            self.logger.exception(f"Error running scraper application: {e}")
        finally:
            # Clean up resources
            self.cleanup()
            self.logger.info("Scraper application shutdown complete")
    
    def cleanup(self):
        """
        Clean up resources.
        """
        if self.db_initialized:
            close_engine()
            self.logger.info("Database resources cleaned up")
        self.logger.info("All resources cleaned up")


def main():
    """
    Main function to run the scraper application.
    """
    try:
        # First try with database
        app = ScraperApp()
        if not app.db_initialized:
            print("\nWARNING: Database connection failed or Session test failed. Running in DB-less mode.")
            print("Check your PostgreSQL connection and credentials in .env file.")
            print("Common issues:")
            print("  1. PostgreSQL service might not be running")
            print("  2. Incorrect username/password in .env file")
            print("  3. Database might not exist")
            print("  4. SQLAlchemy Session configuration issue")
            print("\nContinuing without database persistence...\n")
        
        try:
            app.run(run_immediately=True, use_scheduler=True)
        except KeyboardInterrupt:
            print("\nStopping application...")
        finally:
            app.cleanup()
    except Exception as e:
        print(f"\nCritical error starting application: {e}")
        print("Please check the logs for more information.")


if __name__ == '__main__':
    main()
