

### 1. Module Email Graph (`email_graph/`)
**Objectif** : Construire et analyser un graphe relationnel à partir des emails pour comprendre les réseaux de communication.

**Fonctionnalités principales** :
- Construction de graphes NetworkX représentant les relations entre utilisateurs, messages et conversations
- Analyse des métriques de communication (contacts importants, threads actifs)
- Extraction de réseaux de communication pour visualisation

### 2. Module Semantic Search (`semantic_search/`)
**Objectif** : Permettre la recherche en langage naturel dans les emails.

**Fonctionnalités principales** :
- Transformation de requêtes naturelles en requêtes structurées
- Fusion intelligente entre analyse NLP (spaCy) et LLM (Mistral 7B)
- Support multilingue (français/anglais)

### 3. Module Flow Démarrage (`flow_demarrage.py`)
**Objectif** : Orchestrer le pipeline complet depuis l'import des emails jusqu'à la construction du graphe.

**Fonctionnalités principales** :
- Export des emails depuis Gmail
- Classification automatique des emails
- Construction du graphe de communication

## Flux de Données

```
1. Import des emails (Gmail API)
    ↓
2. Classification par IA (catégories, priorités)
    ↓
3. Construction du graphe (NetworkX)
    ↓
4. Indexation pour recherche
    ↓
5. Interface de recherche sémantique
```

## Structure des Données

### Nœuds du Graphe
- **Messages** : Emails individuels avec métadonnées
- **Utilisateurs** : Expéditeurs et destinataires
- **Threads** : Conversations groupées

### Relations
- **SENT** : Utilisateur → Message
- **RECEIVED/CC/BCC** : Message → Utilisateur
- **PART_OF_THREAD** : Message → Thread
- **EMAILED** : Utilisateur → Utilisateur

## Technologies Utilisées

- **Backend** : Python, FastAPI
- **Graphe** : NetworkX
- **NLP** : spaCy (fr_core_news_sm)
- **LLM** : Mistral 7B (GGUF)
- **Base de données** : MongoDB (prévu)
- **Frontend** : React/Electron (prévu)

## Installation et Configuration

Se référer aux README spécifiques de chaque module pour les détails d'installation.

## Modules Détaillés

- [Module Email Graph](./email_graph/README.md)
- [Module Semantic Search](./semantic_search/README.md)
- [Module Flow Démarrage](./flow_README.md)

## Points d'Entrée Principaux

1. **Construction du graphe** : `email_graph/build_graph_main.py`
2. **API de recherche** : `semantic_search/endpoints.py`
3. **Pipeline complet** : `services/flow_demarrage.py`

## Considérations de Performance

- Traitement par lots pour les gros volumes d'emails
- Mise en cache des résultats de parsing
- Indexation optimisée pour la recherche rapide

## Évolutions Futures

- Amélioration continue des modèles IA et de la recherche semantique