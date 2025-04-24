# Guide de Test d'Intégration des Emails du Projet ACCORD


## Prérequis

Avant de commencer le processus de test, veuillez vous assurer que vous disposez de :

- Un environnement Python avec toutes les dépendances installées
- Accès au code source du projet ACCORD
- Un compte Gmail autorisé pour les tests
- Le fichier `credentials.json` pour l'authentification à l'API Google
- Votre adresse email ajoutée à la liste des utilisateurs de test autorisés

## Options de Test

Vous avez deux options pour tester le flux de traitement des emails :

1. **Avec votre compte Google réel** : Récupère et traite vos emails actuels
2. **Avec des données simulées** : Utilise des données de test générées cependant il accédera toujours à votre compte Gmail

## Option 1 : Test avec Votre Compte Google

### Configuration et Exécution

1. Démarrez le serveur FastAPI en exécutant l'application principale :
   ```bash
   python -m backend.app.main
   ```

2. Ouvrez le script d'exportation des emails dans votre éditeur :
   ```
   backend/app/email_providers/google/export_gmail_to_json.py
   ```

3. Exécutez la fonction d'exportation avec votre adresse email :
   ```python
   export_emails_to_json("votre.email@gmail.com", 100, "../data", 5000)
   ```
   
   Explication des paramètres :
   - Premier paramètre : Votre adresse Gmail
   - Deuxième paramètre : Nombre maximum d'emails à récupérer (100 dans cet exemple)
   - Troisième paramètre : Répertoire de sortie pour stocker les données des emails
   - Quatrième paramètre : Taille de lot pour le traitement

4. Suivez les instructions d'authentification dans votre navigateur pour accorder l'accès à votre compte Gmail.

### Flux du Processus

Lors de l'exécution, le système va :
1. Se connecter aux API de Google en utilisant l'authentification OAuth
2. Récupérer vos emails (limités au nombre spécifié), None pour tous recuperer
3. Sauvegarder les emails dans des fichiers JSON par lots
4. Appliquer la classification IA pour catégoriser chaque email
5. Générer un graphe de relations montrant les modèles de communication

## Option 2 : Test avec des Données Simulées

Si vous préférez ne pas utiliser vos emails réels ou ne pouvez pas accéder à l'API de Google, vous pouvez tester avec des données simulées :

1. Générez des données d'emails simulées en exécutant :
   ```python
   # Exécuter le générateur de données simulées
   from backend.app.utils.dataGenerator.mainGenerator import main as mockdataGenerator
   mockdataGenerator()
   ```

2. Modifiez le script d'exportation pour utiliser des données simulées au lieu de l'API Google :
   - Ouvrez `backend/app/email_providers/google/export_gmail_to_json.py`
   - Commentez ces lignes :
     ```python
     classify_exported_emails(output_dir)
     build_graph_main(input_dir=output_dir, output_dir=f"{output_dir}/graph", central_user=email)
     ```
   - Décommentez ces lignes :
     ```python
     classify_exported_emails()
     build_graph_main()
     ```

## Dépannage

Si vous rencontrez des problèmes lors des tests :

- **Échecs d'authentification** : Assurez-vous que votre email est ajouté à la liste des utilisateurs de test
- **Identifiants manquants** : Contactez les administrateurs du projet pour obtenir le fichier `credentials.json`
- **Erreurs de classification** : Vérifiez que toutes les dépendances du modèle IA sont correctement installées
- **Erreurs de chemin de fichier** : Vérifiez que tous les chemins de répertoire existent et sont accessibles

## Informations de Contact

Pour obtenir de l'aide concernant les tests ou pour demander l'accès à la liste des utilisateurs de test, veuillez contacter les administrateurs du projet.
