"""
Services de transformation pour les utilisateurs.
"""

import uuid
from ...utils.email_utils import normalize_email, extract_email_parts
from .config import DEFAULT_USER_ATTRIBUTES, USER_ID_PREFIX


def create_user_id():
    """
    Génère un nouvel ID unique pour un utilisateur

    Returns:
        str: ID utilisateur unique
    """
    return f"{USER_ID_PREFIX}{str(uuid.uuid4())}"


def build_user_attributes(email_address, is_central_user=False):
    """
    Construit les attributs d'un utilisateur à partir de son email

    Args:
        email_address (str): Adresse email
        is_central_user (bool): Si c'est l'utilisateur central

    Returns:
        dict: Attributs de l'utilisateur
    """
    clean_email = normalize_email(email_address)
    email, domain, name = extract_email_parts(email_address)

    attributes = DEFAULT_USER_ATTRIBUTES.copy()
    attributes.update({
        'email': clean_email,
        'name': name,
        'domain': domain,
        'is_central_user': is_central_user,
        'connection_strength': 0.0
    })

    return attributes


def extract_email_participants(email_data):
    """
    Extrait et organise tous les participants d'un email par type

    Args:
        email_data (dict): Données d'email

    Returns:
        dict: Dictionnaire avec les listes d'emails par type
    """
    from ...shared_utils import process_email_list

    # Extraire l'expéditeur
    from_email = email_data.get("From", "")

    # Extraire les destinataires
    to_emails = process_email_list(email_data.get("To", ""))
    cc_emails = process_email_list(email_data.get("Cc", ""))
    bcc_emails = process_email_list(email_data.get("Bcc", ""))

    return {
        'from': from_email,
        'to': to_emails,
        'cc': cc_emails,
        'bcc': bcc_emails
    }