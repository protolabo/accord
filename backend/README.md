
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

- [x] **Étape 1: Récupération des emails**
  - [x] Implémenter l'authentification Gmail OAuth et outlook

- [x] **Étape 2: Stockage temporaire**
  - [x] Créer la structure de stockage sécurisée (Json crypté si possible)

- [x] **Étape 3: Indexation de mails**

- [x] **Étape 4: Construction du graphe de connexion**
  - [x] Identifier les relations entre emails
  - [x] Identifier les relations entre contacts

- [ ] **Étape 5: Classification des emails**

- [ ] **Étape 6: Génération des threads**

- [x] **Étape 7: Stockage de notre structures de connexion de mails**

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
