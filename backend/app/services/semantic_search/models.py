"""
Modèles Pydantic pour la recherche sémantique.
Définit les structures de données pour les requêtes et réponses.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum

class QueryType(str, Enum):
    """Types de requêtes supportées"""
    SEMANTIC = "semantic"           # Recherche par similarité sémantique
    CONTACT = "contact"            # Recherche de contacts
    THREAD = "thread"              # Recherche de threads/conversations
    TOPIC = "topic"                # Recherche par sujet
    TIME_RANGE = "time_range"      # Recherche temporelle
    COMBINED = "combined"          # Requête combinée

class SearchFilter(BaseModel):
    """Filtres de recherche"""
    contact_email: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    has_attachments: Optional[bool] = None
    labels: Optional[List[str]] = None
    topic_ids: Optional[List[str]] = None
    thread_id: Optional[str] = None

class SemanticQuery(BaseModel):
    """Structure sémantique parsée"""
    query_type: QueryType
    semantic_text: Optional[str] = None
    filters: SearchFilter = Field(default_factory=SearchFilter)
    limit: int = Field(default=10, ge=1, le=100)
    include_snippets: bool = True
    similarity_threshold: float = Field(default=0.3, ge=0.1, le=1.0)

class NaturalLanguageRequest(BaseModel):
    """Requête en langage naturel"""
    query: str = Field(..., min_length=3, max_length=500)
    user_context: Optional[Dict[str, Any]] = None #time_zone user
    central_user_email: Optional[str] = None

class SearchResult(BaseModel):
    """Résultat de recherche"""
    message_id: str
    score: float
    subject: str
    snippet: str
    sender: str
    date: str
    thread_id: Optional[str] = None
    topics: List[str] = []
    interface_type: Optional[str] = None

class SemanticSearchResponse(BaseModel):
    """Réponse complète de recherche sémantique"""
    original_query: str
    parsed_query: SemanticQuery
    results: List[SearchResult]
    total_found: int
    execution_time_ms: float
    suggestions: List[str] = []