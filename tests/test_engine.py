from unittest.mock import MagicMock
from scraper.engine import ScraperEngine


def test_engine_scrape_static(monkeypatch):
    engine = ScraperEngine()

    mock_resp = MagicMock()
    mock_resp.text = "<html><head><title>Test Static</title></head><body><h1>Hello</h1></body></html>"
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: mock_resp)

    html = engine.scrape_static("https://example.com")
    assert "Test Static" in html


def test_engine_scrape_and_parse(monkeypatch):
    engine = ScraperEngine()

    mock_resp = MagicMock()
    mock_resp.text = """
    <html>
      <body>
        <article class="product_pod">
          <h3><a href="/prod/1" title="Product 1">Product 1</a></h3>
          <p class="price_color">$15.00</p>
        </article>
      </body>
    </html>
    """
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: mock_resp)

    items = engine.scrape_and_parse(
        url="https://example.com",
        parser_name="ecommerce",
        dynamic=False
    )
    assert len(items) == 1
    assert items[0]["title"] == "Product 1"
    assert items[0]["price"] == 15.00
