"""
API FastAPI pour la recherche sémantique.
Endpoint principal: /semantic-search/parse
"""

debuguerBreakpoint = True

import time
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import ValidationError

from backend.app.services.semantic_search.models import (
    NaturalLanguageRequest,
    SemanticSearchResponse,
    SemanticQuery
)
from backend.app.services.semantic_search.llm_engine import get_query_parser, MistralQueryParser

# Router pour les endpoints de recherche sémantique
router = APIRouter(prefix="/semantic-search", tags=["semantic-search"])


async def get_parser() -> MistralQueryParser:
    """Dependency pour récupérer le parser LLM"""
    return get_query_parser()


@router.post("/parse", response_model=Dict[str, Any])
async def parse_natural_language_query(
        request: NaturalLanguageRequest,
        parser: MistralQueryParser = Depends(get_parser)
):
    """
    Parse une requête en langage naturel vers structure sémantique.

    Cette API transforme une requête utilisateur comme "emails de Marie hier"
    en structure JSON utilisable pour la recherche dans le graphe.

    Args:
        request: Requête contenant le texte en langage naturel
        parser: Instance du parser LLM Mistral

    Returns:
        Structure sémantique JSON pour le frontend
    """
    start_time = time.time()

    try:
        # Parser la requête avec le LLM
        parsed_result = parser.parse_query(
            query=request.query,
            user_context=request.user_context
        )

        # Validation avec Pydantic
        try:
            semantic_query = SemanticQuery(**parsed_result)
        except ValidationError as e:
            # Si validation échoue, utiliser fallback
            print(f"⚠️ Validation échouée, utilisation du fallback: {e}")
            fallback_result = parser._fallback_parser(request.query)
            semantic_query = SemanticQuery(**fallback_result)

        processing_time = (time.time() - start_time) * 1000

        response = {
            "success": True,
            "semantic_query": semantic_query.dict(),
            "processing_time_ms": processing_time,
            "model_info": {
                "used_llm": parsed_result.get('_meta', {}).get('model_used', 'unknown'),
                "parsing_confidence": 0.9 if 'mistral' in str(parsed_result.get('_meta', {})) else 0.6
            }
        }

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du parsing de la requête: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Vérification de l'état du service de recherche sémantique"""
    parser = get_query_parser()

    return {
        "status": "healthy",
        "llm_available": parser.model is not None,
        "model_path": parser.config.model_path,
        "service": "semantic-search"
    }


@router.post("/test-query")
async def test_query_parsing(
        query: str,
        parser: MistralQueryParser = Depends(get_parser)
):
    """
    Endpoint de test pour vérifier le parsing de requêtes.
    Utile pendant le développement.
    """
    try:
        result = parser.parse_query(query)
        return {
            "original_query": query,
            "parsed_result": result,
            "model_used": result.get('_meta', {}).get('model_used', 'unknown')
        }
    except Exception as e:
        return {
            "error": str(e),
            "original_query": query
        }