import logging
import time
from typing import Optional
import schedule
from scraper.engine import ScraperEngine
from scraper.database import (
    init_db,
    create_job,
    update_job_status,
    save_scraped_items
)
import config

logger = logging.getLogger(__name__)


def execute_scrape_job(
    url: str,
    parser_name: str = "generic",
    dynamic: bool = True,
    wait_for_selector: Optional[str] = None,
    scroll_count: int = 0
) -> None:
    """Execute a single scrape run directly and save results into SQLite."""
    init_db()
    job = create_job(target_url=url, parser_name=parser_name)
    update_job_status(job.id, status="RUNNING")
    print(f"\n[Scheduler] Running scheduled scrape for: {url} (Job #{job.id})...")

    try:
        engine = ScraperEngine()
        items = engine.scrape_and_parse(
            url=url,
            parser_name=parser_name,
            dynamic=dynamic,
            wait_for_selector=wait_for_selector,
            scroll_count=scroll_count
        )
        saved = save_scraped_items(job_id=job.id, target_url=url, items=items)
        update_job_status(job.id, status="COMPLETED", items_count=saved)
        print(f"[Scheduler] Successfully finished Job #{job.id}. Collected {saved} items.")
    except Exception as e:
        print(f"[Scheduler] Error executing job #{job.id}: {e}")
        update_job_status(job.id, status="FAILED", error_message=str(e))


def run_standalone_scheduler(
    url: str,
    interval_seconds: int = 60,
    parser_name: str = "generic",
    dynamic: bool = True,
    wait_for_selector: Optional[str] = None,
    scroll_count: int = 0
) -> None:
    """
    Runs an in-process standalone scheduler loop using 'schedule'.
    Does not require Redis or external task brokers.
    """
    print(f"=== Standalone Scraper Scheduler Started ===")
    print(f"Target URL: {url}")
    print(f"Interval: Every {interval_seconds} seconds")
    print(f"Engine: Dynamic={dynamic}, Parser={parser_name}")
    print(f"Press Ctrl+C to stop.\n")

    # Run immediately once on start
    execute_scrape_job(
        url=url,
        parser_name=parser_name,
        dynamic=dynamic,
        wait_for_selector=wait_for_selector,
        scroll_count=scroll_count
    )

    # Schedule recurring runs
    schedule.every(interval_seconds).seconds.do(
        execute_scrape_job,
        url=url,
        parser_name=parser_name,
        dynamic=dynamic,
        wait_for_selector=wait_for_selector,
        scroll_count=scroll_count
    )

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Scheduler] Stopped by user.")
