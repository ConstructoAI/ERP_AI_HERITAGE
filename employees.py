import json
import os
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional, Any

# === CONSTANTES CONSTRUCTION QUÉBEC - CONSTRUCTO AI INC. ===

# Départements spécifiques construction au Québec
DEPARTEMENTS = [
    "CHANTIER",            # Équipes terrain, gros oeuvre
    "STRUCTURE_BÉTON",     # Coffrage, béton, fondations
    "CHARPENTE_BOIS",      # Ossature bois, toiture
    "FINITION",            # Plâtrerie, peinture, carrelage
    "MÉCANIQUE_BÂTIMENT",  # Plomberie, chauffage, ventilation
    "ÉLECTRICITÉ",         # Installation électrique
    "INGÉNIERIE",          # Conception, plans, calculs
    "QUALITÉ_CONFORMITÉ",  # Inspection, conformité RBQ/CCQ
    "ADMINISTRATION",      # Bureau, comptabilité, RH
    "COMMERCIAL",          # Ventes, soumissions, développement
    "DIRECTION"            # Supervision, contremaîtrise
]

# Statuts adaptés contexte québécois
STATUTS_EMPLOYE = [
    "ACTIF",               # Employé en service
    "CONGÉ",               # Congé personnel/parental
    "FORMATION",           # En formation/perfectionnement
    "ARRÊT_TRAVAIL",       # Maladie/accident de travail
    "INACTIF"              # Temporairement inactif
]

# Niveaux de compétence selon standards québécois
NIVEAUX_COMPETENCE = ["DÉBUTANT", "INTERMÉDIAIRE", "AVANCÉ", "EXPERT"]

# Types de contrat québécois
TYPES_CONTRAT = [
    "CDI",                 # Contrat à durée indéterminée
    "CDD",                 # Contrat à durée déterminée  
    "TEMPORAIRE",          # Travail temporaire/saisonnier
    "STAGE",               # Stagiaire
    "APPRENTISSAGE"        # Programme d'apprentissage
]

# Compétences spécifiques construction au Québec - CONSTRUCTO AI INC.
COMPETENCES_DISPONIBLES = [
    # === CHARPENTERIE ET MENUISERIE ===
    "Charpenterie résidentielle", "Charpenterie commerciale", "Charpenterie institutionnelle",
    "Ossature bois plateforme", "Ossature bois ballon", "Charpente traditionnelle",
    "Installation toiture", "Pose de revêtement", "Lecture de plans construction",
    "Certification CCQ Charpentier", "Escaliers et rampes", "Finition intérieure",
    "Isolation thermique", "Pare-vapeur", "Assemblage ossature",
    "Portes et fenêtres", "Revêtement extérieur", "Terrasses et balcons",
    "Calfeutrage", "Étanchéité", "Menuiserie architecturale",
    
    # === MAÇONNERIE ET BÉTON ===
    "Coffrage de fondations", "Coffrage murs", "Coffrage dalles", "Coulage béton",
    "Finition béton", "Béton décoratif", "Maçonnerie brique", "Maçonnerie bloc",
    "Maçonnerie pierre", "Pierre naturelle", "Crépi et stuc", "Jointoiement",
    "Réparation béton", "Dalle sur sol", "Murs de fondation", "Trottoirs et entrées",
    "Béton estampé", "Lecture de plans structure", "Nivelage et implantation",
    "Armature béton", "Test affaissement béton", "Cure béton",
    
    # === QUALITÉ ET CONFORMITÉ ===
    "Inspection structure", "Conformité RBQ", "Normes CCQ",
    "Code du bâtiment", "Test béton", "Contrôle qualité",
    "Certification matériaux", "Vérification plans", "Inspection fondations",
    "ISO 9001", "Documentation conformité", "Rapports d'inspection",
    "Vérification sécurité", "Audit chantier",
    
    # === CONCEPTION ET INGÉNIERIE ===
    "AutoCAD", "Revit", "SketchUp", "Plans construction",
    "Devis technique", "Calcul structure", "Dessin bâtiment",
    "Code construction Québec", "Normes CSA", "Plans d'exécution",
    "Plans architecturaux", "Mécanique bâtiment", "Électricité bâtiment",
    "Estimation projets", "Analyse sol",
    
    # === GESTION ET COMMERCIAL ===
    "Estimation projets", "ERP/MRP", "Gestion production",
    "Planification atelier", "Ordonnancement", "Approvisionnement",
    "Service client", "Négociation", "Soumission commerciale",
    "Gestion équipe", "Formation employés", "Suivi budget",
    "Analyse coûts", "Amélioration continue",
    
    # === ÉQUIPEMENTS CONSTRUCTION ===
    "Grue à tour", "Chargeuse-pelleteuse", "Bétonnière",
    "Compacteur", "Nacelle élévatrice", "Scie à béton",
    "Marteau-piqueur", "Génératrice chantier", "Pompe à béton",
    
    # === MATÉRIAUX CONSTRUCTION ===
    "Béton", "Bois d'oeuvre", "Acier structural", "Brique",
    "Pierre", "Plâtre", "Isolants", "Bardeaux", "Membrane",
    "Revêtements", "Céramique", "Armature béton",
    
    # === SÉCURITÉ ET RÉGLEMENTATION QUÉBEC ===
    "CNESST", "Cadenassage LOTO", "Espaces clos",
    "Travail en hauteur", "SIMDUT 2015", "Premiers soins",
    "Sécurité atelier", "Prévention accidents", "EPI",
    "Manipulation matières dangereuses", "Protection incendie",
    
    # === LANGUES ET COMMUNICATION ===
    "Français", "Anglais", "Espagnol", "Communication technique",
    "Rédaction rapports", "Présentation client"
]

class GestionnaireEmployes:
    """
    ARCHITECTURE SQLITE UNIFIÉE : Gestionnaire employés Constructo AI Inc.
    Compatible avec ERPDatabase de app.py
    """
    
    def __init__(self, db=None):
        """Initialise le gestionnaire avec base SQLite"""
        # Compatibilité avec app.py - récupérer ERPDatabase depuis session_state
        if db is None:
            if hasattr(st.session_state, 'erp_db'):
                self.db = st.session_state.erp_db
            else:
                st.error("❌ ERPDatabase non disponible - Initialiser depuis app.py")
                self.db = None
        else:
            self.db = db
        
        self.employes = []  # Cache des employés (pour compatibilité interface)
        
        if self.db:
            self._load_employes_from_db()
            
            # Vérifier si données employés existent, sinon initialiser Constructo AI Inc.
            if not self.employes:
                self._initialiser_donnees_employes_constructo_ai()
            
            # Initialiser les compétences construction
            self._init_competences_construction()
    
    def _load_employes_from_db(self):
        """Charge les employés depuis SQLite avec leurs compétences"""
        if not self.db:
            return
            
        try:
            # Récupérer employés avec informations manager
            employes_rows = self.db.execute_query("""
                SELECT e.*, 
                       m.prenom as manager_prenom, 
                       m.nom as manager_nom
                FROM employees e
                LEFT JOIN employees m ON e.manager_id = m.id
                ORDER BY e.id
            """)
            
            self.employes = []
            for emp_row in employes_rows:
                employe = dict(emp_row)
                
                # Récupérer compétences de l'employé
                competences_rows = self.db.execute_query("""
                    SELECT nom_competence, niveau, certifie, date_obtention 
                    FROM employee_competences 
                    WHERE employee_id = ?
                    ORDER BY nom_competence
                """, (employe['id'],))
                
                employe['competences'] = [
                    {
                        'nom': row['nom_competence'],
                        'niveau': row['niveau'],
                        'certifie': bool(row['certifie']),
                        'date_obtention': row['date_obtention']
                    }
                    for row in competences_rows
                ]
                
                # Récupérer projets assignés
                projets_rows = self.db.execute_query("""
                    SELECT project_id FROM project_assignments WHERE employee_id = ?
                """, (employe['id'],))
                
                employe['projets_assignes'] = [row['project_id'] for row in projets_rows]
                
                self.employes.append(employe)
                
        except Exception as e:
            st.error(f"Erreur chargement employés SQLite: {e}")
            self.employes = []

    def _calculer_salaire_construction(self, poste, experience_annees=5):
        """Calcule le salaire selon les standards québécois construction 2024 - Constructo AI Inc."""
        salaires_base_qc = {
            # === MÉTIERS DE LA CONSTRUCTION ===
            "Charpentier-menuisier": 65000,
            "Charpentier général": 62000,
            "Manoeuvre spécialisé": 48000,
            "Manoeuvre général": 45000,
            "Maçon": 68000,
            "Maçon-briqueteur": 65000,
            "Coffreur": 60000,
            "Coffreur-ferrailleur": 62000,
            "Couvreur": 63000,
            "Couvreur-bardeur": 60000,
            "Plombier": 72000,
            "Plombier-chauffagiste": 75000,
            "Électricien construction": 74000,
            "Électricien industriel": 76000,
            "Plâtrier-tireur de joints": 58000,
            "Peintre-finisseur": 54000,
            "Carreleur-mosaïste": 56000,
            "Opérateur machinerie lourde": 68000,
            "Grutier": 70000,
            # === POSTES TECHNIQUES ===
            "Dessinateur-projeteur": 70000,
            "Technologue architecture": 65000,
            "Inspecteur qualité construction": 66000,
            "Arpenteur-géomètre junior": 55000,
            "Estimateur construction": 75000,
            "Chargé de projet construction": 78000,
            "Coordonnateur chantier": 68000,
            "Coordonnateur sécurité CNESST": 62000,
            # === GESTION ET ADMINISTRATION ===
            "Contremaître général": 85000,
            "Surintendant chantier": 90000,
            "Directeur construction": 95000,
            "Adjointe administrative": 47000,
            "Secrétaire de chantier": 42000,
            "Réceptionniste": 38000
        }
        base = salaires_base_qc.get(poste, 47000)
        # Ajustement selon expérience (1.5% par année)
        facteur_exp = 1 + (experience_annees * 0.015)
        return int(base * facteur_exp)

    def _calculer_salaire_avec_experience(self, poste, experience_annees=5):
        """Calcule le salaire avec bonus d'expérience selon standards Constructo AI Inc."""
        # Obtenir le salaire de base selon le poste de construction
        salaire_base = self._calculer_salaire_construction(poste, experience_annees)
        
        # Bonus selon expérience (1.8% par année d'expérience)
        facteur_experience = 1 + (experience_annees * 0.018)
        
        # Bonus selon certifications spécialisées
        bonus_certifications = {
            "RBQ licence": 1.05,  # +5% si licence RBQ
            "CCQ spécialisé": 1.08,  # +8% si spécialisation CCQ
            "CNESST formateur": 1.06  # +6% si formateur sécurité
        }
        
        return int(salaire_base * facteur_experience)

    def _get_competences_par_poste(self, poste):
        """Retourne les compétences typiques selon le poste Constructo AI Inc."""
        competences_map = {
            "Charpentier-menuisier": [
                {'nom': 'Charpenterie résidentielle', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Coffrage béton', 'niveau': 'INTERMÉDIAIRE', 'certifie': False},
                {'nom': 'Lecture de plans construction', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Installation toiture', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'CNESST', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Certification CCQ', 'niveau': 'AVANCÉ', 'certifie': True}
            ],
            "Manoeuvre": [
                {'nom': 'Manutention matériaux', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Outils pneumatiques', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Grue mobile', 'niveau': 'INTERMÉDIAIRE', 'certifie': True},
                {'nom': 'Bétonnière', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'CNESST', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Français', 'niveau': 'AVANCÉ', 'certifie': True}
            ],
            "Maçon": [
                {'nom': 'Maçonnerie brique', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Maçonnerie pierre', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Finition béton', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Crépi et stuc', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'CNESST', 'niveau': 'AVANCÉ', 'certifie': True}
            ],
            "Coffreur": [
                {'nom': 'Coffrage de fondations', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Coffrage béton', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Lecture de plans structure', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'CNESST', 'niveau': 'AVANCÉ', 'certifie': True}
            ],
            "Couvreur": [
                {'nom': 'Installation toiture', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Bardeaux', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Membrane', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'CNESST', 'niveau': 'AVANCÉ', 'certifie': True}
            ],
            "Dessinateur": [
                {'nom': 'AutoCAD', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Revit', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Dessin bâtiment', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Code construction Québec', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Plans d\'exécution', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Français', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Anglais', 'niveau': 'AVANCÉ', 'certifie': True}
            ],
            "Inspecteur qualité": [
                {'nom': 'Inspection structure', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Conformité RBQ', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Code du bâtiment', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Documentation conformité', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'CNESST', 'niveau': 'AVANCÉ', 'certifie': True}
            ],
            "Contremaître/Superviseur": [
                {'nom': 'Gestion équipe', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Planification atelier', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Sécurité atelier', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'CNESST', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Lecture de plans mécaniques', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Français', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Anglais', 'niveau': 'AVANCÉ', 'certifie': True}
            ],
            "Estimateur et intégration ERP": [
                {'nom': 'Estimation projets', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'ERP/MRP', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Analyse coûts', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Soumission commerciale', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Français', 'niveau': 'EXPERT', 'certifie': True}
            ],
            "Développement des affaires": [
                {'nom': 'Service client', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Négociation', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Présentation client', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Français', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Anglais', 'niveau': 'AVANCÉ', 'certifie': True}
            ],
            "Adjointe administrative": [
                {'nom': 'Gestion production', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Communication technique', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Rédaction rapports', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Français', 'niveau': 'EXPERT', 'certifie': True}
            ],
            "Marketing et web": [
                {'nom': 'Communication technique', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Présentation client', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Français', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Anglais', 'niveau': 'AVANCÉ', 'certifie': True}
            ],
            # === NOUVEAUX MÉTIERS CONSTRUCTION QUÉBEC ===
            "Plombier": [
                {'nom': 'Plomberie résidentielle', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Plomberie commerciale', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Chauffage hydronique', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Certification CCQ', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'CNESST', 'niveau': 'AVANCÉ', 'certifie': True}
            ],
            "Électricien construction": [
                {'nom': 'Installation électrique résidentielle', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Installation électrique commerciale', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Code électrique Québec', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Certification CCQ', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'CNESST', 'niveau': 'AVANCÉ', 'certifie': True}
            ],
            "Opérateur machinerie lourde": [
                {'nom': 'Excavatrice', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Chargeuse-pelleteuse', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Grue mobile', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Permis classe 3', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'CNESST', 'niveau': 'AVANCÉ', 'certifie': True}
            ],
            "Peintre-finisseur": [
                {'nom': 'Peinture intérieure', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Peinture extérieure', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Finition décorative', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'CNESST', 'niveau': 'AVANCÉ', 'certifie': True}
            ],
            "Manoeuvre spécialisé": [
                {'nom': 'Manutention matériaux construction', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Outils pneumatiques', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'Montage échafaudage', 'niveau': 'AVANCÉ', 'certifie': True},
                {'nom': 'CNESST', 'niveau': 'EXPERT', 'certifie': True},
                {'nom': 'Français', 'niveau': 'AVANCÉ', 'certifie': True}
            ]
        }
        return competences_map.get(poste, [
            {'nom': 'CNESST', 'niveau': 'AVANCÉ', 'certifie': True},
            {'nom': 'Français', 'niveau': 'AVANCÉ', 'certifie': True}
        ])

    def _initialiser_donnees_employes_constructo_ai(self):
        """Initialise avec les employés FICTIFS de Constructo AI Inc. 2024"""
        if not self.db:
            return
        
        # Simple vérification pour éviter la double initialisation
        if self.db.get_table_count('employees') > 0:
            return
        
        st.info("🏗️ Initialisation des 24 employés FICTIFS Constructo AI Inc. en SQLite...")
        
        # Données des 24 employés FICTIFS de Constructo AI Inc. (2024)
        employes_data = [
            # === CHANTIER ET GROS ŒUVRE (8 employés) ===
            {
                'id': 1, 'prenom': 'Alexandre', 'nom': 'Dubois',
                'email': 'alexandre.dubois@constructo-ai.ca',
                'telephone': '450-555-0101',
                'poste': 'Manoeuvre spécialisé', 'departement': 'CHANTIER',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2020-03-15',
                'salaire': self._calculer_salaire_construction('Manoeuvre spécialisé', 4),
                'manager_id': 23,  # Jean-Pierre Contremaître
                'competences': self._get_competences_par_poste('Manoeuvre spécialisé'),
                'projets_assignes': [], 'charge_travail': 85,
                'notes': 'Spécialiste manutention et montage - Certification CNESST',
                'photo_url': ''
            },
            {
                'id': 2, 'prenom': 'François', 'nom': 'Tremblay',
                'email': 'francois.tremblay@constructo-ai.ca',
                'telephone': '450-555-0102',
                'poste': 'Charpentier-menuisier', 'departement': 'CHARPENTE_BOIS',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2018-06-01',
                'salaire': self._calculer_salaire_construction('Charpentier-menuisier', 6),
                'manager_id': 23,
                'competences': self._get_competences_par_poste('Charpentier-menuisier'),
                'projets_assignes': [], 'charge_travail': 90,
                'notes': 'Charpentier certifié CCQ - Spécialiste ossature bois',
                'photo_url': ''
            },
            {
                'id': 3, 'prenom': 'André', 'nom': 'Johnson',
                'email': 'andre.johnson@constructo-ai.ca',
                'telephone': '450-555-0103',
                'poste': 'Maçon', 'departement': 'STRUCTURE_BÉTON',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2019-09-15',
                'salaire': self._calculer_salaire_construction('Maçon', 5),
                'manager_id': 23,
                'competences': self._get_competences_par_poste('Maçon'),
                'projets_assignes': [], 'charge_travail': 88,
                'notes': 'Maçon spécialisé brique et pierre - Compagnon CCQ',
                'photo_url': ''
            },
            {
                'id': 4, 'prenom': 'Denis', 'nom': 'Bergeron',
                'email': 'denis.bergeron@constructo-ai.ca',
                'telephone': '450-555-0104',
                'poste': 'Dessinateur-projeteur', 'departement': 'INGÉNIERIE',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2015-01-20',
                'salaire': self._calculer_salaire_construction('Dessinateur-projeteur', 9),
                'manager_id': 24,  # Directeur construction
                'competences': self._get_competences_par_poste('Dessinateur'),
                'projets_assignes': [], 'charge_travail': 95,
                'notes': 'Technologue architecture - Expert AutoCAD et Revit',
                'photo_url': ''
            },
            {
                'id': 5, 'prenom': 'Luc', 'nom': 'Côté',
                'email': 'luc.cote@constructo-ai.ca',
                'telephone': '450-555-0105',
                'poste': 'Coffreur', 'departement': 'STRUCTURE_BÉTON',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2017-11-01',
                'salaire': self._calculer_salaire_construction('Coffreur', 7),
                'manager_id': 23,
                'competences': self._get_competences_par_poste('Coffreur'),
                'projets_assignes': [], 'charge_travail': 87,
                'notes': 'Coffreur expérimenté, spécialiste fondations et dalles',
                'photo_url': ''
            },
            {
                'id': 6, 'prenom': 'Daniel', 'nom': 'Roy',
                'email': 'daniel.roy@constructo-ai.ca',
                'telephone': '450-555-0106',
                'poste': 'Manoeuvre général', 'departement': 'CHANTIER',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2021-04-12',
                'salaire': self._calculer_salaire_construction('Manoeuvre général', 3),
                'manager_id': 23,
                'competences': self._get_competences_par_poste('Manoeuvre spécialisé'),
                'projets_assignes': [], 'charge_travail': 82,
                'notes': 'Manoeuvre polyvalent - Spécialiste nettoyage chantier',
                'photo_url': ''
            },
            {
                'id': 7, 'prenom': 'Denis', 'nom': 'Mercier',
                'email': 'denis.mercier@constructo-ai.ca',
                'telephone': '450-555-0107',
                'poste': 'Coffreur-ferrailleur', 'departement': 'STRUCTURE_BÉTON',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2016-08-15',
                'salaire': self._calculer_salaire_construction('Coffreur-ferrailleur', 8),
                'manager_id': 23,
                'competences': self._get_competences_par_poste('Coffreur'),
                'projets_assignes': [], 'charge_travail': 90,
                'notes': 'Expert coffrage complexe et armature béton',
                'photo_url': ''
            },
            {
                'id': 8, 'prenom': 'Maxime', 'nom': 'Lavoie',
                'email': 'maxime.lavoie@constructo-ai.ca',
                'telephone': '450-555-0108',
                'poste': 'Plombier', 'departement': 'MÉCANIQUE_BÂTIMENT',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2019-02-20',
                'salaire': self._calculer_salaire_construction('Plombier', 5),
                'manager_id': 24,
                'competences': self._get_competences_par_poste('Plombier'),
                'projets_assignes': [], 'charge_travail': 89,
                'notes': 'Plombier certifié, spécialiste résidentiel/commercial',
                'photo_url': ''
            },
            {
                'id': 9, 'prenom': 'Nicolas', 'nom': 'Bouchard',
                'email': 'nicolas.bouchard@constructo-ai.ca',
                'telephone': '450-555-0109',
                'poste': 'Opérateur machinerie lourde', 'departement': 'CHANTIER',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2018-10-05',
                'salaire': self._calculer_salaire_construction('Opérateur machinerie lourde', 6),
                'manager_id': 23,
                'competences': self._get_competences_par_poste('Opérateur machinerie lourde'),
                'projets_assignes': [], 'charge_travail': 86,
                'notes': 'Opérateur excavatrice et grue mobile certifié',
                'photo_url': ''
            },
            {
                'id': 10, 'prenom': 'Louis', 'nom': 'Gonzalez',
                'email': 'louis.gonzalez@constructo-ai.ca',
                'telephone': '450-555-0110',
                'poste': 'Manoeuvre général', 'departement': 'CHARPENTE_BOIS',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2020-07-10',
                'salaire': self._calculer_salaire_construction('Journalier', 4),
                'manager_id': 11,
                'competences': self._get_competences_par_poste('Journalier') + [
                    {'nom': 'Espagnol', 'niveau': 'EXPERT', 'certifie': True}
                ],
                'projets_assignes': [], 'charge_travail': 84,
                'notes': 'Trilingue (français/anglais/espagnol)',
                'photo_url': ''
            },
            # === SUPERVISION ===
            {
                'id': 11, 'prenom': 'Pierre', 'nom': 'Lafleur',
                'email': 'pierre.lafleur@constructo-ai.ca',
                'telephone': '450-555-0111',
                'poste': 'Contremaître/Superviseur', 'departement': 'DIRECTION',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2012-05-01',
                'salaire': self._calculer_salaire_construction('Contremaître/Superviseur', 12),
                'manager_id': None,
                'competences': self._get_competences_par_poste('Contremaître/Superviseur'),
                'projets_assignes': [], 'charge_travail': 100,
                'notes': 'Contremaître principal, responsable production - Badge ID: 111',
                'photo_url': ''
            },
            # === SUITE DES EMPLOYÉS ===
            {
                'id': 12, 'prenom': 'William', 'nom': 'Cédric',
                'email': 'william.cedric@constructo-ai.ca',
                'telephone': '450-555-0112',
                'poste': 'Charpentier général', 'departement': 'CHARPENTE_BOIS',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2021-01-15',
                'salaire': self._calculer_salaire_construction('Soudeur', 3),
                'manager_id': 11,
                'competences': self._get_competences_par_poste('Soudeur'),
                'projets_assignes': [], 'charge_travail': 86,
                'notes': 'Soudeur junior en formation avancée',
                'photo_url': ''
            },
            {
                'id': 13, 'prenom': 'Martin', 'nom': 'Leblanc',
                'email': 'martin.leblanc@constructo-ai.ca',
                'telephone': '450-555-0113',
                'poste': 'Manoeuvre général', 'departement': 'CHARPENTE_BOIS',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2019-05-20',
                'salaire': self._calculer_salaire_construction('Journalier', 5),
                'manager_id': 11,
                'competences': self._get_competences_par_poste('Journalier'),
                'projets_assignes': [], 'charge_travail': 88,
                'notes': 'Journalier expérimenté, polyvalent',
                'photo_url': ''
            },
            {
                'id': 14, 'prenom': 'Roxanne', 'nom': 'Bertrand',
                'email': 'roxanne.bertrand@constructo-ai.ca',
                'telephone': '450-555-0114',
                'poste': 'Inspecteur qualité construction', 'departement': 'QUALITÉ_CONFORMITÉ',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2017-09-01',
                'salaire': self._calculer_salaire_construction('Qualité/Réception', 7),
                'manager_id': 11,
                'competences': self._get_competences_par_poste('Qualité/Réception'),
                'projets_assignes': [], 'charge_travail': 85,
                'notes': 'Responsable qualité et réception matériaux',
                'photo_url': ''
            },
            {
                'id': 15, 'prenom': 'Samuel', 'nom': 'Turcotte',
                'email': 'samuel.turcotte@constructo-ai.ca',
                'telephone': '450-555-0115',
                'poste': 'Manoeuvre général', 'departement': 'CHARPENTE_BOIS',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2022-03-10',
                'salaire': self._calculer_salaire_construction('Journalier', 2),
                'manager_id': 11,
                'competences': self._get_competences_par_poste('Journalier'),
                'projets_assignes': [], 'charge_travail': 80,
                'notes': 'Journalier récent, apprentissage rapide',
                'photo_url': ''
            },
            {
                'id': 16, 'prenom': 'Éric', 'nom': 'Brisebois',
                'email': 'eric.brisebois@constructo-ai.ca',
                'telephone': '450-555-0116',
                'poste': 'Charpentier général', 'departement': 'CHARPENTE_BOIS',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2016-04-15',
                'salaire': self._calculer_salaire_construction('Soudeur', 8),
                'manager_id': 11,
                'competences': self._get_competences_par_poste('Soudeur'),
                'projets_assignes': [], 'charge_travail': 91,
                'notes': 'Soudeur senior, mentor pour juniors',
                'photo_url': ''
            },
            # === COMMERCIAL ET ESTIMATION ===
            {
                'id': 17, 'prenom': 'Jovick', 'nom': 'Desrochers',
                'email': 'jovick.desrochers@constructo-ai.ca',
                'telephone': '450-555-0117',
                'poste': 'Développement des affaires', 'departement': 'COMMERCIAL',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2014-06-01',
                'salaire': self._calculer_salaire_construction('Développement des affaires', 10),
                'manager_id': None,
                'competences': self._get_competences_par_poste('Développement des affaires'),
                'projets_assignes': [], 'charge_travail': 95,
                'notes': 'Développement commercial et relations clients',
                'photo_url': ''
            },
            {
                'id': 18, 'prenom': 'Sylvain', 'nom': 'Leclair',
                'email': 'sylvain.leclair@constructo-ai.ca',
                'telephone': '450-555-0118',
                'poste': 'Estimateur et intégration ERP', 'departement': 'COMMERCIAL',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2013-09-15',
                'salaire': self._calculer_salaire_construction('Estimateur et intégration ERP', 11),
                'manager_id': None,
                'competences': self._get_competences_par_poste('Estimateur et intégration ERP'),
                'projets_assignes': [], 'charge_travail': 98,
                'notes': 'Expert estimation et système ERP',
                'photo_url': ''
            },
            # === ADMINISTRATION ===
            {
                'id': 19, 'prenom': 'Myriam', 'nom': 'Giroux',
                'email': 'myriam.giroux@constructo-ai.ca',
                'telephone': '450-555-0119',
                'poste': 'Adjointe administrative', 'departement': 'ADMINISTRATION',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2018-02-01',
                'salaire': self._calculer_salaire_construction('Adjointe administrative', 6),
                'manager_id': None,
                'competences': self._get_competences_par_poste('Adjointe administrative'),
                'projets_assignes': [], 'charge_travail': 85,
                'notes': 'Gestion administrative et coordination',
                'photo_url': ''
            },
            {
                'id': 20, 'prenom': 'Cindy', 'nom': 'Julien',
                'email': 'cindy.julien@constructo-ai.ca',
                'telephone': '450-555-0120',
                'poste': 'Marketing et web', 'departement': 'ADMINISTRATION',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2020-11-10',
                'salaire': self._calculer_salaire_construction('Marketing et web', 4),
                'manager_id': None,
                'competences': self._get_competences_par_poste('Marketing et web'),
                'projets_assignes': [], 'charge_travail': 80,
                'notes': 'Responsable marketing digital et web',
                'photo_url': ''
            },
            {
                'id': 21, 'prenom': 'Jean-François', 'nom': 'Morin',
                'email': 'jf.morin@constructo-ai.ca',
                'telephone': '450-555-0121',
                'poste': 'Manoeuvre général', 'departement': 'CHARPENTE_BOIS',
                'statut': 'ACTIF', 'type_contrat': 'CDI',
                'date_embauche': '2023-01-10',
                'salaire': self._calculer_salaire_construction('Journalier', 1),
                'manager_id': 11,
                'competences': self._get_competences_par_poste('Journalier'),
                'projets_assignes': [], 'charge_travail': 75,
                'notes': 'Nouvel employé en formation',
                'photo_url': ''
            }
        ]
        
        # Insérer chaque employé en SQLite
        for emp_data in employes_data:
            emp_id = self.ajouter_employe_sql(emp_data)
            if emp_id:
                print(f"✅ Employé {emp_data['prenom']} {emp_data['nom']} initialisé (ID: {emp_id})")
        
        # Recharger depuis SQLite
        self._load_employes_from_db()
        st.success(f"🎉 {len(employes_data)} employés FICTIFS Constructo AI Inc. initialisés en SQLite !")
    
    def forcer_migration_constructo_ai(self):
        """Force la migration vers les employés Constructo AI Inc."""
        if not self.db:
            return False
            
        try:
            st.info("🔄 Suppression des anciennes données...")
            
            # Supprimer toutes les données existantes
            self.db.execute_query("DELETE FROM project_assignments WHERE employee_id IN (SELECT id FROM employees)")
            self.db.execute_query("DELETE FROM employee_competences WHERE employee_id IN (SELECT id FROM employees)")
            self.db.execute_query("DELETE FROM employees")
            
            st.info("🏗️ Insertion des nouveaux employés Constructo AI Inc...")
            
            # Réinitialiser avec les nouvelles données
            self._initialiser_donnees_employes_constructo_ai()
            
            # Recharger le cache
            self._load_employes_from_db()
            
            st.success(f"✅ Migration terminée ! {len(self.employes)} employés Constructo AI Inc. chargés.")
            return True
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la migration : {e}")
            return False

    # --- Méthodes CRUD SQLite ---
    
    def ajouter_employe_sql(self, data_employe):
        """Ajoute un nouvel employé en SQLite avec ses compétences"""
        if not self.db:
            return None
            
        try:
            # Insérer employé principal
            query_emp = '''
                INSERT INTO employees 
                (id, prenom, nom, email, telephone, poste, departement, statut, 
                 type_contrat, date_embauche, salaire, manager_id, charge_travail, 
                 notes, photo_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            emp_id = self.db.execute_insert(query_emp, (
                data_employe.get('id'),
                data_employe['prenom'],
                data_employe['nom'],
                data_employe.get('email'),
                data_employe.get('telephone'),
                data_employe.get('poste'),
                data_employe.get('departement'),
                data_employe.get('statut', 'ACTIF'),
                data_employe.get('type_contrat', 'CDI'),
                data_employe.get('date_embauche'),
                data_employe.get('salaire'),
                data_employe.get('manager_id'),
                data_employe.get('charge_travail', 80),
                data_employe.get('notes'),
                data_employe.get('photo_url')
            ))
            
            # Insérer compétences
            competences = data_employe.get('competences', [])
            for comp in competences:
                self.db.execute_insert('''
                    INSERT INTO employee_competences 
                    (employee_id, nom_competence, niveau, certifie, date_obtention)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    emp_id,
                    comp.get('nom'),
                    comp.get('niveau'),
                    comp.get('certifie', False),
                    comp.get('date_obtention')
                ))
            
            # Insérer assignations projets
            projets_assignes = data_employe.get('projets_assignes', [])
            for proj_id in projets_assignes:
                self.db.execute_insert('''
                    INSERT OR IGNORE INTO project_assignments 
                    (project_id, employee_id, role_projet)
                    VALUES (?, ?, ?)
                ''', (proj_id, emp_id, 'Membre équipe'))
            
            return emp_id
            
        except Exception as e:
            st.error(f"Erreur ajout employé SQLite: {e}")
            return None

    def ajouter_employe(self, data_employe):
        """Interface de compatibilité pour ajouter employé"""
        emp_id = self.ajouter_employe_sql(data_employe)
        if emp_id:
            self._load_employes_from_db()  # Recharger cache
        return emp_id

    def modifier_employe(self, id_employe, data_employe):
        """Modifie un employé existant en SQLite"""
        if not self.db:
            return False
            
        try:
            # Mettre à jour employé principal
            update_fields = []
            params = []
            
            fields_map = {
                'prenom': 'prenom', 'nom': 'nom', 'email': 'email',
                'telephone': 'telephone', 'poste': 'poste', 'departement': 'departement',
                'statut': 'statut', 'type_contrat': 'type_contrat',
                'date_embauche': 'date_embauche', 'salaire': 'salaire',
                'manager_id': 'manager_id', 'charge_travail': 'charge_travail',
                'notes': 'notes', 'photo_url': 'photo_url'
            }
            
            for field, col in fields_map.items():
                if field in data_employe:
                    update_fields.append(f"{col} = ?")
                    params.append(data_employe[field])
            
            if update_fields:
                query = f"UPDATE employees SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
                params.append(id_employe)
                self.db.execute_update(query, tuple(params))
            
            # Mettre à jour compétences si fournies
            if 'competences' in data_employe:
                # Supprimer anciennes compétences
                self.db.execute_update("DELETE FROM employee_competences WHERE employee_id = ?", (id_employe,))
                
                # Ajouter nouvelles compétences
                for comp in data_employe['competences']:
                    self.db.execute_insert('''
                        INSERT INTO employee_competences 
                        (employee_id, nom_competence, niveau, certifie, date_obtention)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        id_employe,
                        comp.get('nom'),
                        comp.get('niveau'),
                        comp.get('certifie', False),
                        comp.get('date_obtention')
                    ))
            
            # Mettre à jour assignations projets si fournies
            if 'projets_assignes' in data_employe:
                # Supprimer anciennes assignations
                self.db.execute_update("DELETE FROM project_assignments WHERE employee_id = ?", (id_employe,))
                
                # Ajouter nouvelles assignations
                for proj_id in data_employe['projets_assignes']:
                    self.db.execute_insert('''
                        INSERT OR IGNORE INTO project_assignments 
                        (project_id, employee_id, role_projet)
                        VALUES (?, ?, ?)
                    ''', (proj_id, id_employe, 'Membre équipe'))
            
            self._load_employes_from_db()  # Recharger cache
            return True
            
        except Exception as e:
            st.error(f"Erreur modification employé SQLite: {e}")
            return False

    def supprimer_employe(self, id_employe):
        """Supprime un employé et ses données associées"""
        if not self.db:
            return False
            
        try:
            # Supprimer les données associées d'abord (contraintes FK)
            self.db.execute_update("DELETE FROM employee_competences WHERE employee_id = ?", (id_employe,))
            self.db.execute_update("DELETE FROM project_assignments WHERE employee_id = ?", (id_employe,))
            self.db.execute_update("DELETE FROM time_entries WHERE employee_id = ?", (id_employe,))
            
            # Mettre à jour les références manager_id
            self.db.execute_update("UPDATE employees SET manager_id = NULL WHERE manager_id = ?", (id_employe,))
            
            # Supprimer l'employé
            self.db.execute_update("DELETE FROM employees WHERE id = ?", (id_employe,))
            
            self._load_employes_from_db()  # Recharger cache
            return True
            
        except Exception as e:
            st.error(f"Erreur suppression employé SQLite: {e}")
            return False

    def get_employe_by_id(self, id_employe):
        """Récupère un employé par ID (depuis cache)"""
        return next((emp for emp in self.employes if emp.get('id') == id_employe), None)

    def get_employes_by_departement(self, departement):
        """Récupère employés par département"""
        return [emp for emp in self.employes if emp.get('departement') == departement]

    def get_employes_by_projet(self, projet_id):
        """Récupère employés assignés à un projet"""
        return [emp for emp in self.employes if projet_id in emp.get('projets_assignes', [])]

    def get_managers(self):
        """Récupère les managers (employés sans manager ou poste de direction)"""
        return [emp for emp in self.employes if not emp.get('manager_id') or emp.get('departement') in ['DIRECTION', 'COMMERCIAL', 'ADMINISTRATION']]

    def get_subordinates(self, manager_id):
        """Récupère les subordonnés d'un manager"""
        return [emp for emp in self.employes if emp.get('manager_id') == manager_id]

    # --- Méthodes d'analyse construction québécoise ---
    
    def get_statistiques_employes(self):
        """Statistiques adaptées pour construction québécoise"""
        if not self.employes:
            return {}
        
        stats = {
            'total': len(self.employes),
            'par_departement': {},
            'par_statut': {},
            'par_type_contrat': {},
            'salaire_moyen': 0,
            'charge_moyenne': 0,
            'competences_populaires': {},
            'certifications_cnesst': 0,
            'langues_parlees': {},
            'anciennete_moyenne': 0,
            'soudeurs_certifies': 0,
            'bilingues': 0,
            'expertise_metallurgie': {}
        }
        
        total_salaire = 0
        total_charge = 0
        total_anciennete = 0
        toutes_competences = {}
        langues = {}
        expertise_metallurgie = {
            'soudage': 0,
            'usinage': 0,
            'qualite': 0,
            'conception': 0,
            'gestion': 0
        }
        
        for emp in self.employes:
            # Départements
            dept = emp.get('departement', 'N/A')
            stats['par_departement'][dept] = stats['par_departement'].get(dept, 0) + 1
            
            # Statuts
            statut = emp.get('statut', 'N/A')
            stats['par_statut'][statut] = stats['par_statut'].get(statut, 0) + 1
            
            # Types de contrat
            contrat = emp.get('type_contrat', 'N/A')
            stats['par_type_contrat'][contrat] = stats['par_type_contrat'].get(contrat, 0) + 1
            
            # Salaires en CAD
            if emp.get('salaire'):
                total_salaire += emp['salaire']
            
            # Charge de travail
            if emp.get('charge_travail'):
                total_charge += emp['charge_travail']
            
            # Ancienneté
            if emp.get('date_embauche'):
                try:
                    date_emb = datetime.strptime(emp['date_embauche'], '%Y-%m-%d')
                    anciennete = (datetime.now() - date_emb).days / 365.25
                    total_anciennete += anciennete
                except:
                    pass
            
            # Analyse des compétences construction
            competences_emp = emp.get('competences', [])
            has_francais = False
            has_anglais = False
            has_soudage = False
            has_cnesst = False
            
            for comp in competences_emp:
                nom_comp = comp.get('nom')
                if nom_comp:
                    toutes_competences[nom_comp] = toutes_competences.get(nom_comp, 0) + 1
                    
                    # Vérifications spécifiques construction
                    if 'CNESST' in nom_comp and comp.get('certifie'):
                        has_cnesst = True
                    if any(mot in nom_comp for mot in ['Soudage', 'MIG', 'TIG']):
                        has_soudage = True
                        expertise_metallurgie['soudage'] += 1
                    if any(mot in nom_comp for mot in ['Découpe', 'Pliage', 'Usinage', 'CNC']):
                        expertise_metallurgie['usinage'] += 1
                    if any(mot in nom_comp for mot in ['Contrôle', 'Qualité', 'Inspection']):
                        expertise_metallurgie['qualite'] += 1
                    if any(mot in nom_comp for mot in ['AutoCAD', 'SolidWorks', 'Dessin']):
                        expertise_metallurgie['conception'] += 1
                    if any(mot in nom_comp for mot in ['Gestion', 'Planification', 'Estimation']):
                        expertise_metallurgie['gestion'] += 1
                    if nom_comp == 'Français':
                        has_francais = True
                    if nom_comp == 'Anglais':
                        has_anglais = True
                    if nom_comp in ['Français', 'Anglais', 'Espagnol']:
                        langues[nom_comp] = langues.get(nom_comp, 0) + 1
            
            # Compteurs spéciaux
            if has_cnesst:
                stats['certifications_cnesst'] += 1
            if has_soudage:
                stats['soudeurs_certifies'] += 1
            if has_francais and has_anglais:
                stats['bilingues'] += 1
        
        # Calculs des moyennes
        if self.employes:
            stats['salaire_moyen'] = total_salaire / len(self.employes)
            stats['charge_moyenne'] = total_charge / len(self.employes)
            stats['anciennete_moyenne'] = total_anciennete / len(self.employes)
        
        # Top 10 compétences
        stats['competences_populaires'] = dict(
            sorted(toutes_competences.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        # Langues et expertise
        stats['langues_parlees'] = langues
        stats['expertise_metallurgie'] = expertise_metallurgie
        
        return stats

    def generer_rapport_rh_metallurgie(self):
        """Génère un rapport RH spécifique construction Constructo AI Inc."""
        stats = self.get_statistiques_employes()
        
        rapport = {
            'date_rapport': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'entreprise': 'Constructo AI Inc. - Construction Québécoise',
            'localisation': 'Québec, Canada',
            'effectif_total': stats['total'],
            'repartition_departements': stats['par_departement'],
            'salaire_moyen_cad': f"{stats['salaire_moyen']:,.0f}$ CAD",
            'anciennete_moyenne': f"{stats['anciennete_moyenne']:.1f} années",
            'taux_certification_cnesst': f"{(stats['certifications_cnesst']/stats['total']*100):.1f}%",
            'soudeurs_certifies': stats['soudeurs_certifies'],
            'employes_bilingues': stats['bilingues'],
            'expertise_metallurgie': stats['expertise_metallurgie'],
            'competences_critiques': {
                'soudage': len([e for e in self.employes if any('Soudage' in c.get('nom', '') for c in e.get('competences', []))]),
                'lecture_plans': len([e for e in self.employes if any('plans' in c.get('nom', '').lower() for c in e.get('competences', []))]),
                'cnesst': stats['certifications_cnesst'],
                'pont_roulant': len([e for e in self.employes if any('Pont roulant' in c.get('nom', '') for c in e.get('competences', []))]),
                'cnc': len([e for e in self.employes if any('CNC' in c.get('nom', '') for c in e.get('competences', []))])
            },
            'recommandations': [
                "Maintenir programme formation CNESST continue",
                "Développer expertise soudage TIG/aluminium", 
                "Renforcer compétences CNC pour usinage",
                "Formation pont roulant pour nouveaux employés"
            ]
        }
        
        return rapport

    # Méthodes de compatibilité (legacy)
    def charger_donnees_employes(self):
        """Méthode de compatibilité - charge depuis SQLite maintenant"""
        self._load_employes_from_db()
    
    def sauvegarder_donnees_employes(self):
        """Méthode de compatibilité - sauvegarde automatique SQLite"""
        pass  # Sauvegarde automatique en SQLite

# --- Fonctions d'affichage Streamlit adaptées SQLite (MISES À JOUR) ---

def render_employes_liste_tab(emp_manager, projet_manager):
    """Interface liste employés - Compatible SQLite Unifié"""
    st.subheader("👥 Employés Constructo AI Inc. - Construction (SQLite)")
    
    col_create, col_search = st.columns([1, 2])
    with col_create:
        if st.button("➕ Nouvel Employé", key="emp_create_btn", use_container_width=True):
            st.session_state.emp_action = "create_employe"
            st.session_state.emp_selected_id = None
    
    with col_search:
        search_term = st.text_input("🔍 Rechercher un employé...", key="emp_search")
    
    # Filtres adaptés construction
    with st.expander("🔍 Filtres avancés", expanded=False):
        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            filtre_dept = st.multiselect(
                "Département:", 
                ['Tous'] + DEPARTEMENTS, 
                default=['Tous']
            )
        with fcol2:
            filtre_statut = st.multiselect("Statut:", ['Tous'] + STATUTS_EMPLOYE, default=['Tous'])
        with fcol3:
            filtre_contrat = st.multiselect("Type contrat:", ['Tous'] + TYPES_CONTRAT, default=['Tous'])
    
    # Filtrage des employés
    employes_filtres = emp_manager.employes
    
    if search_term:
        term = search_term.lower()
        employes_filtres = [
            emp for emp in employes_filtres if
            term in emp.get('prenom', '').lower() or
            term in emp.get('nom', '').lower() or
            term in emp.get('email', '').lower() or
            term in emp.get('poste', '').lower()
        ]
    
    if 'Tous' not in filtre_dept and filtre_dept:
        employes_filtres = [emp for emp in employes_filtres if emp.get('departement') in filtre_dept]
    
    if 'Tous' not in filtre_statut and filtre_statut:
        employes_filtres = [emp for emp in employes_filtres if emp.get('statut') in filtre_statut]
    
    if 'Tous' not in filtre_contrat and filtre_contrat:
        employes_filtres = [emp for emp in employes_filtres if emp.get('type_contrat') in filtre_contrat]
    
    if employes_filtres:
        st.success(f"📊 {len(employes_filtres)} employé(s) trouvé(s) en base SQLite")
        
        # Affichage tableau adapté
        employes_data_display = []
        for emp in employes_filtres:
            manager = emp_manager.get_employe_by_id(emp.get('manager_id')) if emp.get('manager_id') else None
            manager_nom = f"{manager.get('prenom', '')} {manager.get('nom', '')}" if manager else "Autonome"
            
            # Projets assignés
            nb_projets = len(emp.get('projets_assignes', []))
            
            employes_data_display.append({
                "🆔": emp.get('id'),
                "👤 Nom": f"{emp.get('prenom', '')} {emp.get('nom', '')}",
                "💼 Poste": emp.get('poste', ''),
                "🏭 Département": emp.get('departement', ''),
                "📊 Statut": emp.get('statut', ''),
                "💰 Salaire CAD": f"{emp.get('salaire', 0):,}$",
                "👔 Manager": manager_nom,
                "📈 Charge": f"{emp.get('charge_travail', 0)}%",
                "🚀 Projets": nb_projets,
                "📧 Email": emp.get('email', '')
            })
        
        st.dataframe(pd.DataFrame(employes_data_display), use_container_width=True)
        
        # Actions sur employé sélectionné
        st.markdown("---")
        st.markdown("### 🔧 Actions sur un employé")
        selected_emp_id = st.selectbox(
            "Sélectionner un employé:",
            options=[emp['id'] for emp in employes_filtres],
            format_func=lambda eid: next((f"#{eid} - {emp.get('prenom', '')} {emp.get('nom', '')}" for emp in employes_filtres if emp.get('id') == eid), ''),
            key="emp_action_select"
        )
        
        if selected_emp_id:
            col_act1, col_act2, col_act3 = st.columns(3)
            with col_act1:
                if st.button("👁️ Voir Profil", key=f"emp_view_{selected_emp_id}", use_container_width=True):
                    st.session_state.emp_action = "view_employe_details"
                    st.session_state.emp_selected_id = selected_emp_id
            with col_act2:
                if st.button("✏️ Modifier", key=f"emp_edit_{selected_emp_id}", use_container_width=True):
                    st.session_state.emp_action = "edit_employe"
                    st.session_state.emp_selected_id = selected_emp_id
            with col_act3:
                if st.button("🗑️ Supprimer", key=f"emp_delete_{selected_emp_id}", use_container_width=True):
                    st.session_state.emp_confirm_delete_id = selected_emp_id
    else:
        st.info("Aucun employé correspondant aux filtres.")
    
    # Confirmation de suppression
    if st.session_state.get('emp_confirm_delete_id'):
        emp_to_delete = emp_manager.get_employe_by_id(st.session_state.emp_confirm_delete_id)
        if emp_to_delete:
            st.warning(f"⚠️ Supprimer {emp_to_delete.get('prenom')} {emp_to_delete.get('nom')} de la base SQLite ? Action irréversible.")
            col_del1, col_del2 = st.columns(2)
            if col_del1.button("Oui, supprimer SQLite", type="primary", key="emp_confirm_delete_final"):
                if emp_manager.supprimer_employe(st.session_state.emp_confirm_delete_id):
                    st.success("✅ Employé supprimé de SQLite.")
                    del st.session_state.emp_confirm_delete_id
                    st.rerun()
                else:
                    st.error("❌ Erreur suppression SQLite.")
            if col_del2.button("Annuler", key="emp_cancel_delete_final"):
                del st.session_state.emp_confirm_delete_id
                st.rerun()

def render_employes_dashboard_tab(emp_manager, projet_manager):
    """Dashboard RH - Compatible SQLite avec métriques construction"""
    st.subheader("📊 Dashboard RH")
    
    stats = emp_manager.get_statistiques_employes()
    if not stats:
        st.info("Aucune donnée d'employé disponible en SQLite.")
        return
    
    # Métriques principales adaptées Québec
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Total Employés", stats['total'])
    with col2:
        st.metric("💰 Salaire Moyen", f"{stats['salaire_moyen']:,.0f}$ CAD")
    with col3:
        st.metric("🏗️ Certifiés CNESST", stats.get('certifications_cnesst', 0))
    with col4:
        st.metric("🔧 Soudeurs", stats.get('soudeurs_certifies', 0))
    
    # Métriques secondaires construction
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("📊 Charge Moyenne", f"{stats['charge_moyenne']:.1f}%")
    with col6:
        st.metric("📅 Ancienneté Moy.", f"{stats.get('anciennete_moyenne', 0):.1f} ans")
    with col7:
        st.metric("🌍 Bilingues", stats.get('bilingues', 0))
    with col8:
        employes_surcharges = len([emp for emp in emp_manager.employes if emp.get('charge_travail', 0) > 90])
        st.metric("⚠️ Surchargés", employes_surcharges)
    
    # Graphiques adaptés construction
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        if stats['par_departement']:
            # Couleurs spécifiques construction Constructo AI Inc.
            colors_dept = {
                'PRODUCTION': '#ff6b35',     # Orange production
                'STRUCTURE': '#004e89',       # Bleu foncé structure
                'INGÉNIERIE': '#9b59b6',     # Violet ingénierie
                'QUALITÉ': '#2ecc71',        # Vert qualité
                'COMMERCIAL': '#f39c12',     # Orange commercial
                'ADMINISTRATION': '#95a5a6', # Gris administration
                'DIRECTION': '#e74c3c'       # Rouge direction
            }
            
            fig_dept = px.pie(
                values=list(stats['par_departement'].values()),
                names=list(stats['par_departement'].keys()),
                title="🏭 Répartition par Département (SQLite)",
                color=list(stats['par_departement'].keys()),
                color_discrete_map=colors_dept
            )
            fig_dept.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='var(--text-color)'),
                title_x=0.5
            )
            st.plotly_chart(fig_dept, use_container_width=True)
    
    with col_g2:
        if stats['par_statut']:
            colors_statut = {
                'ACTIF': '#2ecc71',
                'CONGÉ': '#f39c12', 
                'FORMATION': '#3498db',
                'ARRÊT_TRAVAIL': '#e74c3c',
                'INACTIF': '#95a5a6'
            }
            fig_statut = px.bar(
                x=list(stats['par_statut'].keys()),
                y=list(stats['par_statut'].values()),
                title="📈 Statut des Employés (SQLite)",
                color=list(stats['par_statut'].keys()),
                color_discrete_map=colors_statut
            )
            fig_statut.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='var(--text-color)'),
                showlegend=False,
                title_x=0.5
            )
            st.plotly_chart(fig_statut, use_container_width=True)
    
    # Expertise construction spécifique
    if stats.get('expertise_metallurgie'):
        st.markdown("---")
        st.markdown("##### 🏗️ Expertise Construction Constructo AI Inc.")
        
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            expertise = stats['expertise_metallurgie']
            fig_expertise = px.bar(
                x=list(expertise.keys()),
                y=list(expertise.values()),
                title="🏗️ Répartition Expertise Construction",
                color=list(expertise.keys()),
                color_discrete_map={
                    'soudage': '#ff6b35',
                    'usinage': '#004e89', 
                    'qualite': '#2ecc71',
                    'conception': '#9b59b6',
                    'gestion': '#f39c12'
                }
            )
            fig_expertise.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='var(--text-color)'),
                showlegend=False,
                title_x=0.5
            )
            st.plotly_chart(fig_expertise, use_container_width=True)
        
        with col_exp2:
            if stats['competences_populaires']:
                fig_comp = px.bar(
                    x=list(stats['competences_populaires'].values()),
                    y=list(stats['competences_populaires'].keys()),
                    orientation='h',
                    title="🎯 Top Compétences Constructo AI Inc."
                )
                fig_comp.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='var(--text-color)'),
                    title_x=0.5
                )
                st.plotly_chart(fig_comp, use_container_width=True)
    
    # Rapport construction Constructo AI Inc.
    st.markdown("---")
    if st.button("📋 Générer Rapport RH Construction Constructo AI Inc. (SQLite)", use_container_width=True):
        rapport = emp_manager.generer_rapport_rh_metallurgie()
        
        st.markdown("### 📊 Rapport RH - Constructo AI Inc. Construction (SQLite)")
        st.markdown(f"**Date:** {rapport['date_rapport']}")
        st.markdown(f"**Entreprise:** {rapport['entreprise']}")
        st.markdown(f"**Localisation:** {rapport['localisation']}")
        
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.markdown(f"**Effectif Total:** {rapport['effectif_total']}")
            st.markdown(f"**Salaire Moyen:** {rapport['salaire_moyen_cad']}")
        with col_r2:
            st.markdown(f"**Ancienneté Moyenne:** {rapport['anciennete_moyenne']}")
            st.markdown(f"**Taux CNESST:** {rapport['taux_certification_cnesst']}")
        with col_r3:
            st.markdown(f"**Soudeurs Certifiés:** {rapport['soudeurs_certifies']}")
            st.markdown(f"**Employés Bilingues:** {rapport['employes_bilingues']}")
        
        # Compétences critiques
        st.markdown("##### 🎯 Compétences Critiques")
        crit_col1, crit_col2 = st.columns(2)
        with crit_col1:
            for comp, nb in rapport['competences_critiques'].items():
                st.metric(comp.replace('_', ' ').title(), nb)
        
        with crit_col2:
            st.markdown("**Recommandations:**")
            for rec in rapport['recommandations']:
                st.markdown(f"• {rec}")

def render_employe_form(emp_manager, employe_data=None):
    """Formulaire employé - Compatible SQLite Unifié avec CORRECTION DU BUG"""
    form_title = "➕ Ajouter un Nouvel Employé Constructo AI Inc. (SQLite)" if employe_data is None else f"✏️ Modifier {employe_data.get('prenom')} {employe_data.get('nom')} (SQLite)"
    
    with st.expander(form_title, expanded=True):
        # GESTION DES COMPÉTENCES AVANT LE FORMULAIRE
        st.markdown("##### 🎯 Gestion des Compétences Construction")
        
        # Initialiser les compétences en session
        if 'competences_form' not in st.session_state:
            st.session_state.competences_form = employe_data.get('competences', []) if employe_data else []
        
        # Interface d'ajout de compétences
        col_comp1, col_comp2, col_comp3, col_comp4 = st.columns([3, 2, 1, 1])
        with col_comp1:
            nouvelle_comp = st.selectbox("Ajouter compétence:", [""] + COMPETENCES_DISPONIBLES, key="new_comp_select")
        with col_comp2:
            niveau_comp = st.selectbox("Niveau:", NIVEAUX_COMPETENCE, key="new_comp_level")
        with col_comp3:
            certifie_comp = st.checkbox("Certifié", key="new_comp_certified")
        with col_comp4:
            if st.button("➕ Ajouter", key="add_comp_btn"):
                if nouvelle_comp:
                    existing = next((comp for comp in st.session_state.competences_form if comp['nom'] == nouvelle_comp), None)
                    if not existing:
                        st.session_state.competences_form.append({
                            'nom': nouvelle_comp,
                            'niveau': niveau_comp,
                            'certifie': certifie_comp
                        })
                        st.rerun()
                    else:
                        st.warning(f"La compétence '{nouvelle_comp}' existe déjà.")
        
        # Afficher les compétences actuelles
        if st.session_state.competences_form:
            st.markdown("**Compétences actuelles:**")
            for i, comp in enumerate(st.session_state.competences_form):
                col_c1, col_c2, col_c3, col_c4 = st.columns([3, 2, 1, 1])
                with col_c1:
                    st.text(comp['nom'])
                with col_c2:
                    st.text(comp['niveau'])
                with col_c3:
                    st.text("✅" if comp['certifie'] else "❌")
                with col_c4:
                    if st.button("🗑️", key=f"del_comp_{i}"):
                        st.session_state.competences_form.pop(i)
                        st.rerun()
        
        st.markdown("---")
        
        # FORMULAIRE PRINCIPAL
        with st.form("emp_form", clear_on_submit=False):
            # Informations personnelles
            st.markdown("##### 👤 Informations Personnelles")
            col1, col2 = st.columns(2)
            
            with col1:
                prenom = st.text_input("Prénom *", value=employe_data.get('prenom', '') if employe_data else "")
                email = st.text_input("Email *", value=employe_data.get('email', '') if employe_data else "", 
                                    help="Format: prenom.nom@constructo-ai.ca")
                telephone = st.text_input("Téléphone", value=employe_data.get('telephone', '450-555-0000') if employe_data else "450-555-0000")
            
            with col2:
                nom = st.text_input("Nom *", value=employe_data.get('nom', '') if employe_data else "")
                photo_url = st.text_input("Photo URL", value=employe_data.get('photo_url', '') if employe_data else "")
            
            # Informations professionnelles
            st.markdown("##### 💼 Informations Professionnelles Constructo AI Inc.")
            col3, col4 = st.columns(2)
            
            with col3:
                poste = st.text_input("Poste *", value=employe_data.get('poste', '') if employe_data else "",
                                    help="Ex: Soudeur, Journalier, Dessinateur, etc.")
                departement = st.selectbox(
                    "Département *",
                    DEPARTEMENTS,
                    index=DEPARTEMENTS.index(employe_data.get('departement')) if employe_data and employe_data.get('departement') in DEPARTEMENTS else 0
                )
                statut = st.selectbox(
                    "Statut *",
                    STATUTS_EMPLOYE,
                    index=STATUTS_EMPLOYE.index(employe_data.get('statut')) if employe_data and employe_data.get('statut') in STATUTS_EMPLOYE else 0
                )
                type_contrat = st.selectbox(
                    "Type de contrat *",
                    TYPES_CONTRAT,
                    index=TYPES_CONTRAT.index(employe_data.get('type_contrat')) if employe_data and employe_data.get('type_contrat') in TYPES_CONTRAT else 0
                )
            
            with col4:
                date_embauche = st.date_input(
                    "Date d'embauche *",
                    value=datetime.strptime(employe_data.get('date_embauche'), '%Y-%m-%d').date() if employe_data and employe_data.get('date_embauche') else datetime.now().date()
                )
                
                # CORRECTION DU BUG: Convertir tous les paramètres en float
                current_salaire = float(employe_data.get('salaire', 47000)) if employe_data else 47000.0
                salaire = st.number_input(
                    "Salaire annuel (CAD) *",
                    min_value=30000.0,  # CHANGÉ: float au lieu de int
                    max_value=150000.0, # CHANGÉ: float au lieu de int
                    value=current_salaire,
                    step=1000.0,        # CHANGÉ: float au lieu de int
                    help="Salaire en dollars canadiens"
                )
                
                # Manager - Liste des managers disponibles
                managers_options = [("", "Autonome")] + [(emp['id'], f"{emp.get('prenom', '')} {emp.get('nom', '')}") for emp in emp_manager.get_managers()]
                current_manager_id = employe_data.get('manager_id') if employe_data else (11 if departement in ['PRODUCTION', 'STRUCTURE', 'QUALITÉ'] else "")
                manager_id = st.selectbox(
                    "Manager",
                    options=[mid for mid, _ in managers_options],
                    format_func=lambda mid: next((name for id_m, name in managers_options if id_m == mid), "Autonome"),
                    index=next((i for i, (mid, _) in enumerate(managers_options) if mid == current_manager_id), 0)
                )
                
                charge_travail = st.slider(
                    "Charge de travail (%)",
                    0, 100,
                    value=employe_data.get('charge_travail', 85) if employe_data else 85,
                    help="Pourcentage de capacité utilisée"
                )
            
            # Compétences dans le formulaire (lecture seule)
            st.markdown("##### 📋 Compétences sélectionnées")
            if st.session_state.competences_form:
                comp_text = ", ".join([f"{comp['nom']} ({comp['niveau']})" for comp in st.session_state.competences_form])
                st.text_area("Compétences:", value=comp_text, disabled=True)
            else:
                st.info("Aucune compétence ajoutée. Utilisez la section ci-dessus.")
            
            # Notes
            notes = st.text_area("Notes", value=employe_data.get('notes', '') if employe_data else "",
                               help="Informations supplémentaires sur l'employé")
            
            st.caption("* Champs obligatoires - Sauvegarde automatique en SQLite")
            
            # Boutons du formulaire
            col_submit, col_cancel = st.columns(2)
            with col_submit:
                submitted = st.form_submit_button("💾 Enregistrer en SQLite", use_container_width=True)
            with col_cancel:
                cancelled = st.form_submit_button("❌ Annuler", use_container_width=True)
            
            # TRAITEMENT DU FORMULAIRE
            if submitted:
                if not prenom or not nom or not email or not poste:
                    st.error("Les champs marqués * sont obligatoires.")
                elif '@' not in email:
                    st.error("Format d'email invalide.")
                else:
                    new_employe_data = {
                        'prenom': prenom,
                        'nom': nom,
                        'email': email,
                        'telephone': telephone,
                        'poste': poste,
                        'departement': departement,
                        'statut': statut,
                        'type_contrat': type_contrat,
                        'date_embauche': date_embauche.strftime('%Y-%m-%d'),
                        'salaire': int(salaire),  # Convertir en int pour stockage
                        'manager_id': manager_id if manager_id else None,
                        'charge_travail': charge_travail,
                        'competences': st.session_state.competences_form,
                        'projets_assignes': employe_data.get('projets_assignes', []) if employe_data else [],
                        'notes': notes,
                        'photo_url': photo_url
                    }
                    
                    try:
                        if employe_data:  # Modification
                            success = emp_manager.modifier_employe(employe_data['id'], new_employe_data)
                            if success:
                                st.success(f"✅ Employé {prenom} {nom} mis à jour en SQLite !")
                            else:
                                st.error("❌ Erreur modification SQLite.")
                        else:  # Création
                            new_id = emp_manager.ajouter_employe(new_employe_data)
                            if new_id:
                                st.success(f"✅ Nouvel employé {prenom} {nom} ajouté en SQLite (ID: {new_id}) !")
                            else:
                                st.error("❌ Erreur création SQLite.")
                        
                        # Nettoyage
                        if 'competences_form' in st.session_state:
                            del st.session_state.competences_form
                        st.session_state.emp_action = None
                        st.session_state.emp_selected_id = None
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Erreur lors de la sauvegarde SQLite : {str(e)}")
            
            if cancelled:
                # Nettoyage lors de l'annulation
                if 'competences_form' in st.session_state:
                    del st.session_state.competences_form
                st.session_state.emp_action = None
                st.session_state.emp_selected_id = None
                st.rerun()

def render_employe_details(emp_manager, projet_manager, employe_data):
    """Détails employé - Compatible SQLite avec focus construction"""
    if not employe_data:
        st.error("Employé non trouvé en SQLite.")
        return
    
    st.subheader(f"👤 Profil: {employe_data.get('prenom')} {employe_data.get('nom')} (SQLite)")
    
    # Informations principales avec design amélioré
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        <div class='info-card'>
            <h4>📋 Informations Personnelles</h4>
            <p><strong>📧 Email:</strong> {employe_data.get('email', 'N/A')}</p>
            <p><strong>📞 Téléphone:</strong> {employe_data.get('telephone', 'N/A')}</p>
            <p><strong>💼 Poste:</strong> {employe_data.get('poste', 'N/A')}</p>
            <p><strong>🏭 Département:</strong> {employe_data.get('departement', 'N/A')}</p>
            <p><strong>📊 Statut:</strong> {employe_data.get('statut', 'N/A')}</p>
            <p><strong>📄 Type contrat:</strong> {employe_data.get('type_contrat', 'N/A')}</p>
            <p><strong>📅 Date embauche:</strong> {employe_data.get('date_embauche', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='info-card'>
            <h4>💰 Informations Financières</h4>
            <p><strong>Salaire:</strong> {employe_data.get('salaire', 0):,}$ CAD/an</p>
            <p><strong>Charge travail:</strong> {employe_data.get('charge_travail', 0)}%</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Manager et hiérarchie
        manager = emp_manager.get_employe_by_id(employe_data.get('manager_id')) if employe_data.get('manager_id') else None
        manager_nom = f"{manager.get('prenom', '')} {manager.get('nom', '')}" if manager else "Autonome"
        
        subordinates = emp_manager.get_subordinates(employe_data['id'])
        
        st.markdown(f"""
        <div class='info-card'>
            <h4>👥 Hiérarchie</h4>
            <p><strong>Manager:</strong> {manager_nom}</p>
            <p><strong>Subordonnés:</strong> {len(subordinates)}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Compétences construction avec catégorisation
    st.markdown("---")
    st.markdown("##### 🎯 Compétences Construction Constructo AI Inc. (SQLite)")
    competences = employe_data.get('competences', [])
    if competences:
        # Grouper par catégorie construction
        comp_soudage = [c for c in competences if any(mot in c.get('nom', '').lower() for mot in ['soudage', 'mig', 'tig', 'soudeur'])]
        comp_usinage = [c for c in competences if any(mot in c.get('nom', '').lower() for mot in ['découpe', 'pliage', 'scie', 'plasma', 'cnc', 'usinage'])]
        comp_securite = [c for c in competences if any(mot in c.get('nom', '').lower() for mot in ['cnesst', 'sécurité', 'loto', 'premiers'])]
        comp_langues = [c for c in competences if c.get('nom') in ['Français', 'Anglais', 'Espagnol']]
        comp_qualite = [c for c in competences if any(mot in c.get('nom', '').lower() for mot in ['contrôle', 'qualité', 'inspection', 'métrologie'])]
        comp_conception = [c for c in competences if any(mot in c.get('nom', '').lower() for mot in ['autocad', 'solidworks', 'dessin', 'plans'])]
        comp_gestion = [c for c in competences if any(mot in c.get('nom', '').lower() for mot in ['gestion', 'planification', 'estimation', 'commercial'])]
        comp_autres = [c for c in competences if c not in comp_soudage + comp_usinage + comp_securite + comp_langues + comp_qualite + comp_conception + comp_gestion]
        
        categories = [
            ("🔥 Soudage", comp_soudage),
            ("⚙️ Usinage", comp_usinage),
            ("🦺 Sécurité", comp_securite),
            ("🔍 Qualité", comp_qualite),
            ("🎨 Conception", comp_conception),
            ("📊 Gestion", comp_gestion),
            ("🗣️ Langues", comp_langues),
            ("🔧 Autres", comp_autres)
        ]
        
        for cat_nom, cat_comps in categories:
            if cat_comps:
                st.markdown(f"**{cat_nom}**")
                comp_cols = st.columns(min(3, len(cat_comps)))
                for i, comp in enumerate(cat_comps):
                    col_idx = i % 3
                    with comp_cols[col_idx]:
                        certif_icon = "🏆" if comp.get('certifie') else "📚"
                        niveau_color = {
                            'DÉBUTANT': '#f39c12',
                            'INTERMÉDIAIRE': '#3498db', 
                            'AVANCÉ': '#2ecc71',
                            'EXPERT': '#9b59b6'
                        }.get(comp.get('niveau'), '#95a5a6')
                        
                        st.markdown(f"""
                        <div class='info-card' style='border-left: 4px solid {niveau_color}; margin-bottom: 0.5rem;'>
                            <h6 style='margin: 0 0 0.2rem 0;'>{certif_icon} {comp.get('nom', 'N/A')}</h6>
                            <p style='margin: 0; font-size: 0.9em;'>{comp.get('niveau', 'N/A')}</p>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.info("Aucune compétence renseignée.")
    
    # Projets assignés avec détails
    st.markdown("---")
    st.markdown("##### 🚀 Projets Assignés Constructo AI Inc. (SQLite)")
    projets_assignes = employe_data.get('projets_assignes', [])
    if projets_assignes and projet_manager and hasattr(projet_manager, 'projets'):
        for proj_id in projets_assignes:
            projet = next((p for p in projet_manager.projets if p.get('id') == proj_id), None)
            if projet:
                statut_color = {
                    'À FAIRE': '#f39c12',
                    'EN COURS': '#3498db',
                    'EN ATTENTE': '#e74c3c', 
                    'TERMINÉ': '#2ecc71',
                    'LIVRAISON': '#9b59b6'
                }.get(projet.get('statut'), '#95a5a6')
                
                st.markdown(f"""
                <div class='info-card' style='border-left: 4px solid {statut_color}; margin-bottom: 0.5rem;'>
                    <h6 style='margin: 0 0 0.2rem 0;'>#{projet.get('id')} - {projet.get('nom_projet', 'N/A')}</h6>
                    <p style='margin: 0; font-size: 0.9em;'>📊 {projet.get('statut', 'N/A')} • 💰 {projet.get('prix_estime', 0):,}$ CAD • 📅 {projet.get('date_prevu', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Aucun projet assigné.")
    
    # Notes avec style
    if employe_data.get('notes'):
        st.markdown("---")
        st.markdown("##### 📝 Notes")
        st.markdown(f"<div class='info-card'><p>{employe_data.get('notes', '')}</p></div>", unsafe_allow_html=True)
    
    # Bouton retour
    if st.button("⬅️ Retour à la liste", key="back_to_emp_list"):
        st.session_state.emp_action = None
        st.rerun()

# Interface principale pour la page employés (MISE À JOUR FINALE)
def show_employees_page():
    """Page principale employés Constructo AI Inc. - Architecture SQLite Unifiée"""
    st.markdown("## 👥 Gestion des Employés - Constructo AI Inc. Construction (SQLite)")
    
    # Vérifier si le gestionnaire employés SQLite existe
    if 'gestionnaire_employes' not in st.session_state:
        st.error("❌ Gestionnaire employés non initialisé.")
        return
    
    emp_manager = st.session_state.gestionnaire_employes
    projet_manager = st.session_state.get('gestionnaire', None)
    
    # Vérification connexion SQLite
    if not emp_manager.db:
        st.error("❌ Base de données SQLite non connectée.")
        return
    
    # Informations sur la base SQLite avec bouton de réinitialisation
    col_info, col_reset = st.columns([3, 1])
    
    with col_info:
        total_employees = emp_manager.db.get_table_count('employees')
        st.info(f"🗄️ Base SQLite : {total_employees} employés • Base: erp_production_dg.db")
    
    with col_reset:
        if st.button("🔄 Migrer vers Constructo AI", help="Supprime les anciennes données DG Inc. et charge les employés Constructo AI Inc."):
            with st.spinner("Migration en cours..."):
                if emp_manager.forcer_migration_constructo_ai():
                    st.balloons()
                    st.rerun()
    
    # Onglets
    tab1, tab2 = st.tabs(["📋 Liste des Employés", "📊 Dashboard RH"])
    
    with tab1:
        render_employes_liste_tab(emp_manager, projet_manager)
    
    with tab2:
        render_employes_dashboard_tab(emp_manager, projet_manager)
    
    # Gestion des actions
    if st.session_state.get('emp_action') == "create_employe":
        render_employe_form(emp_manager)
    elif st.session_state.get('emp_action') == "edit_employe" and st.session_state.get('emp_selected_id'):
        employe_data = emp_manager.get_employe_by_id(st.session_state.emp_selected_id)
        render_employe_form(emp_manager, employe_data)
    elif st.session_state.get('emp_action') == "view_employe_details" and st.session_state.get('emp_selected_id'):
        employe_data = emp_manager.get_employe_by_id(st.session_state.emp_selected_id)
        render_employe_details(emp_manager, projet_manager, employe_data)

# =========================================================================
# MÉTHODES CONSTRUCTION QUÉBEC - AJOUT POUR CONFORMITÉ
# =========================================================================

def _init_competences_construction(self):
    """Initialise les compétences spécifiques construction"""
    self.competences_construction = {
        'metiers_ccq': {
            'Briqueteur-maçon': ['Compagnon', 'Apprenti'],
            'Charpentier-menuisier': ['Compagnon', 'Apprenti'],
            'Couvreur': ['Compagnon', 'Apprenti'],
            'Électricien': ['Compagnon', 'Apprenti'],
            'Ferrailleur': ['Compagnon', 'Apprenti'],
            'Grutier': ['Classe 1', 'Classe 2', 'Classe 3', 'Classe 4'],
            'Opérateur d\'équipement lourd': ['Classe 1', 'Classe 2', 'Classe 3', 'Classe 4'],
            'Peintre': ['Compagnon', 'Apprenti'],
            'Plombier': ['Compagnon', 'Apprenti'],
            'Soudeur': ['Classe A', 'Classe B', 'Classe C'],
            'Tuyauteur': ['Compagnon', 'Apprenti']
        },
        'categories_rbq': {
            '1.1': 'Entrepreneur en bâtiments résidentiels neufs classe I',
            '1.2': 'Entrepreneur en bâtiments résidentiels neufs classe II',
            '1.3': 'Entrepreneur en petits bâtiments',
            '3': 'Entrepreneur en plomberie',
            '4': 'Entrepreneur en électricité',
            '6': 'Entrepreneur en charpente et menuiserie',
            '13': 'Entrepreneur en structures métalliques',
            '16': 'Entrepreneur général'
        },
        'phases_construction': [
            'Excavation et terrassement',
            'Fondations',
            'Charpente',
            'Plomberie',
            'Électricité',
            'Isolation',
            'Plâtrage',
            'Peinture',
            'Revêtements',
            'Finition'
        ]
    }

def _get_carte_ccq_employee(self, employee_id: int) -> Optional[Dict]:
    """Récupère les informations de carte CCQ d'un employé"""
    try:
        query = "SELECT * FROM cartes_ccq WHERE employee_id = ? AND statut = 'Active'"
        result = self.db.execute_query(query, [employee_id])
        return result[0] if result else None
    except Exception:
        return None

def ajouter_competence_construction(self, employee_id: int, competence_data: Dict) -> bool:
    """Ajoute une compétence construction à un employé"""
    try:
        # Ajouter la compétence à la table employee_competences
        query = """
        INSERT INTO employee_competences (employee_id, competence_nom, niveau, certifie, date_obtention)
        VALUES (?, ?, ?, ?, ?)
        """
        
        params = (
            employee_id,
            competence_data['nom'],
            competence_data.get('niveau', 'DÉBUTANT'),
            competence_data.get('certifie', False),
            competence_data.get('date_obtention', datetime.now().isoformat())
        )
        
        self.db.execute_update(query, params)
        
        # Si c'est une carte CCQ, l'ajouter à la table cartes_ccq
        if competence_data.get('type') == 'CCQ':
            carte_data = {
                'employee_id': employee_id,
                'numero_carte': competence_data.get('numero_carte', ''),
                'metier_principal': competence_data['nom'],
                'qualification': competence_data.get('niveau', 'Apprenti'),
                'heures_totales': competence_data.get('heures_totales', 0),
                'date_emission': competence_data.get('date_emission'),
                'date_renouvellement': competence_data.get('date_renouvellement'),
                'asp_construction': competence_data.get('asp_construction', False)
            }
            
            self.db.ajouter_carte_ccq(carte_data)
        
        # Recharger les employés pour mettre à jour le cache
        self._load_employes_from_db()
        return True
        
    except Exception as e:
        st.error(f"Erreur ajout compétence construction: {e}")
        return False

def get_employees_with_ccq_cards(self) -> List[Dict]:
    """Récupère les employés avec leurs cartes CCQ"""
    try:
        query = """
        SELECT 
            e.id, e.nom, e.prenom, e.poste, e.departement,
            c.numero_carte, c.metier_principal, c.qualification,
            c.heures_totales, c.date_renouvellement, c.asp_construction
        FROM employees e
        LEFT JOIN cartes_ccq c ON e.id = c.employee_id
        WHERE c.statut = 'Active' OR c.statut IS NULL
        ORDER BY e.nom, e.prenom
        """
        
        return self.db.execute_query(query)
    except Exception:
        return []

def verifier_conformite_employee_construction(self, employee_id: int) -> Dict:
    """Vérifie la conformité d'un employé pour la construction"""
    try:
        conformite = {
            'est_conforme': True,
            'carte_ccq_valide': False,
            'asp_construction': False,
            'formations_securite': [],
            'alertes': []
        }
        
        # Vérifier carte CCQ
        carte_ccq = self._get_carte_ccq_employee(employee_id)
        if carte_ccq:
            conformite['carte_ccq_valide'] = True
            conformite['asp_construction'] = carte_ccq.get('asp_construction', False)
            
            # Vérifier date renouvellement
            if carte_ccq.get('date_renouvellement'):
                date_renouvellement = datetime.strptime(carte_ccq['date_renouvellement'], '%Y-%m-%d')
                if date_renouvellement < datetime.now():
                    conformite['alertes'].append('Carte CCQ expirée')
                    conformite['est_conforme'] = False
        else:
            conformite['alertes'].append('Aucune carte CCQ enregistrée')
        
        # Vérifier formations sécurité
        employee = self.get_employe_by_id(employee_id)
        if employee:
            competences = employee.get('competences', [])
            formations_securite = []
            
            for comp in competences:
                if comp['nom'] in ['CNESST', 'ASP Construction', 'SIMDUT 2015', 'Premiers soins']:
                    formations_securite.append(comp['nom'])
            
            conformite['formations_securite'] = formations_securite
            
            if 'ASP Construction' not in formations_securite:
                conformite['alertes'].append('Formation ASP Construction manquante')
                conformite['est_conforme'] = False
        
        return conformite
        
    except Exception as e:
        return {'est_conforme': False, 'alertes': [f'Erreur vérification: {e}']}

def get_stats_construction(self) -> Dict:
    """Statistiques spécifiques construction"""
    stats_construction = {
        'employes_avec_ccq': 0,
        'metiers_ccq_actifs': {},
        'formations_asp': 0,
        'conformite_globale': 0,
        'alertes_renouvellement': 0
    }
    
    total_employes = len(self.employes)
    employes_conformes = 0
    
    for emp in self.employes:
        # Vérifier conformité construction
        conformite = self.verifier_conformite_employee_construction(emp['id'])
        
        if conformite['carte_ccq_valide']:
            stats_construction['employes_avec_ccq'] += 1
            
            # Métier CCQ principal
            carte_ccq = self._get_carte_ccq_employee(emp['id'])
            if carte_ccq:
                metier = carte_ccq.get('metier_principal', 'Autre')
                stats_construction['metiers_ccq_actifs'][metier] = stats_construction['metiers_ccq_actifs'].get(metier, 0) + 1
        
        if conformite['asp_construction']:
            stats_construction['formations_asp'] += 1
        
        if conformite['est_conforme']:
            employes_conformes += 1
        
        if conformite['alertes']:
            stats_construction['alertes_renouvellement'] += 1
    
    # Calculer pourcentage de conformité globale
    if total_employes > 0:
        stats_construction['conformite_globale'] = int((employes_conformes / total_employes) * 100)
    
    return stats_construction

# Ajouter les méthodes à la classe EmployeeManager
GestionnaireEmployes._init_competences_construction = _init_competences_construction
GestionnaireEmployes._get_carte_ccq_employee = _get_carte_ccq_employee
GestionnaireEmployes.ajouter_competence_construction = ajouter_competence_construction
GestionnaireEmployes.get_employees_with_ccq_cards = get_employees_with_ccq_cards
GestionnaireEmployes.verifier_conformite_employee_construction = verifier_conformite_employee_construction
GestionnaireEmployes.get_stats_construction = get_stats_construction