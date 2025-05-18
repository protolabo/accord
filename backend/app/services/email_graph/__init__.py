# oria_ui/shared/python/email_graph/__init__.py
"""
Module d'analyse de graphe d'emails pour Oria.

Ce module utilise NetworkX pour construire, analyser et extraire des informations
à partir des emails.
"""

import json
from .processor import EmailGraphProcessor


def process_graph(message_json):
    """
    Fonction d'entrée pour le module de graphe

    Args:
        message_json (str): Chaîne JSON contenant les données et instructions

    Returns:
        str: Résultat au format JSON
    """
    try:
        processor = EmailGraphProcessor()
        return processor.process_graph(message_json)
    except Exception as e:
        # Gestion des erreurs
        error_response = {
            'status': 'error',
            'message': str(e),
            'type': type(e).__name__
        }
        return json.dumps(error_response)