from typing import Dict, List, Any, Optional
import logging
import traceback
from functools import lru_cache

logger = logging.getLogger(__name__)

def handle_parsing_error(query: str, user_id: str, error: Exception) -> List[Dict[str, Any]]:
    """
    Gère les erreurs de parsing en implémentant une stratégie de fallback

    Args:
        query: Requête originale
        user_id: ID de l'utilisateur
        error: Exception levée

    Returns:
        List[Dict]: Résultats de fallback
    """
    error_type = type(error).__name__
    error_msg = str(error)

    logger.error(f"Erreur de parsing: {error_type} - {error_msg}")
    logger.debug(f"Query: '{query}', User: {user_id}")


    # recherche par mots-clés
    keywords = _extract_keywords(query)
    if keywords:
        logger.info(f"Fallback vers recherche par mots-clés: {keywords}")
        return _keyword_search(keywords, user_id)
    else :
        return []


def handle_execution_error(query: str, user_id: str, error: Exception) -> List[Dict[str, Any]]:
    """
    Gère les erreurs d'exécution en implémentant une stratégie de fallback

    Args:
        query: Requête originale
        user_id: ID de l'utilisateur
        error: Exception levée

    Returns:
        List[Dict]: Résultats de fallback
    """
    error_type = type(error).__name__
    error_msg = str(error)

    logger.error(f"Erreur d'exécution: {error_type} - {error_msg}")
    logger.debug(f"Query: '{query}', User: {user_id}")
    logger.debug(traceback.format_exc())


    # Pour les autres erreurs d'exécution
    return [{
        "id": "error-1",
        "type": "error",
        "content": "Une erreur est survenue lors de la recherche.",
        "metadata": {
            "error_type": error_type,
            "suggestions": [
                "Essayez de reformuler votre recherche",
                "Contactez le support si le problème persiste"
            ]
        }
    }]




def _extract_keywords(query: str) -> List[str]:
    """Extrait les mots-clés importants d'une requête"""
    # Version simplifiée - en production, utilisez un vrai NLP
    words = query.lower().split()

    # Filtrer les mots courts et les mots vides
    keywords = [w for w in words if len(w) > 3 and w not in
                ["dans", "avec", "pour", "quel", "quels", "quelle",
                 "quelles", "entre", "comme", "comment"]]

    return keywords


def _keyword_search(keywords: List[str], user_id: str) -> List[Dict[str, Any]]:
    """Effectue une recherche par mots-clés simple"""
    # Implémentation factice - à remplacer par votre logique réelle
    logger.info(f"Recherche par mots-clés: {keywords}")

    # Simuler quelques résultats basiques
    results = []
    for i, keyword in enumerate(keywords[:3]):  # Limiter à 3 mots-clés
        results.append({
            "id": f"fallback-{i + 1}",
            "type": "mail",
            "content": f"Résultat de fallback pour '{keyword}'",
            "metadata": {
                "source": "keyword_search",
                "relevance": 0.5,  # Score de pertinence réduit pour indiquer un fallback
                "keyword": keyword
            }
        })

    return results


