"""
Moteur de recherche dans le graphe NetworkX pour Accord.
 la recherche par contenu, temporelle et par utilisateur selon le scoring de pertinence.
"""

import networkx as nx
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import re
import math
from collections import defaultdict
from enum import Enum


class SearchMode(Enum):
    """Modes de recherche disponibles"""
    CONTENT = "content"  # Recherche par contenu textuel
    TEMPORAL = "temporal"  # Recherche par période
    USER = "user"  # Recherche par utilisateur
    COMBINED = "combined"  # Recherche combinée


@dataclass
class SearchResult:
    """Résultat de recherche enrichi avec métadonnées complètes"""
    # Identifiants
    message_id: str
    thread_id: Optional[str] = None

    # Scores
    total_score: float = 0.0
    content_score: float = 0.0
    temporal_score: float = 0.0
    user_score: float = 0.0
    graph_score: float = 0.0

    # Métadonnées du message
    subject: str = ""
    content: str = ""
    sender_email: str = ""
    sender_name: str = ""
    recipients: List[Dict[str, str]] = field(default_factory=list)
    cc_recipients: List[Dict[str, str]] = field(default_factory=list)
    bcc_recipients: List[Dict[str, str]] = field(default_factory=list)
    date: str = ""
    timestamp: Optional[datetime] = None

    # Attributs additionnels
    has_attachments: bool = False
    attachment_count: int = 0
    is_important: bool = False
    is_unread: bool = False
    labels: List[str] = field(default_factory=list)

    # Contexte du graphe
    thread_size: int = 1
    reply_count: int = 0
    participants_count: int = 0
    sender_centrality: float = 0.0
    content_snippet: str = ""
    matched_terms: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convertit le résultat en dictionnaire avec toutes les métadonnées"""
        return {
            'message_id': self.message_id,
            'thread_id': self.thread_id,
            'scores': {
                'total': round(self.total_score, 3),
                'content': round(self.content_score, 3),
                'temporal': round(self.temporal_score, 3),
                'user': round(self.user_score, 3),
                'graph': round(self.graph_score, 3)
            },
            'metadata': {
                'subject': self.subject,
                'sender': {
                    'email': self.sender_email,
                    'name': self.sender_name,
                    'centrality': round(self.sender_centrality, 3)
                },
                'recipients': {
                    'to': self.recipients,
                    'cc': self.cc_recipients,
                    'bcc': self.bcc_recipients,
                    'total_count': len(self.recipients) + len(self.cc_recipients) + len(self.bcc_recipients)
                },
                'date': self.date,
                'timestamp': self.timestamp.isoformat() if self.timestamp else None,
                'attributes': {
                    'has_attachments': self.has_attachments,
                    'attachment_count': self.attachment_count,
                    'is_important': self.is_important,
                    'is_unread': self.is_unread,
                    'labels': self.labels
                },
                'thread_info': {
                    'thread_size': self.thread_size,
                    'reply_count': self.reply_count,
                    'participants_count': self.participants_count
                }
            },
            'snippet': self.content_snippet,
            'matched_terms': self.matched_terms
        }


class GraphSearchEngine:
    """
    Moteur de recherche dans le graphe NetworkX pour Accord.
    """

    def __init__(self, graph: nx.MultiDiGraph):
        """
        Initialise le moteur de recherche

        Args:
            graph: Graphe NetworkX contenant les emails
        """
        self.graph = graph
        self._build_indexes()
        self._calculate_node_metrics()

    def _build_indexes(self):
        """Construit tous les index nécessaires pour la recherche rapide"""
        print("Construction des index de recherche...")

        # Index par type de nœud
        self.message_nodes = {}
        self.user_nodes = {}
        self.thread_nodes = {}

        # Index temporel (année-mois -> messages)
        self.temporal_index = defaultdict(list)

        # Index textuel inversé (terme -> messages)
        self.inverted_index = defaultdict(set)

        # Index utilisateur -> messages
        self.user_sent_index = defaultdict(set)
        self.user_received_index = defaultdict(set)

        # Index thread -> messages
        self.thread_messages_index = defaultdict(set)

        # TF-IDF: Document frequency
        self.document_frequency = defaultdict(int)
        total_messages = 0

        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get('type', '')

            if node_type == 'message':
                self.message_nodes[node_id] = data
                total_messages += 1

                # Index temporel
                self._index_temporal(node_id, data)

                # Index textuel
                self._index_textual(node_id, data)

                # Index des relations utilisateur
                self._index_user_relations(node_id)

                # Index des threads
                self._index_thread_relations(node_id)

            elif node_type == 'user':
                self.user_nodes[node_id] = data

            elif node_type == 'thread':
                self.thread_nodes[node_id] = data

        # Calculer IDF pour chaque terme
        self.idf_scores = {}
        for term, doc_count in self.document_frequency.items():
            self.idf_scores[term] = math.log(total_messages / (1 + doc_count))

        print(f"Index créés: {len(self.message_nodes)} messages, "
              f"{len(self.user_nodes)} utilisateurs, {len(self.thread_nodes)} threads")

    def _index_temporal(self, message_id: str, data: Dict[str, Any]):
        """Indexe un message par sa date - VERSION CORRIGÉE"""
        date_str = data.get('date')

        if not date_str:
            print(f" Pas de date pour {message_id}: {data}")
            return

        try:
            # Parser la date ISO
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))

            # Index par jour, semaine, mois
            day_key = date.strftime('%Y-%m-%d')
            week_key = f"{date.year}-W{date.isocalendar()[1]:02d}"
            month_key = date.strftime('%Y-%m')

            self.temporal_index[day_key].append(message_id)
            self.temporal_index[week_key].append(message_id)
            self.temporal_index[month_key].append(message_id)

        except Exception as e:
            print(f"❌ Erreur parsing date pour {message_id} ({date_str}): {e}")

    def _index_textual(self, message_id: str, data: Dict[str, Any]):
        """Indexe le contenu textuel d'un message"""
        # Combiner sujet et contenu
        text = f"{data.get('subject', '')} {data.get('content', '')}".lower()

        # Tokenization
        tokens = re.findall(r'\b[a-zA-Z0-9À-ÿ]{3,}\b', text)

        # Compter les occurrences pour TF
        term_frequency = defaultdict(int)
        for token in tokens:
            term_frequency[token] += 1
            self.inverted_index[token].add(message_id)

        # Stocker TF normalisé
        max_freq = max(term_frequency.values()) if term_frequency else 1
        data['_tf'] = {term: freq / max_freq for term, freq in term_frequency.items()}

        # Mettre à jour DF
        for term in set(tokens):
            self.document_frequency[term] += 1

    def _index_user_relations(self, message_id: str):
        """Indexe les relations entre messages et utilisateurs"""
        # Messages envoyés
        for user_id, _, edge_data in self.graph.in_edges(message_id, data=True):
            if edge_data.get('type') == 'SENT':
                self.user_sent_index[user_id].add(message_id)

        # Messages reçus
        for _, user_id, edge_data in self.graph.out_edges(message_id, data=True):
            if edge_data.get('type') in ['RECEIVED', 'CC', 'BCC']:
                self.user_received_index[user_id].add(message_id)

    def _index_thread_relations(self, message_id: str):
        """Indexe les relations entre messages et threads"""
        for _, thread_id, edge_data in self.graph.out_edges(message_id, data=True):
            if edge_data.get('type') == 'PART_OF_THREAD':
                self.thread_messages_index[thread_id].add(message_id)

    def _calculate_node_metrics(self):
        """Calcule les métriques du graphe pour le scoring"""
        print("Calcul des métriques du graphe...")

        # PageRank pour l'importance des utilisateurs
        try:
            # Créer un sous-graphe avec seulement les utilisateurs
            user_subgraph = self.graph.subgraph([n for n in self.graph.nodes()
                                                 if self.graph.nodes[n].get('type') == 'user'])

            if user_subgraph.number_of_nodes() > 0:
                self.user_pagerank = nx.pagerank(user_subgraph, alpha=0.85)
            else:
                self.user_pagerank = {}

        except Exception as e:
            print(f"Erreur calcul PageRank: {e}")
            self.user_pagerank = {}

        # Centralité de degré pour les utilisateurs
        self.user_degree_centrality = {}
        for user_id in self.user_nodes:
            in_degree = self.graph.in_degree(user_id)
            out_degree = self.graph.out_degree(user_id)
            self.user_degree_centrality[user_id] = in_degree + out_degree

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
        if mode == SearchMode.CONTENT:
            results = self._search_by_content(semantic_text, filters)
        elif mode == SearchMode.TEMPORAL:
            results = self._search_by_temporal(filters, semantic_text)
        elif mode == SearchMode.USER:
            results = self._search_by_user(filters, semantic_text)
        else:  # COMBINED
            results = self._search_combined(semantic_text, filters)

        # Enrichir les résultats avec toutes les métadonnées
        enriched_results = []
        for message_id, scores in results.items():
            result = self._create_search_result(message_id, scores, semantic_text)
            if result:
                enriched_results.append(result)

        # Trier par score total
        enriched_results.sort(key=lambda r: r.total_score, reverse=True)

        return enriched_results[:limit]

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

    def _search_by_content(self, query: str, filters: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Recherche par contenu avec TF-IDF et scoring avancé

        Returns:
            Dict[message_id, Dict[score_type, score_value]]
        """
        results = defaultdict(lambda: defaultdict(float))

        if not query:
            return results

        # Tokenizer la requête
        query_tokens = set(re.findall(r'\b[a-zA-Z0-9À-ÿ]{3,}\b', query.lower()))

        # Calculer les scores TF-IDF pour chaque document
        for token in query_tokens:
            if token in self.inverted_index:
                idf = self.idf_scores.get(token, 1.0)

                for message_id in self.inverted_index[token]:
                    message_data = self.message_nodes.get(message_id, {})

                    # Appliquer les filtres
                    if not self._apply_filters(message_id, message_data, filters):
                        continue

                    # TF-IDF score
                    tf = message_data.get('_tf', {}).get(token, 0)
                    tfidf_score = tf * idf
                    results[message_id]['content'] += tfidf_score

                    # Bonus si le terme est dans le sujet
                    subject = message_data.get('subject', '').lower()
                    if token in subject:
                        results[message_id]['content'] += 0.5 * idf

                    # Bonus pour la fraîcheur (decay temporel)
                    date_str = message_data.get('date')
                    if date_str:
                        try:
                            message_date = datetime.fromisoformat(date_str)
                            days_old = (datetime.now() - message_date).days
                            freshness_score = math.exp(-days_old / 30)  # Decay sur 30 jours
                            results[message_id]['temporal'] = freshness_score * 0.3
                        except:
                            pass

        # Normaliser les scores de contenu
        max_content_score = max((scores['content'] for scores in results.values()), default=1.0)
        for message_id in results:
            if max_content_score > 0:
                results[message_id]['content'] /= max_content_score

        return results

    def _search_by_temporal(self, filters: Dict[str, Any], query: str = '') -> Dict[str, Dict[str, float]]:
        """Recherche par période temporelle avec scoring"""
        results = defaultdict(lambda: defaultdict(float))

        date_from_str = filters.get('date_from')
        date_to_str = filters.get('date_to')

        if not date_from_str:
            return results

        try:
            date_from = datetime.fromisoformat(date_from_str)
            date_to = datetime.fromisoformat(date_to_str) if date_to_str else date_from.replace(hour=23, minute=59)

            # Rechercher dans l'index temporel
            current_date = date_from
            while current_date <= date_to:
                day_key = current_date.strftime('%Y-%m-%d')

                for message_id in self.temporal_index.get(day_key, []):
                    message_data = self.message_nodes.get(message_id, {})

                    # Appliquer les filtres
                    if not self._apply_filters(message_id, message_data, filters):
                        continue

                    # Score temporel basé sur la proximité avec la date recherchée
                    message_date = datetime.fromisoformat(message_data['date'])

                    # Distance temporelle normalisée
                    total_range = (date_to - date_from).total_seconds()
                    if total_range > 0:
                        distance = abs((message_date - date_from).total_seconds())
                        temporal_score = 1.0 - (distance / total_range)
                    else:
                        temporal_score = 1.0

                    results[message_id]['temporal'] = temporal_score

                    # Si une requête textuelle est fournie, ajouter le score de contenu
                    if query:
                        content_results = self._search_by_content(query, filters)
                        if message_id in content_results:
                            results[message_id]['content'] = content_results[message_id]['content']

                current_date += timedelta(days=1)

        except Exception as e:
            print(f"Erreur recherche temporelle: {e}")

        return results

    def _search_by_user(self, filters: Dict[str, Any], query: str = '') -> Dict[str, Dict[str, float]]:
        """Recherche par utilisateur avec matching flexible"""
        results = defaultdict(lambda: defaultdict(float))

        contact_email = filters.get('contact_email', '').lower()
        contact_name = filters.get('contact_name', '').lower()

        if not contact_email and not contact_name:
            return results


        # Trouver les utilisateurs correspondants avec matching flexible
        matching_users = []
        for user_id, user_data in self.user_nodes.items():
            email = user_data.get('email', '').lower()
            name = user_data.get('name', '').lower()

            print(f"   Comparaison avec {name} <{email}>")

            match_score = 0

            # Match par email (exact ou contient)
            if contact_email:
                if contact_email == email:
                    match_score = 1.0
                elif contact_email in email or email in contact_email:
                    match_score = 0.8

            # Match par nom (exact, contient, ou prénom)
            if contact_name and match_score == 0:
                if contact_name == name:
                    match_score = 1.0
                elif contact_name in name or name in contact_name:
                    match_score = 0.9
                # Match prénom seulement (Marie vs Marie Dupont)
                elif ' ' in name and contact_name == name.split()[0]:
                    match_score = 0.85

            if match_score > 0:
                matching_users.append((user_id, match_score))
                print(f"   Match trouvé: {name} (score: {match_score})")

        #print(f"🎯 {len(matching_users)} utilisateur(s) correspondant(s)")

        # Pour chaque utilisateur trouvé
        for user_id, user_match_score in matching_users:
            # Importance de l'utilisateur dans le réseau
            user_importance = self.user_pagerank.get(user_id, 0.5)

            # Messages envoyés par l'utilisateur
            for message_id in self.user_sent_index.get(user_id, []):
                message_data = self.message_nodes.get(message_id, {})

                if not self._apply_filters(message_id, message_data, filters):
                    continue

                # Score utilisateur = match * importance * rôle
                results[message_id]['user'] = user_match_score * user_importance * 1.0
                results[message_id]['graph'] = user_importance

                # Ajouter score de contenu si requête fournie
                if query:
                    content_results = self._search_by_content(query, filters)
                    if message_id in content_results:
                        results[message_id]['content'] = content_results[message_id]['content']

            # Messages reçus (score plus faible)
            for message_id in self.user_received_index.get(user_id, []):
                message_data = self.message_nodes.get(message_id, {})

                if not self._apply_filters(message_id, message_data, filters):
                    continue

                # Score réduit pour les messages reçus
                current_score = results[message_id]['user']
                new_score = user_match_score * user_importance * 0.7
                results[message_id]['user'] = max(current_score, new_score)
                results[message_id]['graph'] = user_importance

        return results

    def _search_by_topic(self, filters: Dict[str, Any], query: str = '') -> Dict[str, Dict[str, float]]:
        """Recherche par topics avec mapping flexible"""
        results = defaultdict(lambda: defaultdict(float))

        topic_ids = filters.get('topic_ids', [])
        if not topic_ids:
            return results

        # Dédupliquer les topics d'entrée
        topic_ids = list(set(topic_ids))

        # Mapping plus restrictif
        topic_mappings = {
            'facturation': ['facture', 'bill', 'billing', 'invoice'],
            'projet': ['project'],
            'ia': ['intelligence artificielle', 'ai'],
            'newsletter': ['actualités', 'news'],
            'meeting': ['réunion', 'meeting'],
            'important': ['important', 'urgent', 'critique'],
            'rapport': ['report', 'rapport']
        }

        # Étendre les topics avec leurs synonymes
        expanded_topics = set()
        for topic_id in topic_ids:
            expanded_topics.add(topic_id.lower())
            if topic_id.lower() in topic_mappings:
                expanded_topics.update(topic_mappings[topic_id.lower()])

        print(f" ===> Topics étendus: {expanded_topics}")

        # Chercher dans tous les messages
        for message_id, message_data in self.message_nodes.items():
            score = 0.0

            # 1. Score pour topics explicites du message
            message_topics = [t.lower() for t in message_data.get('topics', [])]
            topic_overlap = set(message_topics).intersection(expanded_topics)
            if topic_overlap:
                score += len(topic_overlap) * 2.0

            # 2. Score pour termes dans le sujet
            subject = message_data.get('subject', '').lower()
            for topic in expanded_topics:
                if topic in subject:
                    score += 1.5
            # 3. Score pour termes dans le contenu
            content = message_data.get('content', '').lower()
            for topic in expanded_topics:
                if topic in content:
                    score += 1.0

            if score > 0:
                results[message_id]['content'] = score

        print(f"🎯 {len(results)} message(s) trouvé(s) par topics")
        return results

    def _search_combined(self, query: str, filters: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Recherche combinée avec fusion des scores"""
        combined_results = defaultdict(lambda: defaultdict(float))

        has_multiple_filters = sum([
            bool(filters.get('topic_ids')),
            bool(filters.get('has_attachments')),
            bool(filters.get('contact_name') or filters.get('contact_email')),
            bool(filters.get('date_from'))
        ]) > 1

        all_results = []

        # Recherche par contenu
        if query:
            content_results = self._search_by_content(query, filters)
            all_results.append(set(content_results.keys()))

        # Recherche par topics
        if filters.get('topic_ids'):
            topic_results = self._search_by_topic(filters, query)
            all_results.append(set(topic_results.keys()))
            for msg_id, scores in topic_results.items():
                combined_results[msg_id].update(scores)

        # Si on a plusieurs critères, faire l'INTERSECTION
        if has_multiple_filters and all_results:
            # Garder seulement les messages présents dans TOUS les résultats
            valid_messages = set.intersection(*all_results) if all_results else set()

            # Filtrer les résultats combinés
            filtered_results = defaultdict(lambda: defaultdict(float))
            for msg_id in valid_messages:
                # Vérifier aussi les filtres booléens
                message_data = self.message_nodes.get(msg_id, {})
                if self._apply_filters(msg_id, message_data, filters):
                    filtered_results[msg_id] = combined_results[msg_id]

            return filtered_results

        # Sinon, retourner tous les résultats (OR)
        return combined_results

    def _apply_filters(self, message_id: str, message_data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Applique les filtres additionnels"""
        if filters.get('has_attachments') is not None:
            message_has_attachments = message_data.get('has_attachments', False)
            if filters['has_attachments'] != message_has_attachments:
                return False

        if filters.get('contact_name'):
            sender_name = message_data.get('sender_name', '').lower()
            filter_name = filters['contact_name'].lower()
            if filter_name not in sender_name:
                # Vérifier aussi via les relations du graphe
                sender_found = False
                for user_id, _, edge_data in self.graph.in_edges(message_id, data=True):
                    if edge_data.get('type') == 'SENT':
                        user_data = self.user_nodes.get(user_id, {})
                        if filter_name in user_data.get('name', '').lower():
                            sender_found = True
                            break
                if not sender_found:
                    return False

        if filters.get('is_unread') and not message_data.get('is_unread', True):
            return False

        if filters.get('is_important') and not message_data.get('is_important'):
            return False

        if filters.get('topic_ids'):
            message_topics = set(message_data.get('topics', []))
            filter_topics = set(filters['topic_ids'])
            if not message_topics.intersection(filter_topics):
                return False

        return True

    def _create_search_result(self, message_id: str, scores: Dict[str, float], query: str) -> Optional[SearchResult]:
        """Crée un résultat de recherche avec toutes les métadonnées"""
        message_data = self.message_nodes.get(message_id)
        if not message_data:
            return None

        # Calculer le score total
        weights = {
            'content': 0.4,
            'temporal': 0.2,
            'user': 0.3,
            'graph': 0.1
        }

        total_score = sum(scores.get(k, 0) * v for k, v in weights.items())

        # Extraire les métadonnées de l'expéditeur
        sender_id = None
        sender_name = ""
        sender_email = message_data.get('from', '')

        for user_id, _, edge_data in self.graph.in_edges(message_id, data=True):
            if edge_data.get('type') == 'SENT':
                sender_id = user_id
                sender_data = self.user_nodes.get(user_id, {})
                sender_name = sender_data.get('name', '')
                sender_email = sender_data.get('email', sender_email)
                break

        # Centralité de l'expéditeur
        sender_centrality = self.user_pagerank.get(sender_id, 0.0) if sender_id else 0.0

        # Extraire les destinataires
        recipients = []
        cc_recipients = []
        bcc_recipients = []

        for _, user_id, edge_data in self.graph.out_edges(message_id, data=True):
            edge_type = edge_data.get('type')
            if edge_type in ['RECEIVED', 'CC', 'BCC']:
                user_data = self.user_nodes.get(user_id, {})
                recipient_info = {
                    'email': user_data.get('email', ''),
                    'name': user_data.get('name', '')
                }

                if edge_type == 'RECEIVED':
                    recipients.append(recipient_info)
                elif edge_type == 'CC':
                    cc_recipients.append(recipient_info)
                elif edge_type == 'BCC':
                    bcc_recipients.append(recipient_info)

        thread_id = None
        thread_size = 1
        for _, tid, edge_data in self.graph.out_edges(message_id, data=True):
            if edge_data.get('type') == 'PART_OF_THREAD':
                thread_id = tid
                thread_size = len(self.thread_messages_index.get(tid, []))
                break

        content = message_data.get('content', '')
        snippet, matched_terms = self._create_snippet(content, query)

        # Parser la date
        timestamp = None
        date_str = message_data.get('date', '')
        if date_str:
            try:
                timestamp = datetime.fromisoformat(date_str)
            except:
                pass

        # Créer le résultat
        return SearchResult(
            message_id=message_id,
            thread_id=thread_id,
            total_score=total_score,
            content_score=scores.get('content', 0),
            temporal_score=scores.get('temporal', 0),
            user_score=scores.get('user', 0),
            graph_score=scores.get('graph', 0),
            subject=message_data.get('subject', ''),
            content=content,
            sender_email=sender_email,
            sender_name=sender_name,
            recipients=recipients,
            cc_recipients=cc_recipients,
            bcc_recipients=bcc_recipients,
            date=date_str,
            timestamp=timestamp,
            has_attachments=message_data.get('has_attachments', False),
            attachment_count=message_data.get('attachment_count', 0),
            is_important=message_data.get('is_important', False),
            is_unread=message_data.get('is_unread', True),
            labels=message_data.get('labels', []),
            thread_size=thread_size,
            reply_count=message_data.get('reply_count', 0),
            participants_count=len(recipients) + len(cc_recipients) + 1,
            sender_centrality=sender_centrality,
            content_snippet=snippet,
            matched_terms=matched_terms
        )

    def _create_snippet(self, content: str, query: str, max_length: int = 150) -> Tuple[str, List[str]]:
        """Crée un extrait du contenu avec les termes recherchés"""
        if not content or not query:
            return content[:max_length] + "..." if len(content) > max_length else content, []

        # Trouver les termes de la requête
        query_tokens = set(re.findall(r'\b[a-zA-Z0-9À-ÿ]{3,}\b', query.lower()))
        content_lower = content.lower()

        # Trouver la première occurrence d'un terme
        best_position = len(content)
        matched_terms = []

        for token in query_tokens:
            pos = content_lower.find(token)
            if pos != -1 and pos < best_position:
                best_position = pos
                matched_terms.append(token)

        # Créer l'extrait centré sur le terme trouvé
        if best_position < len(content):
            start = max(0, best_position - 50)
            end = min(len(content), best_position + 100)

            snippet = content[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(content):
                snippet = snippet + "..."

            return snippet, list(set(matched_terms))

        # retourner le début
        return content[:max_length] + "..." if len(content) > max_length else content, []