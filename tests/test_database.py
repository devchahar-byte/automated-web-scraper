import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scraper.database import (
    Base,
    Job,
    ScrapedItem,
    init_db,
    create_job,
    update_job_status,
    save_scraped_items,
    get_db_session
)


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    test_engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    monkeypatch.setattr("scraper.database.engine", test_engine)
    monkeypatch.setattr("scraper.database.SessionLocal", TestingSessionLocal)
    yield


def test_create_and_update_job():
    job = create_job("https://example.com", parser_name="ecommerce")
    assert job.id is not None
    assert job.target_url == "https://example.com"
    assert job.status == "PENDING"

    update_job_status(job.id, status="COMPLETED", items_count=5)
    
    with get_db_session() as session:
        updated = session.query(Job).filter(Job.id == job.id).first()
        assert updated.status == "COMPLETED"
        assert updated.items_count == 5
        assert updated.finished_at is not None


def test_save_scraped_items():
    job = create_job("https://books.example.com", parser_name="ecommerce")
    items_data = [
        {"title": "Book 1", "price": "19.99", "item_url": "https://books.example.com/1", "rating": "Five"},
        {"title": "Book 2", "price": 29.50, "item_url": "https://books.example.com/2", "stock": "In Stock"}
    ]

    count = save_scraped_items(job.id, "https://books.example.com", items_data)
    assert count == 2

    with get_db_session() as session:
        records = session.query(ScrapedItem).filter(ScrapedItem.job_id == job.id).all()
        assert len(records) == 2
        assert records[0].title == "Book 1"
        assert records[0].price == 19.99
        assert records[0].extra_data.get("rating") == "Five"
        assert records[1].title == "Book 2"
        assert records[1].price == 29.50
