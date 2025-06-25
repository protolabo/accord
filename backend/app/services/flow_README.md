# Module Flow Démarrage

## Objectif Principal

Ce module orchestre le pipeline complet de traitement des emails, depuis l'import initial jusqu'à la construction du graphe analysé. Il coordonne l'ensemble des étapes de manière séquentielle et gère les erreurs à chaque phase.

## Flux d'Exécution

### Phase 1 : Exportation des Emails
**Fonction** : `flowDemarrage()`

**Paramètres** :
- `email` : Adresse Gmail de l'utilisateur (obligatoire)
- `max_emails` : Limite du nombre d'emails (None = tous)
- `output_dir` : Répertoire de sortie des fichiers
- `batch_size` : Taille des lots d'export (défaut: 5000)

**Actions** :
1. Vérification de l'authentification Gmail
2. Récupération des emails via API Gmail
3. Export en fichiers JSON par lots
4. Création d'un index de métadonnées

### Phase 2 : Classification des Emails
**Fonction** : `classify_exported_emails()`

**Objectif** : Enrichir chaque email avec des classifications IA

**Classifications ajoutées** :
- `accord_main_class` : Catégorie principale
- `accord_sub_classes` : Sous-catégories multiples

**Traitement** :
- Lecture séquentielle des fichiers batch
- Classification via pipeline IA
- Mise à jour des fichiers JSON enrichis

### Phase 3 : Construction du Graphe
**Fonction** : Appel à `build_graph_main()`

**Actions** :
1. Chargement des emails classifiés
2. Construction du graphe NetworkX
3. Analyse des relations et métriques
4. Sauvegarde des résultats

## Gestion du Statut

Le module maintient un statut global du processus :

### États possibles
- `processing` : Traitement en cours
- `completed` : Terminé avec succès
- `error` : Erreur pendant le traitement

### Points de progression
- 0% : Démarrage
- 20% : Authentification validée
- 50% : Emails exportés
- 70% : Classification terminée
- 85% : Construction graphe en cours
- 100% : Processus complet

## Structure des Fichiers de Sortie

### Répertoire d'export (`output_dir/`)
```
output_dir/
├── emails_batch_1.json      # Lot 1 d'emails
├── emails_batch_2.json      # Lot 2 d'emails
├── ...
└── index.json              # Métadonnées globales
```

### Format du fichier index
```json
{
  "email": "user@gmail.com",
  "user_id": "user_normalized",
  "total_emails": 15000,
  "total_batches": 3,
  "export_date": "2024-01-15T10:30:00",
  "batches": ["emails_batch_1.json", ...],
  "duration_seconds": 120.5
}
```

### Format des emails enrichis
```json
{
  "Message-ID": "msg123",
  "Subject": "Facture janvier",
  "From": "service@company.com",
  "To": "user@gmail.com",
  "Date": "2024-01-10T09:00:00",
  // ... autres champs originaux ...
  "accord_main_class": "finance",
  "accord_sub_classes": ["facturation", "mensuel"]
}
```

## Gestion des Erreurs

### Points de défaillance gérés
1. **Authentification** : Vérification préalable des credentials
2. **Export** : Gestion des timeouts API Gmail
3. **Classification** : Skip des emails problématiques
4. **Construction graphe** : Validation des données

### Stratégie de récupération
- Logs détaillés à chaque étape
- Sauvegarde progressive (par batch)
- Possibilité de reprendre après interruption

## Optimisations

### Performance
- Export par lots pour limiter la mémoire
- Classification parallèle possible
- Construction graphe incrémentale

### Fiabilité
- Validation des données à chaque étape
- Gestion explicite des exceptions
- Statut persistant pour monitoring

## Configuration Requise

### Authentification Gmail
- Credentials OAuth2 valides
- Token d'accès actualisé
- Permissions de lecture emails

### Ressources système
- RAM : 4GB minimum (8GB recommandé)
- Disque : 10MB par 1000 emails environ
- CPU : Multi-cœurs pour classification

## Intégration avec les Autres Modules

### Dépendances directes
1. **Gmail Service** : API d'export
2. **AI Pipeline** : Classification emails
3. **Email Graph** : Construction et analyse

### Flux de données
```
Gmail API → Fichiers JSON → Classification IA → Graphe NetworkX → Analyse
```

## Utilisation Type

```python
# Lancement complet du pipeline
flowDemarrage(
    email="utilisateur@gmail.com",
    max_emails=10000,  # Limiter pour tests
    output_dir="/path/to/output",
    batch_size=5000
)
```

## Monitoring et Logs

### Informations loggées
- Progression de chaque phase
- Temps d'exécution par étape
- Nombre d'emails traités
- Erreurs et avertissements

### Métriques clés
- Taux de succès classification
- Vitesse de traitement (emails/seconde)
- Utilisation mémoire
- Taille des fichiers générés

## Extensions Possibles

- Support d'autres providers email