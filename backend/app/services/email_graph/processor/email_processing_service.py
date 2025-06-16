"""
Service de traitement des emails individuels.
"""

from ..logging_service import logger
from ..utils.email_utils import normalize_email
from .config import RELATION_WEIGHTS


class EmailProcessingService:
    """Service pour le traitement d'un email individuel"""

    def __init__(self, graph, message_manager, user_manager, thread_manager):
        self.graph = graph
        self.message_manager = message_manager
        self.user_manager = user_manager
        self.thread_manager = thread_manager
        self.central_user_email = None

    def set_central_user(self, central_user_email):
        """Définit l'utilisateur central"""
        self.central_user_email = central_user_email

    def set_managers(self, message_manager, user_manager, thread_manager):
        """Met à jour les gestionnaires"""
        self.message_manager = message_manager
        self.user_manager = user_manager
        self.thread_manager = thread_manager

    def process_single_email(self, email_data):
        """
        Traite un email et ajoute les noeuds et relations au graphe

        Args:
            email_data (dict): Données d'un email

        Returns:
            bool: True si l'email a été traité avec succès
        """
        try:
            # Extraire l'ID du message et du thread
            message_id = email_data.get("Message-ID")
            thread_id = email_data.get("Thread-ID", "")

            if not message_id:
                logger.logger.warning("⚠️ Email sans Message-ID ignoré")
                return False

            # Créer noeud message
            message_node = self.message_manager.create_message(email_data)
            if not message_node:
                logger.logger.error(f"❌ Échec création message: {message_id}")
                return False

            # Créer noeud thread si nécessaire
            if thread_id:
                thread_node = self.thread_manager.create_thread(email_data)
                self._create_message_thread_relation(message_id, thread_id)

            # Traiter l'expéditeur et créer ses relations
            from_user_id = self._process_sender(email_data, message_id)

            # Traiter les destinataires et créer les relations utilisateur-message
            self._process_recipients(email_data, message_id)

            # Créer les relations entre utilisateurs (expéditeur <-> destinataires)
            self._create_user_relations(email_data, from_user_id)

            return True

        except Exception as e:
            message_id = email_data.get('Message-ID', 'UNKNOWN')
            logger.logger.error(f"❌ Erreur traitement email {message_id}: {str(e)}")
            return False

    def _create_message_thread_relation(self, message_id, thread_id):
        """Crée la relation message -> thread"""
        self.graph.add_edge(
            message_id,
            thread_id,
            type="PART_OF_THREAD",
            weight=RELATION_WEIGHTS['part_of_thread']
        )

        logger.relation_created("PART_OF_THREAD", message_id, thread_id,
                                RELATION_WEIGHTS['part_of_thread'])

    def _process_sender(self, email_data, message_id):
        """
        Traite l'expéditeur et crée les relations

        Args:
            email_data (dict): Données d'email
            message_id (str): ID du message

        Returns:
            str|None: ID de l'utilisateur expéditeur
        """
        from_email = email_data.get("From", "")
        if not from_email:
            return None

        # Créer l'utilisateur expéditeur
        from_user_id = self.user_manager.create_user(from_email)
        if not from_user_id:
            return None

        # Déterminer le poids selon l'utilisateur central
        is_central = (normalize_email(from_email) == normalize_email(self.central_user_email)
                      if self.central_user_email else False)
        weight = RELATION_WEIGHTS['sent_central_user'] if is_central else RELATION_WEIGHTS['sent_normal']

        # Créer la relation expéditeur -> message
        self.graph.add_edge(
            from_user_id,
            message_id,
            type="SENT",
            weight=weight
        )

        logger.relation_created("SENT", from_user_id, message_id, weight)

        return from_user_id

    def _process_recipients(self, email_data, message_id):
        """Traite tous les types de destinataires et crée les relations message -> destinataire"""

        # Configuration des types de destinataires
        recipient_configs = [
            ("To", "RECEIVED", RELATION_WEIGHTS['received']),
            ("Cc", "CC", RELATION_WEIGHTS['cc']),
            ("Bcc", "BCC", RELATION_WEIGHTS['bcc'])
        ]

        for field_name, relation_type, weight in recipient_configs:
            self._process_recipient_type(email_data, message_id, field_name, relation_type, weight)

    def _process_recipient_type(self, email_data, message_id, field_name, relation_type, weight):
        """Traite un type spécifique de destinataires"""
        emails_str = email_data.get(field_name, "")
        if not emails_str:
            return

        emails = emails_str.split(",")
        for email in emails:
            email = email.strip()
            if not email:
                continue

            # Créer l'utilisateur destinataire
            user_id = self.user_manager.create_user(email)
            if user_id:
                # Créer la relation message -> destinataire
                self.graph.add_edge(
                    message_id,
                    user_id,
                    type=relation_type,
                    weight=weight
                )

                logger.relation_created(relation_type, message_id, user_id, weight)

    def _create_user_relations(self, email_data, from_user_id):
        """Crée les relations entre l'expéditeur et tous les destinataires"""
        if not from_user_id:
            return

        # Déléguer la création des relations aux gestionnaires d'utilisateurs
        self.user_manager.create_recipient_relationships(email_data, from_user_id)