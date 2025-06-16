"""
Service de calcul des scores et métriques de recherche.
"""

import re
import math
from datetime import datetime
from collections import defaultdict

from .config import TFIDF_CONFIG, SCORING_WEIGHTS


class SearchScoringService:
    """Service pour le calcul des scores de recherche"""

    def __init__(self, indexing_service):
        self.indexing = indexing_service

    def set_indexing_service(self, indexing_service):
        """Met à jour le service d'indexation"""
        self.indexing = indexing_service

    def calculate_content_scores(self, query, filters):
        """
        Calcule les scores de contenu avec TF-IDF

        Args:
            query (str): Requête textuelle
            filters (dict): Filtres à appliquer

        Returns:
            dict: Scores par message_id
        """
        results = defaultdict(lambda: defaultdict(float))

        if not query:
            return results

        # Tokeniser la requête
        query_tokens = set(re.findall(TFIDF_CONFIG['pattern'], query.lower()))

        # Calculer les scores TF-IDF pour chaque document
        for token in query_tokens:
            if token in self.indexing.inverted_index:
                idf = self.indexing.idf_scores.get(token, 1.0)

                for message_id in self.indexing.inverted_index[token]:
                    message_data = self.indexing.message_nodes.get(message_id, {})

                    # TF-IDF score
                    tf = message_data.get('_tf', {}).get(token, 0)
                    tfidf_score = tf * idf
                    results[message_id]['content'] += tfidf_score

                    # Bonus si le terme est dans le sujet
                    subject = message_data.get('subject', '').lower()
                    if token in subject:
                        results[message_id]['content'] += TFIDF_CONFIG['subject_bonus'] * idf

                    # Bonus pour la fraîcheur
                    freshness_score = self._calculate_freshness_score(message_data)
                    results[message_id]['temporal'] = freshness_score * 0.3

        # Normaliser les scores de contenu
        self._normalize_content_scores(results)

        return results

    def calculate_temporal_scores(self, message_ids, date_from, date_to=None):
        """
        Calcule les scores temporels pour une liste de messages

        Args:
            message_ids (list): IDs des messages
            date_from (datetime): Date de début
            date_to (datetime): Date de fin

        Returns:
            dict: Scores temporels par message_id
        """
        results = defaultdict(float)

        if not date_to:
            date_to = date_from.replace(hour=23, minute=59)

        total_range = (date_to - date_from).total_seconds()

        for message_id in message_ids:
            message_data = self.indexing.message_nodes.get(message_id, {})
            date_str = message_data.get('date')

            if not date_str:
                continue

            try:
                message_date = datetime.fromisoformat(date_str)

                # Score basé sur la proximité avec la date recherchée
                if total_range > 0:
                    distance = abs((message_date - date_from).total_seconds())
                    temporal_score = 1.0 - (distance / total_range)
                else:
                    temporal_score = 1.0

                results[message_id] = max(0.0, temporal_score)

            except Exception:
                continue

        return results

    def calculate_user_scores(self, user_matches, role_weights=None):
        """
        Calcule les scores utilisateur avec importance dans le réseau

        Args:
            user_matches (list): Liste de (user_id, match_score)
            role_weights (dict): Poids par rôle (sent/received)

        Returns:
            dict: Scores utilisateur par message_id
        """
        if role_weights is None:
            role_weights = {'sent': 1.0, 'received': 0.7}

        results = defaultdict(float)

        for user_id, user_match_score in user_matches:
            user_importance = self.indexing.user_pagerank.get(user_id, 0.5)

            # Messages envoyés
            for message_id in self.indexing.user_sent_index.get(user_id, []):
                score = user_match_score * user_importance * role_weights['sent']
                results[message_id] = max(results[message_id], score)

            # Messages reçus
            for message_id in self.indexing.user_received_index.get(user_id, []):
                score = user_match_score * user_importance * role_weights['received']
                results[message_id] = max(results[message_id], score)

        return results

    def calculate_graph_scores(self, message_ids):
        """
        Calcule les scores basés sur le graphe (centralité des expéditeurs)

        Args:
            message_ids (list): IDs des messages

        Returns:
            dict: Scores de graphe par message_id
        """
        results = defaultdict(float)

        for message_id in message_ids:
            # Trouver l'expéditeur
            for user_id, _, edge_data in self.indexing.graph.in_edges(message_id, data=True):
                if edge_data.get('type') == 'SENT':
                    user_importance = self.indexing.user_pagerank.get(user_id, 0.0)
                    results[message_id] = user_importance
                    break

        return results

    def calculate_total_scores(self, score_components):
        """
        Calcule les scores totaux à partir des composants

        Args:
            score_components (dict): Dictionnaire des scores par type

        Returns:
            dict: Scores totaux par message_id
        """
        total_scores = defaultdict(float)

        # Rassembler tous les message_ids
        all_message_ids = set()
        for scores in score_components.values():
            all_message_ids.update(scores.keys())

        # Calculer le score total pour chaque message
        for message_id in all_message_ids:
            total_score = 0.0
            for score_type, weight in SCORING_WEIGHTS.items():
                score = score_components.get(score_type, {}).get(message_id, 0.0)
                total_score += score * weight

            total_scores[message_id] = total_score

        return total_scores

    def _calculate_freshness_score(self, message_data):
        """Calcule le score de fraîcheur d'un message"""
        date_str = message_data.get('date')
        if not date_str:
            return 0.0

        try:
            message_date = datetime.fromisoformat(date_str)
            days_old = (datetime.now() - message_date).days
            return math.exp(-days_old / TFIDF_CONFIG['freshness_decay_days'])
        except Exception:
            return 0.0

    def _normalize_content_scores(self, results):
        """Normalise les scores de contenu"""
        max_content_score = max(
            (scores['content'] for scores in results.values()),
            default=1.0
        )

        if max_content_score > 0:
            for message_id in results:
                results[message_id]['content'] /= max_content_score