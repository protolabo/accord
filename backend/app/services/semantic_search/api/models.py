"""
Modèles Pydantic pour l'API de recherche sémantique (version simplifiée sans LLM).
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

from ..config import QueryType, PARSING_CONFIG


class QueryTypeEnum(str, Enum):
    """Types de requêtes supportées"""
    SEMANTIC = "semantic"
    CONTACT = "contact"
    THREAD = "thread"
    TOPIC = "topic"
    TIME_RANGE = "time_range"
    COMBINED = "combined"


class SearchFilter(BaseModel):
    """Filtres de recherche"""
    contact_email: Optional[str] = None
    contact_name: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    has_attachments: Optional[bool] = None
    is_unread: Optional[bool] = None
    is_important: Optional[bool] = None
    labels: Optional[List[str]] = None
    topic_ids: Optional[List[str]] = None
    thread_id: Optional[str] = None

    @validator('contact_email')
    def validate_email(cls, v):
        if v is not None and v.strip():
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v.strip()):
                raise ValueError('Format d\'email invalide')
        return v.strip() if v else None

    @validator('date_from', 'date_to')
    def validate_date(cls, v):
        if v is not None and v.strip():
            try:
                from datetime import datetime
                datetime.strptime(v.strip(), '%Y-%m-%d')
            except ValueError:
                raise ValueError('Format de date invalide (attendu: YYYY-MM-DD)')
        return v.strip() if v else None

    @validator('topic_ids', 'labels')
    def validate_lists(cls, v):
        if v is not None:
            # Filtrer les valeurs vides et limiter la taille
            cleaned = [item.strip() for item in v if item and item.strip()]
            if len(cleaned) > 10:
                raise ValueError('Trop d\'éléments dans la liste (maximum 10)')
            return cleaned
        return None


class SemanticQuery(BaseModel):
    """Structure sémantique parsée"""
    query_type: QueryTypeEnum
    semantic_text: Optional[str] = None
    filters: SearchFilter = Field(default_factory=SearchFilter)
    limit: int = Field(default=10, ge=1, le=100)
    include_snippets: bool = True
    similarity_threshold: float = Field(default=0.3, ge=0.1, le=1.0)

    @validator('semantic_text')
    def validate_semantic_text(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) > 500:
                raise ValueError('Texte sémantique trop long (maximum 500 caractères)')
        return v


class NaturalLanguageRequest(BaseModel):
    """Requête en langage naturel"""
    query: str = Field(..., min_length=2, max_length=500)
    user_context: Optional[Dict[str, Any]] = None
    central_user_email: Optional[str] = None

    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError('La requête ne peut pas être vide')

        v = v.strip()

        if len(v) < PARSING_CONFIG['min_query_length']:
            raise ValueError(f'Requête trop courte (minimum {PARSING_CONFIG["min_query_length"]} caractères)')

        if len(v) > PARSING_CONFIG['max_query_length']:
            raise ValueError(f'Requête trop longue (maximum {PARSING_CONFIG["max_query_length"]} caractères)')

        # Vérifier les caractères suspects
        import re
        suspicious_patterns = [r'<script.*?>', r'javascript:', r'\.\./', r'union.*select']
        for pattern in suspicious_patterns:
            if re.search(pattern, v.lower()):
                raise ValueError('Requête contient des caractères suspects')

        return v

    @validator('central_user_email')
    def validate_central_email(cls, v):
        if v is not None and v.strip():
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v.strip()):
                raise ValueError('Format d\'email central invalide')
        return v.strip() if v else None


class ParsedEntity(BaseModel):
    """Entité extraite lors du parsing"""
    type: str
    value: str
    original: str
    confidence: float = Field(ge=0.0, le=1.0)


class ProcessingInfo(BaseModel):
    """Informations sur le traitement de la requête"""
    transformation_time_ms: float
    parsing_method: str = "spacy_patterns"
    confidence: float = Field(ge=0.0, le=1.0)
    original_intent: str
    language_detected: Optional[str] = None


class DebugInfo(BaseModel):
    """Informations de debug (optionnelles)"""
    parsed_entities: List[ParsedEntity] = Field(default_factory=list)
    extracted_filters: Dict[str, Any] = Field(default_factory=dict)
    semantic_text: str = ""


class ErrorInfo(BaseModel):
    """Informations d'erreur"""
    message: str
    details: List[str] = Field(default_factory=list)
    type: str = "processing_error"


class SemanticSearchResponse(BaseModel):
    """Réponse complète de l'API de recherche sémantique"""
    success: bool
    semantic_query: Optional[SemanticQuery] = None
    processing_info: ProcessingInfo
    debug_info: Optional[DebugInfo] = None
    error: Optional[ErrorInfo] = None

    @validator('semantic_query')
    def validate_semantic_query_presence(cls, v, values):
        # Si success=True, semantic_query doit être présent
        if values.get('success') and v is None:
            raise ValueError('semantic_query requis quand success=True')
        return v

    @validator('error')
    def validate_error_presence(cls, v, values):
        # Si success=False, error doit être présent
        if not values.get('success', True) and v is None:
            raise ValueError('error requis quand success=False')
        return v


class HealthResponse(BaseModel):
    """Réponse du endpoint de santé"""
    status: str
    spacy_available: bool
    spacy_model: Optional[str] = None
    service: str = "semantic-search"
    timestamp: float


class ServiceInfo(BaseModel):
    """Informations détaillées sur le service"""
    service_name: str
    version: str
    description: str
    capabilities: List[str]
    models: Dict[str, Any]
    performance: Dict[str, Any]


class TestQueryResponse(BaseModel):
    """Réponse du endpoint de test"""
    original_query: str
    parsed_result: Dict[str, Any]
    parsing_method: str = "spacy_patterns"
    success: bool
    error: Optional[str] = None