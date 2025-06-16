"""
Module de recherche sémantique Accord - Version spaCy uniquement.

Ce module fournit les services de transformation de requêtes en langage naturel
pour l'application Accord.

Composants principaux:
- Query Parser: Analyse spaCy + patterns enrichis
- Query Transformer: Transformation optimisée
- API Endpoints: Interface REST pour le frontend
- Validation Services: Validation robuste des données

Usage:
    from semantic_search import app
    # Lancer avec uvicorn app:app
"""

from .main import app
from .core.query_parser import get_query_parser
from .core.query_transformer import get_query_transformer
from .api.models import (
    NaturalLanguageRequest,
    SemanticQuery,
    SearchFilter,
    QueryTypeEnum
)

__version__ = "2.0.0"
__all__ = [
    "app",
    "get_query_parser",
    "get_query_transformer",
    "NaturalLanguageRequest",
    "SemanticQuery",
    "SearchFilter",
    "QueryTypeEnum"
]