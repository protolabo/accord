"""
Module de recherche dans le graphe d'emails
"""

from .search_manager import GraphSearchEngine
from .result_service import SearchResult
from .config import SearchMode

__all__ = [
    'GraphSearchEngine',
    'SearchResult',
    'SearchMode'
]