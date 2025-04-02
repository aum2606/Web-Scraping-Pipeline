"""
Database connection module.
Handles database connection pooling and session management.
"""

import logging
from typing import Dict, Any
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

# Setup logger
logger = logging.getLogger(__name__)

# Global engine variable
_engine = None
Session = None

def get_connection_string(db_config:Dict[str,Any])->str:
    """
    Generate a connection string from databse configuration
    Args:
        db_config: Database configuration dictionary
    Returns:
        Databse connection string
    """
    db_type = db_config.get('type','postgresql')
    db_user = db_config.get('user','postgres')
    db_password = db_config.get('password','143aum')
    db_host = db_config.get('host','localhost')
    db_port = db_config.get('port',5432)
    db_name = db_config.get('name','scraper_db')

    return f"{db_type}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    

def get_engine(db_config:Dict[str,Any]=None, force_new:bool=False)->Engine:
    """
    Get or create an SQLAlchemy engine  with connection pooling
    Args:
        db_config: Database configuration dictionary
        force_new: If true, creates a new engine even if one already exists
    Returns:
        SQLAlchemy engine instance
    """
    global _engine,Session

    if _engine is None or force_new:
        if db_config is None:
            raise ValueError("Databse configuration is required to create a new engine")
        
        connection_string = get_connection_string(db_config)

        #create engine with connection pooling
        _engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            echo=False
        )
        #create session factory
        session_factory = sessionmaker(bind=_engine)
        Session = scoped_session(session_factory)
        
        logger.info(f"Created new database engine for {db_config.get('host')}:{db_config.get('port')}")
    
    return _engine


def close_engine() -> None:
    """
    Close the database engine and dispose of all connections.
    """
    global _engine, Session
    
    if _engine is not None:
        if Session is not None:
            Session.remove()
        _engine.dispose()
        _engine = None
        Session = None
        logger.info("Database engine closed and all connections disposed")


# For direct execution
if __name__ == '__main__':
    # Setup logging
    pass