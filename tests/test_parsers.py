from scraper.parsers.generic import GenericParser
from scraper.parsers.e_commerce import EcommerceParser
from scraper.parsers import get_parser


SAMPLE_ECOMMERCE_HTML = """
<!DOCTYPE html>
<html>
<body>
  <article class="product_pod">
    <h3><a href="catalogue/a-light-in-the-attic_1000/index.html" title="A Light in the Attic">A Light in the ...</a></h3>
    <div class="product_price">
      <p class="price_color">£51.77</p>
      <p class="instock availability">In stock</p>
    </div>
    <p class="star-rating Three"></p>
  </article>
  <article class="product_pod">
    <h3><a href="catalogue/tipping-the-velvet_999/index.html" title="Tipping the Velvet">Tipping the Velvet</a></h3>
    <div class="product_price">
      <p class="price_color">£53.74</p>
      <p class="instock availability">In stock</p>
    </div>
    <p class="star-rating One"></p>
  </article>
</body>
</html>
"""

SAMPLE_CARDS_HTML = """
<!DOCTYPE html>
<html>
<head><title>Tech Blog</title></head>
<body>
  <article>
    <h2><a href="/post/ai-updates">Latest in AI</a></h2>
    <p class="price">$19.00</p>
  </article>
  <article>
    <h2><a href="/post/python-tips">Python Tips & Tricks</a></h2>
    <p class="price">$25.50</p>
  </article>
</body>
</html>
"""


def test_ecommerce_parser():
    parser = EcommerceParser()
    items = parser.parse(SAMPLE_ECOMMERCE_HTML, url="http://books.toscrape.com/")
    assert len(items) == 2
    assert items[0]["title"] == "A Light in the Attic"
    assert items[0]["price"] == 51.77
    assert items[0]["rating"] == "Three"
    assert items[0]["availability"] == "In stock"
    assert "catalogue/a-light-in-the-attic_1000/index.html" in items[0]["item_url"]

    assert items[1]["title"] == "Tipping the Velvet"
    assert items[1]["price"] == 53.74
    assert items[1]["rating"] == "One"


def test_generic_parser():
    parser = GenericParser()
    items = parser.parse(SAMPLE_CARDS_HTML, url="https://example.com")
    assert len(items) == 2
    assert items[0]["title"] == "Latest in AI"
    assert items[0]["price"] == 19.00
    assert "https://example.com/post/ai-updates" in items[0]["item_url"]


def test_parser_registry():
    p1 = get_parser("ecommerce")
    assert isinstance(p1, EcommerceParser)
    p2 = get_parser("generic")
    assert isinstance(p2, GenericParser)
