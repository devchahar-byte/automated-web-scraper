import logging
import time
from typing import Any, Dict, List, Optional
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import config
from scraper.parsers import get_parser

logger = logging.getLogger(__name__)


class ScraperEngine:
    """
    Dynamic Web Scraping Engine utilizing Selenium for JavaScript rendering
    and BeautifulSoup for structured DOM parsing.
    """

    def __init__(self, headless: Optional[bool] = None):
        self.headless = config.SELENIUM_HEADLESS if headless is None else headless
        self._driver: Optional[webdriver.Remote] = None

    def _init_driver(self) -> webdriver.Remote:
        """Initialize Chrome (or Edge fallback) in headless mode."""
        # Try Chrome
        try:
            options = ChromeOptions()
            if self.headless:
                options.add_argument("--headless=new")
            options.add_argument(f"--window-size={config.SELENIUM_WINDOW_SIZE}")
            options.add_argument(f"user-agent={config.USER_AGENT}")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--log-level=3")
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(config.SELENIUM_PAGE_TIMEOUT)
            return driver
        except Exception as e:
            logger.warning(f"Failed to start Chrome driver ({e}), falling back to Edge...")

        # Fallback to Edge
        try:
            options = EdgeOptions()
            if self.headless:
                options.add_argument("--headless=new")
            options.add_argument(f"--window-size={config.SELENIUM_WINDOW_SIZE}")
            options.add_argument(f"user-agent={config.USER_AGENT}")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--log-level=3")
            driver = webdriver.Edge(options=options)
            driver.set_page_load_timeout(config.SELENIUM_PAGE_TIMEOUT)
            return driver
        except Exception as err:
            logger.error(f"Failed to initialize any browser driver: {err}")
            raise RuntimeError(f"Web browser driver could not be initialized: {err}")

    def scrape_dynamic(
        self,
        url: str,
        wait_for_selector: Optional[str] = None,
        scroll_count: int = 0,
        scroll_delay: float = 1.0,
        timeout: int = 15
    ) -> str:
        """
        Renders a dynamic URL using Selenium, waiting for JS elements and executing scrolling if needed.
        Returns rendered page source HTML.
        """
        driver = self._init_driver()
        try:
            logger.info(f"Loading dynamic URL: {url}")
            driver.get(url)

            # Wait for specific selector if requested
            if wait_for_selector:
                logger.info(f"Waiting for selector: {wait_for_selector}")
                WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
                )
            else:
                # Brief settle wait for dynamic JS
                time.sleep(2.0)

            # Perform dynamic infinite scrolling if requested
            if scroll_count > 0:
                logger.info(f"Performing {scroll_count} dynamic scrolls...")
                for i in range(scroll_count):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(scroll_delay)

            return driver.page_source
        finally:
            driver.quit()

    def scrape_static(self, url: str) -> str:
        """Fast fallback using requests for static or pre-rendered pages."""
        headers = {"User-Agent": config.USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=config.SELENIUM_PAGE_TIMEOUT)
        resp.raise_for_status()
        return resp.text

    def scrape_and_parse(
        self,
        url: str,
        parser_name: str = "generic",
        dynamic: bool = True,
        wait_for_selector: Optional[str] = None,
        scroll_count: int = 0,
        parser_kwargs: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        End-to-end scraper execution: renders HTML (dynamic or static) and parses into structured records.
        """
        parser = get_parser(parser_name, **(parser_kwargs or {}))

        if dynamic:
            html = self.scrape_dynamic(
                url=url,
                wait_for_selector=wait_for_selector,
                scroll_count=scroll_count
            )
        else:
            html = self.scrape_static(url=url)

        items = parser.parse(html, url=url)
        logger.info(f"Extracted {len(items)} items using parser '{parser_name}' from {url}")
        return items
