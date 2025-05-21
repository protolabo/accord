from typing import Dict, Any
from backend.app.services.semantic_search.models.query_schemas import EmailQuery
from backend.app.services.email_graph.utils.email_utils import normalize_email


def build_graph_query(email_query: EmailQuery) -> Dict[str, Any]:
    """
    Transforme un objet EmailQuery en requête pour le moteur de graphe

    Args:
        email_query: Objet EmailQuery validé

    Returns:
        dict: Requête formatée pour le moteur de graphe
    """
    # Sélectionner le constructeur approprié selon le type d'entité
    builders = {
        "mail": build_mail_query,
        "thread": build_thread_query,
        "user": build_user_query
    }

    builder = builders.get(email_query.entity)
    if not builder:
        raise ValueError(f"Type d'entité non supporté: {email_query.entity}")

    return builder(email_query)


def build_mail_query(email_query: EmailQuery) -> Dict[str, Any]:
    """
    Construit une requête pour rechercher des emails dans le graphe

    Args:
        email_query: Requête validée de type 'mail'

    Returns:
        dict: Requête formatée pour le moteur de graphe
    """
    # Structure de base de la requête
    # Dans votre graphe, les mails sont des noeuds "message"
    query = {
        "entity_type": "message",
        "conditions": [],
        "sort": {},
        "limit": email_query.limit or 20
    }

    # Traitement des filtres
    if email_query.filters:
        for filter in email_query.filters:
            # Conversion des types de filtres en conditions de graphe
            if filter.edge == "sent_by":
                # relation SENT de user → message
                query["conditions"].append({
                    "type": "relationship",
                    "direction": "incoming",
                    "relation": "SENT",
                    "from_type": "user",
                    "attribute": "email",
                    "value": normalize_email(filter.value)
                })

            elif filter.edge == "received_by":
                #  relation RECEIVED de message → user
                query["conditions"].append({
                    "type": "relationship",
                    "direction": "outgoing",
                    "relation": "RECEIVED",
                    "to_type": "user",
                    "attribute": "email",
                    "value": normalize_email(filter.value)
                })

            elif filter.edge == "cc_to":
                # relation CC de message → user
                query["conditions"].append({
                    "type": "relationship",
                    "direction": "outgoing",
                    "relation": "CC",
                    "to_type": "user",
                    "attribute": "email",
                    "value": normalize_email(filter.value)
                })

            elif filter.edge == "bcc_to":
                #  relation BCC de message → user
                query["conditions"].append({
                    "type": "relationship",
                    "direction": "outgoing",
                    "relation": "BCC",
                    "to_type": "user",
                    "attribute": "email",
                    "value": normalize_email(filter.value)
                })

            elif filter.edge == "part_of_thread":
                #  relation PART_OF_THREAD de message → thread
                query["conditions"].append({
                    "type": "relationship",
                    "direction": "outgoing",
                    "relation": "PART_OF_THREAD",
                    "to_type": "thread",
                    "to_id": filter.value
                })

            elif filter.edge == "has_label":
                # Attribut "labels" sur les noeuds message
                query["conditions"].append({
                    "type": "attribute",
                    "attribute": "labels",
                    "operator": "contains",
                    "value": filter.value
                })

            elif filter.edge == "has_category":
                # Attribut "categories" sur les noeuds message
                query["conditions"].append({
                    "type": "attribute",
                    "attribute": "categories",
                    "operator": "contains",
                    "value": filter.value
                })

            elif filter.edge == "has_attachment":
                # Attribut "attachment" sur les noeuds message
                if filter.value.lower() in ["yes", "true", "1"]:
                    query["conditions"].append({
                        "type": "attribute",
                        "attribute": "attachment",
                        "operator": "not_empty"
                    })

            elif filter.edge == "contains_text":
                # Recherche dans le sujet ou le snippet
                query["conditions"].append({
                    "type": "or",
                    "conditions": [
                        {
                            "type": "attribute",
                            "attribute": "subject",
                            "operator": "contains",
                            "value": filter.value
                        },
                        {
                            "type": "attribute",
                            "attribute": "snippet",
                            "operator": "contains",
                            "value": filter.value
                        }
                    ]
                })
            elif filter.edge == "date_before":
                # Utiliser directement la valeur fournie par le LLM
                query["conditions"].append({
                    "type": "attribute",
                    "attribute": "date",
                    "operator": "lte",
                    "value": filter.value
                })

            elif filter.edge == "date_after":
                # Utiliser directement la valeur fournie par le LLM
                query["conditions"].append({
                    "type": "attribute",
                    "attribute": "date",
                    "operator": "gte",
                    "value": filter.value
                })

            elif filter.edge == "from_domain":
                # Recherche par domaine d'email
                query["conditions"].append({
                    "type": "attribute",
                    "attribute": "from_email",
                    "operator": "ends_with",
                    "value": "@" + filter.value.lstrip("@")
                })

    # Traitement du tri
    if email_query.sort:
        field_mapping = {
            "date": "date",
            "connection_strength": "from_email.connection_strength"  # Relation vers l'utilisateur
        }

        sort_field = field_mapping.get(email_query.sort.field, "date")
        sort_direction = email_query.sort.order

        query["sort"] = {
            "field": sort_field,
            "direction": sort_direction
        }
    else:
        # Tri par défaut: date décroissante (plus récent d'abord)
        query["sort"] = {
            "field": "date",
            "direction": "desc"
        }

    return query


def build_thread_query(email_query: EmailQuery) -> Dict[str, Any]:
    """
    Construit une requête pour rechercher des threads dans le graphe

    Args:
        email_query: Requête validée de type 'thread'

    Returns:
        dict: Requête formatée pour le moteur de graphe
    """
    # Structure de base de la requête
    query = {
        "entity_type": "thread",
        "conditions": [],
        "sort": {},
        "limit": email_query.limit or 20
    }

    # Traitement des filtres
    if email_query.filters:
        for filter in email_query.filters:
            if filter.edge == "sent_by" or filter.edge == "received_by":
                # Pour les threads, rechercher les participants
                query["conditions"].append({
                    "type": "attribute",
                    "attribute": "participants",
                    "operator": "contains",
                    "value": normalize_email(filter.value)
                })

            elif filter.edge == "contains_text":
                # Recherche par sujet du thread
                query["conditions"].append({
                    "type": "attribute",
                    "attribute": "subject",
                    "operator": "contains",
                    "value": filter.value
                })


            elif filter.edge == "date_before":

                # Utiliser directement la valeur fournie par le LLM

                query["conditions"].append({

                    "type": "attribute",

                    "attribute": "date",

                    "operator": "lte",

                    "value": filter.value

                })


            elif filter.edge == "date_after":

                # Utiliser directement la valeur fournie par le LLM

                query["conditions"].append({

                    "type": "attribute",

                    "attribute": "date",

                    "operator": "gte",

                    "value": filter.value

                })

    # Traitement du tri
    if email_query.sort:
        field_mapping = {
            "date": "last_message_date",
            "message_count": "message_count",
            "thread_size": "message_count"
        }

        sort_field = field_mapping.get(email_query.sort.field, "last_message_date")
        sort_direction = email_query.sort.order

        query["sort"] = {
            "field": sort_field,
            "direction": sort_direction
        }
    else:
        # Tri par défaut: date du dernier message décroissante
        query["sort"] = {
            "field": "last_message_date",
            "direction": "desc"
        }

    return query


def build_user_query(email_query: EmailQuery) -> Dict[str, Any]:
    """
    Construit une requête pour rechercher des utilisateurs dans le graphe

    Args:
        email_query: Requête validée de type 'user'

    Returns:
        dict: Requête formatée pour le moteur de graphe
    """
    # Structure de base de la requête
    query = {
        "entity_type": "user",
        "conditions": [],
        "sort": {},
        "limit": email_query.limit or 20
    }

    # Traitement des filtres
    if email_query.filters:
        for filter in email_query.filters:
            if filter.edge == "from_domain":
                # Filtrage par domaine d'email
                query["conditions"].append({
                    "type": "attribute",
                    "attribute": "domain",
                    "operator": "equals",
                    "value": filter.value.lstrip("@")
                })

            elif filter.edge == "contains_text":
                # Recherche par nom ou email
                query["conditions"].append({
                    "type": "or",
                    "conditions": [
                        {
                            "type": "attribute",
                            "attribute": "name",
                            "operator": "contains",
                            "value": filter.value
                        },
                        {
                            "type": "attribute",
                            "attribute": "email",
                            "operator": "contains",
                            "value": filter.value
                        }
                    ]
                })

    # Traitement du tri
    if email_query.sort:
        field_mapping = {
            "connection_strength": "connection_strength"
        }

        sort_field = field_mapping.get(email_query.sort.field, "connection_strength")
        sort_direction = email_query.sort.order

        query["sort"] = {
            "field": sort_field,
            "direction": sort_direction
        }
    else:
        # Tri par défaut: force de connexion décroissante
        query["sort"] = {
            "field": "connection_strength",
            "direction": "desc"
        }

    return query


