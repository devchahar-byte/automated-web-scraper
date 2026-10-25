from celery import Celery
from celery.schedules import crontab
import config

app = Celery("web_scraper")

app.conf.update(
    broker_url=config.CELERY_BROKER_URL,
    result_backend=config.CELERY_RESULT_BACKEND,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=config.CELERY_TIMEZONE,
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    # Periodic schedule (Celery Beat)
    beat_schedule={
        "scrape-quotes-every-hour": {
            "task": "scraper.tasks.scrape_url_task",
            "schedule": float(config.DEFAULT_SCRAPE_INTERVAL_SECONDS),
            "args": ["https://quotes.toscrape.com/scroll", "ecommerce"],
            "kwargs": {
                "dynamic": True,
                "wait_for_selector": ".quote",
                "scroll_count": 2
            }
        },
        "scrape-books-every-day-midnight": {
            "task": "scraper.tasks.scrape_url_task",
            "schedule": crontab(hour=0, minute=0),
            "args": ["http://books.toscrape.com/", "ecommerce"],
            "kwargs": {
                "dynamic": True,
                "wait_for_selector": "article.product_pod"
            }
        }
    }
)

# Auto-discover tasks from scraper.tasks
app.autodiscover_tasks(["scraper"])
