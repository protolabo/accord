"""
Processeur principal du graphe d'emails.

Cette classe coordonne l'ensemble du processus de construction et d'analyse
du graphe d'emails.
"""

import json
import networkx as nx
from datetime import datetime

from .models.message_node import MessageNodeManager
from .models.user_node import UserNodeManager
from .models.thread_node import ThreadNodeManager
from .utils.email_utils import normalize_email
from .analysis.metrics import GraphMetricsAnalyzer
from .analysis.network_extraction import NetworkExtractor


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
            if isinstance(message_json, str):
                message = json.loads(message_json)
            else:
                message = message_json

            # Extraction des paramètres
            emails = message.get("mails", [])
            self.central_user_email = message.get("central_user")
            max_emails = message.get("max_emails")

            # Limiter le nombre d'emails si nécessaire
            if max_emails and max_emails < len(emails):
                emails = emails[:max_emails]

            # Configurer les gestionnaires
            self.user_manager.set_central_user(self.central_user_email)

            # Construction du graphe
            self._build_graph(emails)

            # Analyse du graphe
            result = self._analyze_graph()

            # Génération des statistiques
            stats = self.metrics_analyzer.calculate_stats()
            result["stats"] = stats

            # Ajout des métadonnées
            result["metadata"] = {
                "timestamp": datetime.now().isoformat(),
                "emails_processed": len(emails),
                "central_user": self.central_user_email
            }

            return json.dumps(result)

        except Exception as e:
            # Gestion d'erreurs avec détails pour faciliter le débogage
            error_response = {
                'status': 'error',
                'message': str(e),
                'type': type(e).__name__
            }
            return json.dumps(error_response)

    def _build_graph(self, emails):
        """
        Construit le graphe à partir des données d'emails

        Args:
            emails (list): Liste d'objets email à traiter
        """
        # Réinitialiser le graphe au besoin
        if self.graph.number_of_nodes() > 0:
            # multidirection :ok
            self.graph = nx.MultiDiGraph()
            # Réinitialiser les gestionnaires avec le nouveau graphe

            # juste une initialisation
            self.message_manager.set_graph(self.graph)
            self.user_manager.set_graph(self.graph)
            self.thread_manager.set_graph(self.graph)
            self.metrics_analyzer.set_graph(self.graph)
            self.network_extractor.set_graph(self.graph)

        print(f"Construction du graphe pour {len(emails)} emails...")

        # Traitement de chaque email
        # idx c'est pour le login d'avancement
        # on boucle sur chaque mails
        for idx, email in enumerate(emails):
            self._process_email(email)

            # Logging d'avancement périodique
            if idx > 0 and idx % 1000 == 0:
                print(f"Traité {idx}/{len(emails)} emails...")

        print(
            f"Construction terminée. Graphe contient {self.graph.number_of_nodes()} noeuds et {self.graph.number_of_edges()} relations.")

    def _process_email(self, email_data):
        """
        Traite un email et ajoute les noeuds et relations au graphe
        Note : un seul mail

        Args:
            email_data (dict): Données d'un email

        Returns:
            bool: True si l'email a été traité avec succès
        """
        try:
            # Extraire l'ID du message et du thread
            message_id = email_data.get("Message-ID")
            thread_id = email_data.get("Thread-ID", "")

            if not message_id:
                return False

            # Créer noeud message
            message_node = self.message_manager.create_message(email_data)
            if not message_node:
                return False

            # Créer noeud thread si nécessaire
            if thread_id:
                thread_node = self.thread_manager.create_thread(email_data)

                # Lier le message au thread
                # le thread peuvent avoir un poids, ce qui est interessant
                self.graph.add_edge(
                    message_id,
                    thread_id,
                    type="PART_OF_THREAD",
                    weight=1.0
                )

            # Traiter l'expéditeur
            from_email = email_data.get("From", "")
            from_user_id = None

            # ici le but c'est de creer la relation entre l'utilisateur et le message
            if from_email:
                from_user_id = self.user_manager.create_user(from_email)
                # Relation expéditeur -> message
                is_central = normalize_email(from_email) == normalize_email(
                    self.central_user_email) if self.central_user_email else False
                weight = 3.0 if is_central else 1.0

                # ceci cree la relation entre le message et l'utilisateur donc on a besoin de l'id de l'utilisateur
                self.graph.add_edge(
                    from_user_id,
                    message_id,
                    type="SENT",
                    weight=weight
                )


            user_relations = self.user_manager.create_recipient_relationships(email_data, from_user_id)


            # Traiter séparément les relations entre le message et les destinataires
            # To
            to_emails = email_data.get("To", "").split(",") if email_data.get("To") else []
            for email in to_emails:
                if not email.strip():
                    continue
                to_user_id = self.user_manager.create_user(email.strip())
                if to_user_id:

                    # Relation message -> destinataire
                    # comme mentionnne celui-ci ne fait que cree la relation entre le message et l'utilisateur
                    # donc on a besoin de l'id de l'utilisateur'
                    self.graph.add_edge(
                        message_id,
                        to_user_id,
                        type="RECEIVED",
                        weight=1.0
                    )

            # CC
            cc_emails = email_data.get("Cc", "").split(",") if email_data.get("Cc") else []
            for email in cc_emails:
                if not email.strip():
                    continue
                cc_user_id = self.user_manager.create_user(email.strip())
                if cc_user_id:

                    # Relation message -> CC
                    self.graph.add_edge(
                        message_id,
                        cc_user_id,
                        type="CC",
                        weight=0.8
                    )

            # BCC
            bcc_emails = email_data.get("Bcc", "").split(",") if email_data.get("Bcc") else []
            for email in bcc_emails:
                if not email.strip():
                    continue
                bcc_user_id = self.user_manager.create_user(email.strip())
                if bcc_user_id:
                    # Relation message -> BCC
                    self.graph.add_edge(
                        message_id,
                        bcc_user_id,
                        type="BCC",
                        weight=0.6
                    )



            return True

        except Exception as e:
            print(f"Erreur lors du traitement de l'email {email_data.get('Message-ID')}: {str(e)}")
            return False

    def _analyze_graph(self):
        """
        Analyse le graphe et calcule diverses métriques

        Returns:
            dict: Résultats de l'analyse
        """

        result = {
            "central_user": self.central_user_email,
            "top_contacts": self.metrics_analyzer.get_top_contacts(10),
            "top_threads": self.metrics_analyzer.get_top_threads(5),
            "communication_network": self.network_extractor.extract_communication_network()
        }

        return result