---
title: ERP AI
emoji: 🏭
colorFrom: green
colorTo: blue
sdk: streamlit
sdk_version: 1.47.1
app_file: app.py
pinned: false
license: mit
tags:
- erp
- manufacturing
- production
- streamlit
- industrial
- business
- management
---

# ERP Constructo AI Inc. 🏭

Une solution complète de gestion de production industrielle avec 61 postes de travail, intégration TimeTracker temps réel, et interface moderne.

## 🚀 Démo en Direct

Cette application est déployée sur Hugging Face Spaces. Cliquez sur "App" ci-dessus pour l'essayer !

## ✨ Fonctionnalités Principales

### 🏭 **Production & Postes de Travail**
- 61 postes de travail configurés (Soudage, CNC, Assemblage, etc.)
- Gammes de fabrication automatiques
- Analyse de capacité en temps réel
- Routage intelligent des opérations

### 📊 **Gestion de Projets**
- Multi-vues : Dashboard, Kanban, Gantt, Calendrier
- Suivi de progression avec sous-tâches
- Nomenclature (BOM) avec calculs automatiques
- IDs automatiques professionnels

### 🤝 **CRM Intégré**
- Gestion complète des contacts clients
- Historique des interactions
- Suivi commercial avancé

### 👥 **Ressources Humaines**
- Dashboard RH avec métriques
- Gestion des employés et compétences
- Assignations automatiques

### ⏱️ **TimeTracker**
- Synchronisation ERP ↔ TimeTracker
- Calcul automatique des revenus
- Export complet des données

### 📦 **Inventaire**
- Mesures hybrides (Impérial + Métrique)
- Conversion automatique sophistiquée
- Gestion intelligente des stocks

## 🛠️ Utilisation

1. **Lancez l'application** en cliquant sur "App"
2. **Explorez les modules** via le menu latéral
3. **Testez les fonctionnalités** avec les données de démonstration
4. **Naviguez entre les vues** : Dashboard, Kanban, Gantt, etc.

## 📱 Interface

L'application propose plusieurs interfaces spécialisées :

- **Dashboard** : Métriques temps réel avec graphiques interactifs
- **Kanban** : Gestion visuelle des projets par statuts
- **Gantt** : Planning temporel interactif
- **Calendrier** : Vue mensuelle des événements
- **Inventaire** : Gestion complète des stocks

## 💼 Données de Démonstration

L'application inclut des projets industriels réalistes :

- **Châssis Automobile** (AutoTech Corp.) - 35,000$ CAD
- **Structure Industrielle** (BâtiTech Inc.) - 58,000$ CAD
- **Pièce Aéronautique** (AeroSpace Ltd) - 75,000$ CAD

## 🔧 Technologies

- **Streamlit** - Framework web Python
- **Plotly** - Visualisations interactives
- **Pandas** - Manipulation de données
- **SQLite** - Base de données intégrée

## 🏗️ Structure du Projet

```
├── app.py                 # Application principale
├── database_sync.py       # Synchronisation TimeTracker
├── crm.py                # Module CRM
├── employees.py          # Gestion RH
├── postes_travail.py     # Configuration des postes
├── timetracker.py        # Interface temps réel
├── requirements.txt      # Dépendances
└── README.md            # Documentation
```

## 🎯 Cas d'Usage

### Manufacturing PME
- Gestion de production métallurgie
- Suivi des commandes clients
- Planification des ressources

### Sous-Traitance Automobile
- Production de châssis et composants
- Traçabilité complète
- Livraisons en flux tendu

### Aéronautique & Défense
- Pièces haute précision
- Documentation technique
- Certifications qualité

## 🚀 Installation Locale

Si vous souhaitez exécuter l'application localement :

```bash
# Cloner le repository
git clone https://huggingface.co/spaces/your-username/erp-constructo-ai
cd erp-constructo-ai

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

## 📊 Fonctionnalités Avancées

| Module | Description | Statut |
|--------|-------------|--------|
| **Production** | 61 postes industriels | ✅ |
| **TimeTracker** | Suivi temps réel | ✅ |
| **CRM** | Gestion clients | ✅ |
| **RH** | Employés & compétences | ✅ |
| **Inventaire** | Stock & mesures | ✅ |
| **Projets** | Multi-vues avancées | ✅ |

## 🔒 Sécurité

- Données stockées localement
- Pas de transmission externe
- Interface sécurisée
- Logs d'audit intégrés

## 📄 Licence

MIT License - Utilisation libre pour projets commerciaux et personnels.

## 🤝 Contribution

Contributions bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Suggérer des améliorations
- Proposer de nouvelles fonctionnalités

---

**🏭 Solution ERP complète pour l'industrie moderne**

*Développé avec ❤️ pour la communauté industrielle*