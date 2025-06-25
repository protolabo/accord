"""
Utilitaires pour le graphe d'emails.
"""

from .email_utils import normalize_email, extract_email_parts


__all__ = [
    'normalize_email',
    'extract_email_parts',
]