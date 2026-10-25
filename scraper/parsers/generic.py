import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
from scraper.parsers.base import BaseParser


class GenericParser(BaseParser):
    """
    A flexible generic parser that extracts structured cards, articles,
    or custom CSS selectors from any rendered web page.
    """
    name = "generic"

    def __init__(self, item_selector: Optional[str] = None, field_selectors: Optional[Dict[str, str]] = None):
        """
        :param item_selector: Optional CSS selector identifying repeating item containers.
        :param field_selectors: Optional dict mapping field name -> CSS selector inside the container.
        """
        self.item_selector = item_selector
        self.field_selectors = field_selectors or {}

    def parse(self, html: str, url: str) -> List[Dict[str, Any]]:
        soup = self.get_soup(html)
        items: List[Dict[str, Any]] = []

        # 1. Custom CSS Selectors Mode if provided
        if self.item_selector:
            cards = soup.select(self.item_selector)
            for card in cards:
                item_data: Dict[str, Any] = {}
                for field, selector in self.field_selectors.items():
                    elem = card.select_one(selector)
                    if elem:
                        if field in ("url", "item_url", "link") and elem.name == "a" and elem.get("href"):
                            item_data[field] = urljoin(url, elem["href"])
                        else:
                            item_data[field] = elem.get_text(strip=True)
                if item_data:
                    items.append(item_data)
            return items

        # 2. Heuristic extraction: Common card/article patterns
        candidate_selectors = [
            "article",
            ".quote",
            ".product-item",
            ".card",
            ".post",
            "li.product",
            ".list-item"
        ]

        found_container = None
        for sel in candidate_selectors:
            matched = soup.select(sel)
            if len(matched) >= 2:
                found_container = sel
                break

        if found_container:
            for elem in soup.select(found_container):
                title_elem = elem.select_one("h1, h2, h3, h4, .title, .text, a")
                link_elem = elem.select_one("a[href]")
                price_elem = elem.select_one(".price, .cost, span.price_color")

                title = title_elem.get_text(strip=True) if title_elem else None
                item_url = urljoin(url, link_elem["href"]) if link_elem and link_elem.get("href") else None
                
                price = None
                if price_elem:
                    price_match = re.search(r"[\d]+(?:[.,]\d+)?", price_elem.get_text())
                    if price_match:
                        price = float(price_match.group(0).replace(",", "."))

                if title or item_url:
                    items.append({
                        "title": title[:300] if title else "Untitled",
                        "price": price,
                        "item_url": item_url or url,
                        "raw_snippet": elem.get_text(strip=True)[:200]
                    })
            if items:
                return items

        # 3. Fallback: Page metadata & Headings
        page_title = soup.title.string.strip() if soup.title and soup.title.string else "No Title"
        meta_desc = ""
        meta_elem = soup.find("meta", attrs={"name": "description"})
        if meta_elem and meta_elem.get("content"):
            meta_desc = meta_elem["content"].strip()

        items.append({
            "title": page_title,
            "item_url": url,
            "description": meta_desc,
            "h1_tags": [h.get_text(strip=True) for h in soup.find_all("h1")[:5]]
        })
        return items
