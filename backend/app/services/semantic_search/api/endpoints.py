"""
API FastAPI pour la recherche sémantique (version simplifiée sans LLM).
"""

import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import ValidationError

from .models import (
    NaturalLanguageRequest,
    SemanticSearchResponse,
    SemanticQuery,
    ProcessingInfo,
    DebugInfo,
    ErrorInfo,
    HealthResponse,
    ServiceInfo,
    TestQueryResponse
)
from ..core.query_transformer import get_query_transformer, SemanticQueryTransformer
from ..services.parsing_service import NLPParsingService
from ..services.validation_service import QueryValidationService


# Router pour les endpoints de recherche sémantique
router = APIRouter(prefix="/semantic-search", tags=["semantic-search"])


async def get_transformer() -> SemanticQueryTransformer:
    """Dependency pour récupérer le transformer"""
    return get_query_transformer()


async def get_parser() -> NLPParsingService:
    """Dependency pour récupérer le parser"""
    return NLPParsingService()


@router.post("/parse", response_model=SemanticSearchResponse)
async def parse_natural_language_query(
    request: NaturalLanguageRequest,
    transformer: SemanticQueryTransformer = Depends(get_transformer)
):
    """
    Parse une requête en langage naturel vers structure sémantique.

    Cette API transforme une requête utilisateur comme "emails de Marie hier"
    en structure JSON utilisable pour la recherche dans le graphe.

    Args:
        request: Requête contenant le texte en langage naturel
        transformer: Instance du transformer spaCy

    Returns:
        Structure sémantique JSON pour le frontend
    """
    start_time = time.time()

    try:
        # Transformer la requête
        result = transformer.transform_query(request)

        if result.get('success'):
            # Créer la réponse de succès
            processing_info = ProcessingInfo(**result['processing_info'])

            debug_info = None
            if 'debug_info' in result:
                debug_info = DebugInfo(**result['debug_info'])

            # Valider avec Pydantic
            try:
                semantic_query = SemanticQuery(**result['semantic_query'])
            except ValidationError as e:
                # Si validation échoue, retourner une erreur
                error_info = ErrorInfo(
                    message="Erreur de validation de la requête sémantique",
                    details=[str(err) for err in e.errors()],
                    type="validation_error"
                )

                return SemanticSearchResponse(
                    success=False,
                    processing_info=processing_info,
                    error=error_info
                )

            return SemanticSearchResponse(
                success=True,
                semantic_query=semantic_query,
                processing_info=processing_info,
                debug_info=debug_info
            )

        else:
            # Créer la réponse d'erreur
            processing_info = ProcessingInfo(**result['processing_info'])
            error_info = ErrorInfo(**result['error'])

            return SemanticSearchResponse(
                success=False,
                processing_info=processing_info,
                error=error_info
            )

    except Exception as e:
        # Erreur inattendue
        processing_time = (time.time() - start_time) * 1000

        processing_info = ProcessingInfo(
            transformation_time_ms=processing_time,
            parsing_method="spacy_patterns",
            confidence=0.0,
            original_intent="unknown"
        )

        error_info = ErrorInfo(
            message=f"Erreur lors du parsing de la requête: {str(e)}",
            type="unexpected_error"
        )

        return SemanticSearchResponse(
            success=False,
            processing_info=processing_info,
            error=error_info
        )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Vérification de l'état du service de recherche sémantique"""
    try:
        parser = NLPParsingService()
        spacy_available = parser.nlp_model is not None
        spacy_model = None

        if spacy_available:
            # Détecter le modèle spaCy utilisé
            if hasattr(parser.nlp_model, 'meta'):
                spacy_model = parser.nlp_model.meta.get('name', 'unknown')
            else:
                spacy_model = 'loaded'

        return HealthResponse(
            status="healthy",
            spacy_available=spacy_available,
            spacy_model=spacy_model,
            service="semantic-search",
            timestamp=time.time()
        )

    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            spacy_available=False,
            spacy_model=None,
            service="semantic-search",
            timestamp=time.time()
        )


@router.get("/info", response_model=ServiceInfo)
async def service_info():
    """Informations détaillées sur le service"""
    try:
        parser = NLPParsingService()
        spacy_available = parser.nlp_model is not None
        spacy_model_name = "unknown"

        if spacy_available and hasattr(parser.nlp_model, 'meta'):
            spacy_model_name = parser.nlp_model.meta.get('name', 'unknown')

        return ServiceInfo(
            service_name="Accord Semantic Search",
            version="2.0.0",
            description="Service de transformation de requêtes en langage naturel (spaCy only)",
            capabilities=[
                "Parse de langage naturel avec spaCy",
                "Extraction d'entités (NER)",
                "Détection d'intention",
                "Transformation en structure sémantique",
                "Support multilingue (FR/EN)",
                "Patterns enrichis"
            ],
            models={
                "nlp_parser": {
                    "available": spacy_available,
                    "type": "spaCy NER + Patterns enrichis",
                    "model_name": spacy_model_name
                }
            },
            performance={
                "target_latency_ms": 100,  # Plus rapide sans LLM
                "max_query_length": 500,
                "supported_languages": ["fr", "en", "auto"],
                "confidence_threshold": 0.5
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des informations: {str(e)}"
        )


@router.post("/test-query", response_model=TestQueryResponse)
async def test_query_parsing(
    query: str,
    include_debug: bool = True,
    parser: NLPParsingService = Depends(get_parser)
):
    """
    Endpoint de test pour vérifier le parsing de requêtes.
    Utile pendant le développement.
    """
    try:
        # Validation simple
        if not query or len(query.strip()) < 2:
            return TestQueryResponse(
                original_query=query,
                parsed_result={},
                parsing_method="spacy_patterns",
                success=False,
                error="Requête trop courte ou vide"
            )

        # Parser la requête
        result = parser.parse_query(query.strip())

        # Filtrer les informations sensibles si pas de debug
        if not include_debug:
            # Supprimer les informations détaillées
            filtered_result = {
                'intent': result.get('intent'),
                'confidence': result.get('confidence'),
                'entity_count': len(result.get('entities', [])),
                'language': result.get('language'),
                'has_filters': bool(result.get('filters'))
            }
            result = filtered_result

        return TestQueryResponse(
            original_query=query,
            parsed_result=result,
            parsing_method="spacy_patterns",
            success=True
        )

    except Exception as e:
        return TestQueryResponse(
            original_query=query,
            parsed_result={},
            parsing_method="spacy_patterns",
            success=False,
            error=str(e)
        )


@router.get("/patterns/languages")
async def get_supported_languages():
    """Retourne les langues supportées par les patterns"""
    return {
        "supported_languages": ["fr", "en", "auto"],
        "default_language": "auto",
        "detection_automatic": True,
        "fallback_enabled": True
    }


@router.get("/patterns/entity-types")
async def get_supported_entity_types():
    """Retourne les types d'entités supportés"""
    return {
        "entity_types": [
            {
                "type": "PERSON",
                "description": "Nom de personne",
                "examples": ["Marie", "Jean Dupont"]
            },
            {
                "type": "EMAIL",
                "description": "Adresse email",
                "examples": ["marie@example.com"]
            },
            {
                "type": "TEMPORAL",
                "description": "Expression temporelle",
                "examples": ["hier", "la semaine dernière", "2024-01-15"]
            },
            {
                "type": "TOPIC",
                "description": "Sujet ou catégorie",
                "examples": ["facture", "newsletter", "projet"]
            },
            {
                "type": "ORGANIZATION",
                "description": "Nom d'organisation",
                "examples": ["Google", "Microsoft"]
            }
        ]
    }


@router.get("/patterns/intent-types")
async def get_supported_intent_types():
    """Retourne les types d'intentions supportés"""
    return {
        "intent_types": [
            {
                "type": "search_semantic",
                "description": "Recherche par contenu/sens",
                "examples": ["emails sur le projet"]
            },
            {
                "type": "search_contact",
                "description": "Recherche par expéditeur/contact",
                "examples": ["emails de Marie", "messages de jean@example.com"]
            },
            {
                "type": "search_temporal",
                "description": "Recherche temporelle",
                "examples": ["emails d'hier", "messages de la semaine dernière"]
            },
            {
                "type": "search_topic",
                "description": "Recherche par sujet/catégorie",
                "examples": ["factures", "newsletters"]
            },
            {
                "type": "search_combined",
                "description": "Recherche combinée",
                "examples": ["emails de Marie hier sur le projet"]
            }
        ]
    }