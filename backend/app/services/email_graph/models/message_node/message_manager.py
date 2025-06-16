"""
Gestionnaire principal pour les nœuds de message.
"""

from typing import Dict, Any, Optional
from .message_validator import validate_message_id, check_message_exists
from .message_transformer import build_message_attributes
from ...logging_service import logger


class MessageNodeManager:
    """Gestionnaire pour la création et la manipulation des nœuds de message."""

    def __init__(self, graph):
        """
        Initialise le gestionnaire de nœuds de message

        Args:
            graph: Instance NetworkX pour stocker les nœuds
        """
        self.graph = graph

    def set_graph(self, graph):
        """
        Met à jour l'instance de graphe

        Args:
            graph: Nouvelle instance NetworkX
        """
        self.graph = graph

    def create_message(self, email_data: Dict[str, Any]) -> Optional[str]:
        """
        Crée un noeud message à partir des données d'email

        Args:
            email_data (dict): Données d'un email

        Returns:
            str: ID du message créé
        """
        # Validation de l'ID du message
        message_id = validate_message_id(email_data)
        if not message_id:
            return None

        # Si le message existe déjà, retourner son ID
        if check_message_exists(self.graph, message_id):
            return message_id

        # Construire les attributs du message
        message_attributes = build_message_attributes(email_data, message_id)

        # Ajouter le noeud au graphe avec tous les attributs
        self.graph.add_node(message_id, **message_attributes)

        # Logger la création
        logger.message_created(
            message_id,
            message_attributes['subject'],
            message_attributes['from'],
            message_attributes['date'],
            message_attributes['topics'],
            message_attributes['has_attachments']
        )

        return message_id