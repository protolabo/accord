"""
Module de recherche sémantique Accord - Backend.

Ce module fournit les services de transformation de requêtes en langage naturel
pour l'application accord.

Composants principaux:
- Query Parser: Analyse NLP + règles heuristiques
- LLM Engine: Mistral 7B GGUF pour parsing avancé
- Query Transformer: Fusion intelligente et transformation
- API Endpoints: Interface REST pour le frontend

Usage:
    from semantic_search import app
    # Lancer avec uvicorn app:app
"""

from .main import app
from .parsing.query_parser import get_query_parser
from .query_transformer import get_query_transformer
from .llm_engine import get_query_parser as get_llm_parser
from .models import (
    NaturalLanguageRequest,
    SemanticQuery,
    SearchFilter,
    QueryType
)

__version__ = "1.0.0"
__all__ = [
    "app",
    "get_query_parser",
    "get_query_transformer",
    "get_llm_parser",
    "NaturalLanguageRequest",
    "SemanticQuery",
    "SearchFilter",
    "QueryType"
]