from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime


class EmailFilter(BaseModel):
    edge: str = Field(
        description="Type de relation dans le graphe"
    )
    value: str = Field(
        description="Valeur recherchée pour cette relation"
    )

    @validator('edge')
    def validate_edge_type(cls, v):
        # Liste des relations disponibles dans le graphe d'emails
        # Correspond aux types de relations définis dans user_node.py,
        # message_node.py et thread_node.py
        valid_edges = [
            "sent_by",  # Relation SENT dans graph: utilisateur -> message
            "received_by",  # Relation RECEIVED dans graph: message -> utilisateur
            "cc_to",  # Relation CC dans graph: message -> utilisateur
            "bcc_to",  # Relation BCC dans graph: message -> utilisateur
            "part_of_thread",  # Relation PART_OF_THREAD dans graph: message -> thread
            "has_label",  # Attribut "labels" sur les noeuds de message
            "has_category",  # Attribut "categories" sur les noeuds de message
            "has_attachment",  # Attribut "attachment" sur les noeuds de message
            "contains_text",  # Recherche dans "subject" ou "snippet" des messages
            "date_before",  # Filtrage sur l'attribut "date" des messages
            "date_after",  # Filtrage sur l'attribut "date" des messages
            "from_domain"  # Filtrage sur l'attribut "domain" des utilisateurs
        ]
        if v not in valid_edges:
            raise ValueError(f"Edge type must be one of: {', '.join(valid_edges)}")
        return v


class EmailSorting(BaseModel):
    field: str = Field(
        description="Champ sur lequel trier les résultats"
    )
    order: Literal["asc", "desc"] = Field(
        description="Ordre de tri (asc/desc)"
    )

    @validator('field')
    def validate_sort_field(cls, v):
        # Champs disponibles pour le tri, extraits des attributs
        # présents dans les différents noeuds du graphe
        valid_fields = [
            "date",  # Attribut "date" des messages
            "connection_strength",  # Attribut des noeuds utilisateur
            "message_count",  # Attribut des noeuds thread
            "thread_size"  # Alternative pour message_count
        ]
        if v not in valid_fields:
            raise ValueError(f"Sort field must be one of: {', '.join(valid_fields)}")
        return v


class EmailQuery(BaseModel):
    # Les types d'entités correspondent aux trois principaux noeuds
    # définis dans votre graphe d'emails
    entity: Literal["mail", "thread", "user"] = Field(
        description="Type d'entité recherchée"
    )

    # Liste de filtres à appliquer, chacun représentant
    # une condition sur une relation ou un attribut
    filters: Optional[List[EmailFilter]] = Field(
        description="Filtres à appliquer",
        default=[]
    )

    # Configuration de tri pour ordonner les résultats
    sort: Optional[EmailSorting] = Field(
        description="Spécification du tri",
        default=None  # Si non spécifié, un tri par défaut sera appliqué
    )

    # Nombre maximum de résultats à retourner
    limit: Optional[int] = Field(
        description="Nombre maximum de résultats",
        default=20,
        ge=1,  # Au moins 1 résultat
        le=100  # Maximum
    )

    class Config:
        # Exemple concret pour aider le LLM à comprendre le format attendu
        schema_extra = {
            "example": {
                "entity": "mail",
                "filters": [
                    {"edge": "sent_by", "value": "john@example.com"},
                    {"edge": "part_of_thread", "value": "thread-123"}
                ],
                "sort": {"field": "date", "order": "desc"},
                "limit": 10
            }
        }