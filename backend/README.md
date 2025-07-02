# Accord Backend

## Fonctionnalités principales

- **Authentification OAuth2** - Intégration sécurisée avec Gmail via Google OAuth
- **Classification IA** - Analyse automatique et catégorisation des emails
- **Graphe de communication** - Analyse des relations et patterns de communication
- **Recherche sémantique** - Recherche en langage naturel avec NLP et LLM
- **Analytics** - Métriques et insights sur les communications
- **Export automatisé** - Sauvegarde et traitement par lots des emails

## Architecture

```
backend/
├── app/
│   ├── core/                     # Configuration et sécurité
│   ├── email_providers/          # Intégrations (Gmail, etc.)
│   │   └── google/              # Module Gmail OAuth & API
│   ├── routes/                   # Endpoints FastAPI
│   ├── services/                 # Logique métier
│   │   ├── ai/                  # Classification IA
│   │   ├── email_graph/         # Analyse de graphe
│   │   └── semantic_search/     # Recherche NLP/LLM
│   ├── data/                    # Données et storage
│   └── utils/                   # Utilitaires
```

## Installation rapide

### Prérequis

- Python 3.9+
- Credentials Google Cloud Platform

### Installation

```bash
cd accord/backend

# Installer les dépendances
pip install -r requirements.txt

# Configuration des variables d'environnement
cp .env.example .env
# Éditer .env avec vos configurations

# Lancer le serveur de développement
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Configuration Google OAuth

1. Créer un projet dans [Google Cloud Console](https://console.cloud.google.com)
2. Activer l'API Gmail
3. Créer des credentials OAuth 2.0
4. Télécharger le fichier `credentials.json`
5. Placer le fichier dans `app/email_providers/google/`

##  API Endpoints

### Authentification
```
GET  /auth/gmail                 # Initier l'authentification Gmail
GET  /auth/callback              # Callback OAuth
GET  /auth/status                # Vérifier le statut d'auth
POST /auth/google/token          # Générer token JWT
```

### Gestion des emails
```
POST /export/gmail               # Exporter les emails Gmail
GET  /export/gmail/status        # Statut de l'export
GET  /emails                     # Récupérer les emails exportés
GET  /emails/classified          # Emails avec classification IA
```

### Recherche sémantique
```
POST /semantic-search/parse      # Parser requête naturelle
GET  /semantic-search/health     # Santé du service
```

### Données de test
```
GET  /mock/classified-emails    # Emails classifiés de test
```

## Modules spécialisés

### 1. Module Gmail (`email_providers/google/`)
- **Objectif** : Authentification et récupération des emails Gmail
- **Technologies** : Google OAuth2, Gmail API
- **Fonctionnalités** :
  - Flux d'authentification complet
  - Export par lots avec gestion des quotas
  - Gestion des tokens et rafraîchissement automatique

### 2. Module IA (`services/ai/`)
- **Objectif** : Classification automatique des emails


### 3. Module Graphe (`services/email_graph/`)
- **Objectif** : Analyse des relations de communication
- **Technologies** : NetworkX, analyse de graphes
- **Fonctionnalités** :
  - Construction de graphes de communication
  - Export

### 4. Module Recherche Sémantique (`services/semantic_search/`)
- **Objectif** : Recherche en langage naturel
- **Technologies** : spaCy, Mistral LLM, patterns regex
- **Fonctionnalités** :
  - Parsing de requêtes multilingues (FR/EN)
  - Extraction d'entités (dates, contacts, topics)
  - Fusion NLP + LLM pour cas complexes

## Configuration

### Variables d'environnement

```bash
# Google OAuth
GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
GOOGLE_TOKEN_DIR=/path/to/tokens
GMAIL_REDIRECT_URI=http://localhost:8000/api/auth/gmail/callback

# Sécurité
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# encore optionnel
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=accord

# IA & ML
HUGGINGFACE_MODEL_PATH=/path/to/models
MISTRAL_MODEL_PATH=/path/to/mistral-7b.gguf
```

### Structure des données

#### Email exporté
```json
{
  "Message-ID": "unique_id",
  "Thread-ID": "thread_id",
  "Date": "2024-01-15T10:30:00Z",
  "From": "sender@example.com",
  "To": "recipient@example.com",
  "Subject": "Email subject",
  "Body": {
    "plain": "Text content",
    "html": "<html>HTML content</html>"
  },
  "Attachments": [
    {
      "filename": "document.pdf",
      "mimeType": "application/pdf",
      "size": 12345
    }
  ],
  "accord_main_class": "professional",
  "accord_sub_classes": ["project", "important"]
}
```

##  Tests et développement

### Lancer les tests
```bash
# Tests unitaires
python -m pytest app/services/email_graph/tests/

# Tests d'intégration
python -m pytest tests/integration/

# Tests avec couverture
pytest --cov=app tests/
```

### Mode développement
```bash
# Lancer avec rechargement automatique
uvicorn app.main:app --reload

# Avec données de test
python -m app.services.semantic_search.test_semantic_search_flow.main --mode enhanced

# Test du graphe d'emails
python -m app.services.email_graph.build_graph_main
```


### Problèmes courants

**Erreur d'authentification Gmail**
```bash
# Vérifier les credentials
ls -la app/email_providers/google/credentials.json

# Vérifier les permissions OAuth
# Aller dans Google Cloud Console > APIs & Services > Credentials
```

**Modèle Mistral non trouvé**
```bash
# Télécharger le modèle
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/Mistral-7B-Instruct-v0.3-Q4_K_M.gguf

#verifier le chemin vers le modele en locale
dans accord/backend/app/services/semantic_search/llm_engine.py
```
