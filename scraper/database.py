import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    ForeignKey,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
import config

Base = declarative_base()


class Job(Base):
    """Tracks every execution of a scraper run."""
    __tablename__ = "scrape_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_url = Column(String(500), nullable=False)
    parser_name = Column(String(100), nullable=False, default="generic")
    status = Column(String(50), nullable=False, default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED
    items_count = Column(Integer, default=0)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    items = relationship("ScrapedItem", back_populates="job", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "target_url": self.target_url,
            "parser_name": self.parser_name,
            "status": self.status,
            "items_count": self.items_count,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "error_message": self.error_message,
        }


class ScrapedItem(Base):
    """Stores structured records scraped from dynamic pages."""
    __tablename__ = "scraped_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("scrape_jobs.id"), nullable=False, index=True)
    target_url = Column(String(500), nullable=False)
    title = Column(String(500), nullable=True)
    price = Column(Float, nullable=True)
    item_url = Column(String(500), nullable=True)
    extra_data_json = Column(Text, nullable=True)
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    job = relationship("Job", back_populates="items")

    @property
    def extra_data(self) -> Dict[str, Any]:
        if self.extra_data_json:
            try:
                return json.loads(self.extra_data_json)
            except Exception:
                return {}
        return {}

    @extra_data.setter
    def extra_data(self, data: Dict[str, Any]) -> None:
        self.extra_data_json = json.dumps(data) if data else None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "id": self.id,
            "job_id": self.job_id,
            "target_url": self.target_url,
            "title": self.title,
            "price": self.price,
            "item_url": self.item_url,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
        }
        if self.extra_data_json:
            d["extra_data"] = self.extra_data
        return d


# Database engine & session maker
engine = create_engine(config.DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(custom_engine=None) -> None:
    """Initialize database tables."""
    target_engine = custom_engine or engine
    Base.metadata.create_all(bind=target_engine)


def get_db_session() -> Session:
    """Return a new database session."""
    return SessionLocal()


def create_job(target_url: str, parser_name: str = "generic") -> Job:
    """Create a new scrape job in PENDING state."""
    with get_db_session() as session:
        job = Job(
            target_url=target_url,
            parser_name=parser_name,
            status="PENDING",
            started_at=datetime.now(timezone.utc)
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        return job


def update_job_status(
    job_id: int,
    status: str,
    items_count: int = 0,
    error_message: Optional[str] = None
) -> None:
    """Update status, count, and completion timestamp for a job."""
    with get_db_session() as session:
        job = session.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = status
            job.items_count = items_count
            if error_message:
                job.error_message = error_message
            if status in ("COMPLETED", "FAILED"):
                job.finished_at = datetime.now(timezone.utc)
            session.commit()


def save_scraped_items(job_id: int, target_url: str, items: List[Dict[str, Any]]) -> int:
    """Save scraped records associated with a job."""
    if not items:
        return 0

    with get_db_session() as session:
        records = []
        for item in items:
            title = item.get("title")
            price = item.get("price")
            item_url = item.get("item_url") or item.get("url")
            
            # Reserved keys; rest goes to extra_data
            reserved = {"title", "price", "item_url", "url"}
            extra = {k: v for k, v in item.items() if k not in reserved}

            rec = ScrapedItem(
                job_id=job_id,
                target_url=target_url,
                title=title,
                price=float(price) if price is not None and str(price).replace('.', '', 1).isdigit() else None,
                item_url=item_url,
                scraped_at=datetime.now(timezone.utc)
            )
            rec.extra_data = extra
            records.append(rec)

        session.bulk_save_objects(records)
        session.commit()
        return len(records)
