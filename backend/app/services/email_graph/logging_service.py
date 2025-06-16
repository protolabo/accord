"""
Service de logging centralisé pour le graphe d'emails.
"""

import logging
from typing import Optional, Any


class EmailGraphLogger:
    """Logger centralisé pour les opérations du graphe d'emails"""

    def __init__(self, name: str = "email_graph"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def message_created(self, message_id: str, subject: str, from_email: str,
                        date: str, topics: list, has_attachments: bool):
        """Log de création de message"""
        self.logger.info(f"✅ Message créé: {message_id}")
        self.logger.info(f"   Sujet: {subject}")
        self.logger.info(f"   De: {from_email}")
        self.logger.info(f"   Date: {date}")
        self.logger.info(f"   Topics: {topics}")
        self.logger.info(f"   Pièces jointes: {has_attachments}")

    def message_ignored(self, email_data: dict, reason: str):
        """Log d'ignorance de message"""
        self.logger.warning(f"⚠️ Message ignoré ({reason}): {email_data}")

    def date_parse_success(self, message_id: str, date_iso: str):
        """Log de parsing de date réussi"""
        self.logger.info(f"✅ Date parsée pour {message_id}: {date_iso}")

    def date_parse_error(self, message_id: str, date_str: str, error: Exception):
        """Log d'erreur de parsing de date"""
        self.logger.warning(f"⚠️ Erreur parsing date pour {message_id} ({date_str}): {error}")

    def thread_created(self, thread_id: str, message_count: int):
        """Log de création de thread"""
        self.logger.info(f"✅ Thread créé: {thread_id} ({message_count} messages)")

    def user_created(self, user_id: str, email: str, is_central: bool):
        """Log de création d'utilisateur"""
        status = "central" if is_central else "normal"
        self.logger.info(f"✅ Utilisateur créé: {user_id} ({email}) - {status}")

    def relation_created(self, relation_type: str, source: str, target: str, weight: float):
        """Log de création de relation"""
        self.logger.info(f"✅ Relation créée: {source} --{relation_type}({weight})--> {target}")


# Instance globale
logger = EmailGraphLogger()