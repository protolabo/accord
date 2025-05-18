# oria_ui/shared/python/email_graph/models/thread_node.py
"""
Gestionnaire de nœuds de thread pour le graphe d'emails.
"""

from datetime import datetime


class ThreadNodeManager:
    """Gestionnaire pour la création et la manipulation des nœuds de thread."""

    def __init__(self, graph):
        """
        Initialise le gestionnaire de nœuds de thread

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

    def create_thread(self, email_data):
        """
        Crée ou met à jour un noeud de thread

        Args:
            email_data (dict): Données d'un email

        Returns:
            str: ID du thread
        """
        thread_id = email_data.get("Thread-ID", "")
        if not thread_id:
            return None

        # Si le thread existe déjà, le mettre à jour
        if self.graph.has_node(thread_id):
            thread_data = self.graph.nodes[thread_id]

            # Incrémenter le compteur de messages
            thread_data["message_count"] = thread_data.get("message_count", 0) + 1

            # Mettre à jour la date du dernier message
            current_date = email_data.get("Internal-Date", "")
            if current_date:
                try:
                    date = datetime.fromisoformat(current_date.replace('Z', '+00:00'))
                    current_iso = date.isoformat()

                    if thread_data.get("last_message_date", "") < current_iso:
                        thread_data["last_message_date"] = current_iso
                except (ValueError, TypeError):
                    pass

            # Mettre à jour les participants
            participants = set(thread_data.get("participants", []))

            # Ajouter expéditeur
            from_email = email_data.get("From", "")
            if from_email:
                participants.add(from_email)

            # Ajouter destinataires
            to_emails = email_data.get("To", "").split(",") if email_data.get("To") else []
            cc_emails = email_data.get("Cc", "").split(",") if email_data.get("Cc") else []

            for email in to_emails + cc_emails:
                if email and email.strip():
                    participants.add(email.strip())

            thread_data["participants"] = list(participants)

            return thread_id

        # Créer un nouveau thread
        message_id = email_data.get("Message-ID", "")
        date_str = email_data.get("Internal-Date", "")

        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            date_iso = date.isoformat()
        except (ValueError, TypeError):
            date_iso = ""

        # Initialiser la liste des participants
        participants = []
        from_email = email_data.get("From", "")
        if from_email:
            participants.append(from_email)

        to_emails = email_data.get("To", "").split(",") if email_data.get("To") else []
        cc_emails = email_data.get("Cc", "").split(",") if email_data.get("Cc") else []

        for email in to_emails + cc_emails:
            if email and email.strip():
                participants.append(email.strip())

        # Ajouter le noeud au graphe
        self.graph.add_node(
            thread_id,
            type="thread",
            first_message_id=message_id,
            message_count=1,
            last_message_date=date_iso,
            participants=participants,
            topics=[],
            subject=email_data.get("Subject", "")
        )

        return thread_id
