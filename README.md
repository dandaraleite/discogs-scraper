# Discogs Scraper

A Python web scraper for collecting music artist and album data from Discogs, with a focus on specific genres. This project uses Selenium for web scraping and provides a complete pipeline for data collection and processing.

## Install (local development on Linux)
1. **Install `uv` (project dependency manager)**
Follow the installation instructions:
[Install uv](https://docs.astral.sh/uv/getting-started/installation/)
<br>

2. **Create and activate a virtual environment**
```bash
uv sync (It installs the dependencies and also creates the .venv file.)
source .venv/bin/activate
```


## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Dependencies](#dependencies)
- [Usage](#usage)
  - [Basic Usage](#basic-usage)
  - [Configuration](#configuration)
  - [Example Workflow](#example-workflow)
- [Running Tests](#running-tests)
- [Build Guide](#build-guide)
- [Contributing](#contributing)

## Features

- **Genre-based Artist Scraping**: Retrieve artist URLs from Discogs genre pages (Most Collected, Top Artists, Early Masters, etc.)
- **Artist Data Extraction**: Collect detailed information about artists including biographies, member information, and discography
- **Album Data Collection**: Scrape album information for each artist, including titles, release years, and metadata
- **Web Driver Management**: Automatic browser driver management using webdriver-manager
- **Data Persistence**: Save scraped data to JSONL format for easy processing and analysis
- **Error Handling**: Robust error handling and retry mechanisms
- **Rate Limiting**: Built-in delays to respect Discogs rate limits
- **Cookie Management**: Automatic cookie rejection for cleaner scraping sessions

## Requirements

- **Python**: 3.12 or higher
- **Operating System**: Linux, macOS, or Windows with Chrome/Chromium browser installed
- **Internet Connection**: Required for accessing Discogs

## Usage

### Basic Usage

#### 1. Simple Script Execution

Create a Python script to run the scraper:
```
python rock_genre/pipeline_runner.py
```

## Development Practices and Linting

### Run tests / coverage
Run unit tests and coverage (configured in `pytest.ini`):
```bash
pytest
```

## Linters, type-check and pre-commit:
- Run all hooks locally:
```bash
pre-commit run --all-files
```

## Author
Dandara Leite <dandaraleite2@gmail.com>

## Additional Resources

- [Discogs API Documentation](https://www.discogs.com/developers/)
- [Selenium Documentation](https://www.selenium.dev/documentation/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)


---
