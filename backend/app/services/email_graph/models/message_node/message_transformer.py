"""
Services de transformation et enrichissement pour les messages.
"""

from ...shared_utils import parse_email_date, process_email_list
from ...utils.email_utils import normalize_email
from ...logging_service import logger
from .config import DEFAULT_MESSAGE_ATTRIBUTES, FIELD_MAPPING


def parse_message_date(email_data, message_id):
    """
    Parse et valide la date du message

    Args:
        email_data (dict): Données d'email
        message_id (str): ID du message pour le logging

    Returns:
        str: Date ISO ou chaîne vide
    """
    date_str = email_data.get("Date")
    date_iso = ""

    if date_str:
        date_iso = parse_email_date(date_str)
        if date_iso:
            logger.date_parse_success(message_id, date_iso)
        else:
            logger.date_parse_error(message_id, date_str, "Format non supporté")

    return date_iso


def process_recipient_lists(email_data):
    """
    Traite et normalise les listes de destinataires

    Args:
        email_data (dict): Données d'email

    Returns:
        tuple: (to_emails, cc_emails, bcc_emails)
    """
    to_emails = process_email_list(email_data.get("To", ""))
    cc_emails = process_email_list(email_data.get("Cc", ""))
    bcc_emails = process_email_list(email_data.get("Bcc", ""))

    return to_emails, cc_emails, bcc_emails


def build_message_attributes(email_data, message_id):
    """
    Construit le dictionnaire complet des attributs du message

    Args:
        email_data (dict): Données d'email
        message_id (str): ID du message

    Returns:
        dict: Attributs du message
    """
    # Partir des attributs par défaut
    attributes = DEFAULT_MESSAGE_ATTRIBUTES.copy()

    # Parser la date
    date_iso = parse_message_date(email_data, message_id)

    # Traiter l'expéditeur
    from_email = normalize_email(email_data.get("From", ""))

    # Traiter les destinataires
    to_emails, cc_emails, bcc_emails = process_recipient_lists(email_data)

    # Construire les attributs finaux
    attributes.update({
        'thread_id': email_data.get("Thread-ID", ""),
        'date': date_iso,
        'subject': email_data.get("Subject", ""),
        'content': email_data.get("Content", ""),
        'from': from_email,
        'from_email': from_email,  # temporaire
        'to': to_emails,
        'cc': cc_emails,
        'bcc': bcc_emails,
        'has_attachments': email_data.get("has_attachments", False),
        'attachment_count': email_data.get("attachment_count", 0),
        'is_important': email_data.get("is_important", False),
        'is_unread': email_data.get("is_unread", True),
        'topics': email_data.get("topics", []),
        'labels': email_data.get("Labels", []),
        'categories': email_data.get("Categories", []),
        'attachments': email_data.get("Attachments", []),
        'snippet': email_data.get("Snippet", "")
    })

    return attributes