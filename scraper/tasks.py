import logging
from typing import Any, Dict, Optional
from scraper.celery_app import app
from scraper.database import (
    init_db,
    create_job,
    update_job_status,
    save_scraped_items
)
from scraper.engine import ScraperEngine

logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def scrape_url_task(
    self,
    url: str,
    parser_name: str = "generic",
    dynamic: bool = True,
    wait_for_selector: Optional[str] = None,
    scroll_count: int = 0,
    parser_kwargs: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Celery task that performs web scraping and persists collected data into SQLite.
    """
    init_db()
    job = create_job(target_url=url, parser_name=parser_name)
    job_id = job.id
    update_job_status(job_id, status="RUNNING")

    logger.info(f"Started scrape job #{job_id} for URL: {url} (dynamic={dynamic})")
    engine = ScraperEngine()

    try:
        items = engine.scrape_and_parse(
            url=url,
            parser_name=parser_name,
            dynamic=dynamic,
            wait_for_selector=wait_for_selector,
            scroll_count=scroll_count,
            parser_kwargs=parser_kwargs
        )

        saved_count = save_scraped_items(job_id=job_id, target_url=url, items=items)
        update_job_status(job_id, status="COMPLETED", items_count=saved_count)
        logger.info(f"Completed scrape job #{job_id}. Saved {saved_count} items.")

        return {
            "job_id": job_id,
            "status": "COMPLETED",
            "url": url,
            "items_count": saved_count
        }

    except Exception as exc:
        err_msg = str(exc)
        logger.error(f"Scrape job #{job_id} failed: {err_msg}", exc_info=True)
        update_job_status(job_id, status="FAILED", error_message=err_msg)
        # Attempt retry if Celery retry is configured
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {
            "job_id": job_id,
            "status": "FAILED",
            "url": url,
            "error": err_msg
        }


@app.task
def export_data_task(job_id: Optional[int] = None, export_format: str = "csv") -> str:
    """
    Celery task to export collected records to CSV or JSON.
    """
    from scraper.exporter import export_data
    return export_data(job_id=job_id, export_format=export_format)
