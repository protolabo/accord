"""
Gestionnaire principal du processeur de graphe d'emails.
"""

import json
import networkx as nx
from datetime import datetime

from ..models.message_node import MessageNodeManager
from ..models.user_node import UserNodeManager
from ..models.thread_node import ThreadNodeManager
from ..analysis.metrics import GraphMetricsAnalyzer
from ..analysis.network_extraction import NetworkExtractor
from ..logging_service import logger

from .email_processing_service import EmailProcessingService
from .graph_building_service import GraphBuildingService
from .analysis_service import GraphAnalysisService
from .config import ERROR_MESSAGES


class EmailGraphProcessor:
    """
    Processeur de graphe d'emails utilisant NetworkX pour l'analyse
    et la visualisation des relations d'emails.
    """

    def __init__(self):
        """Initialise le processeur de graphe"""
        # Graphe principal - stocke tous les noeuds et relations
        self.graph = nx.MultiDiGraph()

        # Configuration
        self.central_user_email = None

        # Gestionnaires de nœuds
        self.message_manager = MessageNodeManager(self.graph)
        self.user_manager = UserNodeManager(self.graph)
        self.thread_manager = ThreadNodeManager(self.graph)

        # Analyseurs
        self.metrics_analyzer = GraphMetricsAnalyzer(self.graph)
        self.network_extractor = NetworkExtractor(self.graph)

        # Services de traitement
        self.email_processing_service = EmailProcessingService(
            self.graph, self.message_manager, self.user_manager, self.thread_manager
        )
        self.graph_building_service = GraphBuildingService(self.email_processing_service)
        self.analysis_service = GraphAnalysisService(
            self.graph, self.metrics_analyzer, self.network_extractor
        )

        # Cache pour l'optimisation
        self.email_cache = {}

    def process_graph(self, message_json):
        """
        Point d'entrée principal pour traiter les données et construire le graphe

        Args:
            message_json (str): Chaîne JSON contenant les données et instructions

        Returns:
            str: Résultat au format JSON
        """
        try:
            # Décodage du message JSON
            message = self._parse_input_message(message_json)

            # Extraction des paramètres
            emails = message.get("mails", [])
            self.central_user_email = message.get("central_user")
            max_emails = message.get("max_emails")

            # Configurer les gestionnaires
            self.user_manager.set_central_user(self.central_user_email)

            # Construction du graphe
            build_stats = self._build_graph(emails, max_emails)

            # Analyse du graphe
            analysis_result = self._analyze_graph(build_stats.get('emails_processed', 0))

            return json.dumps(analysis_result)

        except Exception as e:
            # Gestion d'erreurs avec détails pour faciliter le débogage
            error_response = self._generate_error_response(e)
            return json.dumps(error_response)

    def _parse_input_message(self, message_json):
        """Parse le message JSON d'entrée"""
        if isinstance(message_json, str):
            try:
                return json.loads(message_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"{ERROR_MESSAGES['json_parse_error']}: {str(e)}")
        else:
            return message_json

    def _build_graph(self, emails, max_emails=None):
        """
        Construit le graphe à partir des données d'emails

        Args:
            emails (list): Liste d'objets email à traiter
            max_emails (int): Limite du nombre d'emails

        Returns:
            dict: Statistiques de construction
        """
        # Réinitialiser le graphe si nécessaire
        if self.graph.number_of_nodes() > 0:
            self.graph = self._reinitialize_graph()

        # Déléguer la construction au service
        build_stats = self.graph_building_service.build_graph_from_emails(
            emails, self.central_user_email, max_emails
        )

        # Log du résumé final
        logger.logger.info(
            f"🎯 Construction terminée: {self.graph.number_of_nodes()} nœuds, "
            f"{self.graph.number_of_edges()} relations"
        )

        return build_stats

    def _reinitialize_graph(self):
        """Réinitialise le graphe et tous les gestionnaires"""
        new_graph = self.graph_building_service.reinitialize_graph(
            self.graph, self.message_manager, self.user_manager, self.thread_manager
        )

        # Mettre à jour les analyseurs
        self.metrics_analyzer.set_graph(new_graph)
        self.network_extractor.set_graph(new_graph)

        # Mettre à jour les services
        self.analysis_service.set_analyzers(self.metrics_analyzer, self.network_extractor)

        return new_graph

    def _analyze_graph(self, emails_processed):
        """
        Analyse le graphe et calcule diverses métriques

        Args:
            emails_processed (int): Nombre d'emails traités

        Returns:
            dict: Résultats de l'analyse
        """
        return self.analysis_service.analyze_complete_graph(
            self.central_user_email, emails_processed
        )

    def _generate_error_response(self, exception):
        """Génère une réponse d'erreur standardisée"""
        error_response = {
            'status': 'error',
            'message': str(exception),
            'type': type(exception).__name__,
            'timestamp': datetime.now().isoformat()
        }

        logger.logger.error(f"❌ Erreur processeur: {error_response}")
        return error_response

    # Méthodes de compatibilité (si nécessaire)
    def get_graph_statistics(self):
        """Retourne les statistiques actuelles du graphe"""
        return {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'central_user': self.central_user_email
        }

    def reset_processor(self):
        """Remet à zéro le processeur"""
        self.graph = nx.MultiDiGraph()
        self.central_user_email = None
        self.email_cache = {}

        # Réinitialiser tous les gestionnaires
        self._reinitialize_graph()

        logger.logger.info("🔄 Processeur réinitialisé")