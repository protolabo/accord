"""
Services de validation pour les nœuds de thread.
"""

from ...logging_service import logger


def validate_thread_id(email_data):
    """
    Valide la présence de l'ID du thread

    Args:
        email_data (dict): Données d'email

    Returns:
        str|None: Thread-ID si valide, None sinon
    """
    thread_id = email_data.get("Thread-ID", "")

    if not thread_id:
        logger.logger.warning("⚠️ Email sans Thread-ID ignoré")
        return None

    return thread_id


def validate_thread_data(email_data):
    """
    Valide les données nécessaires pour créer/mettre à jour un thread

    Args:
        email_data (dict): Données d'email

    Returns:
        bool: True si les données sont valides
    """
    if not isinstance(email_data, dict):
        return False

    # Vérifier au minimum la présence du Thread-ID
    if not email_data.get("Thread-ID"):
        return False

    return True


def check_thread_exists(graph, thread_id):
    """
    Vérifie si un thread existe dans le graphe

    Args:
        graph: Instance NetworkX
        thread_id (str): ID du thread

    Returns:
        bool: True si le thread existe
    """
    return graph.has_node(thread_id) and graph.nodes.get(thread_id, {}).get("type") == "thread"


def validate_message_for_thread(email_data):
    """
    Valide qu'un message peut être ajouté à un thread

    Args:
        email_data (dict): Données d'email

    Returns:
        tuple: (is_valid, message_id)
    """
    message_id = email_data.get("Message-ID", "")

    if not message_id:
        logger.logger.warning("⚠️ Message sans ID ne peut pas être ajouté au thread")
        return False, None

    return True, message_id