"""
Service d'analyse du graphe et calcul des métriques.
"""

from datetime import datetime
from ..logging_service import logger
from .config import ANALYSIS_CONFIG


class GraphAnalysisService:
    """Service pour l'analyse du graphe et le calcul des métriques"""

    def __init__(self, graph, metrics_analyzer, network_extractor):
        self.graph = graph
        self.metrics_analyzer = metrics_analyzer
        self.network_extractor = network_extractor

    def set_analyzers(self, metrics_analyzer, network_extractor):
        """Met à jour les analyseurs"""
        self.metrics_analyzer = metrics_analyzer
        self.network_extractor = network_extractor

    def analyze_complete_graph(self, central_user_email=None, emails_processed=0):
        """
        Effectue l'analyse complète du graphe

        Args:
            central_user_email (str): Email de l'utilisateur central
            emails_processed (int): Nombre d'emails traités

        Returns:
            dict: Résultats complets de l'analyse
        """
        logger.logger.info("📊 Début de l'analyse du graphe...")

        try:
            # Analyse principale
            analysis_result = self._perform_core_analysis(central_user_email)

            # Statistiques détaillées
            if ANALYSIS_CONFIG['include_stats']:
                stats = self._calculate_detailed_stats()
                analysis_result["stats"] = stats

            # Métadonnées
            if ANALYSIS_CONFIG['include_metadata']:
                metadata = self._generate_metadata(central_user_email, emails_processed)
                analysis_result["metadata"] = metadata

            logger.logger.info("✅ Analyse du graphe terminée avec succès")
            return analysis_result

        except Exception as e:
            logger.logger.error(f"❌ Erreur lors de l'analyse du graphe: {str(e)}")
            return self._generate_error_result(str(e))

    def _perform_core_analysis(self, central_user_email):
        """Effectue l'analyse principale du graphe"""
        result = {
            "central_user": central_user_email,
            "top_contacts": self._get_top_contacts(),
            "top_threads": self._get_top_threads(),
            "communication_network": self._extract_communication_network()
        }

        logger.logger.info(f"📈 Top contacts: {len(result['top_contacts'])}")
        logger.logger.info(f"🧵 Top threads: {len(result['top_threads'])}")

        return result

    def _get_top_contacts(self):
        """Récupère les top contacts"""
        try:
            return self.metrics_analyzer.get_top_contacts(ANALYSIS_CONFIG['top_contacts_limit'])
        except Exception as e:
            logger.logger.error(f"❌ Erreur calcul top contacts: {e}")
            return []

    def _get_top_threads(self):
        """Récupère les top threads"""
        try:
            return self.metrics_analyzer.get_top_threads(ANALYSIS_CONFIG['top_threads_limit'])
        except Exception as e:
            logger.logger.error(f"❌ Erreur calcul top threads: {e}")
            return []

    def _extract_communication_network(self):
        """Extrait le réseau de communication"""
        try:
            return self.network_extractor.extract_communication_network()
        except Exception as e:
            logger.logger.error(f"❌ Erreur extraction réseau communication: {e}")
            return {}

    def _calculate_detailed_stats(self):
        """Calcule les statistiques détaillées"""
        try:
            stats = self.metrics_analyzer.calculate_stats()

            # Ajouter des métriques du graphe
            stats.update({
                'graph_density': self._calculate_graph_density(),
                'connected_components': self._count_connected_components(),
                'average_degree': self._calculate_average_degree()
            })

            return stats

        except Exception as e:
            logger.logger.error(f"❌ Erreur calcul statistiques: {e}")
            return {}

    def _generate_metadata(self, central_user_email, emails_processed):
        """Génère les métadonnées de l'analyse"""
        return {
            "timestamp": datetime.now().isoformat(),
            "emails_processed": emails_processed,
            "central_user": central_user_email,
            "graph_info": {
                "nodes": self.graph.number_of_nodes(),
                "edges": self.graph.number_of_edges(),
                "is_directed": self.graph.is_directed(),
                "is_multigraph": self.graph.is_multigraph()
            }
        }

    def _calculate_graph_density(self):
        """Calcule la densité du graphe"""
        try:
            num_nodes = self.graph.number_of_nodes()
            num_edges = self.graph.number_of_edges()

            if num_nodes <= 1:
                return 0.0

            # Pour un graphe dirigé: densité = edges / (nodes * (nodes-1))
            max_edges = num_nodes * (num_nodes - 1)
            return num_edges / max_edges if max_edges > 0 else 0.0

        except Exception:
            return 0.0

    def _count_connected_components(self):
        """Compte les composants connexes"""
        try:
            # Convertir en graphe non-dirigé pour les composants connexes
            undirected = self.graph.to_undirected()
            import networkx as nx
            return nx.number_connected_components(undirected)
        except Exception:
            return 0

    def _calculate_average_degree(self):
        """Calcule le degré moyen des nœuds"""
        try:
            degrees = [self.graph.degree(node) for node in self.graph.nodes()]
            return sum(degrees) / len(degrees) if degrees else 0.0
        except Exception:
            return 0.0

    def _generate_error_result(self, error_message):
        """Génère un résultat d'erreur standardisé"""
        return {
            'status': 'error',
            'message': error_message,
            'central_user': None,
            'top_contacts': [],
            'top_threads': [],
            'communication_network': {},
            'stats': {},
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'error': True
            }
        }