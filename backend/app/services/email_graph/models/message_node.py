# oria_ui/shared/python/email_graph/models/message_node.py
"""
Gestionnaire de nœuds de message pour le graphe d'emails.
"""

from datetime import datetime
from ..utils.email_utils import normalize_email


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

    def create_message(self, email_data):
        """
        Crée un noeud message à partir des données d'email

        Args:
            email_data (dict): Données d'un email

        Returns:
            str: ID du message créé
        """
        message_id = email_data.get("Message-ID")

        # Si le message existe déjà, retourner son ID
        if self.graph.has_node(message_id):
            return message_id

        # Convertir la date en format ISO
        date_str = email_data.get("Internal-Date")
        if date_str:
            try:
                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                date_iso = date.isoformat()
            except (ValueError, TypeError):
                date_iso = ""
        else:
            date_iso = ""

        # Normaliser les emails
        # obtenir toutes les informations du mails
        from_email = normalize_email(email_data.get("From", ""))

        to_list = email_data.get("To", "").split(",") if email_data.get("To") else []
        cc_list = email_data.get("Cc", "").split(",") if email_data.get("Cc") else []
        bcc_list = email_data.get("Bcc", "").split(",") if email_data.get("Bcc") else []

        to_emails = [normalize_email(e) for e in to_list if e.strip()]
        cc_emails = [normalize_email(e) for e in cc_list if e.strip()]
        bcc_emails = [normalize_email(e) for e in bcc_list if e.strip()]

        # Ajouter le noeud au graphe
        """
        message_id est la clé unique qui représente le nœud dans le graphe.
        Tout ce qui suit sous forme de clé=valeur sont des attributs rattachés à ce nœud.
        """

        self.graph.add_node(
            message_id,
            type="message",
            thread_id=email_data.get("Thread-ID", ""),
            date=date_iso,
            labels=email_data.get("Labels", []),
            categories=email_data.get("Categories", []),
            attachment=email_data.get("Attachments", []),
            from_email=from_email,
            to=to_emails,
            cc=cc_emails,
            bcc=bcc_emails,
            subject=email_data.get("Subject", ""),
            snippet=email_data.get("Snippet", "")
        )

        return message_id