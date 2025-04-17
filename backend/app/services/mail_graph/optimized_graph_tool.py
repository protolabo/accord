# Chemin: backend/app/services/mail_graph/test/optimized_graph_test.py

import os
import json
import logging
from collections import defaultdict
from datetime import datetime

# Configuration du logging
logger = logging.getLogger(__name__)


class OptimizedGraphQueryTool:
    """
    Outil optimisé pour interroger et manipuler les données du graphe d'emails.
    Charge les données de manière efficace et fournit des méthodes d'accès rapide.
    """

    def __init__(self, graph_dir):
        """
        Initialise l'outil de requête de graphe optimisé.

        Args:
            graph_dir: Chemin vers le répertoire contenant les données du graphe
        """
        self.graph_dir = graph_dir

        # Structures principales
        self.users = {}  # email -> user_node
        self.message_map = {}  # message_id -> message_node
        self.threads = {}  # thread_id -> thread_node
        self.topics = {}  # topic_id -> topic_node
        self.relations = []  # liste de toutes les relations/arêtes

        # Index pour une recherche rapide
        self.word_index = defaultdict(set)  # mot -> ensemble de message_ids
        self.entity_index = defaultdict(set)  # entité -> ensemble de message_ids
        self.subject_index = defaultdict(set)  # terme de sujet -> ensemble de message_ids

        # Charger toutes les données
        self._load_graph_data()
        self._load_indices()

        # Compter les éléments chargés pour le logging
        logger.info(f"Graphe chargé: {len(self.users)} utilisateurs, {len(self.message_map)} messages, "
                    f"{len(self.threads)} fils de discussion, {len(self.topics)} sujets, "
                    f"{len(self.relations)} relations")

    def _load_graph_data(self):
        """Charge les données principales du graphe."""
        try:
            # Charger les utilisateurs
            users_path = os.path.join(self.graph_dir, "users.json")
            if os.path.exists(users_path):
                with open(users_path, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
                logger.info(f"Chargé {len(self.users)} utilisateurs")

            # Charger les messages
            messages_path = os.path.join(self.graph_dir, "messages.json")
            if os.path.exists(messages_path):
                with open(messages_path, 'r', encoding='utf-8') as f:
                    self.message_map = json.load(f)
                logger.info(f"Chargé {len(self.message_map)} messages")

            # Charger les fils de discussion
            threads_path = os.path.join(self.graph_dir, "threads.json")
            if os.path.exists(threads_path):
                with open(threads_path, 'r', encoding='utf-8') as f:
                    self.threads = json.load(f)
                logger.info(f"Chargé {len(self.threads)} fils de discussion")

            # Charger les sujets
            topics_path = os.path.join(self.graph_dir, "topics.json")
            if os.path.exists(topics_path):
                with open(topics_path, 'r', encoding='utf-8') as f:
                    self.topics = json.load(f)
                logger.info(f"Chargé {len(self.topics)} sujets")

            # Charger les relations
            relations_path = os.path.join(self.graph_dir, "thread_relations.json")
            if os.path.exists(relations_path):
                with open(relations_path, 'r', encoding='utf-8') as f:
                    self.relations = json.load(f)
                logger.info(f"Chargé {len(self.relations)} relations de fils")

            # Enrichir les messages avec les contenus de sujet et d'aperçu pour la recherche sémantique
            self._enrich_messages()

        except Exception as e:
            logger.error(f"Erreur lors du chargement des données du graphe: {str(e)}")
            raise RuntimeError(f"Impossible de charger les données du graphe: {str(e)}")

    def _load_indices(self):
        """Charge les indices pour une recherche rapide."""
        indices_dir = os.path.join(self.graph_dir, "indices")
        if not os.path.exists(indices_dir):
            logger.warning(f"Répertoire d'indices non trouvé: {indices_dir}")
            return

        try:
            # Charger l'index des mots
            word_index_path = os.path.join(indices_dir, "word_index.json")
            if os.path.exists(word_index_path):
                with open(word_index_path, 'r', encoding='utf-8') as f:
                    word_data = json.load(f)
                    for word, message_ids in word_data.items():
                        self.word_index[word] = set(message_ids)
                logger.info(f"Chargé {len(self.word_index)} entrées d'index de mots")

            # Charger l'index des entités
            entity_index_path = os.path.join(indices_dir, "entity_index.json")
            if os.path.exists(entity_index_path):
                with open(entity_index_path, 'r', encoding='utf-8') as f:
                    entity_data = json.load(f)
                    for entity, message_ids in entity_data.items():
                        self.entity_index[entity] = set(message_ids)
                logger.info(f"Chargé {len(self.entity_index)} entrées d'index d'entités")

            # Charger l'index des sujets
            subject_index_path = os.path.join(indices_dir, "subject_index.json")
            if os.path.exists(subject_index_path):
                with open(subject_index_path, 'r', encoding='utf-8') as f:
                    subject_data = json.load(f)
                    for term, message_ids in subject_data.items():
                        self.subject_index[term] = set(message_ids)
                logger.info(f"Chargé {len(self.subject_index)} entrées d'index de sujets")

        except Exception as e:
            logger.error(f"Erreur lors du chargement des indices: {str(e)}")
            # Continue même si les indices ne peuvent pas être chargés
            # Cela permettra au moins aux fonctionnalités de base de fonctionner

    def _enrich_messages(self):
        """
        Enrichit les messages avec des données dérivées pour la recherche sémantique.
        Ajoute des champs comme 'subject' et 'snippet' qui sont utiles pour
        générer des embeddings et améliorer la recherche.
        """
        # Créer un cache d'accès rapide pour récupérer les fils par ID de message
        message_to_thread = {}
        for thread_id, thread in self.threads.items():
            for rel in self.relations:
                if rel.get("relation_type") == "PART_OF_THREAD" and rel.get("target_id") == thread_id:
                    message_id = rel.get("source_id")
                    message_to_thread[message_id] = thread_id

        # Enrichir chaque message
        for msg_id, message in self.message_map.items():
            try:
                # Ajouter le sujet depuis le fil associé
                if msg_id in message_to_thread:
                    thread_id = message_to_thread[msg_id]
                    if thread_id in self.threads:
                        thread = self.threads[thread_id]
                        # Récupérer le premier message du fil pour le sujet
                        first_msg_id = thread.get("first_message_id")
                        if first_msg_id in self.message_map:
                            first_message = self.message_map[first_msg_id]
                            # Extraire le sujet des données originales ou du fil
                            subject = first_message.get("subject", "")
                            if not subject and "topics" in thread:
                                subject = " ".join(thread.get("topics", []))
                            message["subject"] = subject

                # Créer un extrait du contenu du message (snippet)
                # Dans une application réelle, cela proviendrait du contenu du message
                # Ici, nous simulons avec les données disponibles
                from_email = message.get("from", "")
                to_emails = ", ".join(message.get("to", []))
                date_str = message.get("date", "")

                # Créer un snippet simulé
                snippet = f"From {from_email} to {to_emails}. "
                if date_str:
                    try:
                        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        snippet += f"Sent on {date.strftime('%Y-%m-%d')}. "
                    except (ValueError, TypeError):
                        pass

                # Ajouter des informations sur les pièces jointes
                if message.get("attachment"):
                    snippet += "Contains attachments. "

                message["snippet"] = snippet

                # Ajouter un champ has_attachment pour une recherche facile
                message["has_attachment"] = bool(message.get("attachment"))

            except Exception as e:
                logger.warning(f"Erreur lors de l'enrichissement du message {msg_id}: {str(e)}")

    ################################################################################################

    def get_message_by_id(self, message_id):
        """
        Récupère un message par son ID.

        Args:
            message_id: ID du message à récupérer

        Returns:
            Le message ou None s'il n'est pas trouvé
        """
        return self.message_map.get(message_id)

    def get_user_by_email(self, email):
        """
        Récupère un utilisateur par son email.

        Args:
            email: Adresse email de l'utilisateur

        Returns:
            L'utilisateur ou None s'il n'est pas trouvé
        """
        return self.users.get(email.lower())

    def get_thread_by_id(self, thread_id):
        """
        Récupère un fil de discussion par son ID.

        Args:
            thread_id: ID du fil à récupérer

        Returns:
            Le fil de discussion ou None s'il n'est pas trouvé
        """
        return self.threads.get(thread_id)

    def get_topic_by_id(self, topic_id):
        """
        Récupère un sujet par son ID.

        Args:
            topic_id: ID du sujet à récupérer

        Returns:
            Le sujet ou None s'il n'est pas trouvé
        """
        return self.topics.get(topic_id)

    def get_messages_by_keyword(self, keyword, limit=100):
        """
        Trouve des messages contenant un mot-clé.

        Args:
            keyword: Mot-clé à rechercher
            limit: Nombre maximum de résultats

        Returns:
            Liste de messages correspondants (au maximum limit)
        """
        keyword = keyword.lower()
        results = []

        # Rechercher dans l'index des mots
        if keyword in self.word_index:
            for msg_id in self.word_index[keyword]:
                if msg_id in self.message_map:
                    results.append(self.message_map[msg_id])
                    if len(results) >= limit:
                        break

        # Si peu de résultats, essayer aussi l'index des sujets
        if len(results) < limit and keyword in self.subject_index:
            for msg_id in self.subject_index[keyword]:
                if msg_id in self.message_map and self.message_map[msg_id] not in results:
                    results.append(self.message_map[msg_id])
                    if len(results) >= limit:
                        break

        return results

    def get_messages_between_dates(self, start_date=None, end_date=None, limit=100):
        """
        Trouve des messages entre deux dates.

        Args:
            start_date: Date de début au format ISO (optionnel)
            end_date: Date de fin au format ISO (optionnel)
            limit: Nombre maximum de résultats

        Returns:
            Liste de messages correspondants (au maximum limit)
        """
        results = []

        for msg_id, message in self.message_map.items():
            date_str = message.get("date", "")
            if not date_str:
                continue

            try:
                msg_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))

                # Vérifier la date de début
                if start_date:
                    start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    if msg_date < start:
                        continue

                # Vérifier la date de fin
                if end_date:
                    end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    if msg_date > end:
                        continue

                # Si on arrive ici, le message est dans la plage de dates
                results.append(message)
                if len(results) >= limit:
                    break

            except (ValueError, TypeError):
                continue

        return results

    def get_messages_by_sender(self, sender_email, limit=100):
        """
        Trouve des messages envoyés par un expéditeur.

        Args:
            sender_email: Email de l'expéditeur à rechercher
            limit: Nombre maximum de résultats

        Returns:
            Liste de messages correspondants (au maximum limit)
        """
        sender_email = sender_email.lower()
        results = []

        for msg_id, message in self.message_map.items():
            from_email = message.get("from", "").lower()
            if sender_email in from_email:
                results.append(message)
                if len(results) >= limit:
                    break

        return results

    def get_messages_to_recipient(self, recipient_email, limit=100):
        """
        Trouve des messages envoyés à un destinataire.

        Args:
            recipient_email: Email du destinataire à rechercher
            limit: Nombre maximum de résultats

        Returns:
            Liste de messages correspondants (au maximum limit)
        """
        recipient_email = recipient_email.lower()
        results = []

        for msg_id, message in self.message_map.items():
            # Vérifier les destinataires principaux
            for to_email in message.get("to", []):
                if recipient_email in to_email.lower():
                    results.append(message)
                    break

            # Vérifier les CC si nous n'avons pas encore atteint la limite
            if len(results) < limit:
                for cc_email in message.get("cc", []):
                    if recipient_email in cc_email.lower():
                        if message not in results:  # Éviter les doublons
                            results.append(message)
                            break

            if len(results) >= limit:
                break

        return results

    def get_recent_messages(self, limit=50):
        """
        Obtient les messages les plus récents.

        Args:
            limit: Nombre maximum de résultats

        Returns:
            Liste de messages triés par date (du plus récent au plus ancien)
        """
        # Trier tous les messages par date (du plus récent au plus ancien)
        sorted_messages = sorted(
            self.message_map.values(),
            key=lambda m: m.get("date", ""),
            reverse=True
        )

        return sorted_messages[:limit]

    def get_important_users(self, limit=20):
        """
        Obtient les utilisateurs les plus importants en fonction de leur force de connexion.

        Args:
            limit: Nombre maximum d'utilisateurs à retourner

        Returns:
            Liste des utilisateurs les plus importants
        """
        # Trier les utilisateurs par force de connexion (décroissante)
        sorted_users = sorted(
            self.users.values(),
            key=lambda u: u.get("connection_strength", 0),
            reverse=True
        )

        return sorted_users[:limit]

    def get_thread_messages(self, thread_id):
        """
        Obtient tous les messages d'un fil de discussion.

        Args:
            thread_id: ID du fil de discussion

        Returns:
            Liste de messages dans le fil, triés chronologiquement
        """
        if thread_id not in self.threads:
            return []

        thread_messages = []

        # Trouver les messages du fil via les relations
        for relation in self.relations:
            if (relation.get("relation_type") == "PART_OF_THREAD" and
                    relation.get("target_id") == thread_id):
                msg_id = relation.get("source_id")
                if msg_id in self.message_map:
                    thread_messages.append(self.message_map[msg_id])

        # Trier par date
        thread_messages.sort(key=lambda m: m.get("date", ""))

        return thread_messages

    def get_conversation_messages(self, user1_email, user2_email, limit=100):
        """
        Obtient les messages échangés entre deux utilisateurs.

        Args:
            user1_email: Email du premier utilisateur
            user2_email: Email du second utilisateur
            limit: Nombre maximum de résultats

        Returns:
            Liste de messages échangés entre les deux utilisateurs
        """
        user1_email = user1_email.lower()
        user2_email = user2_email.lower()
        results = []

        for msg_id, message in self.message_map.items():
            from_email = message.get("from", "").lower()

            # Vérifier si l'expéditeur est l'un des deux utilisateurs
            is_from_user1 = user1_email in from_email
            is_from_user2 = user2_email in from_email

            if not (is_from_user1 or is_from_user2):
                continue

            # Vérifier si le destinataire est l'autre utilisateur
            to_emails = [e.lower() for e in message.get("to", [])]
            cc_emails = [e.lower() for e in message.get("cc", [])]

            is_to_user1 = any(user1_email in e for e in to_emails) or any(user1_email in e for e in cc_emails)
            is_to_user2 = any(user2_email in e for e in to_emails) or any(user2_email in e for e in cc_emails)

            # Si c'est une conversation entre les deux utilisateurs
            if (is_from_user1 and is_to_user2) or (is_from_user2 and is_to_user1):
                results.append(message)
                if len(results) >= limit:
                    break

        # Trier par date
        results.sort(key=lambda m: m.get("date", ""))

        return results

    def get_topic_messages(self, topic_id, limit=100):
        """
        Obtient les messages associés à un sujet.

        Args:
            topic_id: ID du sujet
            limit: Nombre maximum de résultats

        Returns:
            Liste de messages associés au sujet
        """
        if topic_id not in self.topics:
            return []

        topic_messages = []

        # Trouver les messages du sujet via les relations
        for relation in self.relations:
            if (relation.get("relation_type") == "HAS_TOPIC" and
                    relation.get("target_id") == topic_id):
                msg_id = relation.get("source_id")
                if msg_id in self.message_map:
                    topic_messages.append(self.message_map[msg_id])
                    if len(topic_messages) >= limit:
                        break

        return topic_messages

    def get_stats(self):
        """
        Obtient des statistiques sur le graphe.

        Returns:
            Dictionnaire de statistiques
        """
        # Calculer les statistiques de base
        stats = {
            "users_count": len(self.users),
            "messages_count": len(self.message_map),
            "threads_count": len(self.threads),
            "topics_count": len(self.topics),
            "relations_count": len(self.relations),
            "word_index_count": len(self.word_index),
            "entity_index_count": len(self.entity_index),
            "subject_index_count": len(self.subject_index)
        }

        # Analyser la distribution des dates de messages
        dates = []
        for message in self.message_map.values():
            date_str = message.get("date", "")
            if date_str:
                try:
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    dates.append(date)
                except (ValueError, TypeError):
                    continue

        if dates:
            stats["oldest_message"] = min(dates).isoformat()
            stats["newest_message"] = max(dates).isoformat()
            stats["message_count_with_date"] = len(dates)

        # Compter les messages avec pièces jointes
        stats["messages_with_attachments"] = sum(
            1 for msg in self.message_map.values() if msg.get("attachment")
        )

        return stats