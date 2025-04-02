"""
Logging configuration module.
Sets up logging for the application.
"""

import os
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any


def setup_logging(config: Dict[str, Any]) -> None:
    """
    Set up logging based on configuration.
    
    Args:
        config: Logging configuration dictionary.
    """
    # Get configuration values
    log_level_str = config.get('level', 'INFO').upper()
    log_format = config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    date_format = config.get('date_format', '%Y-%m-%d %H:%M:%S')
    file_rotation = config.get('file_rotation', 'midnight')
    backup_count = config.get('backup_count', 7)
    
    # Convert log level string to logging constant
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).resolve().parent.parent.parent / 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a formatter
    formatter = logging.Formatter(log_format, date_format)
    
    # Set up the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Create file handler with rotation
    log_file = log_dir / 'scraper.log'
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_file,
        when=file_rotation,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Suppress verbose logging from some modules
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    # Log confirmation message
    logging.info(f"Logging configured with level {log_level_str}")


# For direct execution
if __name__ == '__main__':
    # Test configuration
    test_config = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'date_format': '%Y-%m-%d %H:%M:%S',
        'file_rotation': 'midnight',
        'backup_count': 7
    }
    
    # Setup logging
    setup_logging(test_config)
    
    # Test logging
    logger = logging.getLogger(__name__)
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    logger.critical("This is a CRITICAL message")
    
    print("Logging configuration test completed successfully!")
    print(f"Log file created at: {Path(__file__).resolve().parent.parent.parent / 'logs' / 'scraper.log'}")