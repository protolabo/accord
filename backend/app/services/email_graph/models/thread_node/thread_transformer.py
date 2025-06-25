"""
Services de transformation pour les threads.
"""

from ...shared_utils import parse_email_date, extract_participants_from_email
from ...logging_service import logger
from .config import DEFAULT_THREAD_ATTRIBUTES, DATE_FIELD_PRIORITY


def find_best_date_field(email_data):
    """
    Trouve le meilleur champ de date disponible selon la priorité définie

    Args:
        email_data (dict): Données d'email

    Returns:
        str: Valeur de date trouvée ou chaîne vide
    """
    for field in DATE_FIELD_PRIORITY:
        date_value = email_data.get(field, "")
        if date_value:
            return date_value

    return ""


def parse_thread_date(email_data, thread_id):
    """
    Parse et valide la date pour un thread

    Args:
        email_data (dict): Données d'email
        thread_id (str): ID du thread pour le logging

    Returns:
        str: Date ISO ou chaîne vide
    """
    date_str = find_best_date_field(email_data)

    if not date_str:
        logger.logger.warning(f"⚠️ Aucune date trouvée pour le thread {thread_id}")
        return ""

    date_iso = parse_email_date(date_str)

    if not date_iso:
        logger.logger.warning(f"⚠️ Erreur parsing date pour thread {thread_id}: {date_str}")

    return date_iso


def extract_thread_participants(email_data):
    """
    Extrait la liste unique des participants d'un thread

    Args:
        email_data (dict): Données d'email

    Returns:
        list: Liste des participants uniques
    """
    return extract_participants_from_email(email_data)


def build_new_thread_attributes(email_data, thread_id):
    """
    Construit les attributs pour un nouveau thread

    Args:
        email_data (dict): Données d'email
        thread_id (str): ID du thread

    Returns:
        dict: Attributs du thread
    """
    message_id = email_data.get("Message-ID", "")
    date_iso = parse_thread_date(email_data, thread_id)
    participants = extract_thread_participants(email_data)
    topics = email_data.get("topics", [])
    subject = email_data.get("Subject", "")

    attributes = DEFAULT_THREAD_ATTRIBUTES.copy()
    attributes.update({
        'first_message_id': message_id,
        'message_count': 1,
        'last_message_date': date_iso,
        'participants': participants,
        'topics': topics,
        'subject': subject
    })

    return attributes


def update_thread_participants(current_participants, email_data):
    """
    Met à jour la liste des participants d'un thread

    Args:
        current_participants (list): Participants actuels
        email_data (dict): Données du nouveau message

    Returns:
        list: Liste mise à jour des participants
    """
    # Convertir en set pour éviter les doublons
    participants = set(current_participants) if current_participants else set()

    # Ajouter les nouveaux participants
    new_participants = extract_thread_participants(email_data)
    participants.update(new_participants)

    return list(participants)


def should_update_date(current_date, new_date):
    """
    Détermine si la date du thread doit être mise à jour

    Args:
        current_date (str): Date actuelle du thread
        new_date (str): Nouvelle date à comparer

    Returns:
        bool: True si la date doit être mise à jour
    """
    if not new_date:
        return False

    if not current_date:
        return True

    # Comparer les dates ISO
    return new_date > current_date


def update_thread_topics(current_topics, email_data):
    """
    Met à jour la liste des topics d'un thread

    Args:
        current_topics (list): Topics actuels
        email_data (dict): Données du nouveau message

    Returns:
        list: Liste mise à jour des topics
    """
    topics = set(current_topics) if current_topics else set()

    new_topics = email_data.get("topics", [])
    if new_topics:
        topics.update(new_topics)

    return list(topics)