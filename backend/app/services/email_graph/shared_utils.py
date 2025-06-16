"""
Utilitaires partagés pour tous les types de nœuds du graphe d'emails.
"""

from datetime import datetime
from ..utils.email_utils import normalize_email


def parse_email_date(date_str, fallback_key=None):
    """
    Parse et normalise les dates d'email avec support de différents formats

    Args:
        date_str (str): Date à parser
        fallback_key (str): Clé alternative pour le logging

    Returns:
        str: Date au format ISO ou chaîne vide
    """
    if not date_str:
        return ""

    try:
        # Support des formats ISO directement
        if 'T' in date_str:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            # Fallback pour autres formats
            date = datetime.fromisoformat(date_str)
        return date.isoformat()
    except (ValueError, TypeError):
        return ""


def process_email_list(email_string, normalize=True):
    """
    Traite une chaîne d'emails séparés par des virgules

    Args:
        email_string (str): Chaîne d'emails séparés par des virgules
        normalize (bool): Normaliser les emails

    Returns:
        list: Liste d'emails nettoyés
    """
    if not email_string:
        return []

    email_list = email_string.split(",") if email_string else []
    emails = [e.strip() for e in email_list if e.strip()]

    if normalize:
        emails = [normalize_email(e) for e in emails]

    return emails


def extract_participants_from_email(email_data):
    """
    Extrait tous les participants d'un email (expéditeur + destinataires)

    Args:
        email_data (dict): Données d'email

    Returns:
        list: Liste unique des participants
    """
    participants = set()

    # Expéditeur
    from_email = email_data.get("From", "")
    if from_email:
        participants.add(normalize_email(from_email))

    # Destinataires
    to_emails = process_email_list(email_data.get("To", ""))
    cc_emails = process_email_list(email_data.get("Cc", ""))
    bcc_emails = process_email_list(email_data.get("Bcc", ""))

    participants.update(to_emails + cc_emails + bcc_emails)

    return list(participants)


def safe_get_nested_value(data, keys, default=None):
    """
    Récupère une valeur imbriquée de manière sécurisée

    Args:
        data (dict): Dictionnaire source
        keys (list): Liste de clés imbriquées
        default: Valeur par défaut

    Returns:
        any: Valeur trouvée ou valeur par défaut
    """
    try:
        for key in keys:
            data = data[key]
        return data
    except (KeyError, TypeError):
        return default