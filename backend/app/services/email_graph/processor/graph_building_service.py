"""
Service de construction du graphe à partir des données d'emails.
"""

import networkx as nx
from ..logging_service import logger
from .config import BATCH_CONFIG


class GraphBuildingService:
    """Service pour la construction du graphe"""

    def __init__(self, email_processing_service):
        self.email_processing_service = email_processing_service
        self.emails_processed = 0
        self.emails_successful = 0
        self.emails_failed = 0

    def set_email_processing_service(self, email_processing_service):
        """Met à jour le service de traitement des emails"""
        self.email_processing_service = email_processing_service

    def build_graph_from_emails(self, emails, central_user_email=None, max_emails=None):
        """
        Construit le graphe à partir d'une liste d'emails

        Args:
            emails (list): Liste d'objets email à traiter
            central_user_email (str): Email de l'utilisateur central
            max_emails (int): Limite du nombre d'emails à traiter

        Returns:
            dict: Statistiques de construction
        """
        # Réinitialiser les compteurs
        self.emails_processed = 0
        self.emails_successful = 0
        self.emails_failed = 0

        # Limiter le nombre d'emails si nécessaire
        if max_emails and max_emails < len(emails):
            emails = emails[:max_emails]
            logger.logger.info(f"📊 Limitation appliquée: {max_emails} emails sur {len(emails)} originaux")

        # Configurer l'utilisateur central
        if central_user_email:
            self.email_processing_service.set_central_user(central_user_email)

        logger.logger.info(f"🏗️ Construction du graphe pour {len(emails)} emails...")

        # Traitement de chaque email
        for idx, email in enumerate(emails):
            success = self._process_email_with_logging(email, idx, len(emails))
            self.emails_processed += 1

            if success:
                self.emails_successful += 1
            else:
                self.emails_failed += 1

        # Statistiques finales
        stats = self._generate_build_stats()
        self._log_completion_summary(stats)

        return stats

    def reinitialize_graph(self, graph, message_manager, user_manager, thread_manager):
        """
        Réinitialise le graphe et les gestionnaires

        Args:
            graph: Nouveau graphe NetworkX
            message_manager: Gestionnaire de messages
            user_manager: Gestionnaire d'utilisateurs
            thread_manager: Gestionnaire de threads
        """
        logger.logger.info("🔄 Réinitialisation du graphe...")

        # Créer un nouveau graphe vide
        new_graph = nx.MultiDiGraph()

        # Mettre à jour tous les gestionnaires avec le nouveau graphe
        message_manager.set_graph(new_graph)
        user_manager.set_graph(new_graph)
        thread_manager.set_graph(new_graph)

        # Mettre à jour le service de traitement
        self.email_processing_service.set_managers(message_manager, user_manager, thread_manager)

        logger.logger.info("✅ Réinitialisation terminée")

        return new_graph

    def _process_email_with_logging(self, email, idx, total):
        """Traite un email avec logging d'avancement"""
        success = self.email_processing_service.process_single_email(email)

        # Logging d'avancement périodique
        if idx > 0 and idx % BATCH_CONFIG['progress_log_interval'] == 0:
            progress_pct = (idx / total) * 100
            logger.logger.info(f"📈 Progression: {idx}/{total} emails ({progress_pct:.1f}%)")

        return success

    def _generate_build_stats(self):
        """Génère les statistiques de construction"""
        success_rate = (self.emails_successful / self.emails_processed * 100) if self.emails_processed > 0 else 0

        return {
            'emails_processed': self.emails_processed,
            'emails_successful': self.emails_successful,
            'emails_failed': self.emails_failed,
            'success_rate': round(success_rate, 2)
        }

    def _log_completion_summary(self, stats):
        """Log le résumé de completion"""
        logger.logger.info("🎯 Construction du graphe terminée:")
        logger.logger.info(f"   📧 Emails traités: {stats['emails_processed']}")
        logger.logger.info(f"   ✅ Succès: {stats['emails_successful']}")
        logger.logger.info(f"   ❌ Échecs: {stats['emails_failed']}")
        logger.logger.info(f"   📊 Taux de succès: {stats['success_rate']}%")