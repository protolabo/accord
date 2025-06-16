"""
Service de construction et gestion des index de recherche.
"""

import re
import math
from datetime import datetime, timedelta
from collections import defaultdict
import networkx as nx

from ..logging_service import logger
from ..shared_utils import parse_email_date
from .config import TFIDF_CONFIG, PAGERANK_CONFIG


class SearchIndexingService:
    """Service pour la construction et la gestion des index de recherche"""

    def __init__(self, graph):
        self.user_degree_centrality = None
        self.user_pagerank = None
        self.idf_scores = None
        self.document_frequency = None
        self.thread_messages_index = None
        self.user_received_index = None
        self.user_sent_index = None
        self.inverted_index = None
        self.temporal_index = None
        self.thread_nodes = None
        self.user_nodes = None
        self.message_nodes = None
        self.graph = graph
        self.reset_indexes()

    def set_graph(self, graph):
        """Met à jour l'instance de graphe"""
        self.graph = graph

    def reset_indexes(self):
        """Réinitialise tous les index"""
        # Index par type de nœud
        self.message_nodes = {}
        self.user_nodes = {}
        self.thread_nodes = {}

        # Index temporel (clé temporelle -> messages)
        self.temporal_index = defaultdict(list)

        # Index textuel inversé (terme -> messages)
        self.inverted_index = defaultdict(set)

        # Index utilisateur -> messages
        self.user_sent_index = defaultdict(set)
        self.user_received_index = defaultdict(set)

        # Index thread -> messages
        self.thread_messages_index = defaultdict(set)

        # TF-IDF
        self.document_frequency = defaultdict(int)
        self.idf_scores = {}

        # Métriques du graphe
        self.user_pagerank = {}
        self.user_degree_centrality = {}

    def build_all_indexes(self):
        """Construit tous les index nécessaires pour la recherche rapide"""
        logger.logger.info("Construction des index de recherche...")

        self.reset_indexes()
        total_messages = 0

        # Première passe : collecter les données et construire les index de base
        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get('type', '')

            if node_type == 'message':
                self.message_nodes[node_id] = data
                total_messages += 1

                self._index_message_temporal(node_id, data)
                self._index_message_textual(node_id, data)
                self._index_message_user_relations(node_id)
                self._index_message_thread_relations(node_id)

            elif node_type == 'user':
                self.user_nodes[node_id] = data

            elif node_type == 'thread':
                self.thread_nodes[node_id] = data

        # Calculer les scores IDF
        self._calculate_idf_scores(total_messages)

        # Calculer les métriques du graphe
        self._calculate_graph_metrics()

        logger.logger.info(f"Index créés: {len(self.message_nodes)} messages, "
                           f"{len(self.user_nodes)} utilisateurs, {len(self.thread_nodes)} threads")

    def _index_message_temporal(self, message_id, data):
        """Indexe un message par sa date"""
        date_str = data.get('date')

        if not date_str:
            return

        try:
            # Parser la date ISO
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))

            # Index par différentes granularités temporelles
            day_key = date.strftime('%Y-%m-%d')
            week_key = f"{date.year}-W{date.isocalendar()[1]:02d}"
            month_key = date.strftime('%Y-%m')

            self.temporal_index[day_key].append(message_id)
            self.temporal_index[week_key].append(message_id)
            self.temporal_index[month_key].append(message_id)

        except Exception as e:
            logger.logger.warning(f"❌ Erreur parsing date pour {message_id} ({date_str}): {e}")

    def _index_message_textual(self, message_id, data):
        """Indexe le contenu textuel d'un message"""
        # Combiner sujet et contenu
        text = f"{data.get('subject', '')} {data.get('content', '')}".lower()

        # Tokenisation selon la configuration
        tokens = re.findall(TFIDF_CONFIG['pattern'], text)

        # Compter les occurrences pour TF
        term_frequency = defaultdict(int)
        for token in tokens:
            if len(token) >= TFIDF_CONFIG['min_term_length']:
                term_frequency[token] += 1
                self.inverted_index[token].add(message_id)

        # Stocker TF normalisé
        max_freq = max(term_frequency.values()) if term_frequency else 1
        data['_tf'] = {term: freq / max_freq for term, freq in term_frequency.items()}

        # Mettre à jour DF
        for term in set(tokens):
            if len(term) >= TFIDF_CONFIG['min_term_length']:
                self.document_frequency[term] += 1

    def _index_message_user_relations(self, message_id):
        """Indexe les relations entre messages et utilisateurs"""
        # Messages envoyés
        for user_id, _, edge_data in self.graph.in_edges(message_id, data=True):
            if edge_data.get('type') == 'SENT':
                self.user_sent_index[user_id].add(message_id)

        # Messages reçus
        for _, user_id, edge_data in self.graph.out_edges(message_id, data=True):
            if edge_data.get('type') in ['RECEIVED', 'CC', 'BCC']:
                self.user_received_index[user_id].add(message_id)

    def _index_message_thread_relations(self, message_id):
        """Indexe les relations entre messages et threads"""
        for _, thread_id, edge_data in self.graph.out_edges(message_id, data=True):
            if edge_data.get('type') == 'PART_OF_THREAD':
                self.thread_messages_index[thread_id].add(message_id)

    def _calculate_idf_scores(self, total_messages):
        """Calcule les scores IDF pour chaque terme"""
        self.idf_scores = {}
        for term, doc_count in self.document_frequency.items():
            self.idf_scores[term] = math.log(total_messages / (1 + doc_count))

    def _calculate_graph_metrics(self):
        """Calcule les métriques du graphe pour le scoring"""
        logger.logger.info("Calcul des métriques du graphe...")

        # PageRank pour l'importance des utilisateurs
        try:
            user_subgraph = self.graph.subgraph([n for n in self.graph.nodes()
                                                 if self.graph.nodes[n].get('type') == 'user'])

            if user_subgraph.number_of_nodes() > 0:
                self.user_pagerank = nx.pagerank(
                    user_subgraph,
                    alpha=PAGERANK_CONFIG['alpha'],
                    max_iter=PAGERANK_CONFIG['max_iter'],
                    tol=PAGERANK_CONFIG['tol']
                )
            else:
                self.user_pagerank = {}

        except Exception as e:
            logger.logger.error(f"Erreur calcul PageRank: {e}")
            self.user_pagerank = {}

        # Centralité de degré pour les utilisateurs
        self.user_degree_centrality = {}
        for user_id in self.user_nodes:
            in_degree = self.graph.in_degree(user_id)
            out_degree = self.graph.out_degree(user_id)
            self.user_degree_centrality[user_id] = in_degree + out_degree

    def get_index_stats(self):
        """Retourne les statistiques des index"""
        return {
            'messages': len(self.message_nodes),
            'users': len(self.user_nodes),
            'threads': len(self.thread_nodes),
            'temporal_keys': len(self.temporal_index),
            'unique_terms': len(self.inverted_index),
            'user_pagerank_entries': len(self.user_pagerank)
        }