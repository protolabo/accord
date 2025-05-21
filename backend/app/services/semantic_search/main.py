from functools import lru_cache
import time
from typing import Dict, List, Any, Optional

from backend.app.services.semantic_search.llm.chain import create_semantic_parsing_chain
from backend.app.services.semantic_search.graph.query_builder import build_graph_query
from backend.app.services.semantic_search.graph.query_executor import execute_graph_query
from backend.app.services.semantic_search.utils.errors_handlers import handle_parsing_error, handle_execution_error

# Création de la chaîne de traitement (initialisée une seule fois)
_parsing_chain = create_semantic_parsing_chain()


@lru_cache(maxsize=100)
def semantic_search(
        query_text: str,
        user_id: str,
        timeout_ms: int = 500
) -> List[Dict[str, Any]]:
    """
    Point d'entrée principal pour la recherche sémantique

    Args:
        query_text: Requête en langage naturel
        user_id: Identifiant de l'utilisateur
        timeout_ms: Timeout en millisecondes

    Returns:
        Liste des résultats de recherche
    """
    start_time = time.time()

    try:

        # 1. Parsing sémantique - transformation de la requête en structure
        email_query = _parsing_chain.run(
            query=query_text)

        # Vérification du timeout intermédiaire
        if (time.time() - start_time) * 1000 > timeout_ms * 0.4:
            # Simplifier la requête si on approche du timeout
            email_query.filters = email_query.filters[:1] if email_query.filters else []

        # 2. Construction de la requête pour le moteur de graphe
        graph_query = build_graph_query(email_query)

        # 3. Exécution avec le temps restant
        remaining_ms = timeout_ms - int((time.time() - start_time) * 1000)
        results = execute_graph_query(graph_query, timeout_ms=remaining_ms)

        return results

    except Exception as e:
        if "parsing" in str(e).lower():
            return handle_parsing_error(query_text, user_id, e)
        else:
            return handle_execution_error(query_text, user_id, e)