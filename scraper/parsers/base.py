from abc import ABC, abstractmethod
from typing import Any, Dict, List
from bs4 import BeautifulSoup


class BaseParser(ABC):
    """Abstract Base Class for website parsers."""

    name: str = "base"

    @abstractmethod
    def parse(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Extract structured records from the rendered HTML."""
        pass

    def get_soup(self, html: str) -> BeautifulSoup:
        """Helper to create a BeautifulSoup object."""
        try:
            return BeautifulSoup(html, "lxml")
        except Exception:
            return BeautifulSoup(html, "html.parser")
