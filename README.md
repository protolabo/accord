<br/>
<p align="center">
    <img src="./public/logo.png" height=100>
</p>
<br/>

# Accord

> **Avancement du projet** 👉 https://protolabo.github.io/accord/

Dans des environnements de communication virtuelle omniprésents — qu’ils soient professionnels ou personnels — les barrières physiques qui offraient autrefois un meilleur contrôle de l’attention ont disparu. Beaucoup se retrouvent désormais confrontés à une surcharge de messages, des interruptions incessantes et une gestion inefficace de leur attention.

Le projet **Accord** s’attaque à ces défis en repensant l’utilisabilité et l’accessibilité des systèmes de messagerie modernes. Fonctionnant comme un *wrapper* autour des plateformes existantes, Accord propose une personnalisation avancée pour répondre aux besoins spécifiques de chaque utilisateur, tout en intégrant des mécanismes intuitifs pour une gestion efficace de la disponibilité réelle.

Grâce à des fonctionnalités telles que la **classification contextuelle** des messages et les **statuts intelligents**, Accord vise à optimiser la productivité tout en respectant le temps et l’attention de ses utilisateurs.


## 📋 Fonctionnalités

- 🧠 **Classification intelligente des messages** à l’aide de modèles NLP (comme BERT)
- 📂 **Regroupement contextuel** des courriels :
  - **Actions** : messages nécessitant une réponse ou une décision
  - **Informations** : notifications et messages à faible priorité
  - **Threads** : fils de discussion automatiquement organisés par sujet ou par projet
- 📡 **Détection automatique de la disponibilité** (réunion, concentration, absence)
- 🔄 **Intégration transparente** avec les outils de messagerie existants (Outlook, Gmail...)
- 🧩 **Interface adaptable** aux préférences et au contexte de l'utilisateur

## 🌐 Infrastructure

### Base de données

- [**MongoDB**](https://www.mongodb.com/): Base de données NoSQL utilisée pour le stockage des messages, utilisateurs et métadonnées.

### Composantes IA

- [**BERT**](https://huggingface.co/bert-base-uncased): Modèle de traitement de langage naturel utilisé pour classifier et annoter les courriels.

### API

- [**FastAPI**](https://fastapi.tiangolo.com/): Framework Python facilitant le développement d'API de style REST.

### Application web

- [**Electron**](https://www.electronjs.org/): Environnement populaire pour créer des applications desktop à partir de technologies web.
- [**React**](https://react.dev/): Librairie JavaScript pour créer une interface utilisateur dynamique en SPA (Single Page Application).


# 🗂️ Organisation

Le dépôt est structuré de la manière suivante :

- `\backend`: contient le code source de l'API, les modèles de langage et la logique métier.
- `\frontend`: contient l’application Electron avec React (UI).
- `\docs`: contient le site de documentation du projet.

# 🌟 Contribution

Si vous êtes intéressé à participer au projet, veuillez prendre contact avec [Louis-Edouard LAFONTANT](mailto:louis.edouard.lafontant@umontreal.ca).

## Contributeurs

- Louis [@LOUONE](https://github.com/LOUONE)
- Hervé [@h-mbl](https://github.com/h-mbl)
- Xuan [@lxc3001](https://github.com/lxc3001)
