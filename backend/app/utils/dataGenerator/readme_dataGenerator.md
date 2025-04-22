# Module Générateur de données (mails)

## Description
Ce module permet de générer un jeu de données de courriels fictifs réalistes pour le projet Accord.
Il utilise le célèbre dataset Enron comme base pour créer des courriels avec un contenu authentique, tout en ajoutant une structure cohérente et des métadonnées fictives.

## Fonctionnalités
- Conversion du dataset Enron brut au format JSON structuré
- Génération de courriels fictifs avec des conversions réalistes
- Création d'utilisateurs, contacts, projets et fils de discussion
- Simulation de pièces jointes et de catégories
- Maintien de la cohérence des conversations

## Prérequis
- Les bibliothèques Python suivantes:
  - pandas
  - faker
  - tqdm
  - uuid
  - datetime

## Obtention des données Enron
Avant d'exécuter les scripts, vous devez télécharger le dataset Enron:

1. Téléchargez le fichier CSV des emails Enron depuis [Kaggle](https://www.kaggle.com/datasets/wcukierski/enron-email-dataset?resource=download) ou une autre source appropriée
2. Renommez le fichier téléchargé en `emails.csv`
3. Placez-le dans le même répertoire que les scripts

## Structure des fichiers
- `mainGenerator.py`: Script principal qui orchestre le processus complet
- `emailParser.py`: Analyse les emails Enron bruts et les convertit en format JSON structuré
- `enron_data_manager.py`: Gère les données Enron pour la génération de contenu réaliste
- `generatorMail.py`: Génère des courriels fictifs basés sur les données Enron

## Exécution
Pour générer les données, exécutez simplement:
```bash
python mainGenerator.py
```

Le processus se déroule en deux étapes:
1. **Analyse des données Enron**: Conversion du CSV en JSON structuré, il se limite à 100 000 mails
2. **Génération d'emails fictifs**: Création de 1000 courriels réalistes

## Résultats
Après l'exécution, vous trouverez:
- `emails.json`: Données Enron structurées
- Dossier `mockdata/`:
  - `all_emails.json`: 1000 courriels fictifs générés
  - `index.json`: Métadonnées sur les courriels générés

## Paramètres
Les paramètres sont actuellement codés en dur:
- 1000 courriels générés
- 100 000 emails Enron maximum traités
- Sortie dans le dossier `mockdata`

## Erreurs courantes
- **"Le fichier de données Enron n'est pas disponible"**: Assurez-vous que `emails.csv` est présent dans le répertoire


