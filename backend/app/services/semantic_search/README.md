# Module Semantic Search

## Objectif Principal

Ce module transforme des requêtes en langage naturel (français/anglais) en requêtes structurées pour rechercher efficacement dans le graphe d'emails. Il combine analyse linguistique traditionnelle (NLP) et intelligence artificielle (LLM) pour une compréhension optimale.

## Architecture du Module

### 1. Parsing (`parsing/`)
**Rôle** : Analyser et extraire les entités des requêtes naturelles

#### QueryParser
- **Objectif** : Orchestrateur principal du parsing
- **Stratégie** : Fusion NLP (spaCy) + patterns regex enrichis
- **Paramètres** :
  - `query` : Texte de la requête utilisateur
  - `context` : Contexte optionnel (timezone, langue, etc.)

#### Composants spécialisés :
- **LanguageDetector** : Détecte automatiquement fr/en
- **EntityExtractor** : Extrait personnes, dates, emails, topics
- **IntentDetector** : Identifie l'intention de recherche
- **Validator** : Valide et nettoie les entités extraites
- **ConfidenceCalculator** : Évalue la fiabilité du parsing

### 2. LLM Engine (`llm_engine.py`)
**Rôle** : Parsing avancé via Mistral 7B pour cas complexes

- **Modèle** : Mistral-7B-Instruct GGUF (quantifié Q4)
- **Activation** : Quand confiance NLP < 0.8
- **Avantages** :
  - Compréhension contextuelle profonde
  - Gestion des requêtes ambiguës
  - Extraction de filtres complexes

### 3. Query Transformer (`query_transformer.py`)
**Rôle** : Convertir les résultats de parsing en structure de recherche

#### Stratégies de transformation par type :
- **Sémantique** : Recherche par contenu/sens
- **Contact** : Recherche par personne
- **Temporelle** : Recherche par date/période
- **Topic** : Recherche par sujet
- **Thread** : Recherche dans conversations
- **Combinée** : Multi-critères

### 4. API Endpoints (`endpoints.py`)
**Rôle** : Interface REST pour le frontend

- **POST /semantic-search/parse** : Endpoint principal
- **GET /semantic-search/health** : Vérification santé
- **POST /semantic-search/test-query** : Tests de développement

## Types de Requêtes Supportées

### 1. Recherche par Contact
- "emails de Marie"
- "messages envoyés à Pierre"
- "courriels de marie@company.com"

### 2. Recherche Temporelle
- "emails d'hier"
- "messages de la semaine dernière"
- "courriels du 15 mars 2024"
- "emails entre le 1er et le 15 janvier"

### 3. Recherche par Attributs
- "emails avec pièces jointes"
- "messages importants"
- "emails non lus"
- "courriels avec PDF"

### 4. Recherche par Contenu/Topic
- "factures du mois dernier"
- "discussions sur le projet X"
- "newsletter"

### 5. Recherches Combinées
- "emails de Marie avec pièces jointes hier"
- "factures importantes de janvier"
- "messages urgents de l'équipe marketing"

## Patterns Enrichis

### Patterns Temporels
- Relatifs : hier, semaine dernière, mois prochain
- Absolus : dates ISO, formats français/anglais
- Périodes : début/milieu/fin de mois
- Plages : entre deux dates

### Patterns de Contact
- Détection nom/prénom
- Extraction d'emails
- Distinction expéditeur/destinataire
- Groupes et équipes

### Patterns d'Action
- Pièces jointes (avec/sans)
- États (lu/non lu, important)
- Négations et exclusions

## Flux de Traitement

### Phase 1 : Parsing NLP
1. Détection de langue
2. Nettoyage de la requête
3. Extraction d'entités (spaCy + regex)
4. Détection d'intention
5. Calcul de confiance

### Phase 2 : Parsing LLM (si nécessaire)
1. Construction du prompt structuré
2. Appel Mistral 7B
3. Parsing JSON de la réponse
4. Validation et nettoyage

### Phase 3 : Fusion et Transformation
1. Fusion intelligente NLP + LLM
2. Application de la stratégie de transformation
3. Validation finale
4. Enrichissement avec métadonnées

## Structure de Sortie

```json
{
  "success": true,
  "semantic_query": {
    "query_type": "contact",
    "semantic_text": "rapport mensuel",
    "filters": {
      "contact_name": "Marie Dupont",
      "date_from": "2024-01-01",
      "has_attachments": true
    },
    "limit": 20,
    "similarity_threshold": 0.3
  },
  "processing_info": {
    "transformation_time_ms": 145.2,
    "parsing_method": "hybrid_balanced",
    "confidence": 0.85
  }
}
```

## Configuration LLM

### Paramètres du modèle
- `n_ctx` : 8192 (contexte étendu)
- `n_gpu_layers` : 32 (accélération GPU)
- `temperature` : 0.05 (déterministe)
- `max_tokens` : 300

### Optimisations
- Mise en cache du modèle (singleton)
- Prompt engineering pour JSON strict
- Fallback sur parsing règles si échec

## Gestion Multilingue

### Détection automatique
- Analyse des mots-clés caractéristiques
- Score français vs anglais
- Mode "auto" pour patterns bilingues

### Adaptation des patterns
- Mois : janvier/january
- Indicateurs temporels : hier/yesterday
- Formats de dates : DD/MM vs MM/DD

## Points d'Extension

- Support de nouvelles langues
- Patterns personnalisés par domaine
- Intégration d'autres LLM
- Apprentissage des préférences utilisateur

## Dépendances Principales

- **spaCy** : Analyse linguistique
- **llama-cpp-python** : Inférence Mistral
- **langchain** : Parsing structuré (optionnel)
- **FastAPI** : API REST

## Amelioration futur 
- definir des entites personnaliées pour avoir les memes resulats dans les deux langues 

