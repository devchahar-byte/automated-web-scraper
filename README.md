# 🕷️ Automated Web Scraper with Scheduler

An enterprise-ready, automated web scraping tool built with **Python**, **Selenium**, **BeautifulSoup4**, **Celery**, and **SQLite**. Designed for periodic data harvesting from dynamic, JavaScript-rendered websites, with automated scheduling and flexible export to **CSV** or **JSON**.

---

## 🚀 Key Features

- **Live Web Page Dashboard (GitHub Pages Ready)**: Instant, responsive interactive web dashboard in `docs/index.html` with real-time metrics, search, sorting, card/table views, and direct CSV/JSON downloads.
- **Git-Scraping Automation**: Integrated `.github/workflows/scrape_and_publish.yml` that runs on a schedule (cron), executes dynamic Selenium scrapers, saves to SQLite, generates fresh datasets, and publishes directly to GitHub Pages automatically.
- **Dynamic JavaScript Rendering**: Powered by Selenium (headless Chrome/Edge) to handle client-rendered SPA frameworks, infinite scrolling, and delayed DOM elements.
- **High-Performance Parsing**: Combines Selenium DOM capture with BeautifulSoup4 for resilient, high-speed HTML tree parsing.
- **Dual Scheduling Modes**:
  - **Celery + Celery Beat**: Industrial-grade, distributed asynchronous task queue with periodic cron/interval scheduling.
  - **Standalone Loop Scheduler**: Lightweight, zero-dependency in-process scheduler using `schedule` (runs out of the box without requiring Redis).
- **SQLite Database Persistence**: Full schema management via SQLAlchemy ORM tracking job execution runs, statuses (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`), and structured records with JSON payload support.
- **Data Exporting**: Instant export of raw or job-filtered datasets to CSV or JSON formats.
- **CLI Utility**: Intuitive terminal commands for scraping, scheduling, inspecting historical jobs, reviewing records, serving the web dashboard, and exporting data.
- **Docker & Compose Ready**: Pre-configured `Dockerfile` and `docker-compose.yml` bundling the application, Celery workers, Celery beat, and Redis.

---

## 🏗️ Architecture

```
                       +---------------------------------------+
                       |        Scheduler (Beat / CLI)         |
                       +---------------------------------------+
                                           |
                                           v
                             +---------------------------+
                             |   Task Queue / Dispatch   |
                             +---------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
| Scraper Engine                                                                    |
|  1. Selenium WebDriver  -->  Renders dynamic JS / Waits / Infinite Scrolls        |
|  2. BeautifulSoup4      -->  Parses DOM and extracts clean structured records     |
+-----------------------------------------------------------------------------------+
                                           |
                                           v
                            +-----------------------------+
                            |       SQLite Database       |
                            | - scrape_jobs (audit runs)  |
                            | - scraped_items (records)   |
                            +-----------------------------+
                                           |
                                           v
                            +-----------------------------+
                            |      Export Subsystem       |
                            |  -> CSV / JSON / DB Query   |
                            +-----------------------------+
```

---

## 📂 Project Structure

```
automated-web-scraper/
├── .github/workflows/
│   └── scrape_and_publish.yml # Automated CI/CD cron scraper & GitHub Pages publisher
├── docs/                     # Live Web Page Dashboard (GitHub Pages root)
│   ├── index.html            # Interactive web app (Tailwind CSS, search, filters)
│   ├── data.json             # Live dataset stream consumed by the dashboard
│   └── data.csv              # Downloadable CSV dataset
├── .gitignore                # Ignored files, virtualenv, and databases
├── Dockerfile                # Container definition with Chromium
├── docker-compose.yml        # Orchestrates Redis + Celery Worker + Celery Beat
├── requirements.txt          # Project dependencies
├── config.py                 # Environment and application configuration
├── pytest.ini                # Pytest configuration
├── cli.py                    # Unified CLI entrypoint (includes 'web' server)
├── scraper/
│   ├── __init__.py
│   ├── database.py          # SQLAlchemy models (Job, ScrapedItem) & sessions
│   ├── engine.py            # Dynamic Selenium + BS4 extraction engine
│   ├── celery_app.py        # Celery initialization & Beat schedules
│   ├── tasks.py             # Asynchronous Celery tasks
│   ├── scheduler.py         # Standalone scheduler runner
│   ├── exporter.py          # CSV and JSON export routines
│   └── parsers/
│       ├── __init__.py      # Parser registry
│       ├── base.py          # BaseParser abstract interface
│       ├── generic.py       # Heuristic & CSS-selector parser
│       └── e_commerce.py    # Product/catalog parser
├── tests/
│   ├── test_database.py     # Database ORM tests
│   ├── test_engine.py       # Scraper engine tests
│   ├── test_exporter.py     # CSV/JSON export tests
│   └── test_parsers.py      # BeautifulSoup parser tests
└── data/
    ├── exports/             # Default destination for generated CSV/JSON
    └── scraper.db           # SQLite database file (auto-generated)
```

---

## 🌐 Live Web Page & GitHub Pages Publishing

This project is pre-configured to be **100% Live Web Page compatible** out of the box when published to GitHub:

### Step-by-Step Publishing Guide

1. **Create a new repository on GitHub** (e.g. `automated-web-scraper`).
2. **Push your code**:
   ```bash
   git remote add origin https://github.com/<your-username>/automated-web-scraper.git
   git branch -M main
   git push -u origin main
   ```
3. **Enable GitHub Pages**:
   - Go to your repository on GitHub.
   - Navigate to **Settings** > **Pages**.
   - Under **Build and deployment** > **Source**, choose **GitHub Actions** (recommended) or select **Deploy from a branch** > branch `main` and folder `/docs`.
4. **Enjoy Automated Live Scraping**:
   - The included workflow `.github/workflows/scrape_and_publish.yml` will automatically run every 6 hours (and can also be triggered manually in the Actions tab).
   - It runs headless Chrome, executes dynamic scraping, saves to SQLite, generates fresh `docs/data.json` & `docs/data.csv`, commits updates, and deploys your live web page at:
     ```
     https://<your-username>.github.io/automated-web-scraper/
     ```

### Local Preview of the Live Web Dashboard
You can preview the live web page on your local computer anytime:
```bash
python cli.py web
```
This automatically opens `http://localhost:8000` with the interactive dashboard, search bar, and CSV/JSON downloads.

---

## 🛠️ Quickstart Installation

### 1. Clone the repository & Create Environment

```bash
git clone <repository_url>
cd automated-web-scraper

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize the Database

```bash
python cli.py init-db
```

---

## 💻 CLI Usage

The `cli.py` utility provides complete access to all functionality:

### 1. Perform an Instant Scrape
```bash
# Scrape dynamic website using Selenium (headless)
python cli.py scrape "https://quotes.toscrape.com/scroll" --parser ecommerce --wait-for ".quote" --scroll 2

# Scrape static page using fast requests mode
python cli.py scrape "https://quotes.toscrape.com/" --static --parser ecommerce
```

### 2. Run the Standalone Periodic Scheduler
Run automated scrapes periodically without needing Redis or external brokers:
```bash
# Scrape every 60 seconds
python cli.py schedule "https://quotes.toscrape.com/scroll" --interval 60 --parser ecommerce --scroll 1
```

### 3. View Scraping Jobs & Harvested Items
```bash
# View recent jobs and statuses
python cli.py jobs --limit 10

# View scraped items from the database
python cli.py items --limit 20

# View items for a specific job
python cli.py items --job-id 1
```

### 4. Export Collected Data
```bash
# Export all records to CSV
python cli.py export --format csv

# Export specific job data to JSON
python cli.py export --job-id 1 --format json

# Export to custom destination
python cli.py export --format csv --output "./data/exports/my_report.csv"
```

---

## ⚙️ Distributed Scheduling with Celery & Redis

For enterprise production setups requiring distributed worker pools:

### 1. Start Redis
```bash
# Using Docker:
docker run -d -p 6379:6379 --name scraper-redis redis:7-alpine
```

### 2. Start Celery Worker
```bash
celery -A scraper.celery_app worker --loglevel=info --concurrency=2
```

### 3. Start Celery Beat (Periodic Scheduler)
```bash
celery -A scraper.celery_app beat --loglevel=info
```

Periodic schedules can be customized in `scraper/celery_app.py` under the `beat_schedule` dictionary:
```python
"scrape-quotes-every-hour": {
    "task": "scraper.tasks.scrape_url_task",
    "schedule": 3600.0,
    "args": ["https://quotes.toscrape.com/scroll", "ecommerce"],
    "kwargs": {"dynamic": True, "wait_for_selector": ".quote", "scroll_count": 2}
}
```

### 4. Dispatch Asynchronous Tasks from CLI
```bash
python cli.py queue "https://quotes.toscrape.com/" --parser ecommerce
```

---

## 🐳 Docker Compose Deployment

Run the entire pipeline (Redis + Celery Worker + Celery Beat Scheduler) with a single command:

```bash
docker-compose up --build -d
```

Check worker and beat logs:
```bash
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
```

---

## 🧪 Running Unit Tests

Unit tests are written with `pytest` and mock network/database fixtures:

```bash
pytest -v
```

All 9 test suites verify database lifecycle, Selenium engine fallbacks, BeautifulSoup parsers, and CSV/JSON exporters.

---

## 🧩 Adding Custom Parsers

To extract data from a new site with custom selectors, inherit from `BaseParser`:

```python
# scraper/parsers/my_parser.py
from scraper.parsers.base import BaseParser

class MyParser(BaseParser):
    name = "my_parser"

    def parse(self, html: str, url: str):
        soup = self.get_soup(html)
        items = []
        for card in soup.select(".custom-card"):
            items.append({
                "title": card.select_one(".title").text.strip(),
                "price": float(card.select_one(".price").text.replace("$", "")),
                "item_url": url,
            })
        return items
```

Register it in `scraper/parsers/__init__.py`:
```python
from scraper.parsers.my_parser import MyParser
PARSER_REGISTRY["my_parser"] = MyParser
```

---

## 📄 License
MIT License. Created for automated dynamic data collection.
