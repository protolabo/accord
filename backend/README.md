
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
