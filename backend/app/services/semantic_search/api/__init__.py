"""
API FastAPI pour la recherche sémantique.
"""

from .endpoints import router
from .models import (
    NaturalLanguageRequest,
    SemanticSearchResponse,
    SemanticQuery,
    SearchFilter
)

__all__ = [
    "router",
    "NaturalLanguageRequest",
    "SemanticSearchResponse",
    "SemanticQuery",
    "SearchFilter"
]