# README - Frontend Accord

## 📋 Vue d'ensemble

Le frontend d'Accord est une application bureau développée avec React et Electron. Cette architecture permet une interface utilisateur riche tout en offrant les capacités d'une application native.

## 🗂️ Structure du projet

```
/                          
├── backend/               
├── frontend/              
│   ├── package.json       # ⚠️ run dev s'est ici
│   ├── forge.config.js    
│   ├── react-app/        
│   │   ├── package.json  # ⚠️ ne pas utiliser à part pour npm install 

```

## 🚀 Installation

Pour installer et configurer le frontend, suivez ces étapes:

```bash
# 1. Naviguer vers le dossier frontend
cd frontend

# 2. Installer toutes les dépendances (Electron + React)
npm install

# 3. Naviguer vers le dossier frontend/react-app
cd frontend/react-app 

# 2. Installer toutes les dépendances 
npm install 

```

## 📦 Scripts disponibles

Le package.json consolidé offre les scripts suivants:

### Scripts Electron dans frontend/package.json

```bash

# Lancer l'application Electron (sans serveur de développement React)
npm start

# Lancer le développement complet (React + Electron)
npm run dev

# Construire l'application pour la distribution
npm run build

# Créer un paquet pour la distribution
npm run dist

# Créer un paquet pour la distribution (dossier uniquement)
npm run pack
```



## 🔄 Flux de développement

### 📌 Développement 

Pour le développement quotidien, utilisez:

```bash
cd frontend
npm run dev
```

Ce script:
1. Lance le serveur de développement React sur le port 3000
2. Attend que React soit disponible
3. Démarre Electron qui se connecte au serveur React

Vous pourrez voir les changements en temps réel dans l'application Electron.

### Production

Pour construire l'application pour la distribution:

```bash
cd frontend
npm run build
```

Ce script:
1. Construit l'application React avec les optimisations de production
2. Génère les fichiers dans `react-app/build/`
3. Utilise electron-builder pour créer un exécutable

Les fichiers de distribution sont générés dans le dossier `dist/`.

## 🔄 Communication avec le backend

L'application React communique avec le backend FastAPI via HTTP. La configuration du proxy est définie dans `frontend/package.json`:

```json
"proxy": "http://localhost:8000"
```

Cette configuration permet de faire des requêtes vers `/api/...` sans avoir à spécifier l'URL complète du backend.

## ⚠️ Résolution des problèmes courants

### Conflits de versions TypeScript

Si vous rencontrez des erreurs liées à TypeScript:

1. Vérifiez que vous utilisez TypeScript 4.9.5 qui est compatible avec react-scripts
2. Si vous devez utiliser une version plus récente, installez avec `--legacy-peer-deps`

### Erreurs lors de l'installation des dépendances

Si vous rencontrez des erreurs lors de l'installation:

```bash
# Tentez avec l'option legacy-peer-deps
npm install --legacy-peer-deps

# Ou avec force si nécessaire
npm install --force
```

## 📝 Notes importantes

- **Package.json consolidé**: Nous avons regroupé les dépendances Electron et React dans un seul fichier pour simplifier la maintenance
- **TypeScript 4.9.5**: Cette version est utilisée pour assurer la compatibilité avec react-scripts
- **Structure des dossiers**: Maintient la séparation logique entre le code React et Electron
- **Scripts prefixés**: Les scripts React ont été préfixés avec "react-" pour éviter les conflits de noms

## 🏗️ Construction de l'application

Pour construire l'application pour la distribution:

```bash
cd frontend
npm run dist
```

Cela générera:
- Pour Windows: Des installateurs `.exe` et `.msi` dans `dist/`
- Pour macOS: Des fichiers `.dmg` et `.app` dans `dist/`

