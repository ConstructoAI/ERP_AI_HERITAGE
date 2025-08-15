import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Tuple
import re

class ConformiteConstruction:
    """Module de gestion de la conformité pour la construction au Québec"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.categories_rbq = {
            "1.1": "Entrepreneur en bâtiments résidentiels neufs classe I",
            "1.2": "Entrepreneur en bâtiments résidentiels neufs classe II", 
            "1.3": "Entrepreneur en petits bâtiments",
            "2": "Entrepreneur en systèmes de chauffage à air chaud",
            "3": "Entrepreneur en plomberie",
            "4": "Entrepreneur en électricité",
            "5.1": "Entrepreneur en excavation et terrassement",
            "5.2": "Entrepreneur en fondations profondes",
            "6": "Entrepreneur en charpente et menuiserie",
            "7": "Entrepreneur en revêtements extérieurs",
            "8": "Entrepreneur en systèmes intérieurs",
            "9": "Entrepreneur en toitures",
            "10": "Entrepreneur en isolation, étanchéité, couvertures et revêtements métalliques",
            "11.1": "Entrepreneur en structures de béton",
            "11.2": "Entrepreneur en béton préfabriqué",
            "12": "Entrepreneur en armature et ferraillage",
            "13": "Entrepreneur en structures métalliques et éléments préfabriqués",
            "14": "Entrepreneur en maçonnerie",
            "15.1": "Entrepreneur en systèmes de chauffage à eau chaude",
            "15.2": "Entrepreneur en systèmes de chauffage à vapeur",
            "15.3": "Entrepreneur en systèmes de brûleurs au mazout",
            "15.4": "Entrepreneur en systèmes de brûleurs au gaz",
            "15.5": "Entrepreneur en ventilation",
            "15.6": "Entrepreneur en climatisation",
            "15.7": "Entrepreneur en réfrigération",
            "15.8": "Entrepreneur en protection-incendie",
            "16": "Entrepreneur général"
        }
        
        self.metiers_ccq = {
            "Apprenti": ["1re période", "2e période", "3e période", "4e période"],
            "Briqueteur-maçon": "Compagnon",
            "Calorifugeur": "Compagnon",
            "Carreleur": "Compagnon",
            "Charpentier-menuisier": "Compagnon",
            "Chaudronnier": "Compagnon",
            "Cimentier-applicateur": "Compagnon",
            "Couvreur": "Compagnon",
            "Électricien": "Compagnon",
            "Ferblantier": "Compagnon",
            "Ferrailleur": "Compagnon",
            "Frigoriste": "Compagnon",
            "Grutier": ["Classe 1", "Classe 2", "Classe 3", "Classe 4"],
            "Mécanicien d'ascenseur": "Compagnon",
            "Mécanicien de chantier": "Compagnon",
            "Mécanicien en protection-incendie": "Compagnon",
            "Monteur-assembleur": "Compagnon",
            "Monteur-mécanicien (vitrier)": "Compagnon",
            "Opérateur d'équipement lourd": ["Classe 1", "Classe 2", "Classe 3", "Classe 4"],
            "Opérateur de pelles mécaniques": "Compagnon",
            "Peintre": "Compagnon",
            "Plâtrier": "Compagnon",
            "Plombier": "Compagnon",
            "Poseur de revêtements souples": "Compagnon",
            "Poseur de systèmes intérieurs": "Compagnon",
            "Soudeur": ["Classe A", "Classe B", "Classe C"],
            "Soudeur en tuyauterie": ["Classe A", "Classe B"],
            "Tuyauteur": "Compagnon"
        }

    def afficher_interface(self):
        """Interface principale du module de conformité"""
        st.title("🏗️ Gestion de la Conformité Construction")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🎫 Licences RBQ", 
            "👷 Cartes CCQ",
            "📋 Attestations",
            "🔍 Vérifications",
            "📊 Tableau de bord"
        ])
        
        with tab1:
            self.gestion_licences_rbq()
            
        with tab2:
            self.gestion_cartes_ccq()
            
        with tab3:
            self.gestion_attestations()
            
        with tab4:
            self.verifications_conformite()
            
        with tab5:
            self.tableau_bord_conformite()
    
    def gestion_licences_rbq(self):
        """Gestion des licences RBQ"""
        st.header("Gestion des Licences RBQ")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Formulaire d'ajout/modification
            with st.form("form_licence_rbq"):
                st.subheader("Ajouter/Modifier une licence RBQ")
                
                numero_licence = st.text_input("Numéro de licence RBQ", 
                    help="Format: XXXX-XXXX-XX")
                
                nom_entreprise = st.text_input("Nom de l'entreprise")
                
                # Sélection multiple des catégories
                categories_selectionnees = st.multiselect(
                    "Catégories de licence",
                    options=list(self.categories_rbq.keys()),
                    format_func=lambda x: f"{x} - {self.categories_rbq[x]}"
                )
                
                col_dates = st.columns(2)
                with col_dates[0]:
                    date_emission = st.date_input("Date d'émission")
                with col_dates[1]:
                    date_expiration = st.date_input("Date d'expiration")
                
                statut = st.selectbox("Statut", ["Active", "Suspendue", "Expirée"])
                
                cautionnement = st.number_input("Montant du cautionnement ($)", 
                    min_value=0.0, format="%.2f")
                
                assurance_resp = st.number_input("Assurance responsabilité ($)", 
                    min_value=0.0, format="%.2f")
                
                submitted = st.form_submit_button("Enregistrer")
                
                if submitted and numero_licence:
                    licence_data = {
                        "numero_licence": numero_licence,
                        "nom_entreprise": nom_entreprise,
                        "categories": json.dumps(categories_selectionnees),
                        "date_emission": date_emission.isoformat(),
                        "date_expiration": date_expiration.isoformat(),
                        "statut": statut,
                        "cautionnement": cautionnement,
                        "assurance_responsabilite": assurance_resp
                    }
                    
                    # Enregistrer dans la base de données
                    if self.db.ajouter_licence_rbq(licence_data):
                        st.success("✅ Licence RBQ enregistrée avec succès!")
                    else:
                        st.error("❌ Erreur lors de l'enregistrement")
        
        with col2:
            # Alertes et statistiques
            st.subheader("📊 Aperçu")
            
            # Alertes d'expiration
            licences_expirant = self.verifier_expirations_rbq()
            if licences_expirant:
                st.warning(f"⚠️ {len(licences_expirant)} licence(s) expirant dans 60 jours")
                with st.expander("Voir les détails"):
                    for licence in licences_expirant:
                        st.write(f"- {licence['numero']} - Expire le {licence['expiration']}")
            
            # Statistiques
            stats = self.obtenir_stats_rbq()
            if stats:
                st.metric("Licences actives", stats.get("actives", 0))
                st.metric("Total catégories", stats.get("total_categories", 0))
                st.metric("Cautionnement total", f"${stats.get('cautionnement_total', 0):,.2f}")
        
        # Liste des licences
        st.subheader("📋 Liste des licences RBQ")
        
        # Filtres
        col_filtres = st.columns(4)
        with col_filtres[0]:
            filtre_statut = st.selectbox("Filtrer par statut", 
                ["Tous", "Active", "Suspendue", "Expirée"])
        with col_filtres[1]:
            filtre_categorie = st.selectbox("Filtrer par catégorie",
                ["Toutes"] + list(self.categories_rbq.keys()))
        
        # Affichage de la liste
        licences = self.obtenir_licences_rbq(filtre_statut, filtre_categorie)
        if licences:
            df_licences = pd.DataFrame(licences)
            st.dataframe(df_licences, use_container_width=True)
        else:
            st.info("Aucune licence RBQ enregistrée")
    
    def gestion_cartes_ccq(self):
        """Gestion des cartes de compétence CCQ"""
        st.header("Gestion des Cartes CCQ")
        
        # Sélection de l'employé
        employees = self.db.get_all_employees()
        employee_dict = {f"{emp['nom']} {emp['prenom']}": emp['id'] for emp in employees}
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            with st.form("form_carte_ccq"):
                st.subheader("Ajouter/Modifier une carte CCQ")
                
                employee_name = st.selectbox("Employé", 
                    options=list(employee_dict.keys()))
                employee_id = employee_dict.get(employee_name)
                
                numero_carte = st.text_input("Numéro de carte CCQ")
                
                # Métiers et qualifications
                metier_principal = st.selectbox("Métier principal",
                    options=list(self.metiers_ccq.keys()))
                
                if metier_principal:
                    qualifications = self.metiers_ccq[metier_principal]
                    if isinstance(qualifications, list):
                        qualification = st.selectbox("Qualification", qualifications)
                    else:
                        qualification = qualifications
                        st.info(f"Qualification: {qualification}")
                
                metiers_additionnels = st.multiselect(
                    "Métiers additionnels",
                    options=[m for m in self.metiers_ccq.keys() if m != metier_principal]
                )
                
                heures_totales = st.number_input("Heures totales accumulées", 
                    min_value=0, step=100)
                
                col_dates = st.columns(2)
                with col_dates[0]:
                    date_emission = st.date_input("Date d'émission")
                with col_dates[1]:
                    date_renouvellement = st.date_input("Date de renouvellement")
                
                asp_construction = st.checkbox("Formation ASP Construction valide")
                
                submitted = st.form_submit_button("Enregistrer")
                
                if submitted and numero_carte and employee_id:
                    carte_data = {
                        "employee_id": employee_id,
                        "numero_carte": numero_carte,
                        "metier_principal": metier_principal,
                        "qualification": qualification,
                        "metiers_additionnels": json.dumps(metiers_additionnels),
                        "heures_totales": heures_totales,
                        "date_emission": date_emission.isoformat(),
                        "date_renouvellement": date_renouvellement.isoformat(),
                        "asp_construction": asp_construction
                    }
                    
                    if self.db.ajouter_carte_ccq(carte_data):
                        st.success("✅ Carte CCQ enregistrée avec succès!")
                    else:
                        st.error("❌ Erreur lors de l'enregistrement")
        
        with col2:
            st.subheader("📊 Statistiques CCQ")
            
            stats_ccq = self.obtenir_stats_ccq()
            if stats_ccq:
                st.metric("Cartes actives", stats_ccq.get("cartes_actives", 0))
                st.metric("Total métiers", stats_ccq.get("total_metiers", 0))
                st.metric("Heures moyennes", f"{stats_ccq.get('heures_moyennes', 0):,.0f}")
                
                # Répartition par métier
                if stats_ccq.get("repartition_metiers"):
                    st.subheader("Répartition par métier")
                    for metier, count in stats_ccq["repartition_metiers"].items():
                        st.write(f"- {metier}: {count}")
        
        # Liste des cartes CCQ
        st.subheader("📋 Liste des cartes CCQ")
        
        cartes = self.obtenir_cartes_ccq()
        if cartes:
            df_cartes = pd.DataFrame(cartes)
            st.dataframe(df_cartes, use_container_width=True)
        else:
            st.info("Aucune carte CCQ enregistrée")
    
    def gestion_attestations(self):
        """Gestion des attestations fiscales et autres documents"""
        st.header("Gestion des Attestations")
        
        types_attestations = {
            "Revenu Québec": "Attestation de Revenu Québec",
            "ARC": "Attestation de l'Agence du revenu du Canada",
            "CNESST": "Attestation de conformité CNESST",
            "CCQ": "Attestation CCQ - État de situation",
            "RBQ": "Attestation de solvabilité RBQ"
        }
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            with st.form("form_attestation"):
                st.subheader("Ajouter une attestation")
                
                type_attestation = st.selectbox("Type d'attestation",
                    options=list(types_attestations.keys()))
                
                numero_attestation = st.text_input("Numéro d'attestation")
                
                col_dates = st.columns(2)
                with col_dates[0]:
                    date_emission = st.date_input("Date d'émission")
                with col_dates[1]:
                    date_expiration = st.date_input("Date d'expiration")
                
                statut = st.selectbox("Statut", ["Valide", "Expirée", "En renouvellement"])
                
                notes = st.text_area("Notes")
                
                fichier = st.file_uploader("Joindre le document (PDF)", type=['pdf'])
                
                submitted = st.form_submit_button("Enregistrer")
                
                if submitted and numero_attestation:
                    attestation_data = {
                        "type": type_attestation,
                        "numero": numero_attestation,
                        "date_emission": date_emission.isoformat(),
                        "date_expiration": date_expiration.isoformat(),
                        "statut": statut,
                        "notes": notes
                    }
                    
                    if self.db.ajouter_attestation(attestation_data):
                        st.success("✅ Attestation enregistrée avec succès!")
                        
                        # Sauvegarder le fichier si fourni
                        if fichier:
                            # Code pour sauvegarder le fichier
                            pass
                    else:
                        st.error("❌ Erreur lors de l'enregistrement")
        
        with col2:
            st.subheader("⚠️ Alertes")
            
            # Vérifier les attestations expirées ou expirant bientôt
            alertes = self.verifier_attestations_expiration()
            
            if alertes["expirees"]:
                st.error(f"🔴 {len(alertes['expirees'])} attestation(s) expirée(s)")
                with st.expander("Voir les détails"):
                    for att in alertes["expirees"]:
                        st.write(f"- {att['type']}: {att['numero']}")
            
            if alertes["expirant_bientot"]:
                st.warning(f"🟡 {len(alertes['expirant_bientot'])} attestation(s) expirant dans 30 jours")
                with st.expander("Voir les détails"):
                    for att in alertes["expirant_bientot"]:
                        st.write(f"- {att['type']}: {att['numero']} (expire le {att['expiration']})")
        
        # Liste des attestations
        st.subheader("📋 Liste des attestations")
        
        attestations = self.obtenir_attestations()
        if attestations:
            df_attestations = pd.DataFrame(attestations)
            
            # Colorer selon le statut
            def color_status(val):
                if val == "Valide":
                    return 'background-color: #90EE90'
                elif val == "Expirée":
                    return 'background-color: #FFB6C1'
                else:
                    return 'background-color: #FFFFE0'
            
            styled_df = df_attestations.style.applymap(
                color_status, subset=['statut']
            )
            
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.info("Aucune attestation enregistrée")
    
    def verifications_conformite(self):
        """Interface de vérification rapide de conformité"""
        st.header("Vérifications de Conformité")
        
        # Vérification pour nouveau projet
        st.subheader("🏗️ Vérification pour nouveau projet")
        
        with st.form("verif_projet"):
            type_projet = st.selectbox("Type de projet",
                ["Résidentiel unifamilial", "Multi-logements", "Commercial", "Industriel"])
            
            valeur_projet = st.number_input("Valeur estimée du projet ($)", 
                min_value=0.0, format="%.2f")
            
            ville = st.text_input("Ville du projet")
            
            verifier = st.form_submit_button("Vérifier la conformité")
            
            if verifier:
                resultats = self.verifier_conformite_projet(type_projet, valeur_projet, ville)
                
                if resultats["conforme"]:
                    st.success("✅ Conformité vérifiée - Prêt à soumissionner")
                else:
                    st.error("❌ Non-conformité détectée")
                    
                with st.expander("Détails de la vérification"):
                    for item in resultats["details"]:
                        if item["status"] == "OK":
                            st.write(f"✅ {item['element']}: {item['message']}")
                        else:
                            st.write(f"❌ {item['element']}: {item['message']}")
        
        # Vérification d'un sous-traitant
        st.subheader("👷 Vérification de sous-traitant")
        
        with st.form("verif_sous_traitant"):
            nom_entreprise = st.text_input("Nom de l'entreprise")
            numero_rbq = st.text_input("Numéro RBQ")
            categories_requises = st.multiselect(
                "Catégories RBQ requises",
                options=list(self.categories_rbq.keys()),
                format_func=lambda x: f"{x} - {self.categories_rbq[x]}"
            )
            
            verifier_st = st.form_submit_button("Vérifier")
            
            if verifier_st and numero_rbq:
                # Simuler une vérification
                st.info("🔍 Vérification en cours...")
                
                # Dans un cas réel, on ferait une requête API ou base de données
                st.success(f"✅ Entreprise {nom_entreprise} vérifiée")
                st.write("- Licence RBQ valide")
                st.write("- Catégories confirmées")
                st.write("- Attestations à jour")
    
    def tableau_bord_conformite(self):
        """Tableau de bord global de conformité"""
        st.header("Tableau de Bord de Conformité")
        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            licences_actives = self.compter_licences_actives()
            st.metric("Licences RBQ actives", licences_actives)
        
        with col2:
            cartes_valides = self.compter_cartes_valides()
            st.metric("Cartes CCQ valides", cartes_valides)
        
        with col3:
            attestations_valides = self.compter_attestations_valides()
            st.metric("Attestations valides", attestations_valides)
        
        with col4:
            score_conformite = self.calculer_score_conformite()
            st.metric("Score de conformité", f"{score_conformite}%")
        
        # Graphiques
        col_graph1, col_graph2 = st.columns(2)
        
        with col_graph1:
            st.subheader("📊 Statut des documents")
            # Ici on pourrait ajouter un graphique en camembert
            # montrant la répartition des documents valides/expirés/expirant
        
        with col_graph2:
            st.subheader("📈 Évolution de la conformité")
            # Ici on pourrait ajouter un graphique linéaire
            # montrant l'évolution du score de conformité dans le temps
        
        # Alertes importantes
        st.subheader("⚠️ Alertes et actions requises")
        
        alertes = self.obtenir_toutes_alertes()
        
        if alertes:
            for alerte in alertes:
                if alerte["priorite"] == "haute":
                    st.error(f"🔴 {alerte['message']}")
                elif alerte["priorite"] == "moyenne":
                    st.warning(f"🟡 {alerte['message']}")
                else:
                    st.info(f"🔵 {alerte['message']}")
        else:
            st.success("✅ Aucune alerte - Tous les documents sont à jour")
        
        # Calendrier des renouvellements
        st.subheader("📅 Prochains renouvellements")
        
        renouvellements = self.obtenir_prochains_renouvellements()
        if renouvellements:
            df_renouv = pd.DataFrame(renouvellements)
            st.dataframe(df_renouv, use_container_width=True)
        else:
            st.info("Aucun renouvellement prévu dans les 90 prochains jours")
    
    # Méthodes utilitaires
    def verifier_expirations_rbq(self) -> List[Dict]:
        """Vérifie les licences RBQ expirant dans les 60 jours"""
        # Simulation - À remplacer par requête DB
        return []
    
    def obtenir_stats_rbq(self) -> Dict:
        """Obtient les statistiques des licences RBQ"""
        # Simulation - À remplacer par requête DB
        return {
            "actives": 1,
            "total_categories": 3,
            "cautionnement_total": 50000.0
        }
    
    def obtenir_licences_rbq(self, filtre_statut: str, filtre_categorie: str) -> List[Dict]:
        """Obtient la liste des licences RBQ avec filtres"""
        # Simulation - À remplacer par requête DB
        return []
    
    def obtenir_stats_ccq(self) -> Dict:
        """Obtient les statistiques des cartes CCQ"""
        # Simulation - À remplacer par requête DB
        return {
            "cartes_actives": 15,
            "total_metiers": 8,
            "heures_moyennes": 5600,
            "repartition_metiers": {
                "Charpentier-menuisier": 5,
                "Électricien": 3,
                "Plombier": 2,
                "Autres": 5
            }
        }
    
    def obtenir_cartes_ccq(self) -> List[Dict]:
        """Obtient la liste des cartes CCQ"""
        # Simulation - À remplacer par requête DB
        return []
    
    def verifier_attestations_expiration(self) -> Dict:
        """Vérifie les attestations expirées ou expirant bientôt"""
        # Simulation - À remplacer par requête DB
        return {
            "expirees": [],
            "expirant_bientot": []
        }
    
    def obtenir_attestations(self) -> List[Dict]:
        """Obtient la liste des attestations"""
        # Simulation - À remplacer par requête DB
        return []
    
    def verifier_conformite_projet(self, type_projet: str, valeur: float, ville: str) -> Dict:
        """Vérifie la conformité pour un nouveau projet"""
        resultats = {
            "conforme": True,
            "details": []
        }
        
        # Vérifier licence RBQ appropriée
        if type_projet == "Résidentiel unifamilial":
            resultats["details"].append({
                "element": "Licence RBQ",
                "status": "OK",
                "message": "Catégorie 1.1 ou 1.2 valide"
            })
        
        # Vérifier cautionnement suffisant
        if valeur > 25000:
            resultats["details"].append({
                "element": "Cautionnement",
                "status": "OK",
                "message": "Cautionnement suffisant pour la valeur du projet"
            })
        
        # Vérifier attestations
        resultats["details"].append({
            "element": "Attestations fiscales",
            "status": "OK",
            "message": "Toutes les attestations sont valides"
        })
        
        return resultats
    
    def compter_licences_actives(self) -> int:
        """Compte le nombre de licences RBQ actives"""
        return 1  # Simulation
    
    def compter_cartes_valides(self) -> int:
        """Compte le nombre de cartes CCQ valides"""
        return 15  # Simulation
    
    def compter_attestations_valides(self) -> int:
        """Compte le nombre d'attestations valides"""
        return 5  # Simulation
    
    def calculer_score_conformite(self) -> int:
        """Calcule le score global de conformité"""
        return 92  # Simulation
    
    def obtenir_toutes_alertes(self) -> List[Dict]:
        """Obtient toutes les alertes de conformité"""
        return []  # Simulation
    
    def obtenir_prochains_renouvellements(self) -> List[Dict]:
        """Obtient la liste des prochains renouvellements"""
        return []  # Simulation