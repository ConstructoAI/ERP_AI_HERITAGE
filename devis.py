import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import re
from typing import Dict, List, Optional, Any

# --- Constantes partagées ---
STATUTS_DEVIS = ["BROUILLON", "VALIDÉ", "ENVOYÉ", "APPROUVÉ", "TERMINÉ", "ANNULÉ"]
UNITES_VENTE = ["unité", "sac", "m", "m²", "m³", "pièce", "paquet", "boîte", "gallon", "lot", "pi", "pi²", "pi³", "vg³", "pi linéaire", "tonne", "palette", "heure"]

# Tâches de production (copié de app.py)
TACHES_PRODUCTION = [
    # 1. Planification
    "1.1 Définir les besoins et objectifs du projet",
    "1.2 Concevoir les plans architecturaux",
    "1.3 Établir un budget détaillé",
    "1.4 Créer un calendrier prévisionnel",
    "1.5 Obtenir les permis de construire",
    
    # 2. Préparation de la démonstration
    "2.1 Installer les clôtures de sécurité",
    "2.2 Mettre en place la signalisation",
    "2.3 Préparer les équipements de protection",
    "2.4 Organiser le stockage des matériaux",
    
    # 3. Démolition
    "3.1 Déconnecter les services publics",
    "3.2 Retirer les matériaux dangereux",
    "3.3 Démolir la structure existante",
    "3.4 Trier et évacuer les débris",
    
    # 4. Excavation
    "4.1 Marquer les limites de l'excavation",
    "4.2 Creuser pour les fondations",
    "4.3 Préparer le sol pour les semelles",
    "4.4 Niveler le terrain",
    
    # 5. Béton
    "5.1 Préparer les coffrages",
    "5.2 Installer les armatures",
    "5.3 Couler les fondations",
    "5.4 Réaliser les murs de fondation",
    "5.5 Couler les dalles de béton",
    
    # 6. Charpente
    "6.1 Installer les poutres principales",
    "6.2 Monter les murs porteurs",
    "6.3 Poser la charpente de toit",
    "6.4 Installer les solives de plancher",
    
    # 7. Toiture
    "7.1 Installer la membrane d'étanchéité",
    "7.2 Poser les bardeaux d'asphalte",
    "7.3 Installer les gouttières",
    "7.4 Aménager les évents de toit",
    
    # 8. Isolation et étanchéité
    "8.1 Installer l'isolation thermique",
    "8.2 Poser le pare-vapeur",
    "8.3 Sceller les ouvertures",
    "8.4 Vérifier l'étanchéité à l'air",
    
    # 9. Électricité
    "9.1 Installer le panneau électrique",
    "9.2 Tirer les câbles électriques",
    "9.3 Poser les prises et interrupteurs",
    "9.4 Connecter l'éclairage",
    
    # 10. Plomberie
    "10.1 Installer la tuyauterie principale",
    "10.2 Poser les conduites d'alimentation",
    "10.3 Installer les évacuations",
    "10.4 Connecter les appareils sanitaires",
    
    # 11. CVC (Chauffage, Ventilation, Climatisation)
    "11.1 Installer le système de chauffage",
    "11.2 Poser les conduits de ventilation",
    "11.3 Installer la climatisation",
    "11.4 Connecter les thermostats",
    
    # 12. Cloisons et finitions intérieures
    "12.1 Monter les cloisons sèches",
    "12.2 Appliquer l'enduit et les joints",
    "12.3 Poncer et préparer les surfaces",
    "12.4 Peindre les murs et plafonds",
    
    # 13. Revêtements de sol
    "13.1 Préparer le sous-plancher",
    "13.2 Installer les revêtements de sol",
    "13.3 Poser les plinthes",
    "13.4 Effectuer les finitions",
    
    # 14. Menuiserie et ébénisterie
    "14.1 Installer les portes intérieures",
    "14.2 Monter les armoires de cuisine",
    "14.3 Poser les comptoirs",
    "14.4 Installer les moulures",
    
    # 15. Finitions extérieures
    "15.1 Appliquer le revêtement extérieur",
    "15.2 Installer les portes et fenêtres",
    "15.3 Peindre l'extérieur",
    "15.4 Aménager les entrées",
    
    # 16. Nettoyage et finition
    "16.1 Nettoyer le chantier",
    "16.2 Effectuer les retouches finales",
    "16.3 Inspecter la qualité",
    "16.4 Préparer la livraison"
]

# Fonctions utilitaires
def get_quebec_datetime():
    """Retourne la date et heure courante du Québec."""
    return datetime.now()

def _validate_project_id_format(project_id: str) -> bool:
    """Valide le format d'un ID de projet personnalisé."""
    if not project_id:
        return False
    # Permet lettres, chiffres, tirets et underscores
    pattern = r'^[A-Za-z0-9\-_]+$'
    return bool(re.match(pattern, project_id))

class GestionnaireDevis:
    """
    Gestionnaire dédié aux devis, extrait de crm.py pour une meilleure modularité.
    Utilise l'infrastructure 'formulaires' de la base de données unifiée.
    Interagit avec les modules CRM (pour les clients/produits) et Projets (pour la transformation).
    """

    def __init__(self, db, crm_manager, project_manager, product_manager):
        """
        Initialise le gestionnaire de devis.

        Args:
            db: Instance de ERPDatabase.
            crm_manager: Instance de GestionnaireCRM.
            project_manager: Instance de GestionnaireProjetSQL.
            product_manager: Instance de GestionnaireProduits.
        """
        self.db = db
        self.crm_manager = crm_manager
        self.project_manager = project_manager
        self.product_manager = product_manager  # NOUVELLE DÉPENDANCE
        self._init_devis_support()

    def _init_devis_support(self):
        """Initialise le support des devis en vérifiant la contrainte CHECK de la DB."""
        self._devis_compatibility_mode = False
        self._devis_type_db = 'DEVIS'
        
        try:
            # Tente d'insérer une ligne test pour vérifier la contrainte
            test_query = "INSERT INTO formulaires (type_formulaire, numero_document, statut) VALUES ('DEVIS', 'TEST-DEVIS-COMPATIBILITY-UNIQUE', 'BROUILLON')"
            try:
                test_id = self.db.execute_insert(test_query)
                if test_id:
                    self.db.execute_update("DELETE FROM formulaires WHERE id = ?", (test_id,))
                st.success("✅ Support DEVIS natif activé dans le système de formulaires")
            except Exception as e:
                # Si la contrainte échoue, on passe en mode compatibilité
                if "CHECK constraint failed" in str(e):
                    self._devis_compatibility_mode = True
                    self._devis_type_db = 'ESTIMATION'
                    st.warning("⚠️ Mode compatibilité DEVIS activé (via ESTIMATION).")
                else:
                    st.error(f"⚠️ Support devis limité: {e}")
        except Exception as e:
            # En cas d'autre erreur, on active le mode compatibilité par sécurité
            self._devis_compatibility_mode = True
            self._devis_type_db = 'ESTIMATION'
            st.error(f"Erreur initialisation support devis: {e}")

    # --- MÉTHODES MÉTIER (Déplacées de GestionnaireCRM) ---
    
    def generer_numero_devis(self) -> str:
        """Génère un numéro de devis/estimation automatique."""
        try:
            annee = datetime.now().year
            prefix = "EST" if self._devis_compatibility_mode else "DEVIS"
            query = "SELECT numero_document FROM formulaires WHERE numero_document LIKE ? ORDER BY id DESC LIMIT 1"
            pattern = f"{prefix}-{annee}-%"
            result = self.db.execute_query(query, (pattern,))
            
            sequence = 1
            if result:
                last_num = result[0]['numero_document']
                try:
                    sequence = int(last_num.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    sequence = 1
            
            return f"{prefix}-{annee}-{sequence:03d}"
        except Exception as e:
            st.error(f"Erreur génération numéro devis: {e}")
            prefix_fallback = "EST" if self._devis_compatibility_mode else "DEVIS"
            return f"{prefix_fallback}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def create_devis(self, devis_data: Dict[str, Any]) -> Optional[int]:
        """Crée un nouveau devis dans la table formulaires."""
        try:
            numero_devis = self.generer_numero_devis()
            type_formulaire_db = self._devis_type_db
            mode_info = " (mode compatibilité)" if self._devis_compatibility_mode else ""
            
            metadonnees = {
                'type_reel': 'DEVIS', 
                'type_devis': 'STANDARD',
                'tva_applicable': True, 
                'taux_tva': 14.975, 
                'taux_tps': 5.0,
                'taux_tvq': 9.975,
                'devise': 'CAD', 
                'validite_jours': 30, 
                'type_client': 'PARTICULIER',
                'secteur_construction': 'RÉSIDENTIEL',
                'created_by_module': 'DEVIS',
                'compatibility_mode': self._devis_compatibility_mode
            }
            
            query = '''
                INSERT INTO formulaires 
                (type_formulaire, numero_document, project_id, company_id, employee_id,
                 statut, priorite, date_echeance, notes, metadonnees_json)
                VALUES (?, ?, ?, ?, ?, 'BROUILLON', 'NORMAL', ?, ?, ?)
            '''
            
            devis_id = self.db.execute_insert(query, (
                type_formulaire_db, numero_devis, devis_data.get('project_id'),
                devis_data['client_company_id'], devis_data['employee_id'],
                devis_data['date_echeance'], devis_data.get('notes', ''), json.dumps(metadonnees)
            ))
            
            if devis_id:
                if devis_data.get('lignes'):
                    for i, ligne in enumerate(devis_data['lignes'], 1):
                        self.ajouter_ligne_devis(devis_id, i, ligne)
                self.enregistrer_validation(devis_id, devis_data['employee_id'], 'CREATION', f"Devis créé: {numero_devis}{mode_info}")
                return devis_id
            return None
        except Exception as e:
            st.error(f"Erreur création devis: {e}")
            return None

    def modifier_devis(self, devis_id: int, devis_data: Dict[str, Any]) -> bool:
        """Modifie un devis existant."""
        try:
            devis_existant = self.get_devis_complet(devis_id)
            if not devis_existant:
                st.error(f"Devis #{devis_id} non trouvé.")
                return False
            
            statuts_non_modifiables = ['APPROUVÉ', 'TERMINÉ', 'ANNULÉ']
            if devis_existant.get('statut') in statuts_non_modifiables:
                st.error(f"Impossible de modifier un devis au statut '{devis_existant.get('statut')}'")
                return False
            
            query = '''
                UPDATE formulaires 
                SET company_id = ?, employee_id = ?, project_id = ?, 
                    date_echeance = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            
            rows_affected = self.db.execute_update(query, (
                devis_data['client_company_id'], devis_data['employee_id'], devis_data.get('project_id'),
                devis_data['date_echeance'], devis_data.get('notes', ''), devis_id
            ))
            
            if rows_affected > 0:
                # Supprimer les anciennes lignes et ajouter les nouvelles
                self.db.execute_update("DELETE FROM formulaire_lignes WHERE formulaire_id = ?", (devis_id,))
                if devis_data.get('lignes'):
                    for i, ligne in enumerate(devis_data['lignes'], 1):
                        self.ajouter_ligne_devis(devis_id, i, ligne)
                self.enregistrer_validation(devis_id, devis_data['employee_id'], 'MODIFICATION', "Devis modifié via interface")
                return True
            return False
        except Exception as e:
            st.error(f"Erreur modification devis: {e}")
            return False
    
    def supprimer_devis(self, devis_id: int, employee_id: int, motif: str = "") -> bool:
        """Supprime un devis et ses données associées."""
        try:
            devis_existant = self.get_devis_complet(devis_id)
            if not devis_existant:
                st.error(f"Devis #{devis_id} non trouvé.")
                return False
            
            statuts_non_supprimables = ['APPROUVÉ', 'TERMINÉ']
            if devis_existant.get('statut') in statuts_non_supprimables:
                st.error(f"Impossible de supprimer un devis au statut '{devis_existant.get('statut')}'")
                st.info("💡 Conseil: Vous pouvez annuler le devis au lieu de le supprimer.")
                return False
            
            # Enregistrer l'action avant suppression
            self.enregistrer_validation(devis_id, employee_id, 'SUPPRESSION', f"Suppression. Motif: {motif or 'Non spécifié'}")
            
            # Supprimer en cascade
            self.db.execute_update("DELETE FROM formulaire_validations WHERE formulaire_id = ?", (devis_id,))
            self.db.execute_update("DELETE FROM formulaire_lignes WHERE formulaire_id = ?", (devis_id,))
            rows_affected = self.db.execute_update("DELETE FROM formulaires WHERE id = ?", (devis_id,))
            
            if rows_affected > 0:
                st.success(f"✅ Devis #{devis_id} ({devis_existant.get('numero_document')}) supprimé avec succès!")
                return True
            else:
                st.error("Aucune ligne affectée lors de la suppression.")
                return False
        except Exception as e:
            st.error(f"Erreur suppression devis: {e}")
            return False

    def ajouter_ligne_devis(self, devis_id: int, sequence: int, ligne_data: Dict[str, Any]) -> Optional[int]:
        """Ajoute une ligne à un devis."""
        try:
            query = '''
                INSERT INTO formulaire_lignes
                (formulaire_id, sequence_ligne, description, code_article,
                 quantite, unite, prix_unitaire, notes_ligne)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            ligne_id = self.db.execute_insert(query, (
                devis_id, sequence, ligne_data['description'], ligne_data.get('code_article', ''),
                ligne_data['quantite'], ligne_data.get('unite', 'UN'), ligne_data['prix_unitaire'], ligne_data.get('notes', '')
            ))
            
            return ligne_id
        except Exception as e:
            st.error(f"Erreur ajout ligne devis: {e}")
            return None

    def get_devis_complet(self, devis_id: int) -> Dict[str, Any]:
        """Récupère un devis avec tous ses détails."""
        try:
            query = '''
                SELECT f.*, 
                       c.nom as client_nom, 
                       c.adresse, c.ville, c.province, c.code_postal, c.pays,
                       co.prenom || ' ' || co.nom_famille as contact_nom, 
                       co.email as contact_email, co.telephone as contact_telephone,
                       e.prenom || ' ' || e.nom as responsable_nom,
                       p.nom_projet
                FROM formulaires f
                LEFT JOIN companies c ON f.company_id = c.id
                LEFT JOIN contacts co ON c.contact_principal_id = co.id
                LEFT JOIN employees e ON f.employee_id = e.id
                LEFT JOIN projects p ON f.project_id = p.id
                WHERE f.id = ? AND (f.type_formulaire = 'DEVIS' OR (f.type_formulaire = 'ESTIMATION' AND f.metadonnees_json LIKE '%"type_reel": "DEVIS"%'))
            '''
            
            result = self.db.execute_query(query, (devis_id,))
            if not result:
                return {}
            
            devis = dict(result[0])
            
            # Ajouter l'adresse complète formatée
            if devis.get('client_nom'):
                devis['client_adresse_complete'] = self.crm_manager.format_adresse_complete(devis)
            
            # Récupérer les lignes
            query_lignes = 'SELECT * FROM formulaire_lignes WHERE formulaire_id = ? ORDER BY sequence_ligne'
            lignes = self.db.execute_query(query_lignes, (devis_id,))
            devis['lignes'] = [dict(ligne) for ligne in lignes]
            
            # Calculer les totaux
            devis['totaux'] = self.calculer_totaux_devis(devis_id)
            
            # Récupérer l'historique
            query_historique = '''
                SELECT fv.*, e.prenom || ' ' || e.nom as employee_nom
                FROM formulaire_validations fv
                LEFT JOIN employees e ON fv.employee_id = e.id
                WHERE fv.formulaire_id = ?
                ORDER BY fv.date_validation DESC
            '''
            historique = self.db.execute_query(query_historique, (devis_id,))
            devis['historique'] = [dict(h) for h in historique]
            
            # Parser les métadonnées
            try:
                devis['metadonnees'] = json.loads(devis.get('metadonnees_json', '{}'))
            except:
                devis['metadonnees'] = {}
            
            return devis
        except Exception as e:
            st.error(f"Erreur récupération devis complet: {e}")
            return {}

    def calculer_totaux_devis(self, devis_id: int) -> Dict[str, float]:
        """Calcule les totaux d'un devis (HT, TVA, TTC)."""
        try:
            query = 'SELECT quantite, prix_unitaire FROM formulaire_lignes WHERE formulaire_id = ?'
            lignes = self.db.execute_query(query, (devis_id,))
            
            # Calculer le total à partir des lignes
            total_ht_lignes = sum((ligne['quantite'] * ligne['prix_unitaire']) for ligne in lignes)
            
            # Récupérer les métadonnées pour le prix estimé et taux de taxes
            devis_info = self.db.execute_query("SELECT metadonnees_json FROM formulaires WHERE id = ?", (devis_id,))
            
            # Si pas de lignes, utiliser le prix estimé des métadonnées
            total_ht = total_ht_lignes
            if total_ht_lignes == 0 and devis_info:
                try:
                    metadonnees = json.loads(devis_info[0]['metadonnees_json'] or '{}')
                    prix_estime = metadonnees.get('prix_estime', 0)
                    if prix_estime > 0:
                        total_ht = prix_estime
                except:
                    pass
            
            # Récupérer les taux de taxes selon le type de client et secteur
            taux_tps = 5.0  # TPS fédérale
            taux_tvq = 9.975  # TVQ québécoise
            type_client = 'PARTICULIER'
            secteur_construction = 'RÉSIDENTIEL'
            
            if devis_info:
                try:
                    metadonnees = json.loads(devis_info[0]['metadonnees_json'] or '{}')
                    taux_tps = metadonnees.get('taux_tps', 5.0)
                    taux_tvq = metadonnees.get('taux_tvq', 9.975)
                    type_client = metadonnees.get('type_client', 'PARTICULIER')
                    secteur_construction = metadonnees.get('secteur_construction', 'RÉSIDENTIEL')
                except:
                    pass
            
            # Calculer taxes selon le secteur construction
            tps = total_ht * (taux_tps / 100)
            tvq = total_ht * (taux_tvq / 100)
            
            # Remboursement partiel TPS pour construction résidentielle
            tps_remboursement = 0
            if secteur_construction == 'RÉSIDENTIEL' and type_client == 'PARTICULIER':
                tps_remboursement = tps * 0.36  # 36% de remboursement TPS résidentiel
            
            tps_net = tps - tps_remboursement
            total_taxes = tps_net + tvq
            total_ttc = total_ht + total_taxes
            
            return {
                'total_ht': round(total_ht, 2),
                'taux_tps': taux_tps,
                'montant_tps': round(tps, 2),
                'tps_remboursement': round(tps_remboursement, 2),
                'tps_net': round(tps_net, 2),
                'taux_tvq': taux_tvq,
                'montant_tvq': round(tvq, 2),
                'total_taxes': round(total_taxes, 2),
                'total_ttc': round(total_ttc, 2),
                'type_client': type_client,
                'secteur_construction': secteur_construction
            }
        except Exception as e:
            st.error(f"Erreur calcul totaux devis: {e}")
            return {'total_ht': 0, 'taux_tva': 0, 'montant_tva': 0, 'total_ttc': 0}

    def changer_statut_devis(self, devis_id: int, nouveau_statut: str, employee_id: int, commentaires: str = "") -> bool:
        """Change le statut d'un devis avec traçabilité."""
        try:
            result = self.db.execute_query("SELECT statut FROM formulaires WHERE id = ?", (devis_id,))
            if not result:
                st.error(f"Devis #{devis_id} non trouvé.")
                return False
            
            ancien_statut = result[0]['statut']
            
            # Mettre à jour le statut
            affected = self.db.execute_update(
                "UPDATE formulaires SET statut = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (nouveau_statut, devis_id)
            )
            
            if affected > 0:
                # Enregistrer le changement
                self.enregistrer_validation(
                    devis_id, employee_id, 'CHANGEMENT_STATUT',
                    f"Statut changé de {ancien_statut} vers {nouveau_statut}. {commentaires}"
                )
                
                # Actions spéciales selon le nouveau statut
                if nouveau_statut == 'APPROUVÉ':
                    self.on_devis_accepte(devis_id)
                elif nouveau_statut == 'EXPIRÉ':
                    self.on_devis_expire(devis_id)
                
                return True
            return False
        except Exception as e:
            st.error(f"Erreur changement statut devis: {e}")
            return False

    def on_devis_accepte(self, devis_id: int):
        """Actions à effectuer quand un devis est accepté. TRANSFORME LE DEVIS EN PROJET."""
        if not self.project_manager:
            st.error("❌ Le gestionnaire de projets n'est pas disponible. Transformation impossible.")
            return

        try:
            devis = self.get_devis_complet(devis_id)
            
            if not devis:
                st.error(f"❌ Devis #{devis_id} non trouvé. Transformation annulée.")
                return
            
            if devis.get('project_id'):
                st.warning(f"ℹ️ Un projet (#{devis['project_id']}) est déjà lié à ce devis. Aucune action effectuée.")
                return

            # Préparation des données pour le nouveau projet
            project_data = {
                'nom_projet': f"Projet - Devis {devis.get('numero_document', devis_id)}",
                'client_company_id': devis.get('company_id'),
                'client_nom_cache': devis.get('client_nom'),
                'statut': 'À FAIRE',
                'priorite': devis.get('priorite', 'MOYEN'),
                'description': f"Projet créé automatiquement suite à l'acceptation du devis {devis.get('numero_document')}.\n\nNotes du devis:\n{devis.get('notes', '')}",
                'prix_estime': devis.get('totaux', {}).get('total_ht', 0.0),
                'date_soumis': datetime.now().strftime('%Y-%m-%d'),
                'date_prevu': (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d'),
                'employes_assignes': [devis.get('employee_id')] if devis.get('employee_id') else [],
                'tache': 'PROJET_CLIENT',
                'bd_ft_estime': 0.0,
                'client_legacy': '',
                # Ces listes sont pour la compatibilité, les données seront ajoutées après
                'operations': [],
                'materiaux': []
            }
            
            # Création du projet via le gestionnaire de projets
            st.info(f"⏳ Transformation du devis #{devis_id} en projet...")
            project_id = self.project_manager.ajouter_projet(project_data)
            
            if project_id:
                # ======================================================================
                # NOUVEAU : Boucle pour transférer les lignes du devis en matériaux
                # ======================================================================
                lignes_devis = devis.get('lignes', [])
                materiaux_ajoutes = 0
                if lignes_devis:
                    for ligne in lignes_devis:
                        material_data = {
                            'code': ligne.get('code_article'),
                            'designation': ligne.get('description'),
                            'quantite': ligne.get('quantite'),
                            'unite': ligne.get('unite'),
                            'prix_unitaire': ligne.get('prix_unitaire'),
                            'fournisseur': None # Peut être enrichi plus tard
                        }
                        # Utilise la nouvelle méthode de erp_database.py
                        if self.db.add_material_to_project(project_id, material_data):
                            materiaux_ajoutes += 1
                
                st.success(f"✅ Devis transformé avec succès en Projet #{project_id} avec {materiaux_ajoutes} matériau(x) ajouté(s) !")
                # ======================================================================
                
                # Lier le nouveau projet au devis
                self.db.execute_update("UPDATE formulaires SET project_id = ? WHERE id = ?", (project_id, devis_id))
                
                # Enregistrer l'action dans l'historique du devis
                self.enregistrer_validation(
                    devis_id, devis.get('employee_id', 1), 'TERMINAISON',
                    f"Devis transformé en Projet #{project_id}."
                )
                st.balloons()
            else:
                st.error("❌ Échec de la création du projet. La transformation a été annulée.")

        except Exception as e:
            st.error(f"Erreur lors de la transformation du devis en projet: {e}")

    def on_devis_expire(self, devis_id: int):
        """Actions à effectuer quand un devis expire."""
        try:
            st.info(f"Le devis #{devis_id} est maintenant marqué comme expiré.")
        except Exception as e:
            st.error(f"Erreur expiration devis: {e}")

    def enregistrer_validation(self, devis_id: int, employee_id: int, type_validation: str, commentaires: str):
        """Enregistre une validation dans l'historique du devis."""
        try:
            query = '''
                INSERT INTO formulaire_validations
                (formulaire_id, employee_id, type_validation, commentaires)
                VALUES (?, ?, ?, ?)
            '''
            self.db.execute_insert(query, (devis_id, employee_id, type_validation, commentaires))
        except Exception as e:
            st.error(f"Erreur enregistrement validation devis: {e}")

    def get_all_devis(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Récupère tous les devis avec filtres optionnels."""
        try:
            query = f'''
                SELECT f.id, f.numero_document, f.statut, f.priorite, f.date_creation, 
                       f.date_echeance,
                       c.nom as client_nom,
                       e.prenom || ' ' || e.nom as responsable_nom,
                       p.nom_projet
                FROM formulaires f
                LEFT JOIN companies c ON f.company_id = c.id
                LEFT JOIN employees e ON f.employee_id = e.id
                LEFT JOIN projects p ON f.project_id = p.id
                WHERE (f.type_formulaire = 'DEVIS' OR (f.type_formulaire = 'ESTIMATION' AND f.metadonnees_json LIKE '%"type_reel": "DEVIS"%'))
            '''
            
            params = []
            
            if filters:
                if filters.get('statut') and filters['statut'] != 'Tous':
                    query += " AND f.statut = ?"
                    params.append(filters['statut'])
                
                if filters.get('client_id'):
                    query += " AND f.company_id = ?"
                    params.append(filters['client_id'])
                
                if filters.get('responsable_id'):
                    query += " AND f.employee_id = ?"
                    params.append(filters['responsable_id'])
                
                if filters.get('date_debut'):
                    query += " AND DATE(f.date_creation) >= ?"
                    params.append(filters['date_debut'])
                
                if filters.get('date_fin'):
                    query += " AND DATE(f.date_creation) <= ?"
                    params.append(filters['date_fin'])
            
            query += " ORDER BY f.date_creation DESC"
            
            rows = self.db.execute_query(query, tuple(params) if params else None)
            
            # Enrichir avec les totaux
            devis_list = []
            for row in rows:
                devis = dict(row)
                devis['totaux'] = self.calculer_totaux_devis(devis['id'])
                devis_list.append(devis)
            
            return devis_list
        except Exception as e:
            st.error(f"Erreur récupération liste devis: {e}")
            return []

    def get_devis_statistics(self) -> Dict[str, Any]:
        """Statistiques des devis."""
        try:
            stats = {
                'total_devis': 0,
                'par_statut': {},
                'montant_total': 0.0,
                'taux_acceptation': 0.0,
                'devis_expires': 0,
                'en_attente': 0
            }
            
            all_devis = self.get_all_devis()
            
            stats['total_devis'] = len(all_devis)
            
            for devis in all_devis:
                statut = devis['statut']
                if statut not in stats['par_statut']:
                    stats['par_statut'][statut] = {'count': 0, 'montant': 0.0}
                
                stats['par_statut'][statut]['count'] += 1
                stats['par_statut'][statut]['montant'] += devis.get('totaux', {}).get('total_ht', 0.0)
                stats['montant_total'] += devis.get('totaux', {}).get('total_ht', 0.0)
            
            # Taux d'acceptation
            accepted_count = stats['par_statut'].get('ACCEPTÉ', {}).get('count', 0)
            refused_count = stats['par_statut'].get('REFUSÉ', {}).get('count', 0)
            expired_count = stats['par_statut'].get('EXPIRÉ', {}).get('count', 0)
            
            total_decides = accepted_count + refused_count + expired_count
            
            if total_decides > 0:
                stats['taux_acceptation'] = (accepted_count / total_decides) * 100
            
            # Devis expirés
            query_expires = '''
                SELECT COUNT(*) as count FROM formulaires 
                WHERE (type_formulaire = 'DEVIS' OR (type_formulaire = 'ESTIMATION' AND metadonnees_json LIKE '%"type_reel": "DEVIS"%'))
                AND date_echeance < DATE('now') 
                AND statut NOT IN ('ACCEPTÉ', 'REFUSÉ', 'EXPIRÉ', 'ANNULÉ')
            '''
            result = self.db.execute_query(query_expires)
            stats['devis_expires'] = result[0]['count'] if result else 0
            
            # En attente
            stats['en_attente'] = stats['par_statut'].get('ENVOYÉ', {}).get('count', 0) + \
                                 stats['par_statut'].get('BROUILLON', {}).get('count', 0)
            
            return stats
        except Exception as e:
            st.error(f"Erreur statistiques devis: {e}")
            return {}

    def dupliquer_devis(self, devis_id: int, employee_id: int) -> Optional[int]:
        """Duplique un devis existant."""
        try:
            devis_original = self.get_devis_complet(devis_id)
            if not devis_original:
                st.error("Devis original non trouvé pour duplication.")
                return None
            
            # Créer nouveau devis basé sur l'original
            nouveau_devis_data = {
                'client_company_id': devis_original['company_id'],
                'client_contact_id': devis_original.get('client_contact_id'),
                'project_id': devis_original.get('project_id'),
                'employee_id': employee_id,
                'date_echeance': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'notes': f"Copie de {devis_original['numero_document']} - {devis_original.get('notes', '')}",
                'lignes': devis_original['lignes']
            }
            
            nouveau_id = self.create_devis(nouveau_devis_data)
            
            if nouveau_id:
                self.enregistrer_validation(
                    nouveau_id, employee_id, 'CREATION',
                    f"Devis dupliqué depuis #{devis_id} ({devis_original['numero_document']})"
                )
            
            return nouveau_id
        except Exception as e:
            st.error(f"Erreur duplication devis: {e}")
            return None

    # --- EXPORT HTML ---
    
    def export_devis_html(self, devis_id: int) -> Optional[str]:
        """Exporte un devis au format HTML professionnel pour les clients."""
        try:
            devis_data = self.get_devis_complet(devis_id)
            if not devis_data:
                st.error(f"Devis #{devis_id} non trouvé pour export")
                return None
            
            html_content = self.generate_devis_html_template(devis_data)
            return html_content
        except Exception as e:
            st.error(f"Erreur export HTML devis: {e}")
            return None
    
    def generate_devis_html_template(self, devis_data: Dict[str, Any]) -> str:
        """Génère le template HTML pour un devis avec design moderne professionnel."""
        try:
            # Formatage des dates
            date_creation = devis_data.get('date_creation', '')
            if date_creation:
                try:
                    date_creation_formatted = datetime.fromisoformat(date_creation).strftime('%d/%m/%Y')
                except:
                    date_creation_formatted = date_creation[:10] if len(date_creation) >= 10 else date_creation
            else:
                date_creation_formatted = 'N/A'
            
            date_echeance = devis_data.get('date_echeance', '')
            try:
                date_echeance_formatted = datetime.fromisoformat(date_echeance).strftime('%d/%m/%Y') if date_echeance else 'N/A'
            except:
                date_echeance_formatted = date_echeance
            
            # Récupération des totaux
            totaux = devis_data.get('totaux', {})
            total_ht = totaux.get('total_ht', 0)
            taux_tva = totaux.get('taux_tva', 14.975)
            montant_tva = totaux.get('montant_tva', 0)
            total_ttc = totaux.get('total_ttc', 0)
            
            # Formatage du statut pour les badges
            statut = devis_data.get('statut', 'BROUILLON')
            statut_class = {
                'BROUILLON': 'badge-pending',
                'VALIDÉ': 'badge-in-progress',
                'ENVOYÉ': 'badge-in-progress',
                'APPROUVÉ': 'badge-completed',
                'TERMINÉ': 'badge-completed',
                'ANNULÉ': 'badge-on-hold',
                'EXPIRÉ': 'badge-on-hold'
            }.get(statut, 'badge-pending')
            
            priorite = devis_data.get('priorite', 'NORMAL')
            priorite_class = {
                'FAIBLE': 'badge-pending',
                'NORMAL': 'badge-in-progress',
                'ÉLEVÉE': 'badge-on-hold',
                'URGENT': 'badge-on-hold'
            }.get(priorite, 'badge-in-progress')
            
            # Génération des lignes du tableau
            lignes_html = ""
            nb_lignes = 0
            if devis_data.get('lignes'):
                for ligne in devis_data['lignes']:
                    nb_lignes += 1
                    montant_ligne = ligne.get('quantite', 0) * ligne.get('prix_unitaire', 0)
                    code_article = ligne.get('code_article', '')
                    code_display = f"<br><small>Code: {code_article}</small>" if code_article else ""
                    
                    lignes_html += f"""
                    <tr>
                        <td><strong>{ligne.get('description', '')}</strong>{code_display}</td>
                        <td style="text-align: center;">{ligne.get('quantite', 0):,.2f}</td>
                        <td style="text-align: center;">{ligne.get('unite', '')}</td>
                        <td style="text-align: right;">{ligne.get('prix_unitaire', 0):,.2f} $</td>
                        <td style="text-align: right;"><strong>{montant_ligne:,.2f} $</strong></td>
                    </tr>
                    """
            else:
                lignes_html = """
                <tr>
                    <td colspan="5" style="text-align: center; color: #6B7280;">Aucune ligne dans ce devis</td>
                </tr>
                """
            
            # Adresse client formatée
            adresse_client = devis_data.get('client_adresse_complete', f"""
{devis_data.get('client_nom', 'N/A')}<br>
{devis_data.get('adresse', '')}<br>
{devis_data.get('ville', '')}, {devis_data.get('province', '')} {devis_data.get('code_postal', '')}<br>
{devis_data.get('pays', '')}
            """).strip()
            
            # Template HTML modernisé basé sur le design de la demande de prix
            html_template = f"""
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Devis - {devis_data.get('numero_document', 'N/A')}</title>
                <style>
                    :root {{
                        --primary-color: #3B82F6;
                        --primary-color-darker: #2563EB;
                        --primary-color-darkest: #1D4ED8;
                        --primary-color-lighter: #DBEAFE;
                        --background-color: #FAFBFF;
                        --secondary-background-color: #FFFFFF;
                        --text-color: #374151;
                        --text-color-light: #6B7280;
                        --border-color: #E5E7EB;
                        --border-radius-md: 0.5rem;
                        --box-shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
                    }}
                    
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}
                    
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        color: var(--text-color);
                        background-color: var(--background-color);
                        margin: 0;
                        padding: 15px;
                    }}
                    
                    .container {{
                        max-width: 8.5in;
                        margin: 0 auto;
                        background-color: white;
                        border-radius: 12px;
                        box-shadow: var(--box-shadow-md);
                        overflow: hidden;
                        width: 100%;
                    }}
                    
                    .header {{
                        background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-color-darker) 100%);
                        color: white;
                        padding: 30px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }}
                    
                    .logo-container {{
                        display: flex;
                        align-items: center;
                        gap: 20px;
                    }}
                    
                    .logo-box {{
                        background-color: white;
                        width: 70px;
                        height: 45px;
                        border-radius: 8px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
                    }}
                    
                    .logo-text {{
                        font-family: 'Segoe UI', sans-serif;
                        font-weight: 800;
                        font-size: 24px;
                        color: var(--primary-color);
                        letter-spacing: 1px;
                    }}
                    
                    .company-info {{
                        text-align: left;
                    }}
                    
                    .company-name {{
                        font-weight: 700;
                        font-size: 28px;
                        margin-bottom: 5px;
                        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                    }}
                    
                    .company-subtitle {{
                        font-size: 16px;
                        opacity: 0.9;
                    }}
                    
                    .contact-info {{
                        text-align: right;
                        font-size: 14px;
                        line-height: 1.4;
                        opacity: 0.95;
                    }}
                    
                    .document-title {{
                        background: var(--primary-color-lighter);
                        padding: 20px 30px;
                        border-left: 5px solid var(--primary-color);
                    }}
                    
                    .document-title h1 {{
                        color: var(--primary-color-darker);
                        font-size: 24px;
                        margin-bottom: 10px;
                    }}
                    
                    .document-meta {{
                        display: flex;
                        justify-content: space-between;
                        color: var(--text-color-light);
                        font-size: 14px;
                    }}
                    
                    .content {{
                        padding: 25px;
                    }}
                    
                    .section {{
                        margin-bottom: 30px;
                    }}
                    
                    .section-title {{
                        color: var(--primary-color-darker);
                        font-size: 18px;
                        font-weight: 600;
                        margin-bottom: 15px;
                        padding-bottom: 8px;
                        border-bottom: 2px solid var(--primary-color-lighter);
                        display: flex;
                        align-items: center;
                        gap: 10px;
                    }}
                    
                    .info-grid {{
                        display: grid;
                        grid-template-columns: 1fr 1fr 1fr;
                        gap: 15px;
                        margin-bottom: 20px;
                    }}
                    
                    .info-item {{
                        background: var(--background-color);
                        padding: 15px;
                        border-radius: var(--border-radius-md);
                        border-left: 3px solid var(--primary-color);
                    }}
                    
                    .info-label {{
                        font-weight: 600;
                        color: var(--text-color-light);
                        font-size: 12px;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        margin-bottom: 5px;
                    }}
                    
                    .info-value {{
                        font-size: 16px;
                        color: var(--text-color);
                        font-weight: 500;
                    }}
                    
                    .table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 15px 0;
                        border-radius: var(--border-radius-md);
                        overflow: hidden;
                        box-shadow: var(--box-shadow-md);
                    }}
                    
                    .table th {{
                        background: var(--primary-color);
                        color: white;
                        padding: 12px;
                        text-align: left;
                        font-weight: 600;
                        font-size: 14px;
                    }}
                    
                    .table td {{
                        padding: 12px;
                        border-bottom: 1px solid var(--border-color);
                        vertical-align: top;
                    }}
                    
                    .table tr:nth-child(even) {{
                        background-color: var(--background-color);
                    }}
                    
                    .table tr:hover {{
                        background-color: var(--primary-color-lighter);
                    }}
                    
                    .badge {{
                        padding: 4px 12px;
                        border-radius: 20px;
                        font-size: 11px;
                        font-weight: 600;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        display: inline-block;
                    }}
                    
                    .badge-pending {{ background: #fef3c7; color: #92400e; }}
                    .badge-in-progress {{ background: #dbeafe; color: #1e40af; }}
                    .badge-completed {{ background: #d1fae5; color: #065f46; }}
                    .badge-on-hold {{ background: #fee2e2; color: #991b1b; }}
                    
                    .summary-box {{
                        background: linear-gradient(45deg, var(--primary-color-lighter), white);
                        border: 2px solid var(--primary-color);
                        border-radius: var(--border-radius-md);
                        padding: 20px;
                        margin: 20px 0;
                    }}
                    
                    .summary-grid {{
                        display: grid;
                        grid-template-columns: repeat(3, 1fr);
                        gap: 15px;
                    }}
                    
                    .summary-item {{
                        text-align: center;
                        background: white;
                        padding: 15px;
                        border-radius: var(--border-radius-md);
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    
                    .summary-number {{
                        font-size: 24px;
                        font-weight: 700;
                        color: var(--primary-color-darker);
                        display: block;
                    }}
                    
                    .summary-label {{
                        font-size: 12px;
                        color: var(--text-color-light);
                        text-transform: uppercase;
                        font-weight: 600;
                        letter-spacing: 0.5px;
                    }}
                    
                    .totals-box {{
                        background: var(--primary-color-darkest);
                        color: white;
                        padding: 20px;
                        border-radius: var(--border-radius-md);
                        margin: 20px 0;
                    }}
                    
                    .totals-grid {{
                        display: grid;
                        grid-template-columns: repeat(3, 1fr);
                        gap: 15px;
                    }}
                    
                    .total-item {{
                        text-align: center;
                        background: rgba(255, 255, 255, 0.1);
                        padding: 15px;
                        border-radius: var(--border-radius-md);
                    }}
                    
                    .total-amount {{
                        font-size: 22px;
                        font-weight: 700;
                        display: block;
                        margin-bottom: 5px;
                    }}
                    
                    .total-label {{
                        font-size: 12px;
                        opacity: 0.9;
                        text-transform: uppercase;
                        font-weight: 600;
                        letter-spacing: 0.5px;
                    }}
                    
                    .instructions-box {{
                        background: var(--background-color);
                        border-left: 4px solid var(--primary-color);
                        padding: 20px;
                        border-radius: 0 var(--border-radius-md) var(--border-radius-md) 0;
                        margin: 15px 0;
                    }}
                    
                    .footer {{
                        background: var(--primary-color-darkest);
                        color: white;
                        padding: 20px 30px;
                        text-align: center;
                        font-size: 12px;
                        line-height: 1.4;
                    }}
                    
                    .client-address {{
                        background: var(--background-color);
                        border: 2px solid var(--primary-color-lighter);
                        border-radius: var(--border-radius-md);
                        padding: 15px;
                        margin: 15px 0;
                        font-size: 14px;
                        line-height: 1.4;
                    }}
                    
                    @media print {{
                        body {{ 
                            margin: 0; 
                            padding: 0; 
                        }}
                        .container {{ 
                            box-shadow: none; 
                            max-width: 100%;
                            width: 8.5in;
                        }}
                        .table {{ 
                            break-inside: avoid; 
                            font-size: 12px;
                        }}
                        .section {{ 
                            break-inside: avoid-page; 
                        }}
                        .header {{
                            padding: 20px 25px;
                        }}
                        .content {{
                            padding: 20px;
                        }}
                        @page {{
                            size: letter;
                            margin: 0.5in;
                        }}
                    }}
                    
                    @media screen and (max-width: 768px) {{
                        .container {{
                            max-width: 100%;
                            margin: 0 10px;
                        }}
                        .info-grid {{
                            grid-template-columns: 1fr;
                            gap: 10px;
                        }}
                        .summary-grid, .totals-grid {{
                            grid-template-columns: repeat(2, 1fr);
                        }}
                        .header {{
                            flex-direction: column;
                            text-align: center;
                            gap: 15px;
                        }}
                        .contact-info {{
                            text-align: center;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <!-- En-tête -->
                    <div class="header">
                        <div class="logo-container">
                            <div class="logo-box">
                                <div class="logo-text">CA</div>
                            </div>
                            <div class="company-info">
                                <div class="company-name">Constructo AI</div>
                                <div class="company-subtitle">Construction résidentiel et commercial</div>
                            </div>
                        </div>
                        <div class="contact-info">
                            1760 rue Jacques-Cartier Sud<br>
                            Farnham, QC J2N 1Y8<br>
                            Tél.: (514) 820-1972<br>
                            Téléc.: (514) 820-1973
                        </div>
                    </div>
                    
                    <!-- Titre du document -->
                    <div class="document-title">
                        <h1>💰 DEVIS COMMERCIAL</h1>
                        <div class="document-meta">
                            <span><strong>N° Devis:</strong> {devis_data.get('numero_document', 'N/A')}</span>
                            <span><strong>Généré le:</strong> {datetime.now().strftime('%d/%m/%Y à %H:%M')}</span>
                        </div>
                    </div>
                    
                    <!-- Contenu principal -->
                    <div class="content">
                        <!-- Informations générales -->
                        <div class="section">
                            <h2 class="section-title">📋 Informations du Devis</h2>
                            <div class="info-grid">
                                <div class="info-item">
                                    <div class="info-label">Client</div>
                                    <div class="info-value">{devis_data.get('client_nom', 'N/A')}</div>
                                </div>
                                <div class="info-item">
                                    <div class="info-label">Statut</div>
                                    <div class="info-value">
                                        <span class="badge {statut_class}">
                                            {statut}
                                        </span>
                                    </div>
                                </div>
                                <div class="info-item">
                                    <div class="info-label">Priorité</div>
                                    <div class="info-value">
                                        <span class="badge {priorite_class}">
                                            {priorite}
                                        </span>
                                    </div>
                                </div>
                                <div class="info-item">
                                    <div class="info-label">Date Création</div>
                                    <div class="info-value">{date_creation_formatted}</div>
                                </div>
                                <div class="info-item">
                                    <div class="info-label">Date Échéance</div>
                                    <div class="info-value">{date_echeance_formatted}</div>
                                </div>
                                <div class="info-item">
                                    <div class="info-label">Responsable</div>
                                    <div class="info-value">{devis_data.get('responsable_nom', 'N/A')}</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Adresse du client -->
                        <div class="section">
                            <h2 class="section-title">📍 Adresse de Facturation</h2>
                            <div class="client-address">
                                {adresse_client}
                            </div>
                        </div>
                        
                        <!-- Résumé -->
                        <div class="summary-box">
                            <h3 style="color: var(--primary-color-darker); margin-bottom: 15px; text-align: center;">📋 Résumé du Devis</h3>
                            <div class="summary-grid">
                                <div class="summary-item">
                                    <span class="summary-number">{nb_lignes}</span>
                                    <span class="summary-label">Articles</span>
                                </div>
                                <div class="summary-item">
                                    <span class="summary-number">{priorite}</span>
                                    <span class="summary-label">Priorité</span>
                                </div>
                                <div class="summary-item">
                                    <span class="summary-number">{date_echeance_formatted}</span>
                                    <span class="summary-label">Échéance</span>
                                </div>
                            </div>
                        </div>
                
                        <!-- Détail des articles -->
                        <div class="section">
                            <h2 class="section-title">📝 Détail des Prestations</h2>
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Description</th>
                                        <th style="text-align: center;">Quantité</th>
                                        <th style="text-align: center;">Unité</th>
                                        <th style="text-align: center;">Prix Unit.</th>
                                        <th style="text-align: center;">Montant</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {lignes_html}
                                </tbody>
                            </table>
                        </div>
                
                        <!-- Totaux -->
                        <div class="totals-box">
                            <h3 style="text-align: center; margin-bottom: 15px;">💰 Récapitulatif Financier</h3>
                            <div class="totals-grid">
                                <div class="total-item">
                                    <span class="total-amount">{total_ht:,.2f} $</span>
                                    <span class="total-label">Sous-total HT</span>
                                </div>
                                <div class="total-item">
                                    <span class="total-amount">{montant_tva:,.2f} $</span>
                                    <span class="total-label">TVA ({taux_tva:.3f}%)</span>
                                </div>
                                <div class="total-item">
                                    <span class="total-amount">{total_ttc:,.2f} $</span>
                                    <span class="total-label">Total TTC</span>
                                </div>
                            </div>
                        </div>
                
                        <!-- Notes du devis -->
                        {f'''
                        <div class="section">
                            <h2 class="section-title">📝 Notes et Conditions</h2>
                            <div class="instructions-box">
                                {devis_data.get('notes', 'Aucune note particulière.')}
                            </div>
                        </div>
                        ''' if devis_data.get('notes') and devis_data['notes'].strip() else ''}
                        
                        <!-- Instructions -->
                        <div class="instructions-box">
                            <h4 style="color: var(--primary-color-darker); margin-bottom: 10px;">📋 Conditions Générales</h4>
                            <p><strong>• Validité :</strong> Ce devis est valable 30 jours à compter de la date d'émission</p>
                            <p><strong>• Paiement :</strong> Net 30 jours sur réception de facture</p>
                            <p><strong>• Délais :</strong> Les délais de livraison seront confirmés lors de l'acceptation</p>
                            <p><strong>• Acceptation :</strong> Ce devis engage nos services uniquement après acceptation écrite</p>
                            <p><strong>• Contact :</strong> Pour toute question : (514) 820-1972</p>
                        </div>
                        
                    </div>
                    
                    <!-- Pied de page -->
                    <div class="footer">
                        <div><strong>🏗️ Constructo AI</strong> - Devis Commercial</div>
                        <div>Document généré automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</div>
                        <div>📞 (514) 820-1972 | 📧 info@constructo-ai.com | 🌐 www.constructo-ai.com</div>
                        <div style="margin-top: 10px; font-size: 11px; opacity: 0.8;">
                            Merci de mentionner le numéro de devis {devis_data.get('numero_document', 'N/A')} dans votre réponse.
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return html_template
        except Exception as e:
            st.error(f"Erreur génération template HTML: {e}")
            return ""

    def check_devis_id_exists(self, devis_id: str) -> bool:
        """Vérifie si un ID de devis personnalisé existe déjà."""
        try:
            result = self.db.execute_query("SELECT id FROM formulaires WHERE numero_document = ? AND type_formulaire IN ('DEVIS', 'QUOTE')", (devis_id,))
            return len(result) > 0
        except Exception as e:
            st.error(f"Erreur vérification ID devis: {e}")
            return False

    def create_devis_complet(self, devis_data: Dict[str, Any]) -> Optional[int]:
        """Crée un nouveau devis complet avec toutes les informations du formulaire projet."""
        try:
            # Générer le numéro de devis
            if devis_data.get('numero_document'):
                numero_devis = devis_data['numero_document']
            else:
                numero_devis = self.generer_numero_devis()
            
            type_formulaire_db = self._devis_type_db
            mode_info = " (mode compatibilité)" if self._devis_compatibility_mode else ""
            
            # Métadonnées étendues avec les nouvelles informations
            metadonnees = {
                'type_reel': 'DEVIS',
                'type_devis': 'COMPLET',  # Nouveau type pour les devis complets
                'tva_applicable': True,
                'taux_tva': 14.975,
                'taux_tps': 5.0,
                'taux_tvq': 9.975,
                'devise': 'CAD',
                'validite_jours': 30,
                'type_client': 'PARTICULIER',
                'secteur_construction': 'RÉSIDENTIEL',
                'created_by_module': 'DEVIS_COMPLET',
                'compatibility_mode': self._devis_compatibility_mode,
                # Nouvelles métadonnées du projet
                'po_client': devis_data.get('po_client', ''),
                'tache': devis_data.get('tache', ''),
                'date_debut': devis_data.get('date_debut', ''),
                'bd_ft': devis_data.get('bd_ft', 0),
                'prix_estime': devis_data.get('prix_estime', 0),
                'employes_assignes': devis_data.get('employes_assignes', []),
                'client_nom_cache': devis_data.get('client_nom_cache', '')
            }
            
            # Ajouter le nom du devis dans les métadonnées puisque la colonne n'existe pas
            metadonnees['nom_devis'] = devis_data.get('nom', '')
            
            # Validation des clés étrangères avant insertion
            client_company_id = devis_data.get('client_company_id')
            if client_company_id:
                # Vérifier que l'entreprise existe
                company_exists = self.db.execute_query("SELECT id FROM companies WHERE id = ?", (client_company_id,))
                if not company_exists:
                    st.error(f"Entreprise client #{client_company_id} introuvable.")
                    return None
            else:
                client_company_id = None  # Permettre NULL si pas de client entreprise
            
            # Trouver un employé valide ou utiliser None
            employee_id = 1
            employee_exists = self.db.execute_query("SELECT id FROM employees WHERE id = ? AND statut = 'ACTIF'", (employee_id,))
            if not employee_exists:
                # Trouver le premier employé actif
                first_employee = self.db.execute_query("SELECT id FROM employees WHERE statut = 'ACTIF' LIMIT 1")
                if first_employee:
                    employee_id = first_employee[0]['id']
                else:
                    st.error("Aucun employé actif trouvé. Veuillez créer un employé d'abord.")
                    return None
            
            # Insertion principale avec les valeurs validées
            devis_id = self.db.execute_insert('''
                INSERT INTO formulaires 
                (type_formulaire, numero_document, project_id, company_id, employee_id,
                 statut, priorite, date_echeance, notes, metadonnees_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                type_formulaire_db, numero_devis, None,  # project_id sera None pour les devis
                client_company_id, employee_id,
                devis_data.get('statut', 'BROUILLON'), devis_data.get('priorite', 'NORMAL'),
                devis_data.get('date_echeance'), devis_data.get('description', ''), 
                json.dumps(metadonnees)
            ))
            
            if devis_id:
                # Ajouter les lignes de produits/services
                if devis_data.get('lignes'):
                    for i, ligne in enumerate(devis_data['lignes'], 1):
                        self.ajouter_ligne_devis(devis_id, i, ligne)
                
                # Enregistrer les employés assignés dans une table de liaison (si elle existe)
                if devis_data.get('employes_assignes'):
                    try:
                        # Tenter d'insérer dans une table de liaison (optionnel)
                        for emp_id in devis_data['employes_assignes']:
                            try:
                                self.db.execute_insert(
                                    "INSERT OR IGNORE INTO project_employees (project_id, employee_id, role) VALUES (?, ?, 'ASSIGNED')",
                                    (devis_id, emp_id)
                                )
                            except:
                                pass  # Table peut ne pas exister, ignore silencieusement
                    except:
                        pass
                
                # Enregistrer la validation
                self.enregistrer_validation(
                    devis_id, 1, 'CREATION', 
                    f"Devis complet créé: {numero_devis}{mode_info} - Projet: {devis_data.get('nom', '')}"
                )
                
                return devis_id
            return None
        except Exception as e:
            st.error(f"Erreur création devis complet: {e}")
            return None


# --- FONCTIONS UI (Déplacées de crm.py) ---

def render_devis_liste(gestionnaire: GestionnaireDevis):
    """Affiche la liste des devis avec différents modes d'affichage."""
    st.subheader("Liste des Devis")
    
    # Filtres
    col_filtre1, col_filtre2, col_filtre3 = st.columns(3)
    
    with col_filtre1:
        filtre_statut = st.selectbox("Statut", 
            options=["Tous"] + STATUTS_DEVIS,
            key="filtre_statut_devis"
        )
    
    with col_filtre2:
        # Liste des clients
        clients = gestionnaire.crm_manager.entreprises
        client_options = [("", "Tous les clients")] + [(c['id'], c['nom']) for c in clients]
        filtre_client = st.selectbox("Client",
            options=[opt[0] for opt in client_options],
            format_func=lambda x: next((opt[1] for opt in client_options if opt[0] == x), "Tous les clients"),
            key="filtre_client_devis"
        )
    
    with col_filtre3:
        # Période
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            date_debut = st.date_input("Du", value=None, key="date_debut_devis")
        with col_date2:
            date_fin = st.date_input("Au", value=None, key="date_fin_devis")
    
    # Construire les filtres
    filters = {}
    if filtre_statut != "Tous":
        filters['statut'] = filtre_statut
    if filtre_client:
        filters['client_id'] = filtre_client
    if date_debut:
        filters['date_debut'] = date_debut.strftime('%Y-%m-%d')
    if date_fin:
        filters['date_fin'] = date_fin.strftime('%Y-%m-%d')
    
    # Récupérer les devis
    devis_list = gestionnaire.get_all_devis(filters)
    
    if devis_list:
        # Calculer les statistiques de résumé
        total_devis = len(devis_list)
        devis_brouillons = len([d for d in devis_list if d['statut'] == 'BROUILLON'])
        devis_envoyes = len([d for d in devis_list if d['statut'] == 'ENVOYÉ'])
        ca_total = sum(d['totaux']['total_ttc'] for d in devis_list)
        
        # Afficher les métriques de résumé
        st.markdown("---")
        result_col1, result_col2, result_col3, result_col4 = st.columns(4)
        with result_col1:
            st.markdown(f"**📋 {total_devis} devis trouvés**")
        with result_col2:
            st.markdown(f"**📝 {devis_brouillons} brouillons**") 
        with result_col3:
            st.markdown(f"**📧 {devis_envoyes} envoyés**")
        with result_col4:
            st.markdown(f"**💰 CA total: {ca_total:,.2f}$**")
        
        # Mode d'affichage
        view_mode = st.radio(
            "Mode d'affichage:", 
            ["📋 Liste Détaillée", "📊 Tableau Compact", "🃏 Cartes Compactes"], 
            horizontal=True,
            index=["📋 Liste Détaillée", "📊 Tableau Compact", "🃏 Cartes Compactes"].index(
                st.session_state.get('devis_view_mode', "📋 Liste Détaillée")
            ),
            key="devis_view_mode_input"
        )
        st.session_state.devis_view_mode = view_mode
        
        if view_mode == "📊 Tableau Compact":
            show_devis_table_view(devis_list, gestionnaire)
        elif view_mode == "🃏 Cartes Compactes":
            show_devis_card_view(devis_list, gestionnaire)
        else:
            show_devis_detailed_list(devis_list, gestionnaire)
    
    else:
        st.info("Aucun devis trouvé avec les critères sélectionnés.")


def show_devis_detailed_list(devis_list, gestionnaire):
    """Affiche les devis en mode liste détaillée avec actions en ligne."""
    for i, devis in enumerate(devis_list):
        # Conteneur pour chaque devis
        with st.container(border=True):
            col_main, col_actions = st.columns([3, 1])
            
            with col_main:
                # En-tête du devis
                col_info1, col_info2, col_info3 = st.columns(3)
                
                with col_info1:
                    statut_color = {"BROUILLON": "🟡", "VALIDÉ": "🟢", "ENVOYÉ": "🔵", 
                                  "APPROUVÉ": "✅", "TERMINÉ": "⚪", "ANNULÉ": "🔴"}.get(devis['statut'], "⚫")
                    st.markdown(f"**{statut_color} {devis['numero_document']}**")
                    st.caption(f"Client: {devis['client_nom']}")
                
                with col_info2:
                    st.markdown(f"**Statut:** {devis['statut']}")
                    st.caption(f"Créé: {devis['date_creation'][:10] if devis.get('date_creation') else 'N/A'}")
                
                with col_info3:
                    st.markdown(f"**Total TTC:** {devis['totaux']['total_ttc']:,.2f} $")
                    if devis.get('date_echeance'):
                        st.caption(f"Échéance: {devis['date_echeance']}")
                
                # Description courte
                if devis.get('description'):
                    st.caption(f"📝 {devis['description'][:100]}{'...' if len(devis.get('description', '')) > 100 else ''}")
            
            with col_actions:
                # Actions
                peut_supprimer = devis.get('statut') not in ['APPROUVÉ', 'TERMINÉ']
                
                if st.button("👁️ Voir", key=f"voir_devis_{devis['id']}", use_container_width=True):
                    st.session_state.devis_action = "view_details"
                    st.session_state.devis_selected_id = devis['id']
                    st.rerun()
                
                if st.button("📄 Dupliquer", key=f"dupliquer_devis_{devis['id']}", use_container_width=True):
                    nouveau_id = gestionnaire.dupliquer_devis(devis['id'], 1)
                    if nouveau_id:
                        st.success(f"Devis dupliqué! #{nouveau_id}")
                        st.rerun()
                
                if st.button("✏️ Modifier", key=f"edit_devis_{devis['id']}", use_container_width=True):
                    st.session_state.devis_action = "edit"
                    st.session_state.devis_selected_id = devis['id']
                    st.rerun()
                
                if peut_supprimer:
                    if st.button("🗑️ Supprimer", key=f"delete_devis_{devis['id']}", 
                               use_container_width=True, type="secondary"):
                        st.session_state.confirm_delete_devis_id = devis['id']
                        st.rerun()
        
        # Gestion de la confirmation de suppression pour tous les devis
        for devis in devis_list:
            if ('confirm_delete_devis_id' in st.session_state and 
                st.session_state.confirm_delete_devis_id == devis['id']):
                st.markdown("---")
                st.error(f"⚠️ Confirmer la suppression du devis #{devis['id']} - {devis['numero_document']}")
                
                motif = st.text_input("Motif de suppression (optionnel):", key=f"motif_detail_{devis['id']}")
                
                col_conf, col_ann = st.columns(2)
                with col_conf:
                    if st.button("🗑️ SUPPRIMER DÉFINITIVEMENT", key=f"confirm_delete_detail_{devis['id']}", type="primary"):
                        if gestionnaire.supprimer_devis(devis['id'], 1, motif):
                            del st.session_state.confirm_delete_devis_id
                            st.success("✅ Devis supprimé avec succès !")
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la suppression")
                with col_ann:
                    if st.button("❌ Annuler", key=f"cancel_delete_detail_{devis['id']}"):
                        del st.session_state.confirm_delete_devis_id
                        st.rerun()


def show_devis_table_view(devis_list, gestionnaire):
    """Affiche les devis en mode tableau compact avec les mêmes colonnes que les projets."""
    
    def format_currency(value):
        """Formate un montant en devise canadienne."""
        if value is None or value == 0:
            return "0,00 $"
        return f"{value:,.2f} $"
    
    def get_devis_client_name(devis):
        """Récupère le nom du client du devis."""
        if devis.get('client_nom'):
            return devis['client_nom']
        return 'N/A'
    
    # Préparer les données avec les mêmes colonnes que les projets
    df_data = []
    for devis in devis_list:
        client_display_name = get_devis_client_name(devis)
        
        # Calcul de la durée en jours (entre début et échéance)
        duree_jours = "N/A"
        try:
            # Récupérer les dates depuis les métadonnées
            metadonnees = {}
            if devis.get('metadonnees_json'):
                try:
                    metadonnees = json.loads(devis['metadonnees_json'])
                except:
                    pass
            
            date_debut = metadonnees.get('date_debut')
            date_echeance = devis.get('date_echeance')
            
            if date_debut and date_echeance:
                date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d')
                date_fin_obj = datetime.strptime(date_echeance, '%Y-%m-%d')
                duree = (date_fin_obj - date_debut_obj).days
                duree_jours = f"{duree}j"
        except:
            duree_jours = "N/A"
        
        # Récupération des informations depuis les métadonnées
        metadonnees = {}
        if devis.get('metadonnees_json'):
            try:
                metadonnees = json.loads(devis['metadonnees_json'])
            except:
                pass
        
        # Traitement des lignes de produits/services pour l'affichage
        devis_complet = gestionnaire.get_devis_complet(devis['id'])
        lignes_devis = devis_complet.get('lignes', []) if devis_complet else []
        
        produit_display = "Aucun"
        quantite_display = "N/A"
        unite_display = "N/A"
        code_article_display = "N/A"

        if lignes_devis:
            # Pour la colonne "Produits"
            descriptions = [ligne.get('description', 'N/A') for ligne in lignes_devis]
            if len(descriptions) > 1:
                produit_display = f"{descriptions[0]} (+{len(descriptions) - 1} autre(s))"
            elif len(descriptions) == 1:
                produit_display = descriptions[0]

            # Pour la colonne "Quantité" et "Unité"
            quantites = [str(ligne.get('quantite', '0')) for ligne in lignes_devis]
            unites = [ligne.get('unite', '') for ligne in lignes_devis]
            quantite_display = ", ".join(quantites)
            unite_display = ", ".join(list(set(unites))) # Affiche les unités uniques

            # Pour la colonne "Code Article"
            codes = [ligne.get('code_article', 'N/A') for ligne in lignes_devis if ligne.get('code_article')]
            if codes:
                code_article_display = ", ".join(codes)

        df_data.append({
            '🆔 ID': devis.get('id', '?'),
            '🚦 Statut': devis.get('statut', 'N/A'),
            '⭐ Priorité': devis.get('priorite', 'N/A'),
            '📋 No. Devis': devis.get('numero_document', 'N/A'),
            '🧾 No. PO Client': metadonnees.get('po_client', ''),
            '📝 Nom Devis': metadonnees.get('nom_devis', 'N/A')[:35] + ('...' if len(metadonnees.get('nom_devis', '')) > 35 else ''),
            '👤 Client': client_display_name[:25] + ('...' if len(client_display_name) > 25 else ''),
            '✅ Tâche': metadonnees.get('tache', 'N/A'),
            '💰 Prix Estimé': format_currency(devis['totaux']['total_ttc']),
            '📅 Début': metadonnees.get('date_debut', 'N/A'),
            '🏁 Échéance': devis.get('date_echeance', 'N/A'),
            
            # Colonnes produits
            '📦 Produit/Service': produit_display,
            '🔢 Quantité': quantite_display,
            '📏 Unité': unite_display,
            '#️⃣ Code Article': code_article_display
        })
    
    df_devis = pd.DataFrame(df_data)
    
    # Configuration du dataframe identique aux projets
    st.dataframe(
        df_devis, 
        use_container_width=True, 
        height=400,
        column_config={
            "🆔 ID": st.column_config.TextColumn(
                "🆔 ID",
                help="Identifiant unique du devis",
                width="small",
            ),
            "🚦 Statut": st.column_config.TextColumn(
                "🚦 Statut",
                help="Statut actuel du devis",
                width="medium",
            ),
            "📝 Nom Devis": st.column_config.TextColumn(
                "📝 Nom Devis",
                help="Nom complet du devis",
                width="large",
            ),
            "🧾 No. PO Client": st.column_config.TextColumn(
                "🧾 No. PO Client",
                help="Numéro de bon de commande du client",
                width="medium",
            ),
            "👤 Client": st.column_config.TextColumn(
                "👤 Client",
                help="Nom du client",
                width="medium",
            ),
            "💰 Prix Estimé": st.column_config.TextColumn(
                "💰 Prix Estimé",
                help="Prix total estimé du devis",
                width="medium",
            ),
            "📦 Produit/Service": st.column_config.TextColumn(
                "📦 Produit/Service",
                help="Produits ou services inclus dans le devis",
                width="large",
            ),
        },
        hide_index=True
    )
    
    # Actions sur sélection
    st.markdown("---")
    selected_devis_id = st.selectbox(
        "Sélectionner un devis pour actions:",
        options=[d['id'] for d in devis_list],
        format_func=lambda x: f"#{x} - {next((d['numero_document'] for d in devis_list if d['id'] == x), '')}",
        key="selected_devis_table_action"
    )
    
    if selected_devis_id:
        selected_devis = next((d for d in devis_list if d['id'] == selected_devis_id), None)
        peut_supprimer = selected_devis and selected_devis.get('statut') not in ['APPROUVÉ', 'TERMINÉ']
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button("👁️ Voir", key="voir_devis_table", use_container_width=True):
                st.session_state.devis_action = "view_details"
                st.session_state.devis_selected_id = selected_devis_id
                st.rerun()
        with col2:
            if st.button("📄 Dupliquer", key="dupliquer_devis_table", use_container_width=True):
                nouveau_id = gestionnaire.dupliquer_devis(selected_devis_id, 1)
                if nouveau_id:
                    st.success(f"Devis dupliqué! #{nouveau_id}")
                    st.rerun()
        with col3:
            if st.button("✏️ Modifier", key="edit_devis_table", use_container_width=True):
                st.session_state.devis_action = "edit"
                st.session_state.devis_selected_id = selected_devis_id
                st.rerun()
        with col4:
            if st.button("📧 Envoyer", key="send_devis_table", use_container_width=True):
                if gestionnaire.changer_statut_devis(selected_devis_id, 'ENVOYÉ', 1, "Envoyé par interface"):
                    st.success("Devis marqué comme envoyé!")
                    st.rerun()
        with col5:
            if peut_supprimer and st.button("🗑️ Supprimer", key="delete_devis_table", use_container_width=True):
                st.session_state.confirm_delete_devis_id = selected_devis_id
                st.rerun()
    
    # Gestion de la confirmation de suppression
    if ('confirm_delete_devis_id' in st.session_state and 
        st.session_state.confirm_delete_devis_id in [d['id'] for d in devis_list]):
        devis_to_delete = next((d for d in devis_list if d['id'] == st.session_state.confirm_delete_devis_id), None)
        if devis_to_delete:
            st.markdown("---")
            st.error(f"⚠️ Confirmer la suppression du devis #{devis_to_delete['id']} - {devis_to_delete['numero_document']}")
            
            motif = st.text_input("Motif de suppression (optionnel):", key="motif_table")
            
            col_conf, col_ann = st.columns(2)
            with col_conf:
                if st.button("🗑️ SUPPRIMER DÉFINITIVEMENT", key="confirm_delete_table", type="primary"):
                    if gestionnaire.supprimer_devis(st.session_state.confirm_delete_devis_id, 1, motif):
                        del st.session_state.confirm_delete_devis_id
                        st.success("✅ Devis supprimé avec succès !")
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la suppression")
            with col_ann:
                if st.button("❌ Annuler", key="cancel_delete_table"):
                    del st.session_state.confirm_delete_devis_id
                    st.rerun()


def show_devis_card_view(devis_list, gestionnaire):
    """Affiche les devis en mode cartes compactes."""
    # Organiser en grille de 3 colonnes
    for i in range(0, len(devis_list), 3):
        cols = st.columns(3)
        
        for j, col in enumerate(cols):
            if i + j < len(devis_list):
                devis = devis_list[i + j]
                
                with col:
                    # Carte pour chaque devis
                    with st.container(border=True):
                        # En-tête
                        statut_color = {"BROUILLON": "🟡", "VALIDÉ": "🟢", "ENVOYÉ": "🔵", 
                                      "APPROUVÉ": "✅", "TERMINÉ": "⚪", "ANNULÉ": "🔴"}.get(devis['statut'], "⚫")
                        st.markdown(f"**{statut_color} {devis['numero_document']}**")
                        
                        # Informations principales
                        st.caption(f"👤 {devis['client_nom']}")
                        st.caption(f"📅 {devis['date_creation'][:10] if devis.get('date_creation') else 'N/A'}")
                        
                        # Montant
                        st.markdown(f"**💰 {devis['totaux']['total_ttc']:,.2f} $**")
                        
                        # Échéance si présente
                        if devis.get('date_echeance'):
                            st.caption(f"⏰ Échéance: {devis['date_echeance']}")
                        
                        # Actions rapides
                        peut_supprimer_card = devis.get('statut') not in ['APPROUVÉ', 'TERMINÉ']
                        if peut_supprimer_card:
                            col_action1, col_action2, col_action3 = st.columns(3)
                        else:
                            col_action1, col_action2 = st.columns(2)
                        
                        with col_action1:
                            if st.button("👁️", key=f"view_card_{devis['id']}", use_container_width=True, help="Voir détails"):
                                st.session_state.devis_action = "view_details"
                                st.session_state.devis_selected_id = devis['id']
                                st.rerun()
                        with col_action2:
                            if st.button("✏️", key=f"edit_card_{devis['id']}", use_container_width=True, help="Modifier"):
                                st.session_state.devis_action = "edit"  
                                st.session_state.devis_selected_id = devis['id']
                                st.rerun()
                        if peut_supprimer_card:
                            with col_action3:
                                if st.button("🗑️", key=f"delete_card_{devis['id']}", use_container_width=True, help="Supprimer", type="secondary"):
                                    st.session_state.confirm_delete_devis_id = devis['id']
                                    st.rerun()
    
    # Gestion de la confirmation de suppression pour les cartes
    if ('confirm_delete_devis_id' in st.session_state and 
        st.session_state.confirm_delete_devis_id in [d['id'] for d in devis_list]):
        devis_to_delete = next((d for d in devis_list if d['id'] == st.session_state.confirm_delete_devis_id), None)
        if devis_to_delete:
            st.markdown("---")
            st.error(f"⚠️ Confirmer la suppression du devis #{devis_to_delete['id']} - {devis_to_delete['numero_document']}")
            
            motif = st.text_input("Motif de suppression (optionnel):", key="motif_cards")
            
            col_conf, col_ann = st.columns(2)
            with col_conf:
                if st.button("🗑️ SUPPRIMER DÉFINITIVEMENT", key="confirm_delete_cards", type="primary"):
                    if gestionnaire.supprimer_devis(st.session_state.confirm_delete_devis_id, 1, motif):
                        del st.session_state.confirm_delete_devis_id
                        st.success("✅ Devis supprimé avec succès !")
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la suppression")
            with col_ann:
                if st.button("❌ Annuler", key="cancel_delete_cards"):
                    del st.session_state.confirm_delete_devis_id
                    st.rerun()


def render_nouveau_devis_form(gestionnaire: GestionnaireDevis):
    """Formulaire complet pour créer un nouveau devis avec tous les champs du formulaire projet."""
    st.subheader("Créer un Nouveau Devis")

    # Validation préalable des données de base
    companies_count = gestionnaire.db.get_table_count('companies')
    if companies_count == 0:
        st.warning("⚠️ Aucune entreprise en base. Veuillez ajouter des entreprises dans le module CRM d'abord.")
        return

    # Initialisation des données de session
    if 'devis_lignes' not in st.session_state:
        st.session_state.devis_lignes = []

    # ========================================
    # SECTION 1: GESTION DES LIGNES PRODUITS (OPTIONNEL)
    # ========================================
    st.markdown("### 🛒 Lignes du Devis (Optionnel)")
    st.info("💡 **Les lignes de produits sont optionnelles.** Pour un devis de service pur, vous pouvez passer directement aux informations générales ci-dessous.")
    
    # Section pour sélectionner un produit existant
    st.markdown("**Option 1: Ajouter depuis le catalogue produits**")
    with st.container(border=True):
        col_prod1, col_prod2, col_prod3 = st.columns([2, 1, 1])
        
        with col_prod1:
            # Sélection d'un produit
            try:
                produits_options = [("", "Sélectionner un produit...")] + [(p['id'], f"{p['code_produit']} - {p['nom']}") for p in gestionnaire.product_manager.get_all_products()]
            except:
                produits_options = [("", "Aucun produit disponible")]
            
            produit_selectionne = st.selectbox(
                "Produit du catalogue",
                options=[opt[0] for opt in produits_options],
                format_func=lambda x: next((opt[1] for opt in produits_options if opt[0] == x), "Sélectionner un produit..."),
                key="produit_catalogue_select"
            )
        
        with col_prod2:
            quantite_produit = st.number_input("Quantité", min_value=0.01, value=1.0, step=0.1, key="quantite_produit_catalogue", format="%.2f")
        
        with col_prod3:
            st.write("")  # Espacement
            if st.button("➕ Ajouter depuis catalogue", key="add_from_catalog", use_container_width=True):
                if produit_selectionne:
                    try:
                        produit_data = gestionnaire.product_manager.get_produit_by_id(produit_selectionne)
                        if produit_data:
                            st.session_state.devis_lignes.append({
                                'description': f"{produit_data['code_produit']} - {produit_data['nom']}",
                                'quantite': quantite_produit,
                                'unite': produit_data['unite_vente'],
                                'prix_unitaire': produit_data['prix_unitaire'],
                                'code_article': produit_data['code_produit']
                            })
                            st.success(f"Produit {produit_data['code_produit']} ajouté au devis!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erreur lors de l'ajout du produit: {e}")
                else:
                    st.warning("Veuillez sélectionner un produit.")

    st.markdown("**Option 2: Saisie manuelle**")
    # Formulaire pour ajouter une ligne manuellement
    with st.container(border=True):
        col_ligne1, col_ligne2, col_ligne3, col_ligne4, col_ligne5 = st.columns([3, 1, 1, 1, 1])
        with col_ligne1:
            description = st.text_input("Description", key="ligne_description")
        with col_ligne2:
            quantite = st.number_input("Qté", min_value=0.01, value=1.0, step=0.1, key="ligne_quantite", format="%.2f")
        with col_ligne3:
            unite = st.selectbox("Unité", options=UNITES_VENTE, key="ligne_unite")
        with col_ligne4:
            prix_unitaire = st.number_input("Prix U.", min_value=0.0, step=0.01, key="ligne_prix", format="%.2f")
        with col_ligne5:
            st.write("") # Espace pour aligner le bouton
            if st.button("➕ Ajouter", key="ajouter_ligne_btn", use_container_width=True):
                if description and quantite > 0:
                    st.session_state.devis_lignes.append({
                        'description': description,
                        'quantite': quantite,
                        'unite': unite,
                        'prix_unitaire': prix_unitaire
                    })
                    st.rerun()
                else:
                    st.warning("La description et la quantité sont requises.")
    
    # Affichage des lignes déjà ajoutées
    if st.session_state.devis_lignes:
        st.markdown("**Lignes ajoutées au devis :**")
        total_ht_preview = 0
        with st.container(border=True):
            for i, ligne in enumerate(st.session_state.devis_lignes):
                col_disp, col_del = st.columns([10, 1])
                with col_disp:
                    montant = ligne['quantite'] * ligne['prix_unitaire']
                    total_ht_preview += montant
                    st.write(f"• {ligne['description']} ({ligne['quantite']} {ligne['unite']} x {ligne['prix_unitaire']:.2f} $) = **{montant:.2f} $**")
                with col_del:
                    if st.button("🗑️", key=f"remove_ligne_{i}", help="Supprimer la ligne"):
                        st.session_state.devis_lignes.pop(i)
                        st.rerun()
            st.markdown(f"**🔢 Total prévu (HT) : {total_ht_preview:,.2f} $**")
    else:
        st.markdown("**📝 Aucune ligne de produit ajoutée**")
        st.caption("Le prix sera basé sur le montant saisi dans les informations générales ci-dessous.")
    
    st.markdown("---")

    # ========================================
    # SECTION 2: INFORMATIONS GÉNÉRALES DEVIS 
    # ========================================
    st.markdown("### 📋 Informations Générales du Devis")

    # Section ID du devis (optionnelle - Auto par défaut)
    st.markdown("#### 🆔 Numérotation du Devis")
    
    id_choice = st.radio(
        "Choisissez le mode de numérotation:",
        ["🤖 Automatique (recommandé)", "✏️ Numéro personnalisé"],
        help="Automatique: Le système attribue automatiquement le prochain numéro disponible. Personnalisé: Vous choisissez le numéro.",
        key="devis_id_choice"
    )
    
    custom_devis_id = None
    if id_choice == "✏️ Numéro personnalisé":
        custom_devis_id = st.text_input(
            "Numéro de devis personnalisé:",
            value="",
            placeholder="Ex: DEV-001, 2025-DEV-001...",
            help="Entrez un identifiant unique pour ce devis. Peut contenir lettres, chiffres et tirets.",
            key="custom_devis_id_input"
        )
        
        # Validation en temps réel si l'ID est saisi
        if custom_devis_id:
            # Validation du format
            if not _validate_project_id_format(custom_devis_id):
                st.error("❌ Format invalide ! Utilisez uniquement lettres, chiffres et tirets (-, _). Ex: DEV-001")
            elif gestionnaire.check_devis_id_exists(custom_devis_id):
                st.error(f"❌ Le devis #{custom_devis_id} existe déjà ! Choisissez un autre identifiant.")
            else:
                st.success(f"✅ L'identifiant #{custom_devis_id} est disponible.")
        elif custom_devis_id == "":
            st.info("💡 Saisissez votre identifiant personnalisé (ex: DEV-001)")
    else:
        st.info(f"📋 Le prochain numéro automatique sera attribué par le système")
    
    st.markdown("---")

    # Formulaire principal
    with st.form("create_devis_form", clear_on_submit=True):
        
        # Colonnes principales
        fc1, fc2 = st.columns(2)
        with fc1:
            nom = st.text_input("Nom *:", placeholder="Ex: Rénovation cuisine résidentielle")
            po_client = st.text_input("No. PO Client:", placeholder="Ex: PO-12345")

            # Récupérer entreprises depuis SQLite  
            try:
                entreprises_db = gestionnaire.db.execute_query("SELECT id, nom FROM companies ORDER BY nom")
                liste_entreprises_crm_form = [("", "Sélectionner ou laisser vide")] + [(e['id'], e['nom']) for e in entreprises_db]
            except Exception as e:
                st.error(f"Erreur récupération entreprises: {e}")
                liste_entreprises_crm_form = [("", "Aucune entreprise disponible")]

            selected_entreprise_id_form = st.selectbox(
                "Client (Entreprise) :",
                options=[e_id for e_id, _ in liste_entreprises_crm_form],
                format_func=lambda e_id: next((nom for id_e, nom in liste_entreprises_crm_form if id_e == e_id), "Sélectionner..."),
                key="devis_create_client_select"
            )
            
            # Menu déroulant pour les contacts
            try:
                contacts_db = gestionnaire.db.execute_query("""
                    SELECT c.id, c.nom, c.prenom, comp.nom as entreprise_nom 
                    FROM contacts c 
                    LEFT JOIN companies comp ON c.company_id = comp.id 
                    ORDER BY c.nom, c.prenom
                """)
                liste_contacts_form = [("", "Aucun contact disponible")] + [
                    (c['id'], f"{c['nom']} {c['prenom']}" + (f" ({c['entreprise_nom']})" if c['entreprise_nom'] else ""))
                    for c in contacts_db
                ]
            except Exception as e:
                liste_contacts_form = [("", "Aucun contact disponible")]

            selected_contact_id_form = st.selectbox(
                "Ou Contact direct :",
                options=[c_id for c_id, _ in liste_contacts_form],
                format_func=lambda c_id: next((nom for id_c, nom in liste_contacts_form if id_c == c_id), "Aucun contact disponible"),
                key="devis_create_contact_select"
            )
            
            client_nom_direct_form = st.text_input("Ou nom client direct (si non listé) :")
            
            st.markdown("<small>💡 <strong>Hiérarchie client :</strong> 1️⃣ Entreprise → 2️⃣ Contact → 3️⃣ Nom direct</small>", unsafe_allow_html=True)

            statut = st.selectbox("Statut:", STATUTS_DEVIS)
            priorite = st.selectbox("Priorité:", ["NORMAL", "URGENT", "CRITIQUE"])

        with fc2:
            # Utilisation des tâches de production
            tache = st.selectbox("Tâches:", TACHES_PRODUCTION)
            d_debut = st.date_input("Début:", get_quebec_datetime().date())
            d_fin = st.date_input("Fin Prévue:", get_quebec_datetime().date() + timedelta(days=30))
            bd_ft = st.number_input("BD-FT (h):", 0, value=40, step=1)
            prix_estime = st.number_input("Prix ($):", 0.0, value=float(total_ht_preview) if st.session_state.devis_lignes else 10000.0, step=100.0, format="%.2f")

        desc = st.text_area("Description:")

        # Assignation d'employés
        employes_assignes = []
        try:
            employees = gestionnaire.db.execute_query("SELECT id, prenom, nom, poste FROM employees WHERE statut = 'ACTIF'")
            if employees:
                st.markdown("##### 👥 Assignation d'Employés")
                employes_disponibles = [(emp['id'], f"{emp.get('prenom', '')} {emp.get('nom', '')} ({emp.get('poste', '')})") for emp in employees]
                if employes_disponibles:
                    employes_assignes = st.multiselect(
                        "Employés assignés:",
                        options=[emp_id for emp_id, _ in employes_disponibles],
                        format_func=lambda emp_id: next((nom for id_e, nom in employes_disponibles if id_e == emp_id), ""),
                        key="devis_create_employes_assign"
                    )
        except Exception as e:
            st.warning(f"Impossible de charger les employés: {e}")

        st.markdown("<small>* Obligatoire</small>", unsafe_allow_html=True)
        s_btn, c_btn = st.columns(2)
        with s_btn:
            submit = st.form_submit_button("💾 Créer le Devis", use_container_width=True)
        with c_btn:
            cancel = st.form_submit_button("❌ Annuler", use_container_width=True)

        if submit:
            # Validation complète
            if not nom:
                st.error("Nom du devis obligatoire.")
            elif not selected_entreprise_id_form and not selected_contact_id_form and not client_nom_direct_form:
                st.error("Client obligatoire : sélectionnez une entreprise, un contact, ou saisissez un nom direct.")
            elif d_fin < d_debut:
                st.error("Date fin < date début.")
            elif id_choice == "✏️ Numéro personnalisé" and (not custom_devis_id or not _validate_project_id_format(custom_devis_id)):
                st.error("Numéro de devis personnalisé requis et valide.")
            else:
                # Détermination du client
                client_company_id = None
                client_nom_cache_val = ""

                if selected_entreprise_id_form:
                    client_company_id = selected_entreprise_id_form
                    try:
                        entreprise = gestionnaire.db.execute_query("SELECT nom FROM companies WHERE id = ?", (selected_entreprise_id_form,))
                        client_nom_cache_val = entreprise[0]['nom'] if entreprise else ""
                    except:
                        client_nom_cache_val = ""
                elif selected_contact_id_form:
                    try:
                        contact = gestionnaire.db.execute_query("SELECT nom, prenom, company_id FROM contacts WHERE id = ?", (selected_contact_id_form,))
                        if contact:
                            contact_info = contact[0]
                            client_nom_cache_val = f"{contact_info['nom']} {contact_info['prenom']}"
                            client_company_id = contact_info.get('company_id')
                    except:
                        client_nom_cache_val = ""
                else:
                    client_nom_cache_val = client_nom_direct_form

                # Données complètes du devis
                devis_data = {
                    'numero_document': custom_devis_id,  # None si automatique
                    'nom': nom,
                    'po_client': po_client,
                    'client_company_id': client_company_id,
                    'client_nom_cache': client_nom_cache_val,
                    'statut': statut,
                    'priorite': priorite,
                    'tache': tache,
                    'date_debut': d_debut.strftime('%Y-%m-%d'),
                    'date_echeance': d_fin.strftime('%Y-%m-%d'),
                    'bd_ft': bd_ft,
                    'prix_estime': prix_estime,
                    'description': desc,
                    'employes_assignes': employes_assignes,
                    'lignes': st.session_state.devis_lignes
                }
                
                try:
                    devis_id = gestionnaire.create_devis_complet(devis_data)
                    
                    if devis_id:
                        devis_cree = gestionnaire.get_devis_complet(devis_id)
                        st.success(f"✅ Devis créé avec succès ! Numéro : {devis_cree.get('numero_document')}")
                        st.session_state.devis_lignes = []  # Vider les lignes pour le prochain devis
                        st.rerun()
                    else:
                        st.error("Erreur lors de la création du devis.")
                except Exception as e:
                    st.error(f"Erreur lors de la création du devis: {e}")

        if cancel:
            st.session_state.devis_lignes = []
            st.rerun()

def render_devis_details(gestionnaire: GestionnaireDevis, devis_data):
    """Affiche les détails d'un devis avec option de suppression et export HTML."""
    if not devis_data:
        st.error("Devis non trouvé.")
        return

    st.subheader(f"🧾 Détails du Devis: {devis_data.get('numero_document')}")

    # Informations principales
    c1, c2 = st.columns(2)
    with c1:
        st.info(f"**ID:** {devis_data.get('id')}")
        st.write(f"**Client:** {devis_data.get('client_nom', 'N/A')}")
        st.write(f"**Responsable:** {devis_data.get('responsable_nom', 'N/A')}")
        st.write(f"**Statut:** {devis_data.get('statut', 'N/A')}")
    with c2:
        date_creation = devis_data.get('date_creation')
        st.write(f"**Date création:** {date_creation[:10] if date_creation else 'N/A'}")
        st.write(f"**Date échéance:** {devis_data.get('date_echeance', 'N/A')}")
        st.write(f"**Projet lié:** {devis_data.get('nom_projet', 'Aucun')}")

    # Adresse du client
    if devis_data.get('client_adresse_complete'):
        st.markdown("### 📍 Adresse du Client")
        st.text_area("client_adresse_devis", value=devis_data['client_adresse_complete'], height=100, disabled=True, label_visibility="collapsed")

    # Totaux
    totaux = devis_data.get('totaux', {})
    st.markdown("### 💰 Totaux")
    col_total1, col_total2, col_total3 = st.columns(3)
    with col_total1:
        st.metric("Total HT", f"{totaux.get('total_ht', 0):,.2f} $")
    with col_total2:
        st.metric("TVA", f"{totaux.get('montant_tva', 0):,.2f} $")
    with col_total3:
        st.metric("Total TTC", f"{totaux.get('total_ttc', 0):,.2f} $")

    # Lignes du devis
    st.markdown("### 📋 Lignes du Devis")
    if devis_data.get('lignes'):
        lignes_df_data = []
        for ligne in devis_data['lignes']:
            lignes_df_data.append({
                "Description": ligne.get('description', ''),
                "Quantité": ligne.get('quantite', 0),
                "Unité": ligne.get('unite', ''),
                "Prix unitaire": f"{ligne.get('prix_unitaire', 0):,.2f} $",
                "Montant": f"{ligne.get('quantite', 0) * ligne.get('prix_unitaire', 0):,.2f} $"
            })
        
        st.dataframe(pd.DataFrame(lignes_df_data), use_container_width=True)
    else:
        st.info("Aucune ligne dans ce devis.")

    # Notes
    st.markdown("### 📝 Notes")
    st.text_area("devis_detail_notes_display", value=devis_data.get('notes', 'Aucune note.'), height=100, disabled=True, label_visibility="collapsed")

    # Actions
    st.markdown("### 🔧 Actions")
    
    statuts_non_supprimables = ['APPROUVÉ', 'TERMINÉ']
    peut_supprimer = devis_data.get('statut') not in statuts_non_supprimables
    responsable_id = devis_data.get('employee_id', 1)

    if peut_supprimer:
        col_action1, col_action2, col_action3, col_action4, col_action5, col_action6 = st.columns(6)
    else:
        col_action1, col_action2, col_action3, col_action4, col_action5 = st.columns(5)

    with col_action1:
        if st.button("✅ Accepter", key="accepter_devis"):
            if gestionnaire.changer_statut_devis(devis_data['id'], 'APPROUVÉ', responsable_id, "Approuvé via interface"):
                st.success("Devis approuvé !")
                st.rerun()
    
    with col_action2:
        if st.button("❌ Refuser", key="refuser_devis"):
            if gestionnaire.changer_statut_devis(devis_data['id'], 'ANNULÉ', responsable_id, "Refusé/Annulé via interface"):
                st.success("Devis annulé.")
                st.rerun()
    
    with col_action3:
        if st.button("📧 Envoyer", key="envoyer_devis"):
            if gestionnaire.changer_statut_devis(devis_data['id'], 'ENVOYÉ', responsable_id, "Envoyé via interface"):
                st.success("Devis marqué comme envoyé!")
                st.rerun()
    
    with col_action4:
        if st.button("📄 Dupliquer", key="dupliquer_devis"):
            nouveau_id = gestionnaire.dupliquer_devis(devis_data['id'], responsable_id)
            if nouveau_id:
                st.success(f"Devis dupliqué! Nouveau ID: {nouveau_id}")
                st.rerun()

    with col_action5:
        if st.button("📑 Export HTML", key="export_html_devis_details"):
            html_content = gestionnaire.export_devis_html(devis_data['id'])
            if html_content:
                st.download_button(
                    label="💾 Télécharger le devis HTML",
                    data=html_content,
                    file_name=f"devis_{devis_data.get('numero_document')}.html",
                    mime="text/html",
                    key="download_html_devis_details"
                )
                st.success("✅ Devis HTML généré avec succès !")
            else:
                st.error("❌ Erreur lors de l'export HTML.")

    # Bouton de suppression si possible
    if peut_supprimer:
        with col_action6:
            if st.button("🗑️ Supprimer", key="supprimer_devis_btn", type="secondary"):
                st.session_state.confirm_delete_devis_details = devis_data['id']
                st.rerun()

    # Gestion de la confirmation de suppression
    if 'confirm_delete_devis_details' in st.session_state and st.session_state.confirm_delete_devis_details == devis_data['id']:
        st.markdown("---")
        st.error(f"⚠️ **ATTENTION : Suppression définitive du devis {devis_data.get('numero_document')}**")
        st.warning("Cette action est irréversible. Le devis et toutes ses données seront définitivement supprimés de la base de données.")
        
        motif_suppression = st.text_input(
            "Motif de suppression (optionnel):", 
            placeholder="Ex: Erreur de saisie, doublon, demande client...",
            key="motif_suppression_devis"
        )
        
        col_confirm, col_cancel = st.columns(2)
        
        with col_confirm:
            if st.button("🗑️ CONFIRMER LA SUPPRESSION", key="confirm_delete_devis", type="primary"):
                if gestionnaire.supprimer_devis(devis_data['id'], responsable_id, motif_suppression):
                    del st.session_state.confirm_delete_devis_details
                    st.session_state.devis_action = None
                    st.session_state.devis_selected_id = None
                    st.rerun()
                else:
                    del st.session_state.confirm_delete_devis_details
        
        with col_cancel:
            if st.button("❌ Annuler la suppression", key="cancel_delete_devis"):
                del st.session_state.confirm_delete_devis_details
                st.rerun()

    if st.button("Retour à la liste des devis", key="back_to_devis_list_from_details"):
        st.session_state.devis_action = None
        st.rerun()

def render_devis_statistics(gestionnaire: GestionnaireDevis):
    """Affiche les statistiques des devis."""
    st.subheader("Statistiques des Devis")
    
    stats = gestionnaire.get_devis_statistics()
    
    if stats.get('total_devis', 0) > 0:
        # Affichage des métriques principales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Devis", stats.get('total_devis', 0))
        with col2:
            st.metric("Taux d'acceptation", f"{stats.get('taux_acceptation', 0):.1f}%")
        with col3:
            montant_total = stats.get('montant_total', 0.0)
            st.metric("Montant Total (HT)", f"{montant_total:,.0f} $")
        with col4:
            st.metric("En Attente", stats.get('en_attente', 0))
        
        # Graphiques
        if stats.get('par_statut'):
            statut_data = pd.DataFrame([
                {'Statut': k, 'Nombre': v['count'], 'Montant HT': v['montant']}
                for k, v in stats['par_statut'].items() if isinstance(v, dict)
            ])
            
            col_graph1, col_graph2 = st.columns(2)
            
            with col_graph1:
                st.markdown("**Répartition par Statut (Nombre)**")
                st.bar_chart(statut_data.set_index('Statut')['Nombre'])
            
            with col_graph2:
                st.markdown("**Répartition par Statut (Montant HT)**")
                st.bar_chart(statut_data.set_index('Statut')['Montant HT'])
    else:
        st.info("Aucune donnée de devis disponible pour les statistiques.")


def handle_devis_actions(gestionnaire: GestionnaireDevis):
    """Gestionnaire centralisé des actions pour les devis."""
    action = st.session_state.get('devis_action')
    selected_id = st.session_state.get('devis_selected_id')
    
    if action == "view_details" and selected_id:
        devis_data = gestionnaire.get_devis_complet(selected_id)
        render_devis_details(gestionnaire, devis_data)
    elif action == "edit" and selected_id:
        # Pour l'édition, on pourrait créer une fonction render_edit_devis_form similaire
        st.info("Fonction d'édition à implémenter")
        if st.button("Retour"):
            st.session_state.devis_action = None
            st.rerun()

def show_devis_page():
    """Point d'entrée principal pour la page des devis."""
    st.title("🧾 Gestion des Devis")
    
    if 'gestionnaire_devis' not in st.session_state:
        st.error("Gestionnaire de devis non initialisé.")
        return
        
    gestionnaire = st.session_state.gestionnaire_devis

    # Vérifier s'il y a une action en cours
    if st.session_state.get('devis_action'):
        handle_devis_actions(gestionnaire)
        return

    # Statistiques en haut
    stats = gestionnaire.get_devis_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Devis", stats.get('total_devis', 0))
    with col2:
        st.metric("Taux d'acceptation", f"{stats.get('taux_acceptation', 0):.1f}%")
    with col3:
        montant_total = stats.get('montant_total', 0.0)
        st.metric("Montant Total (HT)", f"{montant_total:,.0f} $")
    with col4:
        st.metric("En Attente", stats.get('en_attente', 0))

    tab1, tab2, tab3 = st.tabs(["📋 Liste des Devis", "➕ Nouveau Devis", "📊 Statistiques"])
    
    with tab1:
        render_devis_liste(gestionnaire)
    
    with tab2:
        render_nouveau_devis_form(gestionnaire)
    
    with tab3:
        render_devis_statistics(gestionnaire)

# =========================================================================
# MÉTHODES SPÉCIFIQUES CONSTRUCTION QUÉBEC
# =========================================================================

def calculer_taxes_construction_quebec(total_ht: float, type_client: str, secteur: str, 
                                     province: str = 'QC') -> Dict[str, float]:
    """
    Calcule les taxes pour projets de construction au Québec
    
    Args:
        total_ht: Montant hors taxes
        type_client: 'PARTICULIER', 'ENTREPRISE', 'ORGANISME_PUBLIC'
        secteur: 'RÉSIDENTIEL', 'COMMERCIAL', 'INDUSTRIEL', 'INSTITUTIONNEL'
        province: Province ('QC', 'ON', etc.)
    
    Returns:
        Dict avec détail des taxes
    """
    
    # Taux de base (2024)
    taux_tps = 5.0
    taux_tvq = 9.975
    
    # Calculs de base
    tps = total_ht * (taux_tps / 100)
    tvq = total_ht * (taux_tvq / 100)
    
    # Remboursements spéciaux construction résidentielle
    tps_remboursement = 0
    tvq_remboursement = 0
    
    if secteur == 'RÉSIDENTIEL' and type_client == 'PARTICULIER':
        # Remboursement TPS résidentiel (36%)
        tps_remboursement = tps * 0.36
        
        # Remboursement TVQ résidentiel (maisons neuves)
        if total_ht >= 225000:  # Seuil 2024
            tvq_remboursement = min(tvq * 0.5, 6300)  # Max 6300$ ou 50%
        else:
            tvq_remboursement = tvq * 0.5
    
    # Calculs nets
    tps_net = tps - tps_remboursement
    tvq_net = tvq - tvq_remboursement
    total_taxes = tps_net + tvq_net
    total_ttc = total_ht + total_taxes
    
    return {
        'total_ht': round(total_ht, 2),
        'taux_tps': taux_tps,
        'montant_tps_brut': round(tps, 2),
        'tps_remboursement': round(tps_remboursement, 2),
        'tps_net': round(tps_net, 2),
        'taux_tvq': taux_tvq,
        'montant_tvq_brut': round(tvq, 2),
        'tvq_remboursement': round(tvq_remboursement, 2),
        'tvq_net': round(tvq_net, 2),
        'total_taxes': round(total_taxes, 2),
        'total_ttc': round(total_ttc, 2),
        'economie_fiscale': round(tps_remboursement + tvq_remboursement, 2),
        'type_client': type_client,
        'secteur': secteur
    }

def calculer_cout_ccq(montant_main_oeuvre: float, metiers: List[str]) -> Dict[str, float]:
    """
    Calcule les coûts CCQ pour un projet
    
    Args:
        montant_main_oeuvre: Montant main-d'œuvre
        metiers: Liste des métiers CCQ impliqués
    
    Returns:
        Dict avec détail des coûts CCQ
    """
    
    # Taux CCQ 2024 (simplifié)
    taux_ccq_base = 0.185  # 18.5% approximatif
    
    # Ajustements par métier
    ajustements_metier = {
        'Électricien': 0.02,
        'Plombier': 0.015,
        'Charpentier-menuisier': 0.01,
        'Soudeur': 0.005,
        'Grutier': 0.025
    }
    
    taux_total = taux_ccq_base
    for metier in metiers:
        taux_total += ajustements_metier.get(metier, 0)
    
    # Calculs
    cout_ccq = montant_main_oeuvre * taux_total
    
    return {
        'montant_main_oeuvre': round(montant_main_oeuvre, 2),
        'taux_ccq': round(taux_total * 100, 2),
        'cout_ccq': round(cout_ccq, 2),
        'metiers_impliques': metiers,
        'cout_total_avec_ccq': round(montant_main_oeuvre + cout_ccq, 2)
    }

def calculer_cout_cnesst(montant_main_oeuvre: float, taux_unite: float = 2.53) -> Dict[str, float]:
    """
    Calcule les coûts CNESST pour un projet
    
    Args:
        montant_main_oeuvre: Montant main-d'œuvre
        taux_unite: Taux par 100$ de masse salariale (2024: 2.53$ pour construction)
    
    Returns:
        Dict avec détail des coûts CNESST
    """
    
    cout_cnesst = (montant_main_oeuvre / 100) * taux_unite
    
    return {
        'montant_main_oeuvre': round(montant_main_oeuvre, 2),
        'taux_unite': taux_unite,
        'cout_cnesst': round(cout_cnesst, 2),
        'cout_total_avec_cnesst': round(montant_main_oeuvre + cout_cnesst, 2)
    }

def generer_devis_construction_complet(devis_data: Dict) -> Dict:
    """
    Génère un devis construction complet avec tous les calculs spécialisés
    
    Args:
        devis_data: Données du devis avec spécifications construction
    
    Returns:
        Dict avec devis complet et calculs spécialisés
    """
    
    # Extraire données de base
    total_ht = devis_data.get('total_ht', 0)
    montant_main_oeuvre = devis_data.get('montant_main_oeuvre', 0)
    type_client = devis_data.get('type_client', 'PARTICULIER')
    secteur = devis_data.get('secteur', 'RÉSIDENTIEL')
    metiers_ccq = devis_data.get('metiers_ccq', [])
    
    # Calculs spécialisés
    taxes = calculer_taxes_construction_quebec(total_ht, type_client, secteur)
    
    couts_ccq = calculer_cout_ccq(montant_main_oeuvre, metiers_ccq)
    couts_cnesst = calculer_cout_cnesst(montant_main_oeuvre)
    
    # Calcul du total final
    total_avec_charges = total_ht + couts_ccq['cout_ccq'] + couts_cnesst['cout_cnesst']
    taxes_finales = calculer_taxes_construction_quebec(total_avec_charges, type_client, secteur)
    
    return {
        'devis_base': devis_data,
        'ventilation_couts': {
            'materiaux': total_ht - montant_main_oeuvre,
            'main_oeuvre': montant_main_oeuvre,
            'charges_ccq': couts_ccq['cout_ccq'],
            'charges_cnesst': couts_cnesst['cout_cnesst'],
            'sous_total': total_avec_charges
        },
        'taxes_detaillees': taxes_finales,
        'resume_financier': {
            'total_ht': total_ht,
            'total_charges': couts_ccq['cout_ccq'] + couts_cnesst['cout_cnesst'],
            'total_avant_taxes': total_avec_charges,
            'total_taxes': taxes_finales['total_taxes'],
            'total_ttc': taxes_finales['total_ttc'],
            'economie_fiscale': taxes_finales['economie_fiscale']
        },
        'conformite': {
            'metiers_ccq': metiers_ccq,
            'charges_conformes': True,
            'taxes_conformes': True
        }
    }

# Ajouter les méthodes à la classe GestionnaireDevis
GestionnaireDevis.calculer_taxes_construction_quebec = calculer_taxes_construction_quebec
GestionnaireDevis.calculer_cout_ccq = calculer_cout_ccq
GestionnaireDevis.calculer_cout_cnesst = calculer_cout_cnesst
GestionnaireDevis.generer_devis_construction_complet = generer_devis_construction_complet