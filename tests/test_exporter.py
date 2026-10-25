import json
import csv
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scraper.database import Base, create_job, save_scraped_items
from scraper.exporter import export_data


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    test_engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    monkeypatch.setattr("scraper.database.engine", test_engine)
    monkeypatch.setattr("scraper.database.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("config.EXPORTS_DIR", tmp_path)
    yield


def test_export_to_csv(tmp_path):
    job = create_job("https://example.com/items")
    save_scraped_items(job.id, "https://example.com/items", [
        {"title": "Item A", "price": 10.5, "item_url": "https://example.com/a"},
        {"title": "Item B", "price": 20.0, "item_url": "https://example.com/b"}
    ])

    csv_file = tmp_path / "out.csv"
    res = export_data(job_id=job.id, export_format="csv", output_path=str(csv_file))
    assert Path(res).exists()

    with open(res, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["title"] == "Item A"
        assert float(rows[0]["price"]) == 10.5
        assert rows[1]["title"] == "Item B"


def test_export_to_json(tmp_path):
    job = create_job("https://example.com/items")
    save_scraped_items(job.id, "https://example.com/items", [
        {"title": "Gadget X", "price": 99.99, "brand": "Apex"}
    ])

    json_file = tmp_path / "out.json"
    res = export_data(job_id=job.id, export_format="json", output_path=str(json_file))
    assert Path(res).exists()

    with open(res, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["title"] == "Gadget X"
        assert data[0]["price"] == 99.99
        assert data[0]["extra_data"]["brand"] == "Apex"
