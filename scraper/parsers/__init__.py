from typing import Dict, Type
from scraper.parsers.base import BaseParser
from scraper.parsers.generic import GenericParser
from scraper.parsers.e_commerce import EcommerceParser

PARSER_REGISTRY: Dict[str, Type[BaseParser]] = {
    "generic": GenericParser,
    "ecommerce": EcommerceParser,
}


def get_parser(name: str = "generic", **kwargs) -> BaseParser:
    """Retrieve an initialized parser instance by name."""
    parser_cls = PARSER_REGISTRY.get(name.lower(), GenericParser)
    return parser_cls(**kwargs)
