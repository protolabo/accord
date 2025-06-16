"""
Services de validation pour les nœuds utilisateur.
"""

from ...shared_utils import safe_get_nested_value
from ...logging_service import logger
from ...utils.email_utils import normalize_email


def validate_email_address(email_address):
    """
    Valide et normalise une adresse email

    Args:
        email_address (str): Adresse email à valider

    Returns:
        str|None: Email normalisé si valide, None sinon
    """
    if not email_address:
        return None

    clean_email = normalize_email(email_address)

    if not clean_email or '@' not in clean_email:
        logger.logger.warning(f"⚠️ Email invalide ignoré: {email_address}")
        return None

    return clean_email


def validate_user_exists(graph, user_id):
    """
    Vérifie si un utilisateur existe dans le graphe

    Args:
        graph: Instance NetworkX
        user_id (str): ID de l'utilisateur

    Returns:
        bool: True si l'utilisateur existe
    """
    return graph.has_node(user_id) and graph.nodes.get(user_id, {}).get("type") == "user"


def validate_relation_participants(graph, source_id, target_id):
    """
    Valide que les deux participants d'une relation existent et sont différents

    Args:
        graph: Instance NetworkX
        source_id (str): ID de l'utilisateur source
        target_id (str): ID de l'utilisateur cible

    Returns:
        bool: True si la relation peut être créée
    """
    # Vérifier que les utilisateurs existent
    if not validate_user_exists(graph, source_id) or not validate_user_exists(graph, target_id):
        return False

    # Ne pas créer de relation avec soi-même
    if source_id == target_id:
        return False

    return True


def find_existing_user_by_email(graph, email):
    """
    Trouve un utilisateur existant par son email

    Args:
        graph: Instance NetworkX
        email (str): Email à rechercher

    Returns:
        str|None: ID de l'utilisateur si trouvé, None sinon
    """
    clean_email = normalize_email(email)

    for node, data in graph.nodes(data=True):
        if data.get("type") == "user" and data.get("email") == clean_email:
            return node

    return None