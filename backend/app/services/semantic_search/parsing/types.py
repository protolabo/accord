"""
Types et structures de données pour le parsing de requêtes 
"""

from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class IntentType(Enum):
    """Types d'intention détectés dans les requêtes """
    SEARCH_SEMANTIC = "search_semantic"  # Recherche par contenu/sens
    SEARCH_CONTACT = "search_contact"  # Recherche par expéditeur/contact
    SEARCH_TEMPORAL = "search_temporal"  # Recherche temporelle
    SEARCH_TOPIC = "search_topic"  # Recherche par sujet/catégorie
    SEARCH_THREAD = "search_thread"  # Recherche dans conversations
    SEARCH_ATTACHMENT = "search_attachment"  # Recherche avec fichiers joints
    SEARCH_COMBINED = "search_combined"  # Requête combinée
    UNKNOWN = "unknown"


@dataclass
class ParsedEntity:
    """Entité extraite de la requête """
    type: str  # Type d'entité (PERSON, DATE, EMAIL, etc.)
    value: str  # Valeur normalisée
    original: str  # Texte original
    confidence: float  # Score de confiance


@dataclass
class QueryContext:
    """Contexte de la requête utilisateur """
    user_email: Optional[str] = None
    timezone: str = "UTC"
    language: str = "fr"
    recent_searches: List[str] = None