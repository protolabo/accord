
# 1) Email Parser
Pour installer les dépendances :
```bash
pip install -r requirements.txt
```

## Installation et Configuration

1. Téléchargez le dataset Enron depuis Kaggle :
   - Rendez-vous sur [https://www.kaggle.com/datasets/wcukierski/enron-email-dataset](https://www.kaggle.com/datasets/wcukierski/enron-email-dataset?resource=download)
   - Téléchargez le fichier ZIP

2. Préparation des données :
   - Extrayez le fichier `emails.csv` du ZIP
   - Placez `emails.csv` dans `./backend/data`

## Utilisation

3. Exécutez le script :
```bash
python emailParser.py
```

4. Résultat :
   - Le script génère un fichier `emails.json` dans le dossier `./backend/data`

# 2) Section Recherche

## Préparation des Données

- [ ] **Étape 1: Récupération des emails**
  - [ ] Implémenter l'authentification Gmail OAuth et outlook

- [ ] **Étape 2: Stockage temporaire**
  - [ ] Créer la structure de stockage sécurisée (Json crypté si possible)

- [ ] **Étape 3: Indexation de mails**

- [ ] **Étape 4: Construction du graphe de connexion**
  - [ ] Identifier les relations entre emails
  - [ ] Identifier les relations entre contacts

- [ ] **Étape 5: Classification des emails**

- [ ] **Étape 6: Génération des threads**

- [ ] **Étape 7: Stockage de notre structures de connexion de mails**

- [ ] **Étape 8: Nettoyage des données brutes**


## Recherche Sémantique

- [ ] **Étape 9: Analyse sémantique avec RoBERTa**
  - [ ] Extraction des entités et concepts clés

- [ ] **Étape 10: Transformation en requête structurée**
  - [ ] Extraction des contraintes de recherche
  - [ ] Expansion des requêtes (contexte)

- [ ] **Étape 11: Faire la recherche**

- [ ] **Étape 12: Présentation des résultats**
  - [ ] Organisation par pertinence et chronologie