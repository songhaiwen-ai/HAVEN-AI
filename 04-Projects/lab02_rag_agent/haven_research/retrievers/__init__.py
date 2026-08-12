"""
retrievers 包入口
"""
from .base import BaseRetriever
from .duckduckgo import DuckDuckGoRetriever

__all__ = [
    "BaseRetriever",
    "DuckDuckGoRetriever"
]
