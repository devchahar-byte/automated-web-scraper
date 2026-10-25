import re
from typing import Any, Dict, List
from urllib.parse import urljoin
from scraper.parsers.base import BaseParser


class EcommerceParser(BaseParser):
    """
    Parser specialized for product/catalog pages (e.g., e-commerce, book stores, quotes).
    Extracts title, price, rating, availability, tags, and product URLs.
    """
    name = "ecommerce"

    def parse(self, html: str, url: str) -> List[Dict[str, Any]]:
        soup = self.get_soup(html)
        items: List[Dict[str, Any]] = []

        # Target books.toscrape or similar e-commerce structures
        products = soup.select("article.product_pod, .product, .quote")

        if products:
            for p in products:
                # 1. Title (prefer full 'title' attribute if available)
                title_elem = p.select_one("h3 a, .title a, .text")
                title = ""
                if title_elem:
                    title = title_elem.get("title", "").strip() or title_elem.get_text(strip=True)

                # 2. Product Link
                link_elem = p.select_one("h3 a, a[href]")
                item_url = urljoin(url, link_elem["href"]) if link_elem and link_elem.get("href") else url

                # 3. Price
                price = None
                price_elem = p.select_one(".price_color, .price, .amount")
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    match = re.search(r"[\d]+(?:[.,]\d+)?", price_text)
                    if match:
                        price = float(match.group(0).replace(",", "."))

                # 4. Availability / Stock
                instock_elem = p.select_one(".instock, .availability")
                availability = instock_elem.get_text(strip=True) if instock_elem else None

                # 5. Rating or Author
                rating_elem = p.select_one("p.star-rating")
                rating = None
                if rating_elem:
                    classes = rating_elem.get("class", [])
                    rating = [c for c in classes if c != "star-rating"]
                    rating = rating[0] if rating else None

                author_elem = p.select_one(".author")
                author = author_elem.get_text(strip=True) if author_elem else None

                # 6. Tags
                tags = [t.get_text(strip=True) for t in p.select(".tags .tag")]

                extra = {}
                if availability:
                    extra["availability"] = availability
                if rating:
                    extra["rating"] = rating
                if author:
                    extra["author"] = author
                if tags:
                    extra["tags"] = tags

                item = {
                    "title": title or "Unnamed Item",
                    "price": price,
                    "item_url": item_url,
                    **extra
                }
                items.append(item)

        return items
