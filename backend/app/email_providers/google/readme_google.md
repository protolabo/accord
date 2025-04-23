# Module d'Authentification et d'Export Gmail

## Fonctionnalités principales

- Authentification OAuth2 avec Google (flux d'autorisation via navigateur)
- Gestion des tokens d'authentification (génération, stockage sécurisé, rafraîchissement)
- Récupération des emails depuis l'API Gmail (avec support de pagination)
- Export des emails vers des fichiers JSON (par lots pour gérer les grands volumes)
- Endpoints API pour déclencher l'authentification et l'export des emails
- Exécution des exports en arrière-plan pour ne pas bloquer les requêtes HTTP


## Installation et configuration

1. Placez votre fichier `credentials.json` dans le répertoire spécifié dans `settings.py`
2. Assurez-vous que les répertoires pour les tokens et les exports existent
3. Vérifiez que les URI de redirection dans votre projet GCP correspondent à ceux définis dans `settings.py`

## Structure du code

- `settings.py` - Configuration centralisée pour les chemins et les scopes OAuth
- `gmail_auth.py` - Gestion de l'authentification OAuth2 avec Google
- `gmail_service.py` - Service pour interagir avec l'API Gmail
- `auth.py` - Routes FastAPI pour l'authentification et l'export
- `export_gmail_to_json.py` - Fonctions pour l'export des emails vers JSON

## Utilisation des API

### Authentification

L'authentification se fait en deux étapes :

1. Redirection vers l'URL d'authentification Google : `GET /auth/gmail?email=utilisateur@gmail.com`
2. Callback automatique après authentification : `GET /auth/callback`

Une fois authentifié, l'utilisateur peut vérifier son statut :

```
GET /auth/status?email=utilisateur@gmail.com
```

### Export des emails

Pour déclencher un export des emails :

```
POST /export/gmail
{
    "email": "utilisateur@gmail.com", 
    "max_emails": 1000,         // optionnel, null = tous
    "output_dir": "./data",     // optionnel
    "batch_size": 5000          // optionnel
}
```

Cette opération s'exécute en arrière-plan et retourne immédiatement une confirmation.



## Flux d'authentification

Le flux d'authentification fonctionne comme suit :

1. L'utilisateur est redirigé vers l'écran de consentement Google
2. Après acceptation, Google redirige vers votre callback
3. Le code d'autorisation est échangé contre des tokens d'accès et de rafraîchissement
4. Les tokens sont stockés dans le répertoire spécifié pour une utilisation ultérieure
5. Le token d'accès est automatiquement rafraîchi lorsqu'il expire

## Structure des données exportées

Les emails sont exportés avec la structure suivante :

```json
{
  "Message-ID": "unique_id",
  "Thread-ID": "thread_id",
  "Labels": ["INBOX", "CATEGORY_PERSONAL"],
  "Date": "RFC 2822 date format",
  "From": "sender@example.com",
  "To": "recipient@example.com",
  "Subject": "Email subject",
  "Body": {
    "plain": "Texte brut",
    "html": "<html>Version HTML</html>"
  },
  "Attachments": [
    {
      "id": "attachment_id",
      "filename": "document.pdf",
      "mimeType": "application/pdf",
      "size": 12345
    }
  ],
  "Snippet": "Aperçu du contenu..."
}
```

## Dépannage

### Problèmes d'authentification

- Vérifiez que les URI de redirection configurés dans GCP correspondent à ceux utilisés
- Assurez-vous que les scopes demandés sont activés dans le projet GCP
- Vérifiez que le fichier credentials.json est au bon format et contient les bonnes informations

### Erreurs lors de l'export

- L'API Gmail a des quotas de requêtes - des pauses sont intégrées dans le code
- Des problèmes de réseau peuvent interrompre le téléchargement de grands volumes

## Sécurité

Les tokens d'authentification sont stockés localement dans le répertoire TOKEN_DIR spécifié. Ces tokens contiennent des informations sensibles et doivent être protégés :

- Veillez à ce que les permissions des fichiers soient correctement configurées
- Ne partagez pas les tokens entre différentes installations

## Limitations connues

- La récupération de très grandes boîtes mail (>50 000 emails) peut être lente
- Les pièces jointes ne sont pas enregistré juste les metadonnéées qui est collecté
- L'API Gmail peut appliquer des limites de quota qui ralentissent le processus

