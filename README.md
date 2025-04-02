# Web Scraping Pipeline

This project implements a data engineering pipeline that scrapes stock prices and weather data from public sources and stores them in a PostgreSQL database for analysis.

## Features

- Scrapes stock price data from Yahoo Finance
- Collects weather data from OpenWeatherMap API
- Stores data in a PostgreSQL database
- Configurable scraping intervals and target elements
- Containerized with Docker for easy deployment
- Comprehensive logging and error handling

## Project Structure

```
web-scraping-pipeline/
├── .env                    # Environment variables (DB credentials, API keys)
├── .gitignore              # Git ignore file
├── config/
│   └── settings.yaml       # Configuration (URLs, scrape intervals, target elements)
├── data/                   # For storing temporary files or local backups
├── docker-compose.yml      # For running services like DB and scraper app
├── Dockerfile              # For containerizing the scraper application
├── logs/                   # Directory for log files
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
├── src/                    # Main source code directory
│   ├── __init__.py
│   ├── config_loader.py    # Loads configuration from files/env vars
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py   # Handles DB connection pooling
│   │   ├── models.py       # Defines data schema (using SQLAlchemy ORM)
│   │   └── storage_manager.py # Handles data insertion, updates, schema creation
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base_scraper.py # Abstract base class for scrapers
│   │   ├── exceptions.py   # Custom exceptions for scraping errors
│   │   ├── stock_scraper.py  # Specific scraper for stock data
│   │   └── weather_scraper.py # Specific scraper for weather data
│   ├── pipelines/          # Data processing steps (cleaning, validation)
│   │   ├── __init__.py
│   │   └── validation.py   # Data validation logic
│   ├── utils/              # Utility functions (e.g., logging setup, date helpers)
│   │   ├── __init__.py
│   │   └── logging_config.py
│   └── main.py             # Entry point to run the scraping process
└── tests/                  # Unit and integration tests
    ├── __init__.py
    ├── test_database.py
    └── test_scrapers.py
```

## Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose (optional, for containerized deployment)
- PostgreSQL (if running without Docker)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/aum2606/web-scraping-pipeline.git
   cd web-scraping-pipeline
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on the example and update the values:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and API keys
   ```

## Running the Application

### Using Python directly

1. Make sure PostgreSQL is running and accessible with the credentials in your `.env` file.
2. Run the application:
   ```bash
   python -m src.main
   ```

### Using Docker Compose

1. Start the services:
   ```bash
   docker-compose up -d
   ```

2. View logs:
   ```bash
   docker-compose logs -f scraper
   ```

3. Stop the services:
   ```bash
   docker-compose down
   ```

## Configuration

The application can be configured using the `config/settings.yaml` file and environment variables in the `.env` file.

### settings.yaml

- Configure scraping sources, intervals, and selectors
- Adjust database settings
- Modify logging preferences

### .env

- Set database connection details
- Add API keys for external services
- Configure logging level

## Testing

Run the tests using:

```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.