# Accord - Intégration Backend-Frontend

Ce document explique comment l'application Accord intègre le backend (FastAPI) avec le frontend (React/Electron) et standardise les formats d'emails pour Gmail et Outlook.

## Architecture de l'intégration

### Backend (FastAPI)

1. **API Standardisée** : Une API REST centrale qui gère les deux services d'email (Gmail et Outlook)
2. **Format de données unifié** : Un modèle standardisé pour représenter les emails, dossiers et profils utilisateur
3. **Authentification** : JWT pour l'authentification des utilisateurs + OAuth2 pour Gmail et Outlook
4. **Base de données** : MongoDB pour stocker les utilisateurs et les emails

### Frontend (React + Electron)

1. **Service d'email unifié** : Un service qui communique avec l'API backend
2. **Interface utilisateur cohérente** : Les mêmes composants pour afficher les emails Gmail et Outlook
3. **Gestion d'état** : État applicatif qui maintient la cohérence entre les différentes sources d'emails

## Comment démarrer l'application

### Prérequis

- Python 3.9+ pour le backend
- Node.js 16+ pour le frontend
- MongoDB (une instance Atlas est configurée par défaut)
- Identifiants OAuth pour Gmail et Outlook

### Configuration

1. Configurez les variables d'environnement dans le fichier `.env` du backend:

   - Clés d'API pour Gmail et Outlook
   - Configuration MongoDB
   - Clé JWT

2. Installez les dépendances:

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend/react-app
npm install
cd ..
npm install
```

### Démarrage

1. Lancez le backend:

```bash
cd backend
python run.py --reload
```

Le serveur démarrera sur http://localhost:8000. Vous pouvez consulter la documentation API à http://localhost:8000/docs.

2. Lancez le frontend en mode développement:

```bash
cd frontend
npm run dev
```

## Flux d'authentification

1. L'utilisateur choisit un service d'email (Gmail ou Outlook)
2. Le frontend appelle l'API backend pour obtenir l'URL d'authentification
3. L'utilisateur autorise l'application via OAuth
4. Le backend échange le code d'autorisation contre des tokens d'accès et de rafraîchissement
5. Le backend stocke les tokens dans MongoDB et génère un JWT pour le frontend
6. Le frontend utilise le JWT pour toutes les requêtes API suivantes

## Format d'email standardisé

Tous les emails sont convertis à un format commun:

```typescript
interface StandardizedEmail {
  id: string;
  external_id: string;
  platform: string; // 'gmail' ou 'outlook'
  subject: string;
  from: string;
  from_email: string;
  to: string[];
  cc: string[];
  body: string;
  bodyType: "html" | "text";
  date: Date;
  isRead: boolean;
  isImportant: boolean;
  attachments: Array<{
    filename: string;
    content_type: string;
    size: number;
    content_id?: string;
    url?: string;
  }>;
  categories: string[];
  labels?: string[];
  threadId?: string;
}
```

## Endpoints API principaux

- `GET /api/auth/{service}/login` - Obtenir l'URL d'authentification
- `GET /api/auth/{service}/callback` - Callback d'authentification
- `GET /api/emails` - Récupérer les emails
- `GET /api/emails/{id}` - Récupérer un email par ID
- `POST /api/emails` - Envoyer un email
- `PATCH /api/emails/{id}/read` - Marquer un email comme lu/non lu
- `GET /api/folders` - Récupérer les dossiers/labels
- `GET /api/profile` - Récupérer le profil utilisateur

## Synchronisation des emails

Le backend exécute une tâche de synchronisation en arrière-plan qui:

1. Récupère régulièrement les nouveaux emails pour chaque utilisateur
2. Stocke les emails dans MongoDB
3. Met à jour les emails existants (statut de lecture, etc.)

## Troubleshooting

Si vous rencontrez des problèmes:

1. **Problèmes d'authentification**: Vérifiez les journaux backend pour les erreurs OAuth
2. **Emails manquants**: La première synchronisation peut prendre du temps. Vérifiez les journaux backend
3. **Erreurs frontend**: Vérifiez la console du navigateur et les requêtes réseau
4. **API inaccessible**: Vérifiez que le backend est en cours d'exécution et que les requêtes CORS sont correctement configurées
