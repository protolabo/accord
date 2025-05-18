# oria_ui/shared/python/email_graph/utils/__init__.py
"""
Utilitaires pour le graphe d'emails.
"""

from .email_utils import normalize_email, extract_email_parts


__all__ = [
    'normalize_email',
    'extract_email_parts',
]