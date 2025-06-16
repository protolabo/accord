"""
Gestionnaire principal du moteur de recherche dans le graphe NetworkX.
"""

import networkx as nx
from typing import Dict, Any, List

from ..logging_service import logger
from .config import SearchMode
from .indexing_service import SearchIndexingService
from .scoring_service import SearchScoringService
from .search_service import SearchService
from .result_service import SearchResultService, SearchResult


class GraphSearchEngine:
    """
    Moteur de recherche dans le graphe NetworkX pour Accord.
    Gère la recherche par contenu, temporelle et par utilisateur selon le scoring de pertinence.
    """

    def __init__(self, graph: nx.MultiDiGraph):
        """
        Initialise le moteur de recherche

        Args:
            graph: Graphe NetworkX contenant les emails
        """
        self.graph = graph

        # Initialiser les services
        self.indexing_service = SearchIndexingService(graph)
        self.scoring_service = SearchScoringService(self.indexing_service)
        self.search_service = SearchService(self.indexing_service, self.scoring_service)
        self.result_service = SearchResultService(self.indexing_service, self.scoring_service)

        # Construire les index
        self._build_indexes()
        self._calculate_node_metrics()

    def _build_indexes(self):
        """Construit tous les index nécessaires pour la recherche rapide"""
        self.indexing_service.build_all_indexes()

    def _calculate_node_metrics(self):
        """Calcule les métriques du graphe pour le scoring"""
        # Les métriques sont calculées dans le service d'indexation
        stats = self.indexing_service.get_index_stats()
        logger.logger.info(f"Métriques calculées: {stats}")

    def search(self, semantic_query: Dict[str, Any]) -> List[SearchResult]:
        """
        Recherche principale avec scoring avancé

        Args:
            semantic_query: Requête parsée contenant type, texte, filtres, etc.

        Returns:
            Liste des résultats triés par pertinence avec métadonnées complètes
        """
        query_type = semantic_query.get('query_type', 'semantic')
        semantic_text = semantic_query.get('semantic_text', '')
        filters = semantic_query.get('filters', {})
        limit = semantic_query.get('limit', 10)

        # Déterminer le mode de recherche
        mode = self._determine_search_mode(query_type, filters)

        # Exécuter la recherche selon le mode
        search_results = self._execute_search_by_mode(mode, semantic_text, filters)

        # Créer et enrichir les résultats
        enriched_results = self.result_service.create_search_results(
            search_results, semantic_text, limit
        )

        logger.logger.info(f"Recherche terminée: {len(enriched_results)} résultats trouvés")
        return enriched_results

    def _determine_search_mode(self, query_type: str, filters: Dict[str, Any]) -> SearchMode:
        """Détermine le mode de recherche optimal"""
        if query_type == 'contact' or filters.get('contact_email') or filters.get('contact_name'):
            return SearchMode.USER
        elif query_type == 'time_range' or filters.get('date_from'):
            return SearchMode.TEMPORAL
        elif query_type == 'semantic':
            return SearchMode.CONTENT
        else:
            return SearchMode.COMBINED

    def _execute_search_by_mode(self, mode: SearchMode, semantic_text: str, filters: Dict[str, Any]) -> Dict[
        str, Dict[str, float]]:
        """
        Exécute la recherche selon le mode déterminé

        Args:
            mode: Mode de recherche
            semantic_text: Texte de la requête
            filters: Filtres à appliquer

        Returns:
            Résultats de recherche par message_id
        """
        logger.logger.info(f"Exécution recherche mode: {mode.value}")

        if mode == SearchMode.CONTENT:
            return self.search_service.search_by_content(semantic_text, filters)
        elif mode == SearchMode.TEMPORAL:
            return self.search_service.search_by_temporal(filters, semantic_text)
        elif mode == SearchMode.USER:
            return self.search_service.search_by_user(filters, semantic_text)
        else:  # COMBINED
            return self.search_service.search_combined(semantic_text, filters)

    def get_search_statistics(self):
        """
        Retourne les statistiques du moteur de recherche

        Returns:
            dict: Statistiques détaillées
        """
        return {
            'index_stats': self.indexing_service.get_index_stats(),
            'graph_info': {
                'nodes': self.graph.number_of_nodes(),
                'edges': self.graph.number_of_edges(),
                'is_directed': self.graph.is_directed(),
                'is_multigraph': self.graph.is_multigraph()
            }
        }

    def rebuild_indexes(self):
        """
        Reconstruit tous les index (utile après modification du graphe)
        """
        logger.logger.info("Reconstruction des index de recherche...")
        self.indexing_service.build_all_indexes()
        logger.logger.info("Index reconstruits avec succès")

    def update_graph(self, new_graph: nx.MultiDiGraph):
        """
        Met à jour le graphe et reconstruit les index

        Args:
            new_graph: Nouveau graphe NetworkX
        """
        self.graph = new_graph

        # Mettre à jour tous les services
        self.indexing_service.set_graph(new_graph)
        self.scoring_service.set_indexing_service(self.indexing_service)
        self.search_service.set_services(self.indexing_service, self.scoring_service)
        self.result_service.set_services(self.indexing_service, self.scoring_service)

        # Reconstruire les index
        self.rebuild_indexes()

    # Méthodes de compatibilité (pour maintenir l'API existante)
    def _search_by_content(self, query: str, filters: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Méthode de compatibilité"""
        return self.search_service.search_by_content(query, filters)

    def _search_by_temporal(self, filters: Dict[str, Any], query: str = '') -> Dict[str, Dict[str, float]]:
        """Méthode de compatibilité"""
        return self.search_service.search_by_temporal(filters, query)

    def _search_by_user(self, filters: Dict[str, Any], query: str = '') -> Dict[str, Dict[str, float]]:
        """Méthode de compatibilité"""
        return self.search_service.search_by_user(filters, query)

    def _search_combined(self, query: str, filters: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Méthode de compatibilité"""
        return self.search_service.search_combined(query, filters)