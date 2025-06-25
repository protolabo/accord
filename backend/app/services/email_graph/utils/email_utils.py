"""
Utilitaires pour la manipulation des adresses email.
"""

import re
from email.utils import parseaddr


def normalize_email(email):
    """
    Normalise une adresse email pour une comparaison cohérente

    Args:
        email (str): Adresse email à normaliser

    Returns:
        str: Adresse email normalisée
    """
    if not email:
        return ""

    # Extraire l'email du format "Nom <email@domaine>"
    if '<' in email and '>' in email:
        try:
            email = re.search(r'<([^>]+)>', email).group(1)
        except (AttributeError, IndexError):
            return None

    normalized = email.lower().strip()

    return normalized


def extract_email_parts(email_str):
    """
    Extrait l'adresse, le domaine et le nom d'affichage d'une chaîne email.

    Args:
        email_str (str): Chaîne contenant une adresse email,
                         éventuellement précédée d'un nom entre guillemets ou suivi de <...>.

    Returns:
        tuple: (email_address, domain, display_name)
               ou (None, None, None) si l'entrée est vide ou invalide.
    """
    if not email_str:
        return None, None, None

    # parseaddr sépare le display name et l'adresse pure
    display_name, address = parseaddr(email_str)

    # Si l'adresse extraite n'est pas un email valide, on échoue gracieusement
    if not address or '@' not in address:
        return None, None, None

    # Domaine = tout ce qui suit '@'
    domain = address.split('@', 1)[1]

    # Si parseaddr a trouvé un display_name, on l'utilise ;
    # sinon on reconstruit un nom à partir de la partie utilisateur
    if display_name:
        name = display_name
    else:
        username = address.split('@', 1)[0]
        parts = username.split('.')
        name = ' '.join(p.capitalize() for p in parts if p)

    return address, domain, name