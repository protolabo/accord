# Module Email Graph

## Objectif Principal

Ce module construit et analyse un graphe de communication à partir d'emails pour révéler les patterns de communication, identifier les contacts importants et comprendre la structure des échanges.

## Architecture du Module

### 1. Processor (`processor/`)
**Rôle** : Orchestrateur principal du traitement des emails

**Composants** :
- **EmailGraphProcessor** : Point d'entrée principal
  - Paramètres : `message_json` (données emails + config)
  - Retour : JSON avec analyse complète du graphe

- **Services internes** :
  - `EmailProcessingService` : Traite chaque email individuellement
  - `GraphBuildingService` : Construit le graphe progressivement
  - `AnalysisService` : Effectue l'analyse finale

### 2. Models (`models/`)
**Rôle** : Gestion des différents types de nœuds du graphe

#### MessageNodeManager (`message_node/`)
- **Objectif** : Créer et gérer les nœuds représentant les emails
- **Attributs gérés** : 
  - Identifiants (Message-ID, Thread-ID)
  - Métadonnées (date, sujet, contenu)
  - Participants (from, to, cc, bcc)
  - Propriétés (pièces jointes, importance, statut)

#### UserNodeManager (`user_node/`)
- **Objectif** : Créer et gérer les nœuds représentant les utilisateurs
- **Attributs gérés** :
  - Email normalisé
  - Nom extrait
  - Domaine
  - Force de connexion avec l'utilisateur central
- **Relations** : Gère les liens EMAILED entre utilisateurs

#### ThreadNodeManager (`thread_node/`)
- **Objectif** : Créer et gérer les nœuds représentant les conversations
- **Attributs gérés** :
  - Nombre de messages
  - Participants uniques
  - Dates (premier/dernier message)
  - Sujets et topics

### 3. Analysis (`analysis/`)
**Rôle** : Extraction d'insights du graphe construit

#### GraphMetricsAnalyzer
- **Objectif** : Calculer les métriques de communication
- **Métriques principales** :
  - Top contacts par force de connexion
  - Threads les plus actifs
  - Centralité des utilisateurs (PageRank, degré)
  - Densité du graphe

#### NetworkExtractor
- **Objectif** : Extraire le réseau de communication pour visualisation
- **Retour** : Structure JSON avec nœuds et liens pour rendu graphique

### 4. Search (`search/`)
**Rôle** : Moteur de recherche dans le graphe

#### GraphSearchEngine
- **Objectif** : Recherche avancée dans les emails via le graphe
- **Modes de recherche** :
  - **Contenu** : TF-IDF sur texte des messages
  - **Temporel** : Par plage de dates
  - **Utilisateur** : Par expéditeur/destinataire
  - **Combiné** : Fusion multi-critères

#### Services internes :
- **IndexingService** : Construit les index inversés et temporels
- **ScoringService** : Calcule les scores de pertinence
- **SearchService** : Exécute les recherches par type
- **ResultService** : Enrichit et formate les résultats

## Flux de Traitement

### Phase 1 : Construction
1. Réception des données emails (JSON)
2. Pour chaque email :
   - Création du nœud message
   - Création/mise à jour des nœuds utilisateur
   - Création/mise à jour du nœud thread
   - Établissement des relations

### Phase 2 : Analyse
1. Calcul des métriques de centralité
2. Identification des top contacts/threads
3. Extraction du réseau de communication

### Phase 3 : Indexation (si recherche activée)
1. Construction des index textuels (TF-IDF)
2. Construction des index temporels
3. Calcul des scores de pertinence

## Paramètres de Configuration

### Configuration globale
- `central_user` : Email de l'utilisateur principal (obligatoire)
- `max_emails` : Limite du nombre d'emails à traiter
- `batch_size` : Taille des lots pour traitement

### Poids des relations
- `sent_central_user` : 3.0 (emails envoyés par l'utilisateur central)
- `sent_normal` : 1.0 (autres emails envoyés)
- `received` : 1.0 (emails reçus)
- `cc` : 0.8 (copie carbone)
- `bcc` : 0.6 (copie cachée)

### Paramètres d'analyse
- `top_contacts_limit` : 10 (nombre de contacts principaux)
- `top_threads_limit` : 5 (nombre de threads principaux)

## Structure de Sortie

```json
{
  "central_user": "email@example.com",
  "top_contacts": [
    {
      "email": "contact@example.com",
      "name": "Contact Name",
      "connection_strength": 15.5,
      "sent_count": 10,
      "received_count": 5
    }
  ],
  "top_threads": [
    {
      "subject": "Projet X",
      "message_count": 25,
      "participants": ["user1", "user2"],
      "last_message_date": "2024-01-15"
    }
  ],
  "communication_network": {
    "nodes": [...],
    "links": [...]
  },
  "stats": {
    "total_nodes": 1500,
    "total_edges": 3200,
    "node_types": {...}
  }
}
```

## Optimisations Implémentées

- Traitement par lots pour gros volumes
- Cache des emails normalisés
- Index inversés pour recherche rapide
- Calcul incrémental des métriques

## Dépendances Principales

- **NetworkX** : Construction et analyse de graphes
- **python-dateutil** : Parsing de dates
- **pytz** : Gestion des fuseaux horaires
