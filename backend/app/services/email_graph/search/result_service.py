"""
Service de création et d'enrichissement des résultats de recherche.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from ..logging_service import logger
from .config import SNIPPET_CONFIG, SCORING_WEIGHTS


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


class SearchResultService:
    """Service pour la création et l'enrichissement des résultats de recherche"""

    def __init__(self, indexing_service, scoring_service):
        self.indexing = indexing_service
        self.scoring = scoring_service

    def set_services(self, indexing_service, scoring_service):
        """Met à jour les services"""
        self.indexing = indexing_service
        self.scoring = scoring_service

    def create_search_results(self, search_results, query, limit=10):
        """
        Crée une liste de résultats enrichis et triés

        Args:
            search_results (dict): Résultats de recherche par message_id
            query (str): Requête de recherche originale
            limit (int): Nombre maximum de résultats

        Returns:
            List[SearchResult]: Liste des résultats triés
        """
        enriched_results = []

        # Calculer les scores totaux
        total_scores = self.scoring.calculate_total_scores(search_results)

        # Créer les résultats enrichis
        for message_id, scores in search_results.items():
            total_score = total_scores.get(message_id, 0.0)
            result = self._create_single_result(message_id, scores, total_score, query)

            if result:
                enriched_results.append(result)

        # Trier par score total décroissant
        enriched_results.sort(key=lambda r: r.total_score, reverse=True)

        return enriched_results[:limit]

    def _create_single_result(self, message_id, scores, total_score, query):
        """
        Crée un résultat de recherche enrichi pour un message

        Args:
            message_id (str): ID du message
            scores (dict): Scores par type
            total_score (float): Score total calculé
            query (str): Requête originale

        Returns:
            SearchResult|None: Résultat enrichi ou None
        """
        message_data = self.indexing.message_nodes.get(message_id)
        if not message_data:
            return None

        # Extraire les métadonnées de l'expéditeur
        sender_info = self._extract_sender_info(message_id)

        # Extraire les destinataires
        recipients_info = self._extract_recipients_info(message_id)

        # Informations sur le thread
        thread_info = self._extract_thread_info(message_id)

        # Créer le snippet et extraire les termes correspondants
        content = message_data.get('content', '')
        snippet, matched_terms = self._create_content_snippet(content, query)

        # Parser la date
        timestamp = self._parse_message_timestamp(message_data.get('date', ''))

        # Créer le résultat
        return SearchResult(
            message_id=message_id,
            thread_id=thread_info['thread_id'],
            total_score=total_score,
            content_score=scores.get('content', 0),
            temporal_score=scores.get('temporal', 0),
            user_score=scores.get('user', 0),
            graph_score=scores.get('graph', 0),
            subject=message_data.get('subject', ''),
            content=content,
            sender_email=sender_info['email'],
            sender_name=sender_info['name'],
            recipients=recipients_info['to'],
            cc_recipients=recipients_info['cc'],
            bcc_recipients=recipients_info['bcc'],
            date=message_data.get('date', ''),
            timestamp=timestamp,
            has_attachments=message_data.get('has_attachments', False),
            attachment_count=message_data.get('attachment_count', 0),
            is_important=message_data.get('is_important', False),
            is_unread=message_data.get('is_unread', True),
            labels=message_data.get('labels', []),
            thread_size=thread_info['size'],
            reply_count=message_data.get('reply_count', 0),
            participants_count=recipients_info['total_count'],
            sender_centrality=sender_info['centrality'],
            content_snippet=snippet,
            matched_terms=matched_terms
        )

    def _extract_sender_info(self, message_id):
        """Extrait les informations de l'expéditeur"""
        sender_id = None
        sender_name = ""
        sender_email = ""
        sender_centrality = 0.0

        # Chercher l'expéditeur via les relations du graphe
        for user_id, _, edge_data in self.indexing.graph.in_edges(message_id, data=True):
            if edge_data.get('type') == 'SENT':
                sender_id = user_id
                sender_data = self.indexing.user_nodes.get(user_id, {})
                sender_name = sender_data.get('name', '')
                sender_email = sender_data.get('email', '')
                sender_centrality = self.indexing.user_pagerank.get(user_id, 0.0)
                break

        # Fallback sur les données du message
        if not sender_email:
            message_data = self.indexing.message_nodes.get(message_id, {})
            sender_email = message_data.get('from', '')

        return {
            'email': sender_email,
            'name': sender_name,
            'centrality': sender_centrality
        }

    def _extract_recipients_info(self, message_id):
        """Extrait les informations des destinataires"""
        recipients = []
        cc_recipients = []
        bcc_recipients = []

        # Chercher les destinataires via les relations du graphe
        for _, user_id, edge_data in self.indexing.graph.out_edges(message_id, data=True):
            edge_type = edge_data.get('type')
            if edge_type in ['RECEIVED', 'CC', 'BCC']:
                user_data = self.indexing.user_nodes.get(user_id, {})
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

        total_count = len(recipients) + len(cc_recipients) + len(bcc_recipients) + 1  # +1 pour l'expéditeur

        return {
            'to': recipients,
            'cc': cc_recipients,
            'bcc': bcc_recipients,
            'total_count': total_count
        }

    def _extract_thread_info(self, message_id):
        """Extrait les informations du thread"""
        thread_id = None
        thread_size = 1

        # Chercher le thread via les relations
        for _, tid, edge_data in self.indexing.graph.out_edges(message_id, data=True):
            if edge_data.get('type') == 'PART_OF_THREAD':
                thread_id = tid
                thread_size = len(self.indexing.thread_messages_index.get(tid, []))
                break

        return {
            'thread_id': thread_id,
            'size': thread_size
        }

    def _create_content_snippet(self, content, query):
        """
        Crée un extrait du contenu avec les termes recherchés mis en évidence

        Args:
            content (str): Contenu du message
            query (str): Requête de recherche

        Returns:
            tuple: (snippet, matched_terms)
        """
        if not content or not query:
            return self._truncate_content(content), []

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
            start = max(0, best_position - SNIPPET_CONFIG['context_before'])
            end = min(len(content), best_position + SNIPPET_CONFIG['context_after'])

            snippet = content[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(content):
                snippet = snippet + "..."

            return snippet, list(set(matched_terms))

        # Retourner le début du contenu
        return self._truncate_content(content), []

    def _truncate_content(self, content):
        """Tronque le contenu à la longueur maximum"""
        max_length = SNIPPET_CONFIG['max_length']
        if len(content) > max_length:
            return content[:max_length] + "..."
        return content

    def _parse_message_timestamp(self, date_str):
        """Parse la date du message en timestamp"""
        if not date_str:
            return None

        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception:
            return None