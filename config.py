import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EXPORTS_DIR = DATA_DIR / "exports"

DATA_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Database Settings
DATABASE_PATH = os.getenv("SCRAPER_DB_PATH", str(DATA_DIR / "scraper.db"))
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Celery & Broker Settings
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_TIMEZONE = os.getenv("CELERY_TIMEZONE", "UTC")

# Default periodic scrapers interval in seconds (for Celery beat or standalone scheduler)
DEFAULT_SCRAPE_INTERVAL_SECONDS = int(os.getenv("SCRAPE_INTERVAL_SECONDS", "3600"))

# Selenium Settings
SELENIUM_HEADLESS = os.getenv("SELENIUM_HEADLESS", "true").lower() in ("true", "1", "yes")
SELENIUM_PAGE_TIMEOUT = int(os.getenv("SELENIUM_PAGE_TIMEOUT", "20"))
SELENIUM_WINDOW_SIZE = os.getenv("SELENIUM_WINDOW_SIZE", "1920,1080")
USER_AGENT = os.getenv(
    "SCRAPER_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
