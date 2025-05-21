from typing import Dict, List, Any, Optional
import time
import logging
import json
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Exception levée lorsqu'une requête dépasse le timeout"""
    pass


# Charger le graphe JSON une seule fois au démarrage du module
_GRAPH_DATA = None
_GRAPH_FILE_PATH = os.environ.get("EMAIL_GRAPH_PATH", "backend/app/data/mockdata/graph/email_graph_results.json")


def load_graph_data():
    """Charge les données du graphe JSON"""
    global _GRAPH_DATA
    if _GRAPH_DATA is None:
        try:
            with open(_GRAPH_FILE_PATH, 'r', encoding='utf-8') as f:
                _GRAPH_DATA = json.load(f)
            logger.info(
                f"Graphe chargé depuis {_GRAPH_FILE_PATH}: {len(_GRAPH_DATA.get('communication_network', {}).get('nodes', []))} noeuds")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du graphe: {str(e)}")
            _GRAPH_DATA = {"communication_network": {"nodes": [], "links": []}, "top_contacts": [], "top_threads": []}
    return _GRAPH_DATA


def execute_graph_query(query: Dict[str, Any], timeout_ms: int = 500) -> List[Dict[str, Any]]:
    """
    Exécute une requête sur les données du graphe d'emails

    Args:
        query: Requête formatée (générée par query_builder)
        timeout_ms: Timeout en millisecondes

    Returns:
        List[Dict]: Résultats de la requête
    """
    start_time = time.time()

    # Logging de la requête
    logger.debug(f"Exécution de la requête sur le graphe: {query}")

    try:
        # Charger les données du graphe
        graph_data = load_graph_data()

        # Exécution de la recherche avec timeout
        results = _search_in_graph(graph_data, query, timeout_ms)

        # Logging des performances
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Requête exécutée en {elapsed_ms}ms, {len(results)} résultats trouvés")

        return results

    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Erreur lors de l'exécution de la requête (après {elapsed_ms}ms): {str(e)}")

        if elapsed_ms > timeout_ms:
            raise TimeoutError(f"Exécution de la requête trop longue: {elapsed_ms}ms > {timeout_ms}ms")

        # Pour les autres erreurs, on relève l'exception
        raise


def _search_in_graph(graph_data: Dict[str, Any], query: Dict[str, Any], timeout_ms: int) -> List[Dict[str, Any]]:
    """
    Recherche dans les données JSON du graphe

    Args:
        graph_data: Données du graphe chargées
        query: Requête structurée
        timeout_ms: Timeout en millisecondes

    Returns:
        List[Dict]: Résultats formatés
    """
    start_time = time.time()
    entity_type = query["entity_type"]
    results = []

    # Sélectionner la collection de données appropriée selon le type d'entité
    if entity_type == "message":
        # Chercher dans les noeuds de type "message" du réseau
        nodes = [node for node in graph_data.get("communication_network", {}).get("nodes", [])
                 if node.get("type") == "message"]

    elif entity_type == "thread":
        # Utiliser directement les top_threads
        nodes = graph_data.get("top_threads", [])

    elif entity_type == "user":
        # Utiliser les top_contacts et les noeuds utilisateur
        user_nodes = [node for node in graph_data.get("communication_network", {}).get("nodes", [])
                      if node.get("type") == "user"]
        contact_nodes = graph_data.get("top_contacts", [])
        nodes = user_nodes + contact_nodes

    else:
        return []

    # Appliquer les filtres
    filtered_nodes = _apply_filters(nodes, query.get("conditions", []))

    # Vérifier le timeout
    if (time.time() - start_time) * 1000 > timeout_ms:
        raise TimeoutError("Recherche trop longue")

    # Trier les résultats
    sorted_nodes = _sort_results(filtered_nodes, query.get("sort", {}))

    # Limiter le nombre de résultats
    limit = query.get("limit", 20)
    limited_nodes = sorted_nodes[:limit]

    # Formater les résultats
    results = _format_results(limited_nodes, entity_type)

    return results


def _apply_filters(nodes: List[Dict[str, Any]], conditions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Applique les filtres aux noeuds"""
    if not conditions:
        return nodes

    filtered = nodes

    for condition in conditions:
        condition_type = condition.get("type")

        if condition_type == "attribute":
            attribute = condition.get("attribute")
            operator = condition.get("operator")
            value = condition.get("value")

            filtered = [
                node for node in filtered
                if _match_attribute(node, attribute, operator, value)
            ]

        elif condition_type == "relationship":
            # Pour les relations, nous devons vérifier les liens dans le graphe
            # to do
            pass

    return filtered


def _match_attribute(node: Dict[str, Any], attribute: str, operator: str, value: Any) -> bool:
    """Vérifie si un noeud correspond à une condition d'attribut"""
    # Accéder à l'attribut (peut être imbriqué avec des points)
    node_value = node.get(attribute)

    if operator == "equals":
        return node_value == value
    elif operator == "contains":
        if isinstance(node_value, str):
            return value.lower() in node_value.lower()
        elif isinstance(node_value, list):
            return value.lower() in [str(v).lower() for v in node_value]
    elif operator == "lte":
        return node_value <= value
    elif operator == "gte":
        return node_value >= value
    elif operator == "not_empty":
        return bool(node_value)

    return False


def _sort_results(nodes: List[Dict[str, Any]], sort_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Trie les résultats selon les spécifications"""
    if not sort_spec or not nodes:
        return nodes

    field = sort_spec.get("field", "date")
    direction = sort_spec.get("direction", "desc")

    # Fonction de tri qui gère les champs manquants
    def sort_key(node):
        value = node.get(field)
        # Si le champ n'existe pas, utiliser une valeur par défaut
        if value is None:
            if field in ["date", "last_message_date"]:
                return ""
            return 0
        return value

    # Trier les noeuds
    reverse = (direction == "desc")
    return sorted(nodes, key=sort_key, reverse=reverse)


def _format_results(nodes: List[Dict[str, Any]], entity_type: str) -> List[Dict[str, Any]]:
    """
    Formate les noeuds en résultats pour l'interface utilisateur

    Args:
        nodes: Noeuds filtrés et triés
        entity_type: Type d'entité ("message", "thread", "user")

    Returns:
        List[Dict]: Résultats formatés
    """
    results = []

    for node in nodes:
        result = {
            "id": node.get("id", ""),
            "type": entity_type,
            "metadata": {}
        }

        if entity_type == "message":
            result["content"] = node.get("snippet", "")
            result["metadata"] = {
                "date": node.get("date", ""),
                "sender": node.get("from_email", ""),
                "recipients": node.get("to", []),
                "subject": node.get("subject", "")
            }

        elif entity_type == "thread":
            result["content"] = node.get("subject", "")
            result["metadata"] = {
                "message_count": node.get("message_count", 0),
                "last_message_date": node.get("last_message_date", ""),
                "participants": node.get("participants", [])
            }

        elif entity_type == "user":
            result["content"] = node.get("name", "") or node.get("email", "")
            result["metadata"] = {
                "email": node.get("email", ""),
                "domain": node.get("domain", ""),
                "connection_strength": node.get("connection_strength", 0),
                "sent_count": node.get("sent_count", 0),
                "received_count": node.get("received_count", 0)
            }

        results.append(result)

    return results


# Charger les données au démarrage
load_graph_data()