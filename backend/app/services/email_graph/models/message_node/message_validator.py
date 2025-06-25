"""
Services de validation pour les nœuds de message.
"""

from .config import REQUIRED_MESSAGE_FIELDS
from ...logging_service import logger


def validate_message_id(email_data):
    """
    Valide la présence de l'ID du message

    Args:
        email_data (dict): Données d'email

    Returns:
        str|None: Message-ID si valide, None sinon
    """
    message_id = email_data.get("Message-ID")

    if not message_id:
        logger.message_ignored(email_data, "Message sans ID")
        return None

    return message_id


def validate_message_data(email_data):
    """
    Valide la structure complète des données d'email

    Args:
        email_data (dict): Données d'email

    Returns:
        bool: True si valide, False sinon
    """
    if not isinstance(email_data, dict):
        return False

    # Vérifier les champs obligatoires
    for field in REQUIRED_MESSAGE_FIELDS:
        if field not in email_data or not email_data[field]:
            return False

    return True


def check_message_exists(graph, message_id):
    """
    Vérifie si un message existe déjà dans le graphe

    Args:
        graph: Instance NetworkX
        message_id (str): ID du message

    Returns:
        bool: True si le message existe
    """
    return graph.has_node(message_id)