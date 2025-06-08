"""
Gestionnaire de nœuds de message pour le graphe d'emails.
"""

from datetime import datetime
from typing import Dict, Any, Optional
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

    def create_message(self, email_data: Dict[str, Any]) -> Optional[str]:
        """
        Crée un noeud message à partir des données d'email

        Args:
            email_data (dict): Données d'un email

        Returns:
            str: ID du message créé
        """
        message_id = email_data.get("Message-ID")

        if not message_id:
            print(f"⚠️ Message sans ID ignoré: {email_data}")
            return None

        # Si le message existe déjà, retourner son ID
        if self.graph.has_node(message_id):
            return message_id

        date_str = email_data.get("Date")  # Correspond aux données de test
        date_iso = ""

        if date_str:
            try:
                # Support des formats ISO directement
                if 'T' in date_str:
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    # Fallback pour autres formats
                    date = datetime.fromisoformat(date_str)
                date_iso = date.isoformat()
                print(f"✅ Date parsée pour {message_id}: {date_iso}")
            except (ValueError, TypeError) as e:
                print(f"⚠️ Erreur parsing date pour {message_id} ({date_str}): {e}")
                date_iso = ""

        from_email = normalize_email(email_data.get("From", ""))

        # Gérer les listes de destinataires
        to_list = email_data.get("To", "").split(",") if email_data.get("To") else []
        cc_list = email_data.get("Cc", "").split(",") if email_data.get("Cc") else []
        bcc_list = email_data.get("Bcc", "").split(",") if email_data.get("Bcc") else []

        to_emails = [normalize_email(e.strip()) for e in to_list if e.strip()]
        cc_emails = [normalize_email(e.strip()) for e in cc_list if e.strip()]
        bcc_emails = [normalize_email(e.strip()) for e in bcc_list if e.strip()]

        # Utiliser les noms d'attributs attendus par le moteur de recherche
        # Note : Je dois avoir une version identique avec google message structure pour ne pas get des mauvaises cles
        message_attributes = {
            'type': 'message',
            'thread_id': email_data.get("Thread-ID", ""),
            'date': date_iso,

            'subject': email_data.get("Subject", ""),
            'content': email_data.get("Content", ""),

            'from': from_email,
            'from_email': from_email,  #temporaire
            'to': to_emails,
            'cc': cc_emails,
            'bcc': bcc_emails,

            # temporaire
            # ces methodes sont A implementer
            'has_attachments': email_data.get("has_attachments", False),
            'attachment_count': email_data.get("attachment_count", 0),
            'is_important': email_data.get("is_important", False),
            'is_unread': email_data.get("is_unread", True),

            'topics': email_data.get("topics", []),

            'labels': email_data.get("Labels", []),
            'categories': email_data.get("Categories", []),
            'attachments': email_data.get("Attachments", []),
            'snippet': email_data.get("Snippet", "")
        }

        # Ajouter le noeud au graphe avec tous les attributs
        self.graph.add_node(message_id, **message_attributes)

        print(f"✅ Message créé: {message_id}")
        print(f"   Sujet: {message_attributes['subject']}")
        print(f"   De: {message_attributes['from']}")
        print(f"   Date: {message_attributes['date']}")
        print(f"   Topics: {message_attributes['topics']}")
        print(f"   Pièces jointes: {message_attributes['has_attachments']}")

        return message_id