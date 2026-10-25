import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from sqlalchemy import select
from scraper.database import get_db_session, ScrapedItem, init_db
import config


def export_data(
    job_id: Optional[int] = None,
    export_format: str = "csv",
    output_path: Optional[str] = None
) -> str:
    """
    Exports collected records from SQLite to CSV or JSON format.
    :param job_id: Optional Job ID filter
    :param export_format: "csv" or "json"
    :param output_path: Destination file path (defaults to data/exports/...)
    :return: Absolute path to the generated export file
    """
    init_db()
    with get_db_session() as session:
        query = session.query(ScrapedItem)
        if job_id is not None:
            query = query.filter(ScrapedItem.job_id == job_id)
        
        items = query.order_by(ScrapedItem.id.asc()).all()
        records = [item.to_dict() for item in items]

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    prefix = f"job_{job_id}_" if job_id else "all_"

    if not output_path:
        filename = f"export_{prefix}{timestamp}.{export_format.lower()}"
        out_file = config.EXPORTS_DIR / filename
    else:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

    if export_format.lower() == "csv":
        fieldnames = ["id", "job_id", "target_url", "title", "price", "item_url", "scraped_at", "extra_data"]
        with open(out_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for rec in records:
                row = dict(rec)
                if "extra_data" in row and isinstance(row["extra_data"], dict):
                    row["extra_data"] = json.dumps(row["extra_data"])
                writer.writerow(row)
    elif export_format.lower() == "json":
        with open(out_file, mode="w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
    else:
        raise ValueError(f"Unsupported export format: {export_format}. Use 'csv' or 'json'.")

    return str(out_file.resolve())
