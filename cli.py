import argparse
import sys
from scraper.database import init_db, get_db_session, Job, ScrapedItem
from scraper.engine import ScraperEngine
from scraper.exporter import export_data
from scraper.scheduler import run_standalone_scheduler, execute_scrape_job


def cmd_init_db(args):
    init_db()
    print("Database tables initialized successfully.")


def cmd_scrape(args):
    init_db()
    print(f"Scraping {args.url} (dynamic={not args.static}, parser={args.parser})...")
    execute_scrape_job(
        url=args.url,
        parser_name=args.parser,
        dynamic=not args.static,
        wait_for_selector=args.wait_for,
        scroll_count=args.scroll
    )


def cmd_queue(args):
    """Enqueue a job to Celery worker."""
    try:
        from scraper.tasks import scrape_url_task
        print(f"Enqueuing Celery task for: {args.url}")
        res = scrape_url_task.delay(
            url=args.url,
            parser_name=args.parser,
            dynamic=not args.static,
            wait_for_selector=args.wait_for,
            scroll_count=args.scroll
        )
        print(f"Dispatched Celery Task ID: {res.id}")
        print("Run 'celery -A scraper.celery_app worker -l info' to process tasks.")
    except Exception as e:
        print(f"Error queueing task to Celery (ensure Redis/broker is running): {e}")


def cmd_schedule(args):
    init_db()
    run_standalone_scheduler(
        url=args.url,
        interval_seconds=args.interval,
        parser_name=args.parser,
        dynamic=not args.static,
        wait_for_selector=args.wait_for,
        scroll_count=args.scroll
    )


def cmd_jobs(args):
    init_db()
    with get_db_session() as session:
        jobs = session.query(Job).order_by(Job.id.desc()).limit(args.limit).all()
        if not jobs:
            print("No jobs found in database.")
            return

        print(f"{'ID':<6}{'Status':<12}{'Items':<8}{'Started':<22}{'URL'}")
        print("-" * 80)
        for j in jobs:
            started = j.started_at.strftime("%Y-%m-%d %H:%M:%S") if j.started_at else "-"
            print(f"{j.id:<6}{j.status:<12}{j.items_count:<8}{started:<22}{j.target_url[:35]}")


def cmd_items(args):
    init_db()
    with get_db_session() as session:
        query = session.query(ScrapedItem)
        if args.job_id:
            query = query.filter(ScrapedItem.job_id == args.job_id)
        items = query.order_by(ScrapedItem.id.desc()).limit(args.limit).all()

        if not items:
            print("No scraped items found.")
            return

        print(f"{'ID':<6}{'Job':<6}{'Price':<10}{'Title':<40}{'URL'}")
        print("-" * 90)
        for it in items:
            p_str = f"${it.price:.2f}" if it.price is not None else "-"
            t_str = (it.title[:37] + "...") if it.title and len(it.title) > 37 else (it.title or "-")
            url_str = (it.item_url[:30] + "...") if it.item_url and len(it.item_url) > 30 else (it.item_url or "-")
            print(f"{it.id:<6}{it.job_id:<6}{p_str:<10}{t_str:<40}{url_str}")


def cmd_export(args):
    out = export_data(job_id=args.job_id, export_format=args.format, output_path=args.output)
    print(f"Export created successfully: {out}")


def main():
    parser = argparse.ArgumentParser(description="Automated Dynamic Web Scraper with Scheduler & SQLite")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # init-db
    subparsers.add_parser("init-db", help="Initialize the SQLite database schema")

    # scrape
    p_scrape = subparsers.add_parser("scrape", help="Run a one-time dynamic scrape immediately")
    p_scrape.add_argument("url", help="Target URL to scrape")
    p_scrape.add_argument("--parser", default="generic", choices=["generic", "ecommerce"], help="Parser to use")
    p_scrape.add_argument("--static", action="store_true", help="Use fast static requests instead of Selenium")
    p_scrape.add_argument("--wait-for", default=None, help="CSS selector to wait for before extracting")
    p_scrape.add_argument("--scroll", type=int, default=0, help="Number of infinite scroll actions to execute")

    # queue (Celery)
    p_queue = subparsers.add_parser("queue", help="Enqueue scrape job into Celery task queue")
    p_queue.add_argument("url", help="Target URL to scrape")
    p_queue.add_argument("--parser", default="generic", choices=["generic", "ecommerce"], help="Parser to use")
    p_queue.add_argument("--static", action="store_true", help="Use fast static requests instead of Selenium")
    p_queue.add_argument("--wait-for", default=None, help="CSS selector to wait for before extracting")
    p_queue.add_argument("--scroll", type=int, default=0, help="Number of infinite scroll actions to execute")

    # schedule
    p_sched = subparsers.add_parser("schedule", help="Start standalone periodic scraping loop")
    p_sched.add_argument("url", help="Target URL to scrape periodically")
    p_sched.add_argument("--interval", type=int, default=60, help="Interval in seconds between runs")
    p_sched.add_argument("--parser", default="generic", choices=["generic", "ecommerce"], help="Parser to use")
    p_sched.add_argument("--static", action="store_true", help="Use fast static requests instead of Selenium")
    p_sched.add_argument("--wait-for", default=None, help="CSS selector to wait for before extracting")
    p_sched.add_argument("--scroll", type=int, default=0, help="Number of infinite scroll actions to execute")

    # jobs
    p_jobs = subparsers.add_parser("jobs", help="List recent scraping jobs")
    p_jobs.add_argument("--limit", type=int, default=20, help="Max jobs to display")

    # items
    p_items = subparsers.add_parser("items", help="List scraped items from the database")
    p_items.add_argument("--job-id", type=int, default=None, help="Filter items by Job ID")
    p_items.add_argument("--limit", type=int, default=25, help="Max items to display")

    # export
    p_export = subparsers.add_parser("export", help="Export scraped data to CSV or JSON")
    p_export.add_argument("--format", default="csv", choices=["csv", "json"], help="Export format")
    p_export.add_argument("--job-id", type=int, default=None, help="Filter export by Job ID")
    p_export.add_argument("--output", default=None, help="Custom export file path")

    args = parser.parse_args()

    commands = {
        "init-db": cmd_init_db,
        "scrape": cmd_scrape,
        "queue": cmd_queue,
        "schedule": cmd_schedule,
        "jobs": cmd_jobs,
        "items": cmd_items,
        "export": cmd_export,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
