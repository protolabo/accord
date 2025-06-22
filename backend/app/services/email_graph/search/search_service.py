"""
Services de recherche par type (contenu, temporel, utilisateur, etc.).
"""

import re
from datetime import datetime, timedelta
from collections import defaultdict

from ..logging_service import logger
from ..shared_utils import process_email_list
from .config import TOPIC_MAPPINGS


class SearchService:
    """Service pour les différents types de recherche"""

    def __init__(self, indexing_service, scoring_service):
        self.indexing = indexing_service
        self.scoring = scoring_service

    def set_services(self, indexing_service, scoring_service):
        """Met à jour les services"""
        self.indexing = indexing_service
        self.scoring = scoring_service

    def search_by_content(self, query, filters):
        """
        Recherche par contenu avec TF-IDF et scoring avancé

        Args:
            query (str): Requête textuelle
            filters (dict): Filtres à appliquer

        Returns:
            dict: Scores par message_id
        """
        if not query:
            return {}

        # Déléguer le calcul des scores au service de scoring
        results = self.scoring.calculate_content_scores(query, filters)

        # Appliquer les filtres
        filtered_results = {}
        for message_id, scores in results.items():
            message_data = self.indexing.message_nodes.get(message_id, {})
            if self._apply_message_filters(message_id, message_data, filters):
                filtered_results[message_id] = dict(scores)

        return filtered_results

    def search_by_temporal(self, filters, query=''):
        """
        Recherche par période temporelle avec scoring

        Args:
            filters (dict): Filtres incluant date_from et date_to
            query (str): Requête textuelle optionnelle

        Returns:
            dict: Scores par message_id
        """
        date_from_str = filters.get('date_from')
        date_to_str = filters.get('date_to')

        if not date_from_str:
            return {}

        try:
            date_from = datetime.fromisoformat(date_from_str)
            date_to = datetime.fromisoformat(date_to_str) if date_to_str else date_from.replace(hour=23, minute=59)
        except Exception as e:
            logger.logger.error(f"Erreur parsing dates temporelles: {e}")
            return {}

        results = defaultdict(lambda: defaultdict(float))

        # Rechercher dans l'index temporel
        current_date = date_from
        candidate_messages = set()

        while current_date <= date_to:
            day_key = current_date.strftime('%Y-%m-%d')
            candidate_messages.update(self.indexing.temporal_index.get(day_key, []))
            current_date += timedelta(days=1)

        # Calculer les scores temporels
        temporal_scores = self.scoring.calculate_temporal_scores(
            list(candidate_messages), date_from, date_to
        )

        # Filtrer et enrichir les résultats
        for message_id, temporal_score in temporal_scores.items():
            message_data = self.indexing.message_nodes.get(message_id, {})

            if not self._apply_message_filters(message_id, message_data, filters):
                continue

            results[message_id]['temporal'] = temporal_score

            # Ajouter score de contenu si requête fournie
            if query:
                content_results = self.search_by_content(query, filters)
                if message_id in content_results:
                    results[message_id]['content'] = content_results[message_id].get('content', 0)

        return dict(results)

    def search_by_user(self, filters, query=''):
        """
        Recherche par utilisateur avec support expéditeur/destinataire

        Args:
            filters (dict): Filtres incluant contact_email, recipient_email, etc.
            query (str): Requête textuelle optionnelle

        Returns:
            dict: Scores par message_id
        """
        # Gérer les différents types de recherche utilisateur
        contact_email = filters.get('contact_email', '').lower()  # Expéditeur
        contact_name = filters.get('contact_name', '').lower()
        recipient_email = filters.get('recipient_email', '').lower()  # Destinataire
        recipient_name = filters.get('recipient_name', '').lower()

        results = defaultdict(lambda: defaultdict(float))

        # Recherche par expéditeur
        if contact_email or contact_name:
            sender_users = self._find_matching_users(contact_email, contact_name)
            sender_scores = self.scoring.calculate_user_scores(
                sender_users,
                role_weights={'sent': 1.0, 'received': 0.0}  # Seulement les messages envoyés
            )

            for msg_id, score in sender_scores.items():
                results[msg_id]['user'] = score

        #  Recherche par destinataire
        if recipient_email or recipient_name:
            recipient_users = self._find_matching_users(recipient_email, recipient_name)

            # Chercher dans les messages où ces utilisateurs sont destinataires
            for user_id, match_score in recipient_users:
                # Messages où l'utilisateur est destinataire (TO, CC, BCC)
                for message_id in self._find_messages_to_recipient(user_id):
                    message_data = self.indexing.message_nodes.get(message_id, {})

                    if self._apply_message_filters(message_id, message_data, filters):
                        results[message_id]['user'] = max(
                            results[message_id]['user'],
                            match_score * 0.9
                        )

        # Ajouter scores de contenu si requête fournie
        if query:
            content_results = self.search_by_content(query, filters)
            for message_id in results:
                if message_id in content_results:
                    results[message_id]['content'] = content_results[message_id].get('content', 0)

        return dict(results)

    def _find_messages_to_recipient(self, user_id):
        """
        NOUVEAU: Trouve tous les messages envoyés à un utilisateur spécifique

        Args:
            user_id (str): ID de l'utilisateur destinataire

        Returns:
            set: IDs des messages
        """
        messages = set()

        # Chercher toutes les relations entrantes vers cet utilisateur
        for message_id, _, edge_data in self.indexing.graph.in_edges(user_id, data=True):
            edge_type = edge_data.get('type')
            if edge_type in ['RECEIVED', 'CC', 'BCC']:
                messages.add(message_id)

        return messages

    def _apply_message_filters(self, message_id, message_data, filters):
        """Applique les filtres additionnels à un message (version améliorée)"""

        # Filtres existants...

        # NOUVEAU: Filtre type de message (sent/received)
        if filters.get('message_type'):
            message_type = filters['message_type']

            if message_type == 'sent':
                # Vérifier si le message a été envoyé par l'utilisateur central
                is_sent = False
                for user_id, _, edge_data in self.indexing.graph.in_edges(message_id, data=True):
                    if edge_data.get('type') == 'SENT':
                        user_data = self.indexing.user_nodes.get(user_id, {})
                        if user_data.get('is_central_user', False):
                            is_sent = True
                            break
                if not is_sent:
                    return False

            elif message_type == 'received':
                # Vérifier si le message a été reçu par l'utilisateur central
                is_received = False
                for _, user_id, edge_data in self.indexing.graph.out_edges(message_id, data=True):
                    if edge_data.get('type') in ['RECEIVED', 'CC', 'BCC']:
                        user_data = self.indexing.user_nodes.get(user_id, {})
                        if user_data.get('is_central_user', False):
                            is_received = True
                            break
                if not is_received:
                    return False

        # Filtre types de pièces jointes spécifiques
        if filters.get('attachment_types'):
            required_types = set(filters['attachment_types'])
            message_attachments = message_data.get('attachments', [])

            if not message_attachments:
                return False

            # Extraire les extensions des pièces jointes
            attachment_extensions = set()
            for attachment in message_attachments:
                if isinstance(attachment, dict):
                    filename = attachment.get('filename', '')
                else:
                    filename = str(attachment)

                if '.' in filename:
                    ext = filename.split('.')[-1].lower()
                    attachment_extensions.add(ext)

            # Vérifier si au moins un type requis est présent
            if not required_types.intersection(attachment_extensions):
                return False

        #  Filtre destinataire spécifique (complément de search_by_user)
        if filters.get('recipient_name'):
            recipient_name = filters['recipient_name'].lower()
            found = False

            # Vérifier dans les relations du graphe
            for _, user_id, edge_data in self.indexing.graph.out_edges(message_id, data=True):
                if edge_data.get('type') in ['RECEIVED', 'CC', 'BCC']:
                    user_data = self.indexing.user_nodes.get(user_id, {})
                    if recipient_name in user_data.get('name', '').lower():
                        found = True
                        break

            if not found:
                return False

        # Filtres existants...
        if filters.get('has_attachments') is not None:
            message_has_attachments = message_data.get('has_attachments', False)
            if filters['has_attachments'] != message_has_attachments:
                return False

        if filters.get('is_unread') and not message_data.get('is_unread', True):
            return False

        if filters.get('is_important') and not message_data.get('is_important'):
            return False

        if filters.get('is_archived') and not message_data.get('is_archived', False):
            return False

        return True

    def search_by_topic(self, filters, query=''):
        """
        Recherche par topics avec mapping flexible

        Args:
            filters (dict): Filtres incluant topic_ids
            query (str): Requête textuelle optionnelle

        Returns:
            dict: Scores par message_id
        """
        topic_ids = filters.get('topic_ids', [])
        if not topic_ids:
            return {}

        # Dédupliquer et étendre les topics
        topic_ids = list(set(topic_ids))
        expanded_topics = self._expand_topics(topic_ids)

        logger.logger.info(f"Topics étendus: {expanded_topics}")

        results = defaultdict(lambda: defaultdict(float))

        # Chercher dans tous les messages
        for message_id, message_data in self.indexing.message_nodes.items():
            score = self._calculate_topic_score(message_data, expanded_topics)

            if score > 0 and self._apply_message_filters(message_id, message_data, filters):
                results[message_id]['content'] = score

        logger.logger.info(f"🎯 {len(results)} message(s) trouvé(s) par topics")
        return dict(results)

    def search_combined(self, query, filters):
        """
        Recherche combinée avec fusion des scores (version améliorée)

        Args:
            query (str): Requête textuelle
            filters (dict): Filtres multiples

        Returns:
            dict: Scores combinés par message_id
        """
        combined_results = defaultdict(lambda: defaultdict(float))
        all_results = []

        #  Gérer les cas de négation spécialement
        has_negation = (
                filters.get('has_attachments') is False or
                filters.get('is_important') is False
        )

        # Déterminer si on a plusieurs filtres
        active_filters = []
        if filters.get('topic_ids'):
            active_filters.append('topics')
        if filters.get('has_attachments') is not None:
            active_filters.append('attachments')
        if filters.get('contact_name') or filters.get('contact_email'):
            active_filters.append('sender')
        if filters.get('recipient_name') or filters.get('recipient_email'):
            active_filters.append('recipient')
        if filters.get('date_from'):
            active_filters.append('temporal')
        if filters.get('message_type'):
            active_filters.append('message_type')

        has_multiple_filters = len(active_filters) > 1

        # Exécuter les différents types de recherche
        search_results = {}

        # Recherche par contenu
        if query:
            search_results['content'] = self.search_by_content(query, filters)
            all_results.append(set(search_results['content'].keys()))

        # Recherche par topics
        if filters.get('topic_ids'):
            search_results['topics'] = self.search_by_topic(filters, query)
            all_results.append(set(search_results['topics'].keys()))

        # Recherche par utilisateur (expéditeur ou destinataire)
        if any(filters.get(k) for k in ['contact_name', 'contact_email', 'recipient_name', 'recipient_email']):
            search_results['user'] = self.search_by_user(filters, query)
            all_results.append(set(search_results['user'].keys()))

        # Recherche temporelle
        if filters.get('date_from'):
            search_results['temporal'] = self.search_by_temporal(filters, query)
            all_results.append(set(search_results['temporal'].keys()))

        # Pour les filtres de négation ou d'état, on doit chercher dans TOUS les messages
        if has_negation or filters.get('message_type'):
            # Parcourir tous les messages et appliquer les filtres
            all_messages = set()
            for message_id, message_data in self.indexing.message_nodes.items():
                if self._apply_message_filters(message_id, message_data, filters):
                    all_messages.add(message_id)

            # Si on a d'autres résultats, faire l'intersection
            if all_results:
                valid_messages = all_messages.intersection(
                    set.intersection(*all_results) if has_multiple_filters else set.union(*all_results)
                )
            else:
                valid_messages = all_messages
        else:
            # Logique existante pour fusion normale
            if has_multiple_filters and all_results:
                valid_messages = set.intersection(*all_results)
            else:
                valid_messages = set()
                for result_set in all_results:
                    valid_messages.update(result_set)

        # Combiner les scores pour les messages valides
        for message_id in valid_messages:
            for search_type, results in search_results.items():
                if message_id in results:
                    for score_type, score_value in results[message_id].items():
                        combined_results[message_id][score_type] += score_value

        return dict(combined_results)

    def _find_matching_users(self, contact_email, contact_name):
        """Trouve les utilisateurs correspondant aux critères"""
        matching_users = []

        for user_id, user_data in self.indexing.user_nodes.items():
            email = user_data.get('email', '').lower()
            name = user_data.get('name', '').lower()

            match_score = 0

            # Match par email
            if contact_email:
                if contact_email == email:
                    match_score = 1.0
                elif contact_email in email or email in contact_email:
                    match_score = 0.8

            # Match par nom
            if contact_name and match_score == 0:
                if contact_name == name:
                    match_score = 1.0
                elif contact_name in name or name in contact_name:
                    match_score = 0.9
                elif ' ' in name and contact_name == name.split()[0]:
                    match_score = 0.85

            if match_score > 0:
                matching_users.append((user_id, match_score))

        return matching_users

    def _expand_topics(self, topic_ids):
        """Étend les topics avec leurs synonymes"""
        expanded_topics = set()

        for topic_id in topic_ids:
            expanded_topics.add(topic_id.lower())
            if topic_id.lower() in TOPIC_MAPPINGS:
                expanded_topics.update(TOPIC_MAPPINGS[topic_id.lower()])

        return expanded_topics

    def _calculate_topic_score(self, message_data, expanded_topics):
        """Calcule le score de topic pour un message"""
        score = 0.0

        # Score pour topics explicites du message
        message_topics = [t.lower() for t in message_data.get('topics', [])]
        topic_overlap = set(message_topics).intersection(expanded_topics)
        if topic_overlap:
            score += len(topic_overlap) * 2.0

        # Score pour termes dans le sujet
        subject = message_data.get('subject', '').lower()
        for topic in expanded_topics:
            if topic in subject:
                score += 1.5

        # Score pour termes dans le contenu
        content = message_data.get('content', '').lower()
        for topic in expanded_topics:
            if topic in content:
                score += 1.0

        return score

    def _apply_message_filters(self, message_id, message_data, filters):
        """Applique les filtres additionnels à un message"""
        # Filtre pièces jointes
        if filters.get('has_attachments') is not None:
            message_has_attachments = message_data.get('has_attachments', False)
            if filters['has_attachments'] != message_has_attachments:
                return False

        # Filtre nom contact (vérification via graphe)
        if filters.get('contact_name'):
            sender_name = message_data.get('sender_name', '').lower()
            filter_name = filters['contact_name'].lower()
            if filter_name not in sender_name:
                # Vérifier aussi via les relations du graphe
                sender_found = False
                for user_id, _, edge_data in self.indexing.graph.in_edges(message_id, data=True):
                    if edge_data.get('type') == 'SENT':
                        user_data = self.indexing.user_nodes.get(user_id, {})
                        if filter_name in user_data.get('name', '').lower():
                            sender_found = True
                            break
                if not sender_found:
                    return False

        # Filtre messages non lus
        if filters.get('is_unread') and not message_data.get('is_unread', True):
            return False

        # Filtre messages importants
        if filters.get('is_important') and not message_data.get('is_important'):
            return False

        return True