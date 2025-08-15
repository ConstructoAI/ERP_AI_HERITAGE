# assistant_ia.py - Module Assistant IA Claude
# ERP Production DG Inc. - Intelligence Artificielle intégrée
# Analyse intelligente des données métier avec Claude API

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from anthropic import Anthropic
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# Chargement du fichier .env
def load_env_file():
    """Charge le fichier .env s'il existe"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Nettoyer les espaces et guillemets
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value

# Charger les variables d'environnement au démarrage
load_env_file()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AssistantIAClaude:
    """
    Assistant IA utilisant Claude pour analyser les données ERP
    Fournit des insights, recommandations et analyses prédictives
    """
    
    def __init__(self, db, api_key: Optional[str] = None):
        """
        Initialise l'assistant IA
        
        Args:
            db: Instance ERPDatabase pour accéder aux données
            api_key: Clé API Claude (ou depuis variable d'environnement)
        """
        self.db = db
        self.api_key = api_key or os.environ.get('CLAUDE_API_KEY')
        
        if self.api_key:
            try:
                self.client = Anthropic(api_key=self.api_key)
                self.model = "claude-sonnet-4-20250514"
                logger.info("✅ Assistant IA Claude initialisé avec succès")
            except Exception as e:
                logger.error(f"❌ Erreur initialisation Claude: {e}")
                self.client = None
        else:
            logger.warning("⚠️ Clé API Claude non configurée")
            self.client = None
    
    # =========================================================================
    # COLLECTE ET PRÉPARATION DES DONNÉES
    # =========================================================================
    
    def _collecter_donnees_projets(self) -> Dict[str, Any]:
        """Collecte les données projets pour analyse"""
        try:
            # Projets actifs
            projets_actifs = self.db.execute_query("""
                SELECT p.*, 
                       COUNT(DISTINCT o.id) as nb_operations,
                       COUNT(DISTINCT te.id) as nb_pointages,
                       SUM(te.heures) as heures_totales
                FROM projects p
                LEFT JOIN operations o ON p.id = o.project_id
                LEFT JOIN time_entries te ON p.id = te.project_id
                WHERE p.statut IN ('EN COURS', 'À FAIRE')
                GROUP BY p.id
            """)
            
            # Statistiques globales
            stats = self.db.execute_query("""
                SELECT 
                    COUNT(CASE WHEN statut = 'TERMINÉ' THEN 1 END) as projets_termines,
                    COUNT(CASE WHEN statut = 'EN COURS' THEN 1 END) as projets_en_cours,
                    COUNT(CASE WHEN statut = 'À FAIRE' THEN 1 END) as projets_a_faire,
                    AVG(CASE WHEN statut = 'TERMINÉ' AND date_fin_reel IS NOT NULL 
                        THEN julianday(date_fin_reel) - julianday(date_debut_reel) END) as duree_moy_jours,
                    AVG(prix_estime) as budget_moyen
                FROM projects
                WHERE created_at >= date('now', '-6 months')
            """)
            
            return {
                'projets_actifs': [dict(p) for p in projets_actifs],
                'statistiques': dict(stats[0]) if stats else {},
                'nb_projets_actifs': len(projets_actifs)
            }
        except Exception as e:
            logger.error(f"Erreur collecte données projets: {e}")
            return {}
    
    def _collecter_donnees_inventaire(self) -> Dict[str, Any]:
        """Collecte les données d'inventaire pour analyse"""
        try:
            # Articles en alerte
            alertes = self.db.execute_query("""
                SELECT * FROM inventory_items 
                WHERE quantite_metric <= limite_minimale_metric
                ORDER BY (quantite_metric / NULLIF(limite_minimale_metric, 0))
            """)
            
            # Mouvements récents
            mouvements = self.db.execute_query("""
                SELECT 
                    item_id,
                    COUNT(*) as nb_mouvements,
                    SUM(CASE WHEN type_mouvement = 'ENTREE' THEN quantite_metric ELSE 0 END) as total_entrees,
                    SUM(CASE WHEN type_mouvement = 'SORTIE' THEN quantite_metric ELSE 0 END) as total_sorties
                FROM inventory_history
                WHERE created_at >= date('now', '-30 days')
                GROUP BY item_id
                ORDER BY nb_mouvements DESC
                LIMIT 10
            """)
            
            # Valeur totale inventaire (estimation)
            valeur_totale = self.db.execute_query("""
                SELECT 
                    COUNT(*) as nb_articles,
                    SUM(quantite_metric) as quantite_totale
                FROM inventory_items
            """)
            
            return {
                'alertes_stock': [dict(a) for a in alertes],
                'mouvements_frequents': [dict(m) for m in mouvements],
                'valeur_inventaire': dict(valeur_totale[0]) if valeur_totale else {},
                'nb_alertes': len(alertes)
            }
        except Exception as e:
            logger.error(f"Erreur collecte données inventaire: {e}")
            return {}
    
    def _collecter_donnees_crm(self) -> Dict[str, Any]:
        """Collecte les données CRM pour analyse"""
        try:
            # Opportunités par statut
            opportunites = self.db.execute_query("""
                SELECT 
                    statut,
                    COUNT(*) as nombre,
                    SUM(montant) as montant_total,
                    AVG(montant) as montant_moyen
                FROM crm_opportunities
                WHERE created_at >= date('now', '-3 months')
                GROUP BY statut
            """)
            
            # Top clients par CA
            top_clients = self.db.execute_query("""
                SELECT 
                    c.nom as client,
                    COUNT(DISTINCT p.id) as nb_projets,
                    SUM(p.prix_estime) as ca_total,
                    MAX(p.created_at) as dernier_projet
                FROM companies c
                JOIN projects p ON c.id = p.client_company_id
                GROUP BY c.id
                ORDER BY ca_total DESC
                LIMIT 10
            """)
            
            # Activité commerciale récente
            activite_recente = self.db.execute_query("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as nb_interactions
                FROM crm_interactions
                WHERE created_at >= date('now', '-30 days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """)
            
            return {
                'opportunites': [dict(o) for o in opportunites] if opportunites else [],
                'top_clients': [dict(c) for c in top_clients],
                'activite_commerciale': [dict(a) for a in activite_recente] if activite_recente else []
            }
        except Exception as e:
            logger.error(f"Erreur collecte données CRM: {e}")
            return {}
    
    def _collecter_donnees_devis(self) -> Dict[str, Any]:
        """Collecte les données de devis pour analyse"""
        try:
            # Devis par statut
            devis_par_statut = self.db.execute_query("""
                SELECT 
                    statut,
                    COUNT(*) as nombre,
                    SUM(CAST(montant_total AS REAL)) as montant_montant_total,
                    AVG(CAST(montant_total AS REAL)) as montant_moyen_ht
                FROM formulaires
                WHERE type_formulaire = 'ESTIMATION'
                AND created_at >= date('now', '-6 months')
                GROUP BY statut
                ORDER BY montant_montant_total DESC
            """)
            
            # Devis récents avec détails
            devis_recents = self.db.execute_query("""
                SELECT 
                    f.*,
                    c.nom as client_nom,
                    c.type_entreprise,
                    COUNT(fl.id) as nb_articles,
                    SUM(CAST(fl.quantite AS REAL) * CAST(fl.prix_unitaire AS REAL)) as total_calcule
                FROM formulaires f
                LEFT JOIN companies c ON f.company_id = c.id
                LEFT JOIN formulaire_lignes fl ON f.id = fl.formulaire_id
                WHERE f.type_formulaire = 'ESTIMATION'
                GROUP BY f.id
                ORDER BY f.created_at DESC
                LIMIT 20
            """)
            
            # Analyse des taux de conversion
            taux_conversion = self.db.execute_query("""
                SELECT 
                    COUNT(CASE WHEN statut IN ('VALIDÉ', 'ENVOYÉ') THEN 1 END) as devis_envoyes,
                    COUNT(CASE WHEN statut = 'APPROUVÉ' THEN 1 END) as devis_approuves,
                    COUNT(CASE WHEN statut = 'TERMINÉ' THEN 1 END) as devis_termines,
                    COUNT(*) as total_devis,
                    AVG(CAST(montant_total AS REAL)) as montant_moyen
                FROM formulaires
                WHERE type_formulaire = 'ESTIMATION'
                AND created_at >= date('now', '-6 months')
            """)
            
            # Top produits/services dans les devis
            top_produits = self.db.execute_query("""
                SELECT 
                    fl.code_article,
                    fl.description,
                    COUNT(*) as nb_occurrences,
                    SUM(CAST(fl.quantite AS REAL)) as quantite_totale,
                    SUM(CAST(fl.quantite AS REAL) * CAST(fl.prix_unitaire AS REAL)) as ca_total,
                    AVG(CAST(fl.prix_unitaire AS REAL)) as prix_moyen
                FROM formulaire_lignes fl
                JOIN formulaires f ON fl.formulaire_id = f.id
                WHERE f.type_formulaire = 'ESTIMATION'
                AND f.created_at >= date('now', '-6 months')
                GROUP BY fl.code_article, fl.description
                ORDER BY ca_total DESC
                LIMIT 15
            """)
            
            return {
                'devis_par_statut': [dict(d) for d in devis_par_statut] if devis_par_statut else [],
                'devis_recents': [dict(d) for d in devis_recents] if devis_recents else [],
                'taux_conversion': dict(taux_conversion[0]) if taux_conversion else {},
                'top_produits': [dict(p) for p in top_produits] if top_produits else [],
                'nb_devis_recents': len(devis_recents) if devis_recents else 0
            }
        except Exception as e:
            logger.error(f"Erreur collecte données devis: {e}")
            return {}
    
    def _collecter_donnees_production(self) -> Dict[str, Any]:
        """Collecte les données de production pour analyse"""
        try:
            # Charge par poste de travail
            charge_postes = self.db.execute_query("""
                SELECT 
                    wc.nom as poste,
                    COUNT(o.id) as nb_operations,
                    SUM(o.temps_estime) as heures_prevues,
                    SUM(CASE WHEN o.statut = 'EN COURS' THEN 1 ELSE 0 END) as operations_en_cours
                FROM work_centers wc
                LEFT JOIN operations o ON wc.id = o.work_center_id
                WHERE o.statut IN ('À FAIRE', 'EN COURS')
                GROUP BY wc.id
                ORDER BY heures_prevues DESC
            """)
            
            # Performance employés (30 derniers jours)
            performance_employes = self.db.execute_query("""
                SELECT 
                    e.prenom || ' ' || e.nom as employe,
                    COUNT(DISTINCT te.id) as nb_pointages,
                    SUM(te.heures) as heures_totales,
                    COUNT(DISTINCT te.project_id) as nb_projets
                FROM employees e
                LEFT JOIN time_entries te ON e.id = te.employee_id
                WHERE date(te.punch_in) >= date('now', '-30 days')
                GROUP BY e.id
                ORDER BY heures_totales DESC
                LIMIT 10
            """)
            
            return {
                'charge_postes': [dict(c) for c in charge_postes],
                'performance_employes': [dict(p) for p in performance_employes]
            }
        except Exception as e:
            logger.error(f"Erreur collecte données production: {e}")
            return {}
    
    # =========================================================================
    # ANALYSE IA AVEC CLAUDE
    # =========================================================================
    
    def analyser_situation_globale(self) -> Dict[str, Any]:
        """Analyse globale de la situation de l'entreprise"""
        if not self.client:
            return {
                'success': False,
                'error': "Assistant IA non configuré. Veuillez ajouter votre clé API Claude."
            }
        
        try:
            # Collecter toutes les données
            donnees = {
                'projets': self._collecter_donnees_projets(),
                'inventaire': self._collecter_donnees_inventaire(),
                'crm': self._collecter_donnees_crm(),
                'production': self._collecter_donnees_production(),
                'date_analyse': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            
            # Préparer le contexte pour Claude
            contexte = f"""
            Analyse ERP du {donnees['date_analyse']}:
            
            PROJETS:
            - {donnees['projets']['nb_projets_actifs']} projets actifs
            - Durée moyenne: {donnees['projets']['statistiques'].get('duree_moy_jours', 0):.1f} jours
            - Budget moyen: ${donnees['projets']['statistiques'].get('budget_moyen', 0):,.2f}
            
            INVENTAIRE:
            - {donnees['inventaire']['nb_alertes']} articles en alerte stock
            - {donnees['inventaire']['valeur_inventaire'].get('nb_articles', 0)} articles totaux
            
            CRM:
            - {len(donnees['crm']['top_clients'])} clients actifs
            - Opportunités en cours: {sum(o['nombre'] for o in donnees['crm']['opportunites'] if o['statut'] != 'Perdu')}
            
            DEVIS:
            - {donnees['devis']['nb_devis_recents']} devis récents
            - Taux de conversion: {(donnees['devis']['taux_conversion'].get('devis_approuves', 0) / max(donnees['devis']['taux_conversion'].get('total_devis', 1), 1) * 100):.1f}%
            - Montant moyen: ${donnees['devis']['taux_conversion'].get('montant_moyen', 0):,.2f}
            - Top produits: {len(donnees['devis']['top_produits'])} références analysées
            
            PRODUCTION:
            - {len(donnees['production']['charge_postes'])} postes de travail actifs
            - {sum(p['heures_totales'] for p in donnees['production']['performance_employes'])} heures travaillées (30j)
            """
            
            # Appel à Claude pour analyse
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": f"""En tant qu'expert en gestion d'entreprise et ERP, analysez ces données et fournissez:

1. **Résumé exécutif** (3-4 points clés)
2. **Points forts** identifiés
3. **Alertes et risques** à surveiller
4. **Recommandations prioritaires** (3-5 actions)
5. **Indicateurs à suivre**

Données détaillées:
{contexte}

Détails supplémentaires:
{json.dumps(donnees, indent=2, default=str)}

Répondez de manière structurée et professionnelle."""
                }]
            )
            
            return {
                'success': True,
                'analyse': response.content[0].text,
                'donnees_analysees': donnees,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse IA: {e}")
            return {
                'success': False,
                'error': f"Erreur lors de l'analyse: {str(e)}"
            }
    
    def analyser_projet_specifique(self, project_id: str) -> Dict[str, Any]:
        """Analyse approfondie d'un projet spécifique"""
        if not self.client:
            return {'success': False, 'error': "Assistant IA non configuré"}
        
        try:
            # Récupérer les données du projet
            projet = self.db.execute_query("""
                SELECT p.*, c.nom as client_nom
                FROM projects p
                LEFT JOIN companies c ON p.client_company_id = c.id
                WHERE p.id = ?
            """, (project_id,))
            
            if not projet:
                return {'success': False, 'error': "Projet non trouvé"}
            
            projet_data = dict(projet[0])
            
            # Opérations du projet
            operations = self.db.execute_query("""
                SELECT o.*, wc.nom as poste_travail
                FROM operations o
                LEFT JOIN work_centers wc ON o.work_center_id = wc.id
                WHERE o.project_id = ?
                ORDER BY o.sequence_number
            """, (project_id,))
            
            # Temps pointés
            temps = self.db.execute_query("""
                SELECT 
                    te.*,
                    e.prenom || ' ' || e.nom as employe_nom
                FROM time_entries te
                LEFT JOIN employees e ON te.employee_id = e.id
                WHERE te.project_id = ?
                ORDER BY te.punch_in DESC
            """, (project_id,))
            
            # Matériaux
            materiaux = self.db.execute_query("""
                SELECT * FROM materials
                WHERE project_id = ?
            """, (project_id,))
            
            # Calculs de performance
            heures_prevues = sum(o['temps_estime'] for o in operations)
            heures_reelles = sum(t['heures'] for t in temps)
            taux_avancement = len([o for o in operations if o['statut'] == 'TERMINÉ']) / len(operations) * 100 if operations else 0
            
            # Contexte pour Claude
            contexte = f"""
            Projet: {projet_data['nom_projet']}
            Client: {projet_data['client_nom']}
            Statut: {projet_data['statut']}
            Budget: ${projet_data.get('prix_estime', 0):,.2f}
            
            Performance:
            - Heures prévues: {heures_prevues:.1f}h
            - Heures réelles: {heures_reelles:.1f}h
            - Écart: {((heures_reelles/heures_prevues - 1) * 100 if heures_prevues > 0 else 0):.1f}%
            - Avancement: {taux_avancement:.1f}%
            
            Opérations: {len(operations)} étapes
            Employés impliqués: {len(set(t['employe_nom'] for t in temps))}
            Matériaux: {len(materiaux)} items
            """
            
            # Analyse par Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": f"""Analysez ce projet de production et fournissez:

1. **État du projet** (santé globale)
2. **Risques identifiés** 
3. **Optimisations possibles**
4. **Prochaines étapes recommandées**

{contexte}

Soyez précis et orienté action."""
                }]
            )
            
            return {
                'success': True,
                'analyse': response.content[0].text,
                'metriques': {
                    'heures_prevues': heures_prevues,
                    'heures_reelles': heures_reelles,
                    'taux_avancement': taux_avancement,
                    'budget': projet_data.get('prix_estime', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse projet: {e}")
            return {'success': False, 'error': str(e)}
    
    def analyser_devis_specifique(self, devis_id: str) -> Dict[str, Any]:
        """Analyse approfondie d'un devis spécifique"""
        if not self.client:
            return {'success': False, 'error': "Assistant IA non configuré"}
        
        try:
            # Récupérer les données du devis
            devis = self.db.execute_query("""
                SELECT f.*, c.nom as client_nom, c.type_entreprise
                FROM formulaires f
                LEFT JOIN companies c ON f.company_id = c.id
                WHERE f.id = ? AND f.type_formulaire = 'ESTIMATION'
            """, (devis_id,))
            
            if not devis:
                return {'success': False, 'error': "Devis non trouvé"}
            
            devis_data = dict(devis[0])
            
            # Lignes du devis
            lignes = self.db.execute_query("""
                SELECT fl.*, 
                       (CAST(fl.quantite AS REAL) * CAST(fl.prix_unitaire AS REAL)) as montant_ligne,
                       ii.unite_primaire, ii.categorie
                FROM formulaire_lignes fl
                LEFT JOIN inventory_items ii ON fl.code_article = ii.code_produit
                WHERE fl.formulaire_id = ?
                ORDER BY fl.created_at
            """, (devis_id,))
            
            # Historique des validations
            validations = self.db.execute_query("""
                SELECT fv.*, e.prenom || ' ' || e.nom as employe_nom
                FROM formulaire_validations fv
                LEFT JOIN employees e ON fv.employee_id = e.id
                WHERE fv.formulaire_id = ?
                ORDER BY fv.created_at DESC
            """, (devis_id,))
            
            # Comparaison avec devis similaires
            devis_similaires = self.db.execute_query("""
                SELECT 
                    AVG(CAST(montant_total AS REAL)) as montant_moyen,
                    COUNT(*) as nb_devis,
                    AVG(CASE WHEN statut = 'APPROUVÉ' THEN 1.0 ELSE 0.0 END) as taux_approbation
                FROM formulaires
                WHERE type_formulaire = 'ESTIMATION'
                AND company_id = ?
                AND id != ?
                AND created_at >= date('now', '-12 months')
            """, (devis_data['company_id'], devis_id))
            
            # Calculs
            montant_total = sum(float(l['montant_ligne']) for l in lignes if l['montant_ligne'])
            nb_articles = len(lignes)
            prix_moyen_ligne = montant_total / nb_articles if nb_articles > 0 else 0
            
            # Comparaisons
            comparaison = dict(devis_similaires[0]) if devis_similaires and devis_similaires[0][0] else {}
            
            # Contexte pour Claude
            contexte = f"""
            DEVIS #{devis_data['numero_document']}
            Client: {devis_data['client_nom']} ({devis_data['type_entreprise']})
            Statut: {devis_data['statut']}
            Date création: {devis_data['created_at']}
            
            MONTANTS:
            - Total HT: ${montant_total:,.2f}
            - Total TTC: ${float(devis_data.get('total_ttc', 0)):,.2f}
            - Nombre d'articles: {nb_articles}
            - Prix moyen par ligne: ${prix_moyen_ligne:,.2f}
            
            COMPARAISON CLIENT:
            - Devis précédents: {comparaison.get('nb_devis', 0)}
            - Montant moyen historique: ${comparaison.get('montant_moyen', 0):,.2f}
            - Taux d'approbation: {comparaison.get('taux_approbation', 0)*100:.1f}%
            
            VALIDATIONS: {len(validations)} étapes
            
            Articles principaux:
            {chr(10).join([f"- {l['code_article']}: {l['quantite']} x ${float(l['prix_unitaire'] or 0):,.2f}" for l in lignes[:10]])}
            """
            
            # Analyse par Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1200,
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": f"""Analysez ce devis et fournissez:

1. **Évaluation commerciale** (positionnement prix, attractivité)
2. **Probabilité de conversion** (estimation basée sur les données)
3. **Points d'attention** (risques, opportunités)
4. **Recommandations** (actions pour améliorer les chances)
5. **Optimisations** (suggestions de pricing, produits)

{contexte}

Soyez précis et orienté vente/négociation."""
                }]
            )
            
            return {
                'success': True,
                'analyse': response.content[0].text,
                'metriques': {
                    'montant_total': montant_total,
                    'nb_articles': nb_articles,
                    'prix_moyen_ligne': prix_moyen_ligne,
                    'comparaison_historique': comparaison,
                    'nb_validations': len(validations)
                },
                'donnees': {
                    'devis': devis_data,
                    'lignes': [dict(l) for l in lignes],
                    'validations': [dict(v) for v in validations]
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse devis: {e}")
            return {'success': False, 'error': str(e)}
    
    def generer_rapport_previsionnel(self, horizon_jours: int = 30) -> Dict[str, Any]:
        """Génère un rapport prévisionnel pour les prochains jours"""
        if not self.client:
            return {'success': False, 'error': "Assistant IA non configuré"}
        
        try:
            date_fin = datetime.now() + timedelta(days=horizon_jours)
            
            # Projets à livrer
            projets_a_livrer = self.db.execute_query("""
                SELECT * FROM projects
                WHERE date_prevu <= ? AND statut != 'TERMINÉ'
                ORDER BY date_prevu
            """, (date_fin.strftime('%Y-%m-%d'),))
            
            # Charge prévisionnelle
            charge_prevue = self.db.execute_query("""
                SELECT 
                    wc.nom as poste,
                    SUM(o.temps_estime) as heures_totales
                FROM operations o
                JOIN work_centers wc ON o.work_center_id = wc.id
                JOIN projects p ON o.project_id = p.id
                WHERE p.date_prevu <= ? AND o.statut != 'TERMINÉ'
                GROUP BY wc.id
            """, (date_fin.strftime('%Y-%m-%d'),))
            
            # Capacité disponible (estimation)
            nb_employes_actifs = len(self.db.execute_query("SELECT id FROM employees WHERE statut = 'ACTIF'"))
            capacite_totale = nb_employes_actifs * 8 * (horizon_jours * 5/7)  # 8h/jour, 5j/7
            
            contexte = f"""
            Analyse prévisionnelle sur {horizon_jours} jours:
            
            - {len(projets_a_livrer)} projets à terminer
            - Charge totale: {sum(c['heures_totales'] for c in charge_prevue):.0f} heures
            - Capacité disponible: {capacite_totale:.0f} heures ({nb_employes_actifs} employés)
            
            Répartition par poste:
            {json.dumps([dict(c) for c in charge_prevue], indent=2)}
            """
            
            # Analyse prévisionnelle par Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1200,
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": f"""En tant qu'expert en planification de production, analysez cette situation prévisionnelle:

{contexte}

Fournissez:
1. **Analyse de capacité** (suffisante ou non?)
2. **Goulots d'étranglement** identifiés
3. **Plan d'action** pour respecter les délais
4. **Ressources additionnelles** nécessaires
5. **Risques majeurs** à anticiper

Soyez pragmatique et orienté solutions."""
                }]
            )
            
            return {
                'success': True,
                'analyse': response.content[0].text,
                'donnees': {
                    'projets_a_livrer': len(projets_a_livrer),
                    'charge_totale': sum(c['heures_totales'] for c in charge_prevue),
                    'capacite_disponible': capacite_totale,
                    'taux_charge': (sum(c['heures_totales'] for c in charge_prevue) / capacite_totale * 100) if capacite_totale > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur rapport prévisionnel: {e}")
            return {'success': False, 'error': str(e)}
    
    # =========================================================================
    # INTERFACE CONVERSATIONNELLE
    # =========================================================================
    
    def repondre_question(self, question: str, contexte_additionnel: Optional[Dict] = None) -> str:
        """Répond à une question libre de l'utilisateur"""
        if not self.client:
            return "❌ Assistant IA non configuré. Veuillez configurer votre clé API Claude."
        
        try:
            # Collecter un contexte minimal pour aider Claude
            stats_rapides = {
                'nb_projets_actifs': self.db.execute_query("SELECT COUNT(*) as nb FROM projects WHERE statut = 'EN COURS'")[0]['nb'],
                'nb_employes': self.db.execute_query("SELECT COUNT(*) as nb FROM employees WHERE statut = 'ACTIF'")[0]['nb'],
                'nb_clients': self.db.execute_query("SELECT COUNT(*) as nb FROM companies")[0]['nb'],
                'nb_articles_inventaire': self.db.execute_query("SELECT COUNT(*) as nb FROM inventory_items")[0]['nb']
            }
            
            contexte_erp = f"""
            Contexte ERP actuel:
            - Projets en cours: {stats_rapides['nb_projets_actifs']}
            - Employés actifs: {stats_rapides['nb_employes']}
            - Clients: {stats_rapides['nb_clients']}
            - Articles inventaire: {stats_rapides['nb_articles_inventaire']}
            """
            
            if contexte_additionnel:
                contexte_erp += f"\n\nContexte additionnel:\n{json.dumps(contexte_additionnel, indent=2, default=str)}"
            
            # Appel à Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": f"""En tant qu'assistant IA de l'ERP Production DG Inc., répondez à cette question:

Question: {question}

{contexte_erp}

Répondez de manière claire, concise et professionnelle. Si la question nécessite des données spécifiques que vous n'avez pas, suggérez comment les obtenir."""
                }]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Erreur réponse question: {e}")
            return f"❌ Erreur: {str(e)}"
    
    # =========================================================================
    # CONVERSATION NATURELLE AVANCÉE - NOUVEAU MODULE
    # =========================================================================
    
    def conversation_naturelle(self, message_utilisateur: str, contexte_projet: Optional[str] = None) -> str:
        """
        Interface conversationnelle naturelle avec l'assistant IA
        L'assistant fouille toutes les données ERP pertinentes et répond naturellement
        
        Args:
            message_utilisateur: Message/question de l'utilisateur en langage naturel
            contexte_projet: ID ou nom du projet pour analyses contextuelles
        
        Returns:
            Réponse conversationnelle de l'assistant
        """
        if not self.client:
            return "😔 Désolé, je ne suis pas encore configuré. Il me faut une clé API Claude pour pouvoir discuter avec toi."
        
        try:
            # Collecter toutes les données pertinentes
            donnees_completes = self._fouiller_donnees_completes(contexte_projet)
            
            # Analyser l'intention du message
            intention = self._detecter_intention(message_utilisateur)
            
            # Construire le contexte conversationnel
            prompt_conversationnel = self._construire_prompt_conversationnel(
                message_utilisateur, 
                donnees_completes, 
                intention,
                contexte_projet
            )
            
            # Appel à Claude avec personnalité conversationnelle
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1200,
                temperature=0.8,  # Plus créatif pour la conversation
                messages=[{
                    "role": "user", 
                    "content": prompt_conversationnel
                }]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Erreur conversation naturelle: {e}")
            return f"😅 Oups, j'ai eu un petit problème technique : {str(e)}. Tu peux réessayer ?"
    
    def _fouiller_donnees_completes(self, contexte_projet: Optional[str] = None) -> Dict[str, Any]:
        """Fouille TOUTES les données ERP pertinentes pour une conversation riche"""
        donnees = {}
        
        try:
            # 1. DONNÉES PROJETS COMPLÈTES
            if contexte_projet:
                # Projet spécifique avec tous les détails
                projet_info = self.db.execute_query("""
                    SELECT p.*, c.nom as client_nom, c.type_entreprise
                    FROM projects p 
                    LEFT JOIN companies c ON p.client_company_id = c.id
                    WHERE p.id = ? OR p.nom_projet LIKE ?
                """, (contexte_projet, f"%{contexte_projet}%"))
                
                if projet_info:
                    projet = dict(projet_info[0])
                    
                    # Opérations du projet
                    operations = self.db.execute_query("""
                        SELECT o.*, wc.nom as poste_nom, e.prenom || ' ' || e.nom as employe_nom
                        FROM operations o
                        LEFT JOIN work_centers wc ON o.work_center_id = wc.id
                        LEFT JOIN employees e ON o.employee_id = e.id
                        WHERE o.project_id = ?
                        ORDER BY o.numero_sequence
                    """, (projet['id'],))
                    
                    # Time tracking du projet
                    pointages = self.db.execute_query("""
                        SELECT te.*, e.prenom || ' ' || e.nom as employe_nom
                        FROM time_entries te
                        LEFT JOIN employees e ON te.employee_id = e.id
                        WHERE te.project_id = ?
                        ORDER BY te.date_pointage DESC
                        LIMIT 20
                    """, (projet['id'],))
                    
                    # Matériaux utilisés
                    materiaux = self.db.execute_query("""
                        SELECT m.*, ii.nom as materiau_nom, ii.unite_primaire
                        FROM materials m
                        LEFT JOIN inventory_items ii ON m.inventory_item_id = ii.id
                        WHERE m.project_id = ?
                    """, (projet['id'],))
                    
                    donnees['projet_specifique'] = {
                        'info': projet,
                        'operations': [dict(o) for o in operations],
                        'pointages': [dict(p) for p in pointages],
                        'materiaux': [dict(m) for m in materiaux],
                        'avancement': self._calculer_avancement_projet(projet['id'])
                    }
            
            # 2. VUE D'ENSEMBLE TOUS PROJETS
            donnees['projets_globaux'] = self._collecter_donnees_projets()
            
            # 3. DONNÉES ÉQUIPES ET EMPLOYÉS
            donnees['employes'] = self._collecter_donnees_employes()
            
            # 4. INVENTAIRE ET MATÉRIAUX
            donnees['inventaire'] = self._collecter_donnees_inventaire()
            
            # 5. CRM ET CLIENTS
            donnees['crm'] = self._collecter_donnees_crm()
            
            # 5.5. DEVIS ET PROPOSITIONS COMMERCIALES
            donnees['devis'] = self._collecter_donnees_devis()
            
            # 6. PERFORMANCE ET MÉTRIQUES
            donnees['performance'] = self._collecter_metriques_performance()
            
            # 7. PLANIFICATION ET CAPACITÉ
            donnees['planification'] = self._analyser_capacite_planification()
            
            return donnees
            
        except Exception as e:
            logger.error(f"Erreur fouille données complètes: {e}")
            return {'erreur': str(e)}
    
    def _detecter_intention(self, message: str) -> str:
        """Détecte l'intention conversationnelle du message"""
        message_lower = message.lower()
        
        if any(mot in message_lower for mot in ['penses quoi', 'ton avis', 'que penses-tu', 'qu\'en penses-tu']):
            return 'demande_opinion'
        elif any(mot in message_lower for mot in ['comment va', 'comment ça va', 'état de', 'situation']):
            return 'demande_status'
        elif any(mot in message_lower for mot in ['problème', 'souci', 'risque', 'attention']):
            return 'detection_problemes'
        elif any(mot in message_lower for mot in ['conseil', 'recommande', 'suggère', 'que faire']):
            return 'demande_conseil'
        elif any(mot in message_lower for mot in ['budget', 'coût', 'prix', 'rentable']):
            return 'analyse_financiere'
        elif any(mot in message_lower for mot in ['équipe', 'employé', 'qui peut', 'compétence']):
            return 'gestion_equipe'
        elif any(mot in message_lower for mot in ['matériel', 'stock', 'inventaire', 'manque']):
            return 'gestion_materiel'
        elif any(mot in message_lower for mot in ['planning', 'délai', 'retard', 'temps']):
            return 'gestion_temps'
        elif any(mot in message_lower for mot in ['devis', 'estimation', 'proposition', 'cotation', 'offre']):
            return 'gestion_devis'
        elif any(mot in message_lower for mot in ['client', 'vente', 'commercial', 'conversion', 'prospect']):
            return 'analyse_commerciale'
        else:
            return 'question_generale'
    
    def _construire_prompt_conversationnel(self, message: str, donnees: Dict, intention: str, contexte_projet: Optional[str]) -> str:
        """Construit un prompt naturel pour Claude avec toutes les données"""
        
        # Personnalité de base
        prompt = f"""Tu es l'assistant IA expert de Constructo AI Inc., une entreprise de construction au Québec.
        
Tu es un collègue virtuel expérimenté qui connaît parfaitement tous les aspects de l'entreprise. Tu parles naturellement, comme un ami expert qui donne de bons conseils.

CARACTÈRE:
- Tutoies l'utilisateur (tu/toi)
- Utilise un ton amical et professionnel
- Donne des opinions personnalisées basées sur les vraies données
- N'hésite pas à exprimer des préoccupations ou félicitations
- Reste concis mais informatif
- Utilise des emojis appropriés avec parcimonie

DONNÉES EN TEMPS RÉEL DE L'ERP:
{json.dumps(donnees, indent=2, default=str, ensure_ascii=False)}

MESSAGE DE L'UTILISATEUR: "{message}"

INTENTION DÉTECTÉE: {intention}
"""
        
        # Ajout contextuel selon l'intention
        if intention == 'demande_opinion':
            prompt += """
            
INSTRUCTION: L'utilisateur te demande ton opinion. Analyse les données réelles et donne ton point de vue d'expert en construction. Sois franc et constructif."""
            
        elif intention == 'demande_status':
            prompt += """
            
INSTRUCTION: Donne un état de situation naturel, comme si tu faisais le point avec un collègue. Mentionne les points importants."""
            
        elif intention == 'detection_problemes':
            prompt += """
            
INSTRUCTION: Joue le rôle du collègue attentif qui repère les problèmes. Analyse les données pour identifier les vrais risques et alertes."""
            
        elif intention == 'demande_conseil':
            prompt += """
            
INSTRUCTION: Donne des conseils pratiques d'expert basés sur les données réelles. Soit spécifique et actionnable."""
        
        if contexte_projet:
            prompt += f"""
            
CONTEXTE PROJET: L'utilisateur parle du projet "{contexte_projet}". Concentre ta réponse sur ce projet spécifique en utilisant ses vraies données."""
        
        prompt += """

RÉPONSE ATTENDUE: Réponds naturellement comme un collègue expert qui a accès à toutes les données ERP. Sois personnel, informatif et utile."""
        
        return prompt
    
    def _collecter_donnees_employes(self) -> Dict[str, Any]:
        """Collecte données complètes des employés"""
        try:
            employes_actifs = self.db.execute_query("""
                SELECT e.*, COUNT(pa.project_id) as nb_projets_assignes
                FROM employees e
                LEFT JOIN project_assignments pa ON e.id = pa.employee_id
                WHERE e.statut = 'ACTIF'
                GROUP BY e.id
            """)
            
            # Charge de travail actuelle
            charge_actuelle = self.db.execute_query("""
                SELECT 
                    e.id,
                    e.prenom || ' ' || e.nom as nom_complet,
                    COUNT(DISTINCT te.project_id) as projets_actifs,
                    SUM(te.heures) as heures_semaine
                FROM employees e
                LEFT JOIN time_entries te ON e.id = te.employee_id 
                    AND te.date_pointage >= date('now', '-7 days')
                WHERE e.statut = 'ACTIF'
                GROUP BY e.id
            """)
            
            return {
                'employes_actifs': [dict(e) for e in employes_actifs],
                'charge_travail': [dict(c) for c in charge_actuelle],
                'nb_total_actifs': len(employes_actifs)
            }
        except Exception as e:
            return {'erreur': str(e)}
    
    def _collecter_metriques_performance(self) -> Dict[str, Any]:
        """Collecte métriques de performance globales"""
        try:
            # Efficacité projets (estimé vs réel)
            efficacite = self.db.execute_query("""
                SELECT 
                    AVG(CASE WHEN prix_final > 0 THEN (prix_estime / prix_final) * 100 ELSE NULL END) as precision_estimation,
                    COUNT(CASE WHEN statut = 'TERMINÉ' AND date_fin_reel <= date_prevu THEN 1 END) as projets_a_temps,
                    COUNT(CASE WHEN statut = 'TERMINÉ' THEN 1 END) as total_termines
                FROM projects
                WHERE created_at >= date('now', '-6 months')
            """)
            
            # Rentabilité par type de projet  
            rentabilite = self.db.execute_query("""
                SELECT 
                    type_construction,
                    COUNT(*) as nb_projets,
                    AVG(prix_estime) as prix_moyen,
                    AVG(CASE WHEN prix_final > 0 THEN prix_final - prix_estime ELSE NULL END) as marge_moyenne
                FROM projects
                WHERE statut = 'TERMINÉ'
                GROUP BY type_construction
            """)
            
            return {
                'efficacite_globale': dict(efficacite[0]) if efficacite else {},
                'rentabilite_types': [dict(r) for r in rentabilite]
            }
        except Exception as e:
            return {'erreur': str(e)}
    
    def _analyser_capacite_planification(self) -> Dict[str, Any]:
        """Analyse la capacité et planification"""
        try:
            # Charge par poste de travail
            charge_postes = self.db.execute_query("""
                SELECT 
                    wc.nom as poste,
                    wc.capacite_heures as capacite_max,
                    COUNT(o.id) as operations_prevues,
                    SUM(o.temps_estime) as heures_planifiees
                FROM work_centers wc
                LEFT JOIN operations o ON wc.id = o.work_center_id AND o.statut IN ('À FAIRE', 'EN COURS')
                GROUP BY wc.id
                ORDER BY (SUM(o.temps_estime) / wc.capacite_heures) DESC
            """)
            
            return {
                'charge_postes': [dict(c) for c in charge_postes],
                'postes_satures': [dict(c) for c in charge_postes 
                                 if c['heures_planifiees'] and c['capacite_max'] 
                                 and c['heures_planifiees'] > c['capacite_max'] * 0.9]
            }
        except Exception as e:
            return {'erreur': str(e)}
    
    def _calculer_avancement_projet(self, project_id: int) -> Dict[str, Any]:
        """Calcule l'avancement détaillé d'un projet"""
        try:
            operations = self.db.execute_query("""
                SELECT statut, COUNT(*) as nb
                FROM operations
                WHERE project_id = ?
                GROUP BY statut
            """, (project_id,))
            
            heures = self.db.execute_query("""
                SELECT 
                    SUM(temps_estime) as estime_total,
                    SUM(CASE WHEN statut = 'TERMINÉ' THEN temps_estime ELSE 0 END) as estime_termine,
                    COUNT(CASE WHEN statut = 'TERMINÉ' THEN 1 END) as ops_terminees,
                    COUNT(*) as ops_total
                FROM operations
                WHERE project_id = ?
            """, (project_id,))
            
            result = {}
            if operations:
                result['operations_par_statut'] = {op['statut']: op['nb'] for op in operations}
            
            if heures and heures[0]:
                h = heures[0]
                result['avancement_heures'] = (h['estime_termine'] / h['estime_total'] * 100) if h['estime_total'] else 0
                result['avancement_operations'] = (h['ops_terminees'] / h['ops_total'] * 100) if h['ops_total'] else 0
            
            return result
        except Exception as e:
            return {'erreur': str(e)}
    
    # =========================================================================
    # GESTION CRUD DES DEVIS VIA IA
    # =========================================================================
    
    def creer_devis_avec_ia(self, instructions: str, company_id: Optional[int] = None) -> Dict[str, Any]:
        """Crée un devis à partir d'instructions en langage naturel"""
        if not self.client:
            return {'success': False, 'error': "Assistant IA non configuré"}
        
        try:
            # Contexte pour la création
            contexte_creation = "Vous devez analyser les instructions et créer un devis structuré."
            
            # Si company_id fourni, récupérer les infos client
            if company_id:
                client_info = self.db.execute_query("""
                    SELECT c.*, 
                           AVG(CAST(f.montant_total AS REAL)) as montant_moyen_historique
                    FROM companies c
                    LEFT JOIN formulaires f ON c.id = f.company_id AND f.type_formulaire = 'ESTIMATION'
                    WHERE c.id = ?
                    GROUP BY c.id
                """, (company_id,))
                
                if client_info:
                    client_data = dict(client_info[0])
                    contexte_creation += f"""
                    
                    CLIENT:
                    - Nom: {client_data['nom']}
                    - Type: {client_data['type_entreprise']}
                    - Montant moyen historique: ${client_data.get('montant_moyen_historique', 0):,.2f}
                    """
            
            # Analyser les instructions avec Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": f"""Analysez ces instructions pour créer un devis et structurez les informations:

INSTRUCTIONS: {instructions}

{contexte_creation}

Fournissez une réponse JSON avec:
{{
    "titre_devis": "...",
    "description": "...",
    "articles": [
        {{
            "code_article": "...",
            "description": "...",
            "quantite": nombre,
            "prix_unitaire": nombre,
            "unite": "unité/m²/etc"
        }}
    ],
    "notes_particulieres": "...",
    "validite_jours": nombre,
    "conditions_paiement": "..."
}}

Soyez précis et réaliste dans les prix."""
                }]
            )
            
            # Tenter de parser la réponse JSON
            import json
            try:
                devis_structure = json.loads(response.content[0].text)
            except:
                # Si pas JSON, retourner l'analyse textuelle
                return {
                    'success': True,
                    'analyse_creation': response.content[0].text,
                    'devis_id': None,
                    'recommandation': "Structure du devis analysée, création manuelle requise"
                }
            
            # Créer le devis dans la base si structure valide
            if isinstance(devis_structure, dict) and 'articles' in devis_structure:
                from datetime import datetime, timedelta
                
                # Calculer totaux
                montant_total = sum(
                    float(article.get('quantite', 0)) * float(article.get('prix_unitaire', 0))
                    for article in devis_structure.get('articles', [])
                )
                
                # Date de validité
                validite_jours = devis_structure.get('validite_jours', 30)
                date_validite = (datetime.now() + timedelta(days=validite_jours)).strftime('%Y-%m-%d')
                
                # Créer le formulaire devis
                devis_data = {
                    'type_formulaire': 'ESTIMATION',
                    'statut': 'BROUILLON',
                    'company_id': company_id,
                    'titre': devis_structure.get('titre_devis', 'Devis généré par IA'),
                    'description': devis_structure.get('description', ''),
                    'montant_total': str(montant_total),
                    'total_ttc': str(montant_total * 1.15),  # Estimation TVA 15%
                    'date_validite': date_validite,
                    'conditions_paiement': devis_structure.get('conditions_paiement', 'Net 30 jours'),
                    'notes': devis_structure.get('notes_particulieres', '')
                }
                
                # Insérer dans la base
                devis_id = self.db.execute_query("""
                    INSERT INTO formulaires (
                        type_formulaire, statut, company_id, 
                        montant_total, date_echeance, notes, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    devis_data['type_formulaire'], devis_data['statut'], devis_data['company_id'],
                    devis_data['montant_total'], devis_data['date_validite'], 
                    f"Titre: {devis_data['titre']}\nDescription: {devis_data['description']}\nConditions: {devis_data['conditions_paiement']}"
                ), return_lastrowid=True)
                
                # Ajouter les lignes d'articles
                for idx, article in enumerate(devis_structure.get('articles', []), 1):
                    self.db.execute_query("""
                        INSERT INTO formulaire_lignes (
                            formulaire_id, code_article, description, quantite,
                            prix_unitaire, unite, sequence_ligne, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    """, (
                        devis_id, article.get('code_article', ''), article.get('description', ''),
                        str(article.get('quantite', 0)), str(article.get('prix_unitaire', 0)),
                        article.get('unite', 'unité'), idx
                    ))
                
                return {
                    'success': True,
                    'devis_id': devis_id,
                    'analyse_creation': response.content[0].text,
                    'montant_total': montant_total,
                    'nb_articles': len(devis_structure.get('articles', [])),
                    'message': f"Devis créé avec succès (#{devis_id})"
                }
            
            return {
                'success': True,
                'analyse_creation': response.content[0].text,
                'recommandation': "Analyse terminée, vérifiez la structure avant création"
            }
            
        except Exception as e:
            logger.error(f"Erreur création devis IA: {e}")
            return {'success': False, 'error': str(e)}
    
    def modifier_devis_avec_ia(self, devis_id: int, instructions: str) -> Dict[str, Any]:
        """Modifie un devis existant selon les instructions en langage naturel"""
        if not self.client:
            return {'success': False, 'error': "Assistant IA non configuré"}
        
        try:
            # Récupérer le devis existant
            devis_existant = self.analyser_devis_specifique(str(devis_id))
            if not devis_existant['success']:
                return devis_existant
            
            # Analyser les modifications demandées
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1200,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": f"""Analysez ces instructions de modification pour le devis existant:

DEVIS ACTUEL:
{json.dumps(devis_existant['donnees'], indent=2, default=str)}

INSTRUCTIONS DE MODIFICATION: {instructions}

Identifiez:
1. **Quels éléments modifier** (prix, quantités, articles, conditions)
2. **Nouvelles valeurs** à appliquer  
3. **Actions SQL suggérées** (UPDATE, INSERT, DELETE)
4. **Impact sur le total** du devis
5. **Recommandations** avant application

Soyez précis et listez chaque modification clairement."""
                }]
            )
            
            return {
                'success': True,
                'devis_id': devis_id,
                'analyse_modifications': response.content[0].text,
                'devis_actuel': devis_existant['donnees'],
                'recommandation': "Vérifiez les modifications suggérées avant application"
            }
            
        except Exception as e:
            logger.error(f"Erreur modification devis IA: {e}")
            return {'success': False, 'error': str(e)}
    
    def optimiser_prix_devis(self, devis_id: int) -> Dict[str, Any]:
        """Analyse et suggère des optimisations de prix pour un devis"""
        if not self.client:
            return {'success': False, 'error': "Assistant IA non configuré"}
        
        try:
            # Analyser le devis
            analyse_devis = self.analyser_devis_specifique(str(devis_id))
            if not analyse_devis['success']:
                return analyse_devis
            
            # Récupérer des données de marché comparative
            prix_marche = self.db.execute_query("""
                SELECT 
                    fl.code_article,
                    AVG(CAST(fl.prix_unitaire AS REAL)) as prix_moyen,
                    MIN(CAST(fl.prix_unitaire AS REAL)) as prix_min,
                    MAX(CAST(fl.prix_unitaire AS REAL)) as prix_max,
                    COUNT(*) as nb_occurrences
                FROM formulaire_lignes fl
                JOIN formulaires f ON fl.formulaire_id = f.id
                WHERE f.type_formulaire = 'ESTIMATION'
                AND f.created_at >= date('now', '-12 months')
                AND fl.code_article IN (
                    SELECT code_article FROM formulaire_lignes WHERE formulaire_id = ?
                )
                GROUP BY fl.code_article
            """, (devis_id,))
            
            # Analyse concurrentielle avec Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.4,
                messages=[{
                    "role": "user",
                    "content": f"""Analysez l'optimisation pricing de ce devis:

DEVIS À OPTIMISER:
{json.dumps(analyse_devis['donnees'], indent=2, default=str)}

DONNÉES MARCHÉ:
{json.dumps([dict(p) for p in prix_marche], indent=2, default=str)}

Fournissez:
1. **Analyse de positionnement** (prix vs marché)
2. **Articles sur/sous-évalués** 
3. **Optimisations suggérées** (nouveaux prix)
4. **Impact estimé** sur probabilité de conversion
5. **Stratégies de négociation** recommandées
6. **Prix minimum acceptable** (marge préservée)

Soyez orienté business et conversion commerciale."""
                }]
            )
            
            return {
                'success': True,
                'devis_id': devis_id,
                'analyse_pricing': response.content[0].text,
                'donnees_marche': [dict(p) for p in prix_marche],
                'metriques_actuelles': analyse_devis['metriques']
            }
            
        except Exception as e:
            logger.error(f"Erreur optimisation prix IA: {e}")
            return {'success': False, 'error': str(e)}
    
    def generer_relance_client_devis(self, devis_id: int) -> Dict[str, Any]:
        """Génère une proposition de relance client pour un devis en attente"""
        if not self.client:
            return {'success': False, 'error': "Assistant IA non configuré"}
        
        try:
            # Analyser le devis et l'historique client
            analyse_devis = self.analyser_devis_specifique(str(devis_id))
            if not analyse_devis['success']:
                return analyse_devis
            
            devis_data = analyse_devis['donnees']['devis']
            
            # Historique des interactions avec ce client
            interactions = self.db.execute_query("""
                SELECT type_interaction, commentaires, created_at
                FROM crm_interactions
                WHERE company_id = ?
                ORDER BY created_at DESC
                LIMIT 5
            """, (devis_data['company_id'],))
            
            # Générer la relance personnalisée
            response = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                temperature=0.6,
                messages=[{
                    "role": "user",
                    "content": f"""Rédigez une relance commerciale professionnelle et personnalisée:

DEVIS:
- Numéro: {devis_data['numero_document']}
- Date: {devis_data['created_at']}
- Montant: ${float(devis_data.get('montant_total', 0)):,.2f}
- Statut: {devis_data['statut']}

CLIENT: {devis_data.get('client_nom', 'Client')}

HISTORIQUE RÉCENT:
{json.dumps([dict(i) for i in interactions], indent=2, default=str)}

Rédigez un email de relance qui:
1. Rappelle le devis avec tact
2. Apporte de la valeur ajoutée
3. Crée un sentiment d'urgence approprié
4. Propose une action concrète (rdv, appel, etc.)
5. Reste courtois et professionnel

Tone: Professionnel mais chaleureux, orienté solution."""
                }]
            )
            
            return {
                'success': True,
                'devis_id': devis_id,
                'email_relance': response.content[0].text,
                'client_nom': devis_data.get('client_nom', ''),
                'montant_devis': float(devis_data.get('montant_total', 0)),
                'historique_interactions': [dict(i) for i in interactions]
            }
            
        except Exception as e:
            logger.error(f"Erreur génération relance IA: {e}")
            return {'success': False, 'error': str(e)}
    
    # =========================================================================
    # SUGGESTIONS AUTOMATIQUES
    # =========================================================================
    
    def generer_suggestions_quotidiennes(self) -> List[Dict[str, str]]:
        """Génère des suggestions d'actions quotidiennes"""
        suggestions = []
        
        try:
            # Vérifier les stocks bas
            stocks_bas = self.db.execute_query("""
                SELECT nom, quantite_metric, limite_minimale_metric
                FROM inventory_items
                WHERE quantite_metric <= limite_minimale_metric * 1.2
                ORDER BY (quantite_metric / NULLIF(limite_minimale_metric, 0))
                LIMIT 5
            """)
            
            if stocks_bas:
                suggestions.append({
                    'type': 'inventaire',
                    'priorite': 'haute',
                    'titre': f"🚨 {len(stocks_bas)} articles en stock critique",
                    'description': f"Articles à réapprovisionner: {', '.join(s['nom'] for s in stocks_bas[:3])}...",
                    'action': 'Voir l\'inventaire'
                })
            
            # Projets en retard
            projets_retard = self.db.execute_query("""
                SELECT nom_projet, date_prevu
                FROM projects
                WHERE date_prevu < date('now') AND statut != 'TERMINÉ'
                LIMIT 3
            """)
            
            if projets_retard:
                suggestions.append({
                    'type': 'projet',
                    'priorite': 'critique',
                    'titre': f"⏰ {len(projets_retard)} projets en retard",
                    'description': f"Projets à réviser: {', '.join(p['nom_projet'] for p in projets_retard)}",
                    'action': 'Voir les projets'
                })
            
            # Opportunités CRM à suivre
            opportunites_chaudes = self.db.execute_query("""
                SELECT COUNT(*) as nb
                FROM crm_opportunities
                WHERE statut IN ('Proposition', 'Négociation')
                AND updated_at < date('now', '-7 days')
            """)
            
            if opportunites_chaudes and opportunites_chaudes[0]['nb'] > 0:
                suggestions.append({
                    'type': 'crm',
                    'priorite': 'moyenne',
                    'titre': f"💼 {opportunites_chaudes[0]['nb']} opportunités à relancer",
                    'description': "Des opportunités commerciales nécessitent un suivi",
                    'action': 'Voir le CRM'
                })
            
            # Employés sans pointage récent
            employes_inactifs = self.db.execute_query("""
                SELECT COUNT(DISTINCT e.id) as nb
                FROM employees e
                WHERE e.statut = 'ACTIF'
                AND e.id NOT IN (
                    SELECT DISTINCT employee_id 
                    FROM time_entries 
                    WHERE date(punch_in) >= date('now', '-3 days')
                )
            """)
            
            if employes_inactifs and employes_inactifs[0]['nb'] > 0:
                suggestions.append({
                    'type': 'rh',
                    'priorite': 'basse',
                    'titre': f"👥 {employes_inactifs[0]['nb']} employés sans pointage récent",
                    'description': "Vérifier les pointages de temps",
                    'action': 'Voir le timetracker'
                })
            
        except Exception as e:
            logger.error(f"Erreur génération suggestions: {e}")
        
        return sorted(suggestions, key=lambda x: {'critique': 0, 'haute': 1, 'moyenne': 2, 'basse': 3}[x['priorite']])
    
    # =========================================================================
    # GESTION DES PRODUITS AVEC IA
    # =========================================================================
    
    def creer_produit_avec_ia(self, instructions: str) -> Dict[str, Any]:
        """Crée un produit à partir d'instructions en langage naturel"""
        if not self.client:
            return {'success': False, 'error': "Assistant IA non configuré"}
        
        try:
            # Importer les constantes du module produits
            from produits import CATEGORIES_PRODUITS, UNITES_VENTE, NUANCES_MATERIAUX
            
            # Contexte pour la création
            contexte_creation = f"""Vous devez analyser les instructions et créer un produit structuré pour l'industrie de la construction québécoise.

CATÉGORIES DISPONIBLES: {', '.join(CATEGORIES_PRODUITS)}
UNITÉS DE VENTE: {', '.join(UNITES_VENTE)}
NUANCES PAR MATÉRIAU: {json.dumps(NUANCES_MATERIAUX, indent=2)}"""
            
            # Analyser les instructions avec Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": f"""Analysez ces instructions pour créer un produit et structurez les informations:

INSTRUCTIONS: {instructions}

{contexte_creation}

Fournissez une réponse JSON avec:
{{
    "code_produit": "CODE-AUTO-GÉNÉRÉ",
    "nom": "Nom du produit",
    "description": "Description détaillée",
    "categorie": "Une des catégories disponibles",
    "materiau": "Matériau principal",
    "nuance": "Nuance/spécification technique",
    "dimensions": "Dimensions/format",
    "unite_vente": "Unité de vente appropriée",
    "prix_unitaire": nombre,
    "stock_disponible": nombre,
    "stock_minimum": nombre,
    "fournisseur_principal": "Nom du fournisseur suggéré",
    "notes_techniques": "Notes techniques importantes"
}}

Soyez précis et utilisez les catégories/nuances disponibles. Générez un code produit logique."""
                }]
            )
            
            # Tenter de parser la réponse JSON
            try:
                produit_structure = json.loads(response.content[0].text)
            except:
                # Si pas JSON, retourner l'analyse textuelle
                return {
                    'success': True,
                    'analyse_creation': response.content[0].text,
                    'produit_id': None,
                    'recommandation': "Structure du produit analysée, création manuelle requise"
                }
            
            # Créer le produit dans la base si structure valide
            if isinstance(produit_structure, dict) and 'nom' in produit_structure:
                # Valider et nettoyer les données
                produit_data = {
                    'code_produit': produit_structure.get('code_produit', '').upper(),
                    'nom': produit_structure.get('nom', ''),
                    'description': produit_structure.get('description', ''),
                    'categorie': produit_structure.get('categorie', 'Autres'),
                    'materiau': produit_structure.get('materiau', ''),
                    'nuance': produit_structure.get('nuance', ''),
                    'dimensions': produit_structure.get('dimensions', ''),
                    'unite_vente': produit_structure.get('unite_vente', 'unité'),
                    'prix_unitaire': float(produit_structure.get('prix_unitaire', 0)),
                    'stock_disponible': float(produit_structure.get('stock_disponible', 0)),
                    'stock_minimum': float(produit_structure.get('stock_minimum', 0)),
                    'fournisseur_principal': produit_structure.get('fournisseur_principal', ''),
                    'notes_techniques': produit_structure.get('notes_techniques', '')
                }
                
                # Importer et utiliser le gestionnaire de produits
                from produits import GestionnaireProduits
                gestionnaire = GestionnaireProduits(self.db)
                
                # Créer le produit
                produit_id = gestionnaire.ajouter_produit(produit_data)
                
                if produit_id:
                    return {
                        'success': True,
                        'produit_id': produit_id,
                        'analyse_creation': response.content[0].text,
                        'produit_data': produit_data,
                        'message': f"Produit créé avec succès (ID #{produit_id}): {produit_data['nom']}"
                    }
                else:
                    return {
                        'success': False,
                        'error': "Erreur lors de la création du produit dans la base de données"
                    }
            
            return {
                'success': True,
                'analyse_creation': response.content[0].text,
                'recommandation': "Analyse terminée, vérifiez la structure avant création"
            }
            
        except Exception as e:
            logger.error(f"Erreur création produit IA: {e}")
            return {'success': False, 'error': str(e)}
    
    def modifier_produit_avec_ia(self, produit_id: int, instructions: str) -> Dict[str, Any]:
        """Modifie un produit existant selon les instructions en langage naturel"""
        if not self.client:
            return {'success': False, 'error': "Assistant IA non configuré"}
        
        try:
            # Récupérer le produit existant
            from produits import GestionnaireProduits
            gestionnaire = GestionnaireProduits(self.db)
            produit_existant = gestionnaire.get_produit_by_id(produit_id)
            
            if not produit_existant:
                return {'success': False, 'error': f"Produit #{produit_id} non trouvé"}
            
            # Importer les constantes du module produits
            from produits import CATEGORIES_PRODUITS, UNITES_VENTE, NUANCES_MATERIAUX
            
            # Analyser les modifications demandées
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1200,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": f"""Analysez ces instructions de modification pour le produit existant:

PRODUIT ACTUEL:
{json.dumps(dict(produit_existant), indent=2, default=str)}

INSTRUCTIONS DE MODIFICATION: {instructions}

CATÉGORIES DISPONIBLES: {', '.join(CATEGORIES_PRODUITS)}
UNITÉS DE VENTE: {', '.join(UNITES_VENTE)}

Identifiez et structurez les modifications en JSON:
{{
    "modifications": {{
        "champ_à_modifier": "nouvelle_valeur",
        "autre_champ": nouvelle_valeur_numérique
    }},
    "analyse": "Explication des modifications",
    "impact": "Impact sur le stock/prix/fournisseur",
    "recommandations": "Recommandations avant application"
}}

Ne modifiez que les champs explicitement mentionnés dans les instructions."""
                }]
            )
            
            # Parser la réponse
            try:
                modification_structure = json.loads(response.content[0].text)
                modifications = modification_structure.get('modifications', {})
                
                if modifications:
                    # Appliquer les modifications
                    success = gestionnaire.modifier_produit(produit_id, modifications)
                    
                    if success:
                        return {
                            'success': True,
                            'produit_id': produit_id,
                            'modifications_appliquees': modifications,
                            'analyse_modifications': modification_structure.get('analyse', ''),
                            'impact': modification_structure.get('impact', ''),
                            'recommandations': modification_structure.get('recommandations', ''),
                            'message': f"Produit #{produit_id} modifié avec succès"
                        }
                    else:
                        return {'success': False, 'error': "Erreur lors de l'application des modifications"}
                else:
                    return {
                        'success': True,
                        'produit_id': produit_id,
                        'analyse_modifications': response.content[0].text,
                        'recommandation': "Aucune modification spécifique identifiée"
                    }
                    
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'produit_id': produit_id,
                    'analyse_modifications': response.content[0].text,
                    'recommandation': "Analyse textuelle des modifications - vérifiez manuellement"
                }
            
        except Exception as e:
            logger.error(f"Erreur modification produit IA: {e}")
            return {'success': False, 'error': str(e)}
    
    def analyser_produit_specifique(self, produit_id: int) -> Dict[str, Any]:
        """Analyse détaillée d'un produit spécifique"""
        if not self.client:
            return {'success': False, 'error': "Assistant IA non configuré"}
        
        try:
            # Récupérer les données du produit
            from produits import GestionnaireProduits
            gestionnaire = GestionnaireProduits(self.db)
            produit = gestionnaire.get_produit_by_id(produit_id)
            
            if not produit:
                return {'success': False, 'error': f"Produit #{produit_id} non trouvé"}
            
            # Récupérer les mouvements de stock récents
            mouvements = gestionnaire.get_historique_mouvements(produit_id)
            
            # Récupérer les statistiques
            stats = gestionnaire.get_statistics_produits()
            
            # Analyser avec Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.4,
                messages=[{
                    "role": "user",
                    "content": f"""Analysez ce produit de construction et fournissez des insights:

DONNÉES PRODUIT:
{json.dumps(dict(produit), indent=2, default=str)}

MOUVEMENTS RÉCENTS:
{json.dumps([dict(m) for m in mouvements[-10:]], indent=2, default=str) if mouvements else "Aucun mouvement récent"}

STATISTIQUES GLOBALES:
{json.dumps(stats, indent=2, default=str)}

Fournissez une analyse complète incluant:

1. **ÉTAT ACTUEL**
   - Niveau de stock et rotation
   - Positionnement prix/marché
   - Performance commerciale

2. **ANALYSE TECHNIQUE**
   - Conformité aux normes québécoises
   - Qualité des spécifications
   - Compatibilité avec autres produits

3. **OPTIMISATIONS SUGGÉRÉES**
   - Ajustements prix recommandés
   - Niveaux stock optimaux
   - Fournisseurs alternatifs

4. **ALERTES ET RISQUES**
   - Points d'attention
   - Risques identifiés
   - Actions préventives

5. **RECOMMANDATIONS STRATÉGIQUES**
   - Opportunités commerciales
   - Améliorations produit
   - Stratégie approvisionnement

Soyez précis et actionnable."""
                }]
            )
            
            return {
                'success': True,
                'produit_id': produit_id,
                'produit_nom': produit.get('nom', ''),
                'analyse_complete': response.content[0].text,
                'donnees_produit': dict(produit),
                'nb_mouvements_recents': len(mouvements) if mouvements else 0
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse produit IA: {e}")
            return {'success': False, 'error': str(e)}
    
    def optimiser_catalogue_produits(self) -> Dict[str, Any]:
        """Analyse et optimisation globale du catalogue produits"""
        if not self.client:
            return {'success': False, 'error': "Assistant IA non configuré"}
        
        try:
            # Récupérer toutes les données produits
            from produits import GestionnaireProduits
            gestionnaire = GestionnaireProduits(self.db)
            
            # Statistiques globales
            stats = gestionnaire.get_statistics_produits()
            
            # Produits à stock bas
            stock_bas = gestionnaire.get_produits_stock_bas()
            
            # Top produits par catégorie (requête personnalisée)
            top_produits = self.db.execute_query("""
                SELECT categorie, COUNT(*) as nb_produits,
                       AVG(prix_unitaire) as prix_moyen,
                       SUM(stock_disponible * prix_unitaire) as valeur_stock
                FROM produits 
                WHERE actif = 1
                GROUP BY categorie
                ORDER BY nb_produits DESC
            """)
            
            # Analyser avec Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.4,
                messages=[{
                    "role": "user",
                    "content": f"""Analysez ce catalogue de produits de construction québécois et proposez des optimisations:

STATISTIQUES GLOBALES:
{json.dumps(stats, indent=2, default=str)}

PRODUITS EN STOCK BAS:
{json.dumps([dict(p) for p in stock_bas], indent=2, default=str)}

RÉPARTITION PAR CATÉGORIE:
{json.dumps([dict(t) for t in top_produits], indent=2, default=str)}

Fournissez une analyse stratégique complète:

1. **SANTÉ DU CATALOGUE**
   - Diversification des catégories
   - Équilibre prix/qualité
   - Rotation des stocks

2. **OPTIMISATIONS IMMÉDIATES**
   - Produits à réapprovisionner en urgence
   - Ajustements de prix recommandés
   - Produits obsolètes à retirer

3. **STRATÉGIE D'APPROVISIONNEMENT**
   - Négociations fournisseurs prioritaires
   - Quantités optimales de commande
   - Diversification des sources

4. **OPPORTUNITÉS COMMERCIALES**
   - Nouveaux produits à ajouter
   - Bundles/packages suggérés
   - Marchés/segments à développer

5. **PLAN D'ACTION 30/60/90 JOURS**
   - Actions immédiates (30j)
   - Améliorations moyen terme (60j)
   - Stratégie long terme (90j)

Contexte: Industrie construction québécoise, normes CSA/BNQ, saisons hivernales."""
                }]
            )
            
            return {
                'success': True,
                'analyse_catalogue': response.content[0].text,
                'nb_produits_total': stats.get('nb_produits_total', 0),
                'nb_categories': len(top_produits),
                'nb_stock_bas': len(stock_bas),
                'valeur_stock_total': sum(t.get('valeur_stock', 0) for t in top_produits),
                'recommandations_generees': True
            }
            
        except Exception as e:
            logger.error(f"Erreur optimisation catalogue IA: {e}")
            return {'success': False, 'error': str(e)}
    
    # =========================================================================
    # GESTION DES EMPLOYÉS AVEC IA
    # =========================================================================
    
    def creer_employe_avec_ia(self, instructions: str) -> Dict[str, Any]:
        """Crée un employé à partir d'instructions en langage naturel"""
        if not self.client:
            return {'success': False, 'error': "Assistant IA non configuré"}
        
        try:
            # Importer les constantes du module employés
            from employees import DEPARTEMENTS, STATUTS_EMPLOYE, TYPES_CONTRAT, COMPETENCES_DISPONIBLES, NIVEAUX_COMPETENCE
            
            # Contexte pour la création
            contexte_creation = f"""Vous devez analyser les instructions et créer un employé pour l'industrie de la construction québécoise.

DÉPARTEMENTS DISPONIBLES: {', '.join(DEPARTEMENTS)}
STATUTS EMPLOYÉ: {', '.join(STATUTS_EMPLOYE)}
TYPES CONTRAT: {', '.join(TYPES_CONTRAT)}
COMPÉTENCES CONSTRUCTION: {', '.join(COMPETENCES_DISPONIBLES[:20])}... (50+ compétences disponibles)
NIVEAUX COMPÉTENCE: {', '.join(NIVEAUX_COMPETENCE)}"""
            
            # Analyser les instructions avec Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": f"""Analysez ces instructions pour créer un employé et structurez les informations:

INSTRUCTIONS: {instructions}

{contexte_creation}

Fournissez une réponse JSON avec:
{{
    "prenom": "Prénom",
    "nom": "Nom de famille",
    "email": "email@entreprise.com",
    "telephone": "514-123-4567",
    "poste": "Titre du poste",
    "departement": "Un des départements disponibles",
    "statut": "ACTIF",
    "type_contrat": "Un des types disponibles",
    "date_embauche": "YYYY-MM-DD",
    "salaire": nombre_annuel,
    "competences": [
        {{
            "nom": "Nom de la compétence",
            "niveau": "Niveau parmi les disponibles",
            "certifie": true/false,
            "date_obtention": "YYYY-MM-DD ou null"
        }}
    ],
    "notes": "Notes supplémentaires",
    "charge_travail": 80
}}

Calculez un salaire réaliste selon le poste au Québec 2024. Assignez des compétences pertinentes."""
                }]
            )
            
            # Tenter de parser la réponse JSON
            try:
                employe_structure = json.loads(response.content[0].text)
            except:
                # Si pas JSON, retourner l'analyse textuelle
                return {
                    'success': True,
                    'analyse_creation': response.content[0].text,
                    'employe_id': None,
                    'recommandation': "Structure de l'employé analysée, création manuelle requise"
                }
            
            # Créer l'employé dans la base si structure valide
            if isinstance(employe_structure, dict) and 'nom' in employe_structure:
                # Valider et nettoyer les données
                employe_data = {
                    'prenom': employe_structure.get('prenom', ''),
                    'nom': employe_structure.get('nom', ''),
                    'email': employe_structure.get('email', ''),
                    'telephone': employe_structure.get('telephone', ''),
                    'poste': employe_structure.get('poste', ''),
                    'departement': employe_structure.get('departement', 'ADMINISTRATION'),
                    'statut': employe_structure.get('statut', 'ACTIF'),
                    'type_contrat': employe_structure.get('type_contrat', 'CDI'),
                    'date_embauche': employe_structure.get('date_embauche', datetime.now().strftime('%Y-%m-%d')),
                    'salaire': float(employe_structure.get('salaire', 50000)),
                    'competences': employe_structure.get('competences', []),
                    'notes': employe_structure.get('notes', ''),
                    'charge_travail': int(employe_structure.get('charge_travail', 80))
                }
                
                # Importer et utiliser le gestionnaire d'employés
                from employees import GestionnaireEmployes
                gestionnaire = GestionnaireEmployes(self.db)
                
                # Créer l'employé
                employe_id = gestionnaire.ajouter_employe(employe_data)
                
                if employe_id:
                    return {
                        'success': True,
                        'employe_id': employe_id,
                        'analyse_creation': response.content[0].text,
                        'employe_data': employe_data,
                        'nb_competences': len(employe_data['competences']),
                        'message': f"Employé créé avec succès (ID #{employe_id}): {employe_data['prenom']} {employe_data['nom']}"
                    }
                else:
                    return {
                        'success': False,
                        'error': "Erreur lors de la création de l'employé dans la base de données"
                    }
            
            return {
                'success': True,
                'analyse_creation': response.content[0].text,
                'recommandation': "Analyse terminée, vérifiez la structure avant création"
            }
            
        except Exception as e:
            logger.error(f"Erreur création employé IA: {e}")
            return {'success': False, 'error': str(e)}
    
    def modifier_employe_avec_ia(self, employe_id: int, instructions: str) -> Dict[str, Any]:
        """Modifie un employé existant selon les instructions en langage naturel"""
        if not self.client:
            return {'success': False, 'error': "Assistant IA non configuré"}
        
        try:
            # Récupérer l'employé existant
            from employees import GestionnaireEmployes
            gestionnaire = GestionnaireEmployes(self.db)
            
            # Trouver l'employé dans la liste (cache)
            gestionnaire._load_employes_from_db()
            employe_existant = next((emp for emp in gestionnaire.employes if emp['id'] == employe_id), None)
            
            if not employe_existant:
                return {'success': False, 'error': f"Employé #{employe_id} non trouvé"}
            
            # Importer les constantes du module employés
            from employees import DEPARTEMENTS, STATUTS_EMPLOYE, TYPES_CONTRAT, NIVEAUX_COMPETENCE
            
            # Analyser les modifications demandées
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1200,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": f"""Analysez ces instructions de modification pour l'employé existant:

EMPLOYÉ ACTUEL:
{json.dumps(employe_existant, indent=2, default=str)}

INSTRUCTIONS DE MODIFICATION: {instructions}

DÉPARTEMENTS DISPONIBLES: {', '.join(DEPARTEMENTS)}
STATUTS DISPONIBLES: {', '.join(STATUTS_EMPLOYE)}
TYPES CONTRAT: {', '.join(TYPES_CONTRAT)}

Identifiez et structurez les modifications en JSON:
{{
    "modifications": {{
        "champ_à_modifier": "nouvelle_valeur",
        "salaire": nouveau_montant_numerique
    }},
    "analyse": "Explication des modifications",
    "impact_rh": "Impact sur la gestion RH",
    "recommandations": "Recommandations avant application"
}}

Ne modifiez que les champs explicitement mentionnés dans les instructions."""
                }]
            )
            
            # Parser la réponse
            try:
                modification_structure = json.loads(response.content[0].text)
                modifications = modification_structure.get('modifications', {})
                
                if modifications:
                    # Appliquer les modifications
                    success = gestionnaire.modifier_employe(employe_id, modifications)
                    
                    if success:
                        return {
                            'success': True,
                            'employe_id': employe_id,
                            'modifications_appliquees': modifications,
                            'analyse_modifications': modification_structure.get('analyse', ''),
                            'impact_rh': modification_structure.get('impact_rh', ''),
                            'recommandations': modification_structure.get('recommandations', ''),
                            'message': f"Employé #{employe_id} modifié avec succès"
                        }
                    else:
                        return {'success': False, 'error': "Erreur lors de l'application des modifications"}
                else:
                    return {
                        'success': True,
                        'employe_id': employe_id,
                        'analyse_modifications': response.content[0].text,
                        'recommandation': "Aucune modification spécifique identifiée"
                    }
                    
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'employe_id': employe_id,
                    'analyse_modifications': response.content[0].text,
                    'recommandation': "Analyse textuelle des modifications - vérifiez manuellement"
                }
            
        except Exception as e:
            logger.error(f"Erreur modification employé IA: {e}")
            return {'success': False, 'error': str(e)}
    
    # =========================================================================
    # GESTION DES CONTACTS AVEC IA
    # =========================================================================
    
    def creer_contact_avec_ia(self, instructions: str, company_id: Optional[int] = None) -> Dict[str, Any]:
        """Crée un contact à partir d'instructions en langage naturel"""
        if not self.client:
            return {'success': False, 'error': "Assistant IA non configuré"}
        
        try:
            # Contexte pour la création
            contexte_creation = "Vous devez analyser les instructions et créer un contact professionnel."
            
            # Si company_id fourni, récupérer les infos entreprise
            if company_id:
                entreprise_info = self.db.execute_query("""
                    SELECT nom, type_entreprise, secteur 
                    FROM companies WHERE id = ?
                """, (company_id,))
                
                if entreprise_info:
                    entreprise_data = dict(entreprise_info[0])
                    contexte_creation += f"""
                    
ENTREPRISE LIÉE:
- Nom: {entreprise_data['nom']}
- Type: {entreprise_data['type_entreprise']}
- Secteur: {entreprise_data['secteur']}"""
            
            # Analyser les instructions avec Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": f"""Analysez ces instructions pour créer un contact et structurez les informations:

INSTRUCTIONS: {instructions}

{contexte_creation}

Fournissez une réponse JSON avec:
{{
    "prenom": "Prénom",
    "nom_famille": "Nom de famille",
    "email": "email@entreprise.com",
    "telephone": "514-123-4567",
    "role_poste": "Titre du poste",
    "company_id": {company_id if company_id else 'null'},
    "notes": "Notes supplémentaires"
}}

Utilisez un format de téléphone québécois (514-XXX-XXXX) et un email professionnel."""
                }]
            )
            
            # Tenter de parser la réponse JSON
            try:
                contact_structure = json.loads(response.content[0].text)
            except:
                return {
                    'success': True,
                    'analyse_creation': response.content[0].text,
                    'contact_id': None,
                    'recommandation': "Structure du contact analysée, création manuelle requise"
                }
            
            # Créer le contact dans la base si structure valide
            if isinstance(contact_structure, dict) and 'nom_famille' in contact_structure:
                # Valider et nettoyer les données
                contact_data = {
                    'prenom': contact_structure.get('prenom', ''),
                    'nom_famille': contact_structure.get('nom_famille', ''),
                    'email': contact_structure.get('email', ''),
                    'telephone': contact_structure.get('telephone', ''),
                    'role_poste': contact_structure.get('role_poste', ''),
                    'company_id': contact_structure.get('company_id') or company_id,
                    'notes': contact_structure.get('notes', '')
                }
                
                # Importer et utiliser le gestionnaire CRM
                from crm import GestionnaireCRM
                gestionnaire = GestionnaireCRM(self.db)
                
                # Créer le contact
                contact_id = gestionnaire.ajouter_contact(contact_data)
                
                if contact_id:
                    return {
                        'success': True,
                        'contact_id': contact_id,
                        'analyse_creation': response.content[0].text,
                        'contact_data': contact_data,
                        'message': f"Contact créé avec succès (ID #{contact_id}): {contact_data['prenom']} {contact_data['nom_famille']}"
                    }
                else:
                    return {
                        'success': False,
                        'error': "Erreur lors de la création du contact dans la base de données"
                    }
            
            return {
                'success': True,
                'analyse_creation': response.content[0].text,
                'recommandation': "Analyse terminée, vérifiez la structure avant création"
            }
            
        except Exception as e:
            logger.error(f"Erreur création contact IA: {e}")
            return {'success': False, 'error': str(e)}
    
    def modifier_contact_avec_ia(self, contact_id: int, instructions: str) -> Dict[str, Any]:
        """Modifie un contact existant selon les instructions en langage naturel"""
        if not self.client:
            return {'success': False, 'error': "Assistant IA non configuré"}
        
        try:
            # Récupérer le contact existant
            contact_existant = self.db.execute_query("""
                SELECT c.*, co.nom as entreprise_nom
                FROM contacts c
                LEFT JOIN companies co ON c.company_id = co.id
                WHERE c.id = ?
            """, (contact_id,))
            
            if not contact_existant:
                return {'success': False, 'error': f"Contact #{contact_id} non trouvé"}
            
            contact_data = dict(contact_existant[0])
            
            # Analyser les modifications demandées
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": f"""Analysez ces instructions de modification pour le contact existant:

CONTACT ACTUEL:
{json.dumps(contact_data, indent=2, default=str)}

INSTRUCTIONS DE MODIFICATION: {instructions}

Identifiez et structurez les modifications en JSON:
{{
    "modifications": {{
        "champ_à_modifier": "nouvelle_valeur"
    }},
    "analyse": "Explication des modifications",
    "impact": "Impact sur les relations CRM",
    "recommandations": "Recommandations avant application"
}}

Ne modifiez que les champs explicitement mentionnés dans les instructions."""
                }]
            )
            
            # Parser la réponse
            try:
                modification_structure = json.loads(response.content[0].text)
                modifications = modification_structure.get('modifications', {})
                
                if modifications:
                    # Appliquer les modifications
                    from crm import GestionnaireCRM
                    gestionnaire = GestionnaireCRM(self.db)
                    success = gestionnaire.modifier_contact(contact_id, modifications)
                    
                    if success:
                        return {
                            'success': True,
                            'contact_id': contact_id,
                            'modifications_appliquees': modifications,
                            'analyse_modifications': modification_structure.get('analyse', ''),
                            'impact': modification_structure.get('impact', ''),
                            'recommandations': modification_structure.get('recommandations', ''),
                            'message': f"Contact #{contact_id} modifié avec succès"
                        }
                    else:
                        return {'success': False, 'error': "Erreur lors de l'application des modifications"}
                else:
                    return {
                        'success': True,
                        'contact_id': contact_id,
                        'analyse_modifications': response.content[0].text,
                        'recommandation': "Aucune modification spécifique identifiée"
                    }
                    
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'contact_id': contact_id,
                    'analyse_modifications': response.content[0].text,
                    'recommandation': "Analyse textuelle des modifications - vérifiez manuellement"
                }
            
        except Exception as e:
            logger.error(f"Erreur modification contact IA: {e}")
            return {'success': False, 'error': str(e)}
    
    # =========================================================================
    # GESTION DES ENTREPRISES AVEC IA
    # =========================================================================
    
    def creer_entreprise_avec_ia(self, instructions: str) -> Dict[str, Any]:
        """Crée une entreprise à partir d'instructions en langage naturel"""
        if not self.client:
            return {'success': False, 'error': "Assistant IA non configuré"}
        
        try:
            # Importer les constantes du module CRM
            from crm import TYPES_ENTREPRISES_CONSTRUCTION, SECTEURS_CONSTRUCTION
            
            # Contexte pour la création
            contexte_creation = f"""Vous devez analyser les instructions et créer une entreprise de construction québécoise.

TYPES D'ENTREPRISES: {', '.join(TYPES_ENTREPRISES_CONSTRUCTION)}
SECTEURS CONSTRUCTION: {', '.join(SECTEURS_CONSTRUCTION)}"""
            
            # Analyser les instructions avec Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1200,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": f"""Analysez ces instructions pour créer une entreprise et structurez les informations:

INSTRUCTIONS: {instructions}

{contexte_creation}

Fournissez une réponse JSON avec:
{{
    "nom": "Nom de l'entreprise",
    "type_entreprise": "Un des types disponibles",
    "secteur": "Un des secteurs disponibles",
    "adresse": "Adresse civique",
    "ville": "Ville",
    "province": "QC",
    "code_postal": "H1H 1H1",
    "pays": "Canada",
    "site_web": "www.entreprise.com",
    "notes": "Notes supplémentaires"
}}

Utilisez un format d'adresse québécois réaliste."""
                }]
            )
            
            # Tenter de parser la réponse JSON
            try:
                entreprise_structure = json.loads(response.content[0].text)
            except:
                return {
                    'success': True,
                    'analyse_creation': response.content[0].text,
                    'entreprise_id': None,
                    'recommandation': "Structure de l'entreprise analysée, création manuelle requise"
                }
            
            # Créer l'entreprise dans la base si structure valide
            if isinstance(entreprise_structure, dict) and 'nom' in entreprise_structure:
                # Valider et nettoyer les données
                entreprise_data = {
                    'nom': entreprise_structure.get('nom', ''),
                    'type_entreprise': entreprise_structure.get('type_entreprise', 'Entrepreneur général'),
                    'secteur': entreprise_structure.get('secteur', 'Construction résidentielle'),
                    'adresse': entreprise_structure.get('adresse', ''),
                    'ville': entreprise_structure.get('ville', ''),
                    'province': entreprise_structure.get('province', 'QC'),
                    'code_postal': entreprise_structure.get('code_postal', ''),
                    'pays': entreprise_structure.get('pays', 'Canada'),
                    'site_web': entreprise_structure.get('site_web', ''),
                    'notes': entreprise_structure.get('notes', '')
                }
                
                # Importer et utiliser le gestionnaire CRM
                from crm import GestionnaireCRM
                gestionnaire = GestionnaireCRM(self.db)
                
                # Créer l'entreprise
                entreprise_id = gestionnaire.ajouter_entreprise(entreprise_data)
                
                if entreprise_id:
                    return {
                        'success': True,
                        'entreprise_id': entreprise_id,
                        'analyse_creation': response.content[0].text,
                        'entreprise_data': entreprise_data,
                        'message': f"Entreprise créée avec succès (ID #{entreprise_id}): {entreprise_data['nom']}"
                    }
                else:
                    return {
                        'success': False,
                        'error': "Erreur lors de la création de l'entreprise dans la base de données"
                    }
            
            return {
                'success': True,
                'analyse_creation': response.content[0].text,
                'recommandation': "Analyse terminée, vérifiez la structure avant création"
            }
            
        except Exception as e:
            logger.error(f"Erreur création entreprise IA: {e}")
            return {'success': False, 'error': str(e)}
    
    def modifier_entreprise_avec_ia(self, entreprise_id: int, instructions: str) -> Dict[str, Any]:
        """Modifie une entreprise existante selon les instructions en langage naturel"""
        if not self.client:
            return {'success': False, 'error': "Assistant IA non configuré"}
        
        try:
            # Récupérer l'entreprise existante
            entreprise_existante = self.db.execute_query("""
                SELECT * FROM companies WHERE id = ?
            """, (entreprise_id,))
            
            if not entreprise_existante:
                return {'success': False, 'error': f"Entreprise #{entreprise_id} non trouvée"}
            
            entreprise_data = dict(entreprise_existante[0])
            
            # Importer les constantes du module CRM
            from crm import TYPES_ENTREPRISES_CONSTRUCTION, SECTEURS_CONSTRUCTION
            
            # Analyser les modifications demandées
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1200,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": f"""Analysez ces instructions de modification pour l'entreprise existante:

ENTREPRISE ACTUELLE:
{json.dumps(entreprise_data, indent=2, default=str)}

INSTRUCTIONS DE MODIFICATION: {instructions}

TYPES D'ENTREPRISES: {', '.join(TYPES_ENTREPRISES_CONSTRUCTION)}
SECTEURS: {', '.join(SECTEURS_CONSTRUCTION)}

Identifiez et structurez les modifications en JSON:
{{
    "modifications": {{
        "champ_à_modifier": "nouvelle_valeur"
    }},
    "analyse": "Explication des modifications",
    "impact_commercial": "Impact sur les relations commerciales",
    "recommandations": "Recommandations avant application"
}}

Ne modifiez que les champs explicitement mentionnés dans les instructions."""
                }]
            )
            
            # Parser la réponse
            try:
                modification_structure = json.loads(response.content[0].text)
                modifications = modification_structure.get('modifications', {})
                
                if modifications:
                    # Appliquer les modifications
                    from crm import GestionnaireCRM
                    gestionnaire = GestionnaireCRM(self.db)
                    success = gestionnaire.modifier_entreprise(entreprise_id, modifications)
                    
                    if success:
                        return {
                            'success': True,
                            'entreprise_id': entreprise_id,
                            'modifications_appliquees': modifications,
                            'analyse_modifications': modification_structure.get('analyse', ''),
                            'impact_commercial': modification_structure.get('impact_commercial', ''),
                            'recommandations': modification_structure.get('recommandations', ''),
                            'message': f"Entreprise #{entreprise_id} modifiée avec succès"
                        }
                    else:
                        return {'success': False, 'error': "Erreur lors de l'application des modifications"}
                else:
                    return {
                        'success': True,
                        'entreprise_id': entreprise_id,
                        'analyse_modifications': response.content[0].text,
                        'recommandation': "Aucune modification spécifique identifiée"
                    }
                    
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'entreprise_id': entreprise_id,
                    'analyse_modifications': response.content[0].text,
                    'recommandation': "Analyse textuelle des modifications - vérifiez manuellement"
                }
            
        except Exception as e:
            logger.error(f"Erreur modification entreprise IA: {e}")
            return {'success': False, 'error': str(e)}
    
    # =========================================================================
    # GESTION SUPPLY CHAIN AVEC IA
    # =========================================================================
    
    def creer_fournisseur_avec_ia(self, instructions: str) -> Dict[str, Any]:
        """
        Crée un fournisseur via instructions en langage naturel français québécois
        
        Args:
            instructions: Description en français du fournisseur à créer
            
        Returns:
            Dict avec success, fournisseur_id, et détails ou error
        """
        try:
            if not self.api_key:
                return {'success': False, 'error': 'Clé API Claude requise pour la création IA'}
            
            # Import du module fournisseurs
            from fournisseurs import GestionnaireFournisseurs, CATEGORIES_CONSTRUCTION, CERTIFICATIONS_CONSTRUCTION
            
            gestionnaire_fournisseurs = GestionnaireFournisseurs(self.db)
            
            # Construire le prompt système avec les données de référence
            prompt = f"""
Tu es un assistant spécialisé dans la création de fournisseurs pour une entreprise de construction au Québec.

CATÉGORIES DISPONIBLES: {', '.join(CATEGORIES_CONSTRUCTION)}

CERTIFICATIONS DISPONIBLES: {', '.join(CERTIFICATIONS_CONSTRUCTION)}

FORMATS REQUIS:
- Téléphone: format québécois (exemple: 514-555-0123, 418-xxx-xxxx, 1-800-xxx-xxxx)
- Code postal: format canadien (exemple: H3B 2M7, G1A 0A6)
- Email: format valide standard

À partir des instructions suivantes en français québécois:
"{instructions}"

Génère un JSON avec cette structure EXACTE:
{{
    "nom": "Nom de l'entreprise fournisseur",
    "adresse": "Adresse complète avec ville, province et code postal",
    "telephone": "Numéro au format québécois",
    "email": "Adresse email professionnelle",
    "site_web": "URL du site web (optionnel)",
    "personne_contact": "Nom du contact principal",
    "categories": ["catégorie1", "catégorie2"],
    "certifications": ["certification1", "certification2"],
    "delai_paiement_jours": 30,
    "remise_percentage": 0.0,
    "notes": "Notes additionnelles"
}}

IMPORTANT:
- Utilise UNIQUEMENT les catégories et certifications de la liste fournie
- Assure-toi que les formats téléphone et code postal sont québécois
- Si une information n'est pas précisée, utilise des valeurs par défaut logiques
- Respecte EXACTEMENT la structure JSON demandée
"""

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parser la réponse JSON
            response_text = response.content[0].text.strip()
            
            # Nettoyer la réponse si elle contient des balises markdown
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].strip()
            
            fournisseur_data = json.loads(response_text)
            
            # Valider les catégories
            categories_valides = [cat for cat in fournisseur_data.get('categories', []) 
                                if cat in CATEGORIES_CONSTRUCTION]
            fournisseur_data['categories'] = categories_valides
            
            # Valider les certifications
            certifications_valides = [cert for cert in fournisseur_data.get('certifications', [])
                                    if cert in CERTIFICATIONS_CONSTRUCTION]
            fournisseur_data['certifications'] = certifications_valides
            
            # Créer le fournisseur via le gestionnaire
            fournisseur_id = gestionnaire_fournisseurs.create_fournisseur(
                nom=fournisseur_data.get('nom', ''),
                adresse=fournisseur_data.get('adresse', ''),
                telephone=fournisseur_data.get('telephone', ''),
                email=fournisseur_data.get('email', ''),
                site_web=fournisseur_data.get('site_web', ''),
                personne_contact=fournisseur_data.get('personne_contact', ''),
                categories=fournisseur_data.get('categories', []),
                certifications=fournisseur_data.get('certifications', []),
                delai_paiement_jours=fournisseur_data.get('delai_paiement_jours', 30),
                remise_percentage=fournisseur_data.get('remise_percentage', 0.0),
                notes=fournisseur_data.get('notes', '')
            )
            
            return {
                'success': True,
                'fournisseur_id': fournisseur_id,
                'nom': fournisseur_data.get('nom'),
                'nb_categories': len(categories_valides),
                'nb_certifications': len(certifications_valides),
                'donnees_parsees': fournisseur_data
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON création fournisseur: {e}")
            return {'success': False, 'error': f'Erreur format réponse IA: {e}'}
        except Exception as e:
            logger.error(f"Erreur création fournisseur IA: {e}")
            return {'success': False, 'error': str(e)}
    
    def modifier_fournisseur_avec_ia(self, fournisseur_id: int, instructions: str) -> Dict[str, Any]:
        """
        Modifie un fournisseur existant via instructions en langage naturel
        
        Args:
            fournisseur_id: ID du fournisseur à modifier
            instructions: Instructions de modification en français
            
        Returns:
            Dict avec success, modifications_appliquees ou error
        """
        try:
            if not self.api_key:
                return {'success': False, 'error': 'Clé API Claude requise pour la modification IA'}
            
            from fournisseurs import GestionnaireFournisseurs, CATEGORIES_CONSTRUCTION, CERTIFICATIONS_CONSTRUCTION
            
            gestionnaire_fournisseurs = GestionnaireFournisseurs(self.db)
            
            # Récupérer le fournisseur existant
            fournisseur_actuel = self.db.execute_query(
                "SELECT * FROM suppliers WHERE id = ?",
                (fournisseur_id,)
            )
            
            if not fournisseur_actuel:
                return {'success': False, 'error': f'Fournisseur {fournisseur_id} non trouvé'}
            
            fournisseur = fournisseur_actuel[0]
            
            # Récupérer catégories et certifications actuelles
            categories_actuelles = self.db.execute_query(
                "SELECT category FROM supplier_categories WHERE supplier_id = ?",
                (fournisseur_id,)
            )
            categories_actuelles = [cat[0] for cat in categories_actuelles]
            
            certifications_actuelles = self.db.execute_query(
                "SELECT certification FROM supplier_certifications WHERE supplier_id = ?", 
                (fournisseur_id,)
            )
            certifications_actuelles = [cert[0] for cert in certifications_actuelles]
            
            prompt = f"""
Tu es un assistant spécialisé dans la modification de fournisseurs pour une entreprise de construction au Québec.

FOURNISSEUR ACTUEL:
- ID: {fournisseur_id}
- Nom: {fournisseur.get('nom', '')}
- Adresse: {fournisseur.get('adresse', '')}
- Téléphone: {fournisseur.get('telephone', '')}
- Email: {fournisseur.get('email', '')}
- Site web: {fournisseur.get('site_web', '')}
- Contact: {fournisseur.get('personne_contact', '')}
- Délai paiement: {fournisseur.get('delai_paiement_jours', 30)} jours
- Remise: {fournisseur.get('remise_percentage', 0)}%
- Notes: {fournisseur.get('notes', '')}
- Catégories: {categories_actuelles}
- Certifications: {certifications_actuelles}

CATÉGORIES DISPONIBLES: {', '.join(CATEGORIES_CONSTRUCTION)}
CERTIFICATIONS DISPONIBLES: {', '.join(CERTIFICATIONS_CONSTRUCTION)}

INSTRUCTIONS DE MODIFICATION:
"{instructions}"

Génère un JSON avec SEULEMENT les champs à modifier:
{{
    "nom": "nouveau nom si changé",
    "adresse": "nouvelle adresse si changée",
    "telephone": "nouveau téléphone au format québécois si changé",
    "email": "nouvel email si changé", 
    "site_web": "nouveau site web si changé",
    "personne_contact": "nouveau contact si changé",
    "categories": ["nouvelles catégories si changées"],
    "certifications": ["nouvelles certifications si changées"],
    "delai_paiement_jours": nouveau_délai_si_changé,
    "remise_percentage": nouveau_pourcentage_si_changé,
    "notes": "nouvelles notes si changées"
}}

IMPORTANT:
- N'inclus QUE les champs mentionnés dans les instructions
- Utilise UNIQUEMENT les catégories et certifications de la liste fournie
- Pour les catégories/certifications, fournis la liste COMPLÈTE si modifiée
- Respecte les formats québécois pour téléphone et adresse
"""

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parser la réponse
            response_text = response.content[0].text.strip()
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].strip()
            
            modifications = json.loads(response_text)
            
            # Appliquer les modifications
            modifications_appliquees = {}
            
            for champ, valeur in modifications.items():
                if champ in ['categories', 'certifications']:
                    # Traitement spécial pour les listes
                    if champ == 'categories':
                        valeurs_valides = [cat for cat in valeur if cat in CATEGORIES_CONSTRUCTION]
                        if valeurs_valides != categories_actuelles:
                            # Supprimer anciennes catégories
                            self.db.execute_query(
                                "DELETE FROM supplier_categories WHERE supplier_id = ?",
                                (fournisseur_id,)
                            )
                            # Ajouter nouvelles catégories
                            for cat in valeurs_valides:
                                self.db.execute_query(
                                    "INSERT INTO supplier_categories (supplier_id, category) VALUES (?, ?)",
                                    (fournisseur_id, cat)
                                )
                            modifications_appliquees['categories'] = valeurs_valides
                    
                    elif champ == 'certifications':
                        valeurs_valides = [cert for cert in valeur if cert in CERTIFICATIONS_CONSTRUCTION]
                        if valeurs_valides != certifications_actuelles:
                            # Supprimer anciennes certifications
                            self.db.execute_query(
                                "DELETE FROM supplier_certifications WHERE supplier_id = ?",
                                (fournisseur_id,)
                            )
                            # Ajouter nouvelles certifications
                            for cert in valeurs_valides:
                                self.db.execute_query(
                                    "INSERT INTO supplier_certifications (supplier_id, certification) VALUES (?, ?)",
                                    (fournisseur_id, cert)
                                )
                            modifications_appliquees['certifications'] = valeurs_valides
                else:
                    # Modification des champs standards
                    if fournisseur.get(champ) != valeur:
                        self.db.execute_query(
                            f"UPDATE suppliers SET {champ} = ? WHERE id = ?",
                            (valeur, fournisseur_id)
                        )
                        modifications_appliquees[champ] = valeur
            
            return {
                'success': True,
                'fournisseur_id': fournisseur_id,
                'modifications_appliquees': modifications_appliquees,
                'instructions_originales': instructions
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON modification fournisseur: {e}")
            return {'success': False, 'error': f'Erreur format réponse IA: {e}'}
        except Exception as e:
            logger.error(f"Erreur modification fournisseur IA: {e}")
            return {'success': False, 'error': str(e)}
    
    def creer_demande_prix_avec_ia(self, instructions: str) -> Dict[str, Any]:
        """
        Crée une demande de prix via instructions en langage naturel
        
        Args:
            instructions: Description en français de la demande de prix à créer
            
        Returns:
            Dict avec success, form_id et détails ou error
        """
        try:
            if not self.api_key:
                return {'success': False, 'error': 'Clé API Claude requise pour la création IA'}
            
            from fournisseurs import GestionnaireFournisseurs, CATEGORIES_CONSTRUCTION
            
            gestionnaire_fournisseurs = GestionnaireFournisseurs(self.db)
            
            # Récupérer la liste des fournisseurs disponibles
            fournisseurs_disponibles = self.db.execute_query("""
                SELECT id, nom, categories FROM suppliers 
                ORDER BY nom
            """)
            
            # Récupérer la liste des produits disponibles
            produits_disponibles = self.db.execute_query("""
                SELECT id, nom, unite_mesure FROM produits
                ORDER BY nom LIMIT 50
            """)
            
            prompt = f"""
Tu es un assistant spécialisé dans la création de demandes de prix pour une entreprise de construction au Québec.

FOURNISSEURS DISPONIBLES (premiers 20):
{chr(10).join([f"- ID {f[0]}: {f[1]}" for f in fournisseurs_disponibles[:20]])}

PRODUITS DISPONIBLES (premiers 20):
{chr(10).join([f"- ID {p[0]}: {p[1]} ({p[2]})" for p in produits_disponibles[:20]])}

INSTRUCTIONS:
"{instructions}"

Génère un JSON avec cette structure EXACTE:
{{
    "supplier_id": ID_du_fournisseur_choisi,
    "titre": "Titre descriptif de la demande",
    "description": "Description détaillée des besoins",
    "date_limite_reponse": "YYYY-MM-DD",
    "conditions_particulieres": "Conditions spéciales si applicables",
    "lignes": [
        {{
            "produit_id": ID_du_produit,
            "description": "Description spécifique de l'article",
            "quantite": quantité_numérique,
            "unite_mesure": "unité",
            "specifications": "Spécifications techniques"
        }}
    ]
}}

IMPORTANT:
- Choisis le fournisseur le plus approprié selon les catégories
- Utilise UNIQUEMENT les IDs de fournisseurs et produits de la liste
- Date limite: minimum 7 jours à partir d'aujourd'hui
- Quantités numériques uniquement
- Si produit non trouvé, utilise ID 1 avec description détaillée
"""

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parser la réponse
            response_text = response.content[0].text.strip()
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].strip()
                
            demande_data = json.loads(response_text)
            
            # Créer la demande de prix
            form_id = gestionnaire_fournisseurs.create_formulaire_with_lines(
                form_type='DEMANDE_PRIX',
                supplier_id=demande_data['supplier_id'],
                titre=demande_data.get('titre', 'Demande de prix'),
                description=demande_data.get('description', ''),
                date_limite_reponse=demande_data.get('date_limite_reponse'),
                conditions_particulieres=demande_data.get('conditions_particulieres', ''),
                lignes=demande_data.get('lignes', [])
            )
            
            return {
                'success': True,
                'form_id': form_id,
                'type': 'DEMANDE_PRIX',
                'supplier_id': demande_data['supplier_id'],
                'nb_lignes': len(demande_data.get('lignes', [])),
                'titre': demande_data.get('titre'),
                'donnees_parsees': demande_data
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON création demande prix: {e}")
            return {'success': False, 'error': f'Erreur format réponse IA: {e}'}
        except Exception as e:
            logger.error(f"Erreur création demande prix IA: {e}")
            return {'success': False, 'error': str(e)}
    
    def modifier_demande_prix_avec_ia(self, form_id: int, instructions: str) -> Dict[str, Any]:
        """
        Modifie une demande de prix existante via instructions en langage naturel
        
        Args:
            form_id: ID de la demande de prix à modifier
            instructions: Instructions de modification en français
            
        Returns:
            Dict avec success, modifications ou error
        """
        try:
            if not self.api_key:
                return {'success': False, 'error': 'Clé API Claude requise pour la modification IA'}
            
            # Récupérer la demande actuelle
            demande_actuelle = self.db.execute_query(
                "SELECT * FROM supplier_forms WHERE id = ? AND form_type = 'DEMANDE_PRIX'",
                (form_id,)
            )
            
            if not demande_actuelle:
                return {'success': False, 'error': f'Demande de prix {form_id} non trouvée'}
            
            demande = demande_actuelle[0]
            
            # Récupérer les lignes actuelles
            lignes_actuelles = self.db.execute_query(
                "SELECT * FROM supplier_form_lines WHERE form_id = ?",
                (form_id,)
            )
            
            prompt = f"""
Tu es un assistant spécialisé dans la modification de demandes de prix.

DEMANDE ACTUELLE:
- ID: {form_id}
- Fournisseur ID: {demande.get('supplier_id')}
- Titre: {demande.get('titre', '')}
- Description: {demande.get('description', '')}
- Date limite: {demande.get('date_limite_reponse', '')}
- Conditions: {demande.get('conditions_particulieres', '')}

LIGNES ACTUELLES:
{chr(10).join([f"- Ligne {ligne['id']}: {ligne.get('description', '')} - Qté: {ligne.get('quantite', 0)} {ligne.get('unite_mesure', '')}" for ligne in lignes_actuelles])}

INSTRUCTIONS DE MODIFICATION:
"{instructions}"

Génère un JSON avec SEULEMENT les champs à modifier:
{{
    "titre": "nouveau titre si changé",
    "description": "nouvelle description si changée", 
    "date_limite_reponse": "YYYY-MM-DD si changée",
    "conditions_particulieres": "nouvelles conditions si changées",
    "lignes_modifiees": [
        {{
            "ligne_id": ID_de_la_ligne_à_modifier_ou_null_pour_nouvelle,
            "action": "modifier" ou "ajouter" ou "supprimer",
            "description": "description de l'article",
            "quantite": quantité_numérique,
            "unite_mesure": "unité",
            "specifications": "spécifications"
        }}
    ]
}}

IMPORTANT:
- N'inclus QUE les modifications demandées
- Pour lignes_modifiées: ligne_id=null pour nouvelles lignes
- Actions possibles: "modifier", "ajouter", "supprimer"
"""

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parser et appliquer les modifications
            response_text = response.content[0].text.strip()
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
                
            modifications = json.loads(response_text)
            modifications_appliquees = {}
            
            # Modifier les champs de base
            for champ in ['titre', 'description', 'date_limite_reponse', 'conditions_particulieres']:
                if champ in modifications:
                    self.db.execute_query(
                        f"UPDATE supplier_forms SET {champ} = ? WHERE id = ?",
                        (modifications[champ], form_id)
                    )
                    modifications_appliquees[champ] = modifications[champ]
            
            # Traiter les modifications de lignes
            if 'lignes_modifiees' in modifications:
                lignes_traitees = []
                for ligne in modifications['lignes_modifiees']:
                    if ligne.get('action') == 'supprimer' and ligne.get('ligne_id'):
                        self.db.execute_query(
                            "DELETE FROM supplier_form_lines WHERE id = ?",
                            (ligne['ligne_id'],)
                        )
                        lignes_traitees.append(f"Supprimé ligne {ligne['ligne_id']}")
                    
                    elif ligne.get('action') == 'ajouter':
                        nouveau_id = self.db.execute_query(
                            """INSERT INTO supplier_form_lines 
                               (form_id, description, quantite, unite_mesure, specifications)
                               VALUES (?, ?, ?, ?, ?)""",
                            (form_id, ligne.get('description', ''), 
                             ligne.get('quantite', 1), ligne.get('unite_mesure', 'unité'),
                             ligne.get('specifications', '')),
                            get_lastrowid=True
                        )
                        lignes_traitees.append(f"Ajouté ligne {nouveau_id}")
                    
                    elif ligne.get('action') == 'modifier' and ligne.get('ligne_id'):
                        for field in ['description', 'quantite', 'unite_mesure', 'specifications']:
                            if field in ligne:
                                self.db.execute_query(
                                    f"UPDATE supplier_form_lines SET {field} = ? WHERE id = ?",
                                    (ligne[field], ligne['ligne_id'])
                                )
                        lignes_traitees.append(f"Modifié ligne {ligne['ligne_id']}")
                
                modifications_appliquees['lignes_traitees'] = lignes_traitees
            
            return {
                'success': True,
                'form_id': form_id,
                'type': 'DEMANDE_PRIX',
                'modifications_appliquees': modifications_appliquees,
                'instructions_originales': instructions
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON modification demande prix: {e}")
            return {'success': False, 'error': f'Erreur format réponse IA: {e}'}
        except Exception as e:
            logger.error(f"Erreur modification demande prix IA: {e}")
            return {'success': False, 'error': str(e)}
    
    def creer_bon_achat_avec_ia(self, instructions: str) -> Dict[str, Any]:
        """
        Crée un bon d'achat via instructions en langage naturel
        
        Args:
            instructions: Description en français du bon d'achat à créer
            
        Returns:
            Dict avec success, form_id et détails ou error
        """
        try:
            if not self.api_key:
                return {'success': False, 'error': 'Clé API Claude requise pour la création IA'}
            
            from fournisseurs import GestionnaireFournisseurs
            
            gestionnaire_fournisseurs = GestionnaireFournisseurs(self.db)
            
            # Récupérer fournisseurs et produits
            fournisseurs_disponibles = self.db.execute_query("""
                SELECT id, nom FROM suppliers ORDER BY nom
            """)
            
            produits_disponibles = self.db.execute_query("""
                SELECT id, nom, unite_mesure, prix_unitaire FROM produits
                ORDER BY nom LIMIT 50
            """)
            
            prompt = f"""
Tu es un assistant spécialisé dans la création de bons d'achat pour une entreprise de construction au Québec.

FOURNISSEURS DISPONIBLES (premiers 15):
{chr(10).join([f"- ID {f[0]}: {f[1]}" for f in fournisseurs_disponibles[:15]])}

PRODUITS DISPONIBLES (premiers 15):
{chr(10).join([f"- ID {p[0]}: {p[1]} ({p[2]}) - {p[3] or 0}$" for p in produits_disponibles[:15]])}

INSTRUCTIONS:
"{instructions}"

Génère un JSON avec cette structure EXACTE:
{{
    "supplier_id": ID_du_fournisseur,
    "titre": "Titre du bon d'achat",
    "description": "Description de la commande",
    "date_livraison_souhaitee": "YYYY-MM-DD",
    "adresse_livraison": "Adresse de livraison complète",
    "conditions_particulieres": "Conditions spéciales",
    "lignes": [
        {{
            "produit_id": ID_du_produit,
            "description": "Description spécifique",
            "quantite": quantité_numérique,
            "unite_mesure": "unité",
            "prix_unitaire": prix_en_dollars,
            "specifications": "Spécifications si nécessaires"
        }}
    ]
}}

IMPORTANT:
- Utilise UNIQUEMENT les IDs de fournisseurs et produits listés
- Prix en dollars canadiens (format numérique, ex: 125.50)
- Date de livraison: minimum 3 jours ouvrables
- Adresse de livraison au Québec avec code postal
- Quantités et prix numériques uniquement
"""

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514", 
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parser la réponse
            response_text = response.content[0].text.strip()
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].strip()
                
            bon_achat_data = json.loads(response_text)
            
            # Créer le bon d'achat
            form_id = gestionnaire_fournisseurs.create_formulaire_with_lines(
                form_type='BON_ACHAT',
                supplier_id=bon_achat_data['supplier_id'],
                titre=bon_achat_data.get('titre', 'Bon d\'achat'),
                description=bon_achat_data.get('description', ''),
                date_livraison_souhaitee=bon_achat_data.get('date_livraison_souhaitee'),
                adresse_livraison=bon_achat_data.get('adresse_livraison', ''),
                conditions_particulieres=bon_achat_data.get('conditions_particulieres', ''),
                lignes=bon_achat_data.get('lignes', [])
            )
            
            # Calculer le total
            total = sum([
                float(ligne.get('quantite', 0)) * float(ligne.get('prix_unitaire', 0))
                for ligne in bon_achat_data.get('lignes', [])
            ])
            
            return {
                'success': True,
                'form_id': form_id,
                'type': 'BON_ACHAT',
                'supplier_id': bon_achat_data['supplier_id'],
                'nb_lignes': len(bon_achat_data.get('lignes', [])),
                'total_estime': round(total, 2),
                'titre': bon_achat_data.get('titre'),
                'donnees_parsees': bon_achat_data
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON création bon achat: {e}")
            return {'success': False, 'error': f'Erreur format réponse IA: {e}'}
        except Exception as e:
            logger.error(f"Erreur création bon achat IA: {e}")
            return {'success': False, 'error': str(e)}
    
    def modifier_bon_achat_avec_ia(self, form_id: int, instructions: str) -> Dict[str, Any]:
        """
        Modifie un bon d'achat existant via instructions en langage naturel
        
        Args:
            form_id: ID du bon d'achat à modifier
            instructions: Instructions de modification en français
            
        Returns:
            Dict avec success, modifications ou error
        """
        try:
            if not self.api_key:
                return {'success': False, 'error': 'Clé API Claude requise pour la modification IA'}
            
            # Récupérer le bon d'achat actuel
            bon_actuel = self.db.execute_query(
                "SELECT * FROM supplier_forms WHERE id = ? AND form_type = 'BON_ACHAT'",
                (form_id,)
            )
            
            if not bon_actuel:
                return {'success': False, 'error': f'Bon d\'achat {form_id} non trouvé'}
            
            bon = bon_actuel[0]
            
            # Récupérer les lignes actuelles
            lignes_actuelles = self.db.execute_query(
                "SELECT * FROM supplier_form_lines WHERE form_id = ?",
                (form_id,)
            )
            
            # Calculer total actuel
            total_actuel = sum([
                float(ligne.get('quantite', 0)) * float(ligne.get('prix_unitaire', 0))
                for ligne in lignes_actuelles
            ])
            
            prompt = f"""
Tu es un assistant spécialisé dans la modification de bons d'achat.

BON D'ACHAT ACTUEL:
- ID: {form_id}
- Fournisseur ID: {bon.get('supplier_id')}
- Titre: {bon.get('titre', '')}
- Description: {bon.get('description', '')}
- Date livraison: {bon.get('date_livraison_souhaitee', '')}
- Adresse livraison: {bon.get('adresse_livraison', '')}
- Conditions: {bon.get('conditions_particulieres', '')}
- Total actuel: {total_actuel:.2f}$

LIGNES ACTUELLES:
{chr(10).join([f"- Ligne {ligne['id']}: {ligne.get('description', '')} - Qté: {ligne.get('quantite', 0)} à {ligne.get('prix_unitaire', 0)}$" for ligne in lignes_actuelles])}

INSTRUCTIONS DE MODIFICATION:
"{instructions}"

Génère un JSON avec SEULEMENT les champs à modifier:
{{
    "titre": "nouveau titre si changé",
    "description": "nouvelle description si changée",
    "date_livraison_souhaitee": "YYYY-MM-DD si changée", 
    "adresse_livraison": "nouvelle adresse si changée",
    "conditions_particulieres": "nouvelles conditions si changées",
    "lignes_modifiees": [
        {{
            "ligne_id": ID_de_la_ligne_ou_null_pour_nouvelle,
            "action": "modifier" ou "ajouter" ou "supprimer",
            "description": "description",
            "quantite": quantité_numérique,
            "unite_mesure": "unité",
            "prix_unitaire": prix_numérique,
            "specifications": "spécifications"
        }}
    ]
}}

IMPORTANT:
- N'inclus QUE les modifications demandées
- Prix en format numérique (ex: 125.50)
- Actions: "modifier", "ajouter", "supprimer"
"""

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parser et appliquer modifications
            response_text = response.content[0].text.strip()
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
                
            modifications = json.loads(response_text)
            modifications_appliquees = {}
            
            # Modifier champs de base
            for champ in ['titre', 'description', 'date_livraison_souhaitee', 'adresse_livraison', 'conditions_particulieres']:
                if champ in modifications:
                    self.db.execute_query(
                        f"UPDATE supplier_forms SET {champ} = ? WHERE id = ?",
                        (modifications[champ], form_id)
                    )
                    modifications_appliquees[champ] = modifications[champ]
            
            # Traiter les modifications de lignes
            if 'lignes_modifiees' in modifications:
                lignes_traitees = []
                for ligne in modifications['lignes_modifiees']:
                    if ligne.get('action') == 'supprimer' and ligne.get('ligne_id'):
                        self.db.execute_query(
                            "DELETE FROM supplier_form_lines WHERE id = ?",
                            (ligne['ligne_id'],)
                        )
                        lignes_traitees.append(f"Supprimé ligne {ligne['ligne_id']}")
                    
                    elif ligne.get('action') == 'ajouter':
                        nouveau_id = self.db.execute_query(
                            """INSERT INTO supplier_form_lines 
                               (form_id, description, quantite, unite_mesure, prix_unitaire, specifications)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (form_id, ligne.get('description', ''), 
                             ligne.get('quantite', 1), ligne.get('unite_mesure', 'unité'),
                             ligne.get('prix_unitaire', 0.0), ligne.get('specifications', '')),
                            get_lastrowid=True
                        )
                        lignes_traitees.append(f"Ajouté ligne {nouveau_id}")
                    
                    elif ligne.get('action') == 'modifier' and ligne.get('ligne_id'):
                        for field in ['description', 'quantite', 'unite_mesure', 'prix_unitaire', 'specifications']:
                            if field in ligne:
                                self.db.execute_query(
                                    f"UPDATE supplier_form_lines SET {field} = ? WHERE id = ?",
                                    (ligne[field], ligne['ligne_id'])
                                )
                        lignes_traitees.append(f"Modifié ligne {ligne['ligne_id']}")
                
                modifications_appliquees['lignes_traitees'] = lignes_traitees
            
            # Recalculer le nouveau total
            nouvelles_lignes = self.db.execute_query(
                "SELECT quantite, prix_unitaire FROM supplier_form_lines WHERE form_id = ?",
                (form_id,)
            )
            nouveau_total = sum([
                float(ligne[0] or 0) * float(ligne[1] or 0) 
                for ligne in nouvelles_lignes
            ])
            
            return {
                'success': True,
                'form_id': form_id,
                'type': 'BON_ACHAT',
                'modifications_appliquees': modifications_appliquees,
                'ancien_total': total_actuel,
                'nouveau_total': round(nouveau_total, 2),
                'instructions_originales': instructions
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON modification bon achat: {e}")
            return {'success': False, 'error': f'Erreur format réponse IA: {e}'}
        except Exception as e:
            logger.error(f"Erreur modification bon achat IA: {e}")
            return {'success': False, 'error': str(e)}
    
    # =========================================================================
    # GESTION POSTES TRAVAIL & BONS TRAVAIL AVEC IA
    # =========================================================================
    
    def creer_poste_travail_avec_ia(self, instructions: str) -> Dict[str, Any]:
        """
        Crée un poste de travail via instructions en langage naturel français québécois
        
        Args:
            instructions: Description en français du poste de travail à créer
            
        Returns:
            Dict avec success, work_center_id, et détails ou error
        """
        try:
            if not self.api_key:
                return {'success': False, 'error': 'Clé API Claude requise pour la création IA'}
            
            # Départements et catégories disponibles selon le système
            departements_disponibles = [
                'PRODUCTION', 'STRUCTURE', 'QUALITÉ', 'INGÉNIERIE', 
                'ADMINISTRATION', 'COMMERCIAL', 'DIRECTION'
            ]
            
            categories_disponibles = [
                'TERRASSEMENT', 'BÉTON', 'OSSATURE', 'MÉCANIQUE', 
                'FINITION', 'MANUEL', 'INSPECTION'
            ]
            
            statuts_disponibles = ['ACTIF', 'MAINTENANCE', 'INACTIF']
            
            prompt = f"""
Tu es un assistant spécialisé dans la création de postes de travail pour une entreprise de construction au Québec.

DÉPARTEMENTS DISPONIBLES: {', '.join(departements_disponibles)}

CATÉGORIES DISPONIBLES: {', '.join(categories_disponibles)}

STATUTS DISPONIBLES: {', '.join(statuts_disponibles)}

À partir des instructions suivantes en français québécois:
"{instructions}"

Génère un JSON avec cette structure EXACTE:
{{
    "nom": "Nom descriptif du poste de travail",
    "departement": "DEPARTMENT_choisi",
    "categorie": "CATEGORIE_choisie", 
    "type_machine": "Type et modèle de machine si applicable",
    "capacite_theorique": 8.0,
    "operateurs_requis": 1,
    "cout_horaire": 50.0,
    "competences_requises": "Compétences nécessaires pour opérer ce poste",
    "statut": "ACTIF",
    "localisation": "Emplacement physique du poste"
}}

IMPORTANT:
- Utilise UNIQUEMENT les départements et catégories de la liste fournie
- Capacité théorique en heures par jour (0.1 à 24.0)
- Opérateurs requis: nombre entier (1 à 10)
- Coût horaire en dollars canadiens
- Si une information n'est pas précisée, utilise des valeurs par défaut logiques
- Pour les compétences, sois spécifique aux métiers de construction québécois
- Respecte EXACTEMENT la structure JSON demandée
"""

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parser la réponse JSON
            response_text = response.content[0].text.strip()
            
            # Nettoyer la réponse si elle contient des balises markdown
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].strip()
            
            poste_data = json.loads(response_text)
            
            # Validation des valeurs
            if poste_data.get('departement') not in departements_disponibles:
                poste_data['departement'] = 'PRODUCTION'
            
            if poste_data.get('categorie') not in categories_disponibles:
                poste_data['categorie'] = 'MANUEL'
                
            if poste_data.get('statut') not in statuts_disponibles:
                poste_data['statut'] = 'ACTIF'
            
            # Valider les valeurs numériques
            poste_data['capacite_theorique'] = max(0.1, min(24.0, float(poste_data.get('capacite_theorique', 8.0))))
            poste_data['operateurs_requis'] = max(1, min(10, int(poste_data.get('operateurs_requis', 1))))
            poste_data['cout_horaire'] = max(0.0, float(poste_data.get('cout_horaire', 50.0)))
            
            # Créer le poste de travail via la base de données
            work_center_id = self.db.add_work_center(poste_data)
            
            if work_center_id:
                return {
                    'success': True,
                    'work_center_id': work_center_id,
                    'nom': poste_data.get('nom'),
                    'departement': poste_data.get('departement'),
                    'categorie': poste_data.get('categorie'),
                    'capacite_theorique': poste_data.get('capacite_theorique'),
                    'cout_horaire': poste_data.get('cout_horaire'),
                    'donnees_parsees': poste_data
                }
            else:
                return {'success': False, 'error': 'Erreur lors de la création du poste en base'}
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON création poste travail: {e}")
            return {'success': False, 'error': f'Erreur format réponse IA: {e}'}
        except Exception as e:
            logger.error(f"Erreur création poste travail IA: {e}")
            return {'success': False, 'error': str(e)}
    
    def modifier_poste_travail_avec_ia(self, work_center_id: int, instructions: str) -> Dict[str, Any]:
        """
        Modifie un poste de travail existant via instructions en langage naturel
        
        Args:
            work_center_id: ID du poste de travail à modifier
            instructions: Instructions de modification en français
            
        Returns:
            Dict avec success, modifications_appliquees ou error
        """
        try:
            if not self.api_key:
                return {'success': False, 'error': 'Clé API Claude requise pour la modification IA'}
            
            # Récupérer le poste existant
            poste_actuel = self.db.get_work_center_by_id(work_center_id)
            
            if not poste_actuel:
                return {'success': False, 'error': f'Poste de travail {work_center_id} non trouvé'}
            
            departements_disponibles = [
                'PRODUCTION', 'STRUCTURE', 'QUALITÉ', 'INGÉNIERIE', 
                'ADMINISTRATION', 'COMMERCIAL', 'DIRECTION'
            ]
            
            categories_disponibles = [
                'TERRASSEMENT', 'BÉTON', 'OSSATURE', 'MÉCANIQUE', 
                'FINITION', 'MANUEL', 'INSPECTION'
            ]
            
            statuts_disponibles = ['ACTIF', 'MAINTENANCE', 'INACTIF']
            
            prompt = f"""
Tu es un assistant spécialisé dans la modification de postes de travail pour une entreprise de construction au Québec.

POSTE ACTUEL:
- ID: {work_center_id}
- Nom: {poste_actuel.get('nom', '')}
- Département: {poste_actuel.get('departement', '')}
- Catégorie: {poste_actuel.get('categorie', '')}
- Type machine: {poste_actuel.get('type_machine', '')}
- Capacité théorique: {poste_actuel.get('capacite_theorique', 8.0)} h/jour
- Opérateurs requis: {poste_actuel.get('operateurs_requis', 1)}
- Coût horaire: {poste_actuel.get('cout_horaire', 50.0)}$
- Compétences: {poste_actuel.get('competences_requises', '')}
- Statut: {poste_actuel.get('statut', 'ACTIF')}
- Localisation: {poste_actuel.get('localisation', '')}

DÉPARTEMENTS DISPONIBLES: {', '.join(departements_disponibles)}
CATÉGORIES DISPONIBLES: {', '.join(categories_disponibles)}
STATUTS DISPONIBLES: {', '.join(statuts_disponibles)}

INSTRUCTIONS DE MODIFICATION:
"{instructions}"

Génère un JSON avec SEULEMENT les champs à modifier:
{{
    "nom": "nouveau nom si changé",
    "departement": "NOUVEAU_DEPT si changé",
    "categorie": "NOUVELLE_CAT si changée",
    "type_machine": "nouveau type machine si changé",
    "capacite_theorique": nouvelle_capacité_si_changée,
    "operateurs_requis": nouveau_nombre_si_changé,
    "cout_horaire": nouveau_coût_si_changé,
    "competences_requises": "nouvelles compétences si changées",
    "statut": "NOUVEAU_STATUT si changé",
    "localisation": "nouvelle localisation si changée"
}}

IMPORTANT:
- N'inclus QUE les champs mentionnés dans les instructions
- Utilise UNIQUEMENT les départements/catégories/statuts de la liste fournie
- Respecte les contraintes numériques (capacité 0.1-24.0, opérateurs 1-10, coût >= 0)
- Pour compétences, sois spécifique aux métiers construction québécois
"""

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parser la réponse
            response_text = response.content[0].text.strip()
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].strip()
            
            modifications = json.loads(response_text)
            
            # Valider et appliquer les modifications
            modifications_validees = {}
            
            for champ, valeur in modifications.items():
                if champ == 'departement' and valeur not in departements_disponibles:
                    continue
                elif champ == 'categorie' and valeur not in categories_disponibles:
                    continue
                elif champ == 'statut' and valeur not in statuts_disponibles:
                    continue
                elif champ == 'capacite_theorique':
                    valeur = max(0.1, min(24.0, float(valeur)))
                elif champ == 'operateurs_requis':
                    valeur = max(1, min(10, int(valeur)))
                elif champ == 'cout_horaire':
                    valeur = max(0.0, float(valeur))
                
                # Vérifier si la valeur a vraiment changé
                if poste_actuel.get(champ) != valeur:
                    modifications_validees[champ] = valeur
            
            # Appliquer les modifications si il y en a
            if modifications_validees:
                success = self.db.update_work_center(work_center_id, modifications_validees)
                
                if success:
                    return {
                        'success': True,
                        'work_center_id': work_center_id,
                        'modifications_appliquees': modifications_validees,
                        'instructions_originales': instructions
                    }
                else:
                    return {'success': False, 'error': 'Erreur lors de la mise à jour en base'}
            else:
                return {
                    'success': True,
                    'work_center_id': work_center_id,
                    'modifications_appliquees': {},
                    'message': 'Aucune modification nécessaire'
                }
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON modification poste travail: {e}")
            return {'success': False, 'error': f'Erreur format réponse IA: {e}'}
        except Exception as e:
            logger.error(f"Erreur modification poste travail IA: {e}")
            return {'success': False, 'error': str(e)}
    
    def creer_bon_travail_avec_ia(self, instructions: str) -> Dict[str, Any]:
        """
        Crée un bon de travail via instructions en langage naturel français québécois
        
        Args:
            instructions: Description en français du bon de travail à créer
            
        Returns:
            Dict avec success, bt_id, et détails ou error
        """
        try:
            if not self.api_key:
                return {'success': False, 'error': 'Clé API Claude requise pour la création IA'}
            
            from production_management import GestionnaireFormulaires
            
            gestionnaire_bt = GestionnaireFormulaires(self.db)
            
            # Récupérer les projets disponibles pour liaison
            projets_disponibles = self.db.execute_query("""
                SELECT id, nom, client_name FROM projects 
                WHERE statut NOT IN ('TERMINÉ', 'ANNULÉ')
                ORDER BY created_at DESC LIMIT 20
            """)
            
            # Récupérer les employés disponibles
            employes_disponibles = self.db.execute_query("""
                SELECT id, prenom, nom, departement FROM employees
                WHERE statut = 'ACTIF'
                ORDER BY nom LIMIT 30
            """)
            
            priorites_disponibles = ['FAIBLE', 'NORMALE', 'HAUTE', 'URGENTE']
            
            prompt = f"""
Tu es un assistant spécialisé dans la création de bons de travail pour une entreprise de construction au Québec.

PROJETS DISPONIBLES (premiers 10):
{chr(10).join([f"- ID {p[0]}: {p[1]} (Client: {p[2]})" for p in projets_disponibles[:10]])}

EMPLOYÉS DISPONIBLES (premiers 10):
{chr(10).join([f"- ID {e[0]}: {e[1]} {e[2]} ({e[3]})" for e in employes_disponibles[:10]])}

PRIORITÉS DISPONIBLES: {', '.join(priorites_disponibles)}

INSTRUCTIONS:
"{instructions}"

Génère un JSON avec cette structure EXACTE:
{{
    "project_id": ID_du_projet_si_spécifié,
    "project_name": "Nom du projet",
    "client_name": "Nom du client", 
    "client_company_id": ID_entreprise_cliente_si_connue,
    "project_manager": "Nom du chargé de projet",
    "priority": "PRIORITE_choisie",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD", 
    "work_instructions": "Instructions détaillées de travail",
    "safety_notes": "Notes de sécurité spécifiques",
    "quality_requirements": "Exigences qualité",
    "tasks": [
        {{
            "operation": "Nom de l'opération",
            "description": "Description détaillée de la tâche",
            "quantity": 1,
            "planned_hours": 8.0,
            "actual_hours": 0.0,
            "assigned_to": "Nom de l'employé assigné",
            "status": "À FAIRE",
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD"
        }}
    ],
    "materials": [
        {{
            "name": "Nom du matériau",
            "description": "Description du matériau",
            "quantity": 1,
            "unit": "unité",
            "available": true,
            "notes": "Notes sur le matériau"
        }}
    ]
}}

IMPORTANT:
- Si projet spécifié, utilise l'ID de la liste, sinon laisse null
- Priorité parmi: FAIBLE, NORMALE, HAUTE, URGENTE
- Dates au format YYYY-MM-DD (start_date <= end_date)
- Heures planifiées réalistes selon les tâches
- Status tâches: "À FAIRE" par défaut
- Unités matériaux: m³, m², kg, unité, etc.
- Si infos manquantes, utilise des valeurs logiques pour la construction
"""

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parser la réponse
            response_text = response.content[0].text.strip()
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].strip()
                
            bt_data = json.loads(response_text)
            
            # Validation et complétion des données
            if bt_data.get('priority') not in priorites_disponibles:
                bt_data['priority'] = 'NORMALE'
            
            # Générer un numéro de document unique
            bt_data['numero_document'] = gestionnaire_bt.generate_bt_number()
            bt_data['created_by'] = 'Assistant IA'
            
            # Validation des tâches
            taches_validees = []
            for task in bt_data.get('tasks', []):
                if task.get('operation') or task.get('description'):
                    # Compléter les champs manquants
                    task['quantity'] = max(1, int(task.get('quantity', 1)))
                    task['planned_hours'] = max(0.1, float(task.get('planned_hours', 1.0)))
                    task['actual_hours'] = 0.0
                    task['status'] = task.get('status', 'À FAIRE')
                    taches_validees.append(task)
            
            bt_data['tasks'] = taches_validees
            
            # Validation des matériaux
            materiaux_valides = []
            for material in bt_data.get('materials', []):
                if material.get('name'):
                    material['quantity'] = max(1, int(material.get('quantity', 1)))
                    material['unit'] = material.get('unit', 'unité')
                    material['available'] = material.get('available', True)
                    materiaux_valides.append(material)
            
            bt_data['materials'] = materiaux_valides
            
            # Créer le bon de travail
            bt_id = gestionnaire_bt.save_bon_travail(bt_data)
            
            if bt_id:
                return {
                    'success': True,
                    'bt_id': bt_id,
                    'numero_document': bt_data['numero_document'],
                    'project_name': bt_data.get('project_name', ''),
                    'priority': bt_data.get('priority'),
                    'nb_taches': len(taches_validees),
                    'nb_materiaux': len(materiaux_valides),
                    'heures_planifiees': sum([float(t.get('planned_hours', 0)) for t in taches_validees]),
                    'donnees_parsees': bt_data
                }
            else:
                return {'success': False, 'error': 'Erreur lors de la création du bon de travail en base'}
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON création bon travail: {e}")
            return {'success': False, 'error': f'Erreur format réponse IA: {e}'}
        except Exception as e:
            logger.error(f"Erreur création bon travail IA: {e}")
            return {'success': False, 'error': str(e)}
    
    def modifier_bon_travail_avec_ia(self, bt_id: int, instructions: str) -> Dict[str, Any]:
        """
        Modifie un bon de travail existant via instructions en langage naturel
        
        Args:
            bt_id: ID du bon de travail à modifier
            instructions: Instructions de modification en français
            
        Returns:
            Dict avec success, modifications ou error
        """
        try:
            if not self.api_key:
                return {'success': False, 'error': 'Clé API Claude requise pour la modification IA'}
            
            from production_management import GestionnaireFormulaires
            
            gestionnaire_bt = GestionnaireFormulaires(self.db)
            
            # Récupérer le bon de travail actuel
            bt_actuel = gestionnaire_bt.load_bon_travail(bt_id)
            
            if not bt_actuel:
                return {'success': False, 'error': f'Bon de travail {bt_id} non trouvé'}
            
            priorites_disponibles = ['FAIBLE', 'NORMALE', 'HAUTE', 'URGENTE']
            status_taches_disponibles = ['À FAIRE', 'EN COURS', 'TERMINÉ', 'SUSPENDU']
            
            # Résumer l'état actuel
            nb_taches_actuelles = len(bt_actuel.get('tasks', []))
            nb_materiaux_actuels = len(bt_actuel.get('materials', []))
            heures_planifiees_actuelles = sum([float(t.get('planned_hours', 0)) for t in bt_actuel.get('tasks', [])])
            
            prompt = f"""
Tu es un assistant spécialisé dans la modification de bons de travail.

BON DE TRAVAIL ACTUEL:
- ID: {bt_id}
- Numéro: {bt_actuel.get('numero_document', '')}
- Projet: {bt_actuel.get('project_name', '')}
- Client: {bt_actuel.get('client_name', '')}
- Priorité: {bt_actuel.get('priority', '')}
- Date début: {bt_actuel.get('start_date', '')}
- Date fin: {bt_actuel.get('end_date', '')}
- Instructions travail: {bt_actuel.get('work_instructions', '')}
- Sécurité: {bt_actuel.get('safety_notes', '')}
- Qualité: {bt_actuel.get('quality_requirements', '')}
- Nombre tâches: {nb_taches_actuelles}
- Nombre matériaux: {nb_materiaux_actuels}
- Heures planifiées totales: {heures_planifiees_actuelles}

TÂCHES ACTUELLES:
{chr(10).join([f"- Tâche {i+1}: {t.get('operation', '')} - {t.get('description', '')} ({t.get('planned_hours', 0)}h, statut: {t.get('status', '')})" for i, t in enumerate(bt_actuel.get('tasks', []))])}

MATÉRIAUX ACTUELS:
{chr(10).join([f"- Matériau {i+1}: {m.get('name', '')} - {m.get('quantity', 0)} {m.get('unit', '')} ({'Disponible' if m.get('available', True) else 'Non disponible'})" for i, m in enumerate(bt_actuel.get('materials', []))])}

PRIORITÉS DISPONIBLES: {', '.join(priorites_disponibles)}
STATUTS TÂCHES: {', '.join(status_taches_disponibles)}

INSTRUCTIONS DE MODIFICATION:
"{instructions}"

Génère un JSON avec SEULEMENT les champs à modifier:
{{
    "project_name": "nouveau nom projet si changé",
    "client_name": "nouveau nom client si changé",
    "priority": "NOUVELLE_PRIORITE si changée",
    "start_date": "YYYY-MM-DD si changée",
    "end_date": "YYYY-MM-DD si changée",
    "work_instructions": "nouvelles instructions si changées",
    "safety_notes": "nouvelles notes sécurité si changées",
    "quality_requirements": "nouvelles exigences si changées",
    "taches_modifiees": [
        {{
            "index_tache": index_de_la_tache_à_modifier_ou_-1_pour_nouvelle,
            "action": "modifier" ou "ajouter" ou "supprimer",
            "operation": "nom opération",
            "description": "description",
            "planned_hours": heures_planifiées,
            "assigned_to": "assigné à",
            "status": "statut"
        }}
    ],
    "materiaux_modifies": [
        {{
            "index_materiau": index_du_materiau_ou_-1_pour_nouveau,
            "action": "modifier" ou "ajouter" ou "supprimer",
            "name": "nom matériau",
            "description": "description",
            "quantity": quantité,
            "unit": "unité",
            "available": true_ou_false
        }}
    ]
}}

IMPORTANT:
- N'inclus QUE les modifications demandées
- Pour taches_modifiees: index_tache=-1 pour nouvelles tâches (commence à 0 pour existantes)
- Pour materiaux_modifies: index_materiau=-1 pour nouveaux matériaux
- Actions possibles: "modifier", "ajouter", "supprimer"
- Statuts tâches valides: {', '.join(status_taches_disponibles)}
- Priorités valides: {', '.join(priorites_disponibles)}
"""

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parser et appliquer les modifications
            response_text = response.content[0].text.strip()
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
                
            modifications = json.loads(response_text)
            
            # Construire les nouvelles données en partant de l'existant
            nouvelles_donnees = dict(bt_actuel)
            modifications_appliquees = {}
            
            # Modifier les champs de base
            for champ in ['project_name', 'client_name', 'priority', 'start_date', 'end_date', 
                         'work_instructions', 'safety_notes', 'quality_requirements']:
                if champ in modifications and modifications[champ] != bt_actuel.get(champ):
                    if champ == 'priority' and modifications[champ] not in priorites_disponibles:
                        continue
                    nouvelles_donnees[champ] = modifications[champ]
                    modifications_appliquees[champ] = modifications[champ]
            
            # Traiter les modifications de tâches
            taches_traitees = []
            if 'taches_modifiees' in modifications:
                nouvelles_taches = list(nouvelles_donnees.get('tasks', []))
                
                for tache_modif in modifications['taches_modifiees']:
                    index_tache = tache_modif.get('index_tache', -1)
                    action = tache_modif.get('action', 'modifier')
                    
                    if action == 'supprimer' and 0 <= index_tache < len(nouvelles_taches):
                        del nouvelles_taches[index_tache]
                        taches_traitees.append(f"Supprimé tâche {index_tache + 1}")
                        
                    elif action == 'ajouter':
                        nouvelle_tache = {
                            'operation': tache_modif.get('operation', ''),
                            'description': tache_modif.get('description', ''),
                            'quantity': 1,
                            'planned_hours': max(0.1, float(tache_modif.get('planned_hours', 1.0))),
                            'actual_hours': 0.0,
                            'assigned_to': tache_modif.get('assigned_to', ''),
                            'status': tache_modif.get('status', 'À FAIRE'),
                            'start_date': '',
                            'end_date': ''
                        }
                        nouvelles_taches.append(nouvelle_tache)
                        taches_traitees.append(f"Ajouté nouvelle tâche: {nouvelle_tache['operation']}")
                        
                    elif action == 'modifier' and 0 <= index_tache < len(nouvelles_taches):
                        tache_existante = nouvelles_taches[index_tache]
                        for field in ['operation', 'description', 'planned_hours', 'assigned_to', 'status']:
                            if field in tache_modif:
                                if field == 'planned_hours':
                                    tache_existante[field] = max(0.1, float(tache_modif[field]))
                                elif field == 'status' and tache_modif[field] in status_taches_disponibles:
                                    tache_existante[field] = tache_modif[field]
                                elif field not in ['planned_hours', 'status']:
                                    tache_existante[field] = tache_modif[field]
                        taches_traitees.append(f"Modifié tâche {index_tache + 1}")
                
                nouvelles_donnees['tasks'] = nouvelles_taches
                if taches_traitees:
                    modifications_appliquees['taches_traitees'] = taches_traitees
            
            # Traiter les modifications de matériaux
            materiaux_traites = []
            if 'materiaux_modifies' in modifications:
                nouveaux_materiaux = list(nouvelles_donnees.get('materials', []))
                
                for materiau_modif in modifications['materiaux_modifies']:
                    index_materiau = materiau_modif.get('index_materiau', -1)
                    action = materiau_modif.get('action', 'modifier')
                    
                    if action == 'supprimer' and 0 <= index_materiau < len(nouveaux_materiaux):
                        del nouveaux_materiaux[index_materiau]
                        materiaux_traites.append(f"Supprimé matériau {index_materiau + 1}")
                        
                    elif action == 'ajouter':
                        nouveau_materiau = {
                            'name': materiau_modif.get('name', ''),
                            'description': materiau_modif.get('description', ''),
                            'quantity': max(1, int(materiau_modif.get('quantity', 1))),
                            'unit': materiau_modif.get('unit', 'unité'),
                            'available': materiau_modif.get('available', True),
                            'notes': ''
                        }
                        nouveaux_materiaux.append(nouveau_materiau)
                        materiaux_traites.append(f"Ajouté matériau: {nouveau_materiau['name']}")
                        
                    elif action == 'modifier' and 0 <= index_materiau < len(nouveaux_materiaux):
                        materiau_existant = nouveaux_materiaux[index_materiau]
                        for field in ['name', 'description', 'quantity', 'unit', 'available']:
                            if field in materiau_modif:
                                if field == 'quantity':
                                    materiau_existant[field] = max(1, int(materiau_modif[field]))
                                else:
                                    materiau_existant[field] = materiau_modif[field]
                        materiaux_traites.append(f"Modifié matériau {index_materiau + 1}")
                
                nouvelles_donnees['materials'] = nouveaux_materiaux
                if materiaux_traites:
                    modifications_appliquees['materiaux_traites'] = materiaux_traites
            
            # Sauvegarder les modifications
            if modifications_appliquees:
                success = gestionnaire_bt.update_bon_travail(bt_id, nouvelles_donnees)
                
                if success:
                    # Calculer les nouvelles statistiques
                    nouvelles_heures = sum([float(t.get('planned_hours', 0)) for t in nouvelles_donnees.get('tasks', [])])
                    
                    return {
                        'success': True,
                        'bt_id': bt_id,
                        'numero_document': nouvelles_donnees.get('numero_document'),
                        'modifications_appliquees': modifications_appliquees,
                        'anciennes_heures_planifiees': heures_planifiees_actuelles,
                        'nouvelles_heures_planifiees': nouvelles_heures,
                        'nouveau_nb_taches': len(nouvelles_donnees.get('tasks', [])),
                        'nouveau_nb_materiaux': len(nouvelles_donnees.get('materials', [])),
                        'instructions_originales': instructions
                    }
                else:
                    return {'success': False, 'error': 'Erreur lors de la sauvegarde des modifications'}
            else:
                return {
                    'success': True,
                    'bt_id': bt_id,
                    'modifications_appliquees': {},
                    'message': 'Aucune modification nécessaire'
                }
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON modification bon travail: {e}")
            return {'success': False, 'error': f'Erreur format réponse IA: {e}'}
        except Exception as e:
            logger.error(f"Erreur modification bon travail IA: {e}")
            return {'success': False, 'error': str(e)}
    
    # =========================================================================
    # VISUALISATIONS INTELLIGENTES
    # =========================================================================
    
    def creer_dashboard_insights(self) -> Dict[str, Any]:
        """Crée un dashboard avec visualisations et insights"""
        try:
            # Evolution CA sur 6 mois
            evolution_ca = self.db.execute_query("""
                SELECT 
                    strftime('%Y-%m', created_at) as mois,
                    COUNT(*) as nb_projets,
                    SUM(prix_estime) as ca_total
                FROM projects
                WHERE created_at >= date('now', '-6 months')
                GROUP BY strftime('%Y-%m', created_at)
                ORDER BY mois
            """)
            
            # Répartition charge par poste
            charge_postes = self.db.execute_query("""
                SELECT 
                    wc.nom as poste,
                    COUNT(o.id) as nb_operations,
                    SUM(o.temps_estime) as heures_totales
                FROM work_centers wc
                LEFT JOIN operations o ON wc.id = o.work_center_id AND o.statut != 'TERMINÉ'
                GROUP BY wc.id
                HAVING heures_totales > 0
                ORDER BY heures_totales DESC
            """)
            
            # Top 5 clients
            top_clients = self.db.execute_query("""
                SELECT 
                    c.nom as client,
                    COUNT(p.id) as nb_projets,
                    SUM(p.prix_estime) as ca_total
                FROM companies c
                JOIN projects p ON c.id = p.client_company_id
                WHERE p.created_at >= date('now', '-12 months')
                GROUP BY c.id
                ORDER BY ca_total DESC
                LIMIT 5
            """)
            
            # Créer les graphiques Plotly
            fig_ca = go.Figure(data=[
                go.Bar(
                    x=[e['mois'] for e in evolution_ca],
                    y=[e['ca_total'] for e in evolution_ca],
                    text=[f"${e['ca_total']:,.0f}" for e in evolution_ca],
                    textposition='auto',
                    marker_color='#00A971'
                )
            ])
            fig_ca.update_layout(
                title="Évolution du CA (6 derniers mois)",
                xaxis_title="Mois",
                yaxis_title="Chiffre d'affaires ($)",
                showlegend=False
            )
            
            fig_charge = go.Figure(data=[
                go.Pie(
                    labels=[c['poste'] for c in charge_postes],
                    values=[c['heures_totales'] for c in charge_postes],
                    hole=0.4
                )
            ])
            fig_charge.update_layout(
                title="Répartition de la charge par poste"
            )
            
            fig_clients = go.Figure(data=[
                go.Bar(
                    y=[c['client'] for c in top_clients],
                    x=[c['ca_total'] for c in top_clients],
                    orientation='h',
                    text=[f"${c['ca_total']:,.0f}" for c in top_clients],
                    textposition='auto',
                    marker_color='#1F2937'
                )
            ])
            fig_clients.update_layout(
                title="Top 5 clients (12 derniers mois)",
                xaxis_title="Chiffre d'affaires ($)",
                yaxis_title="Client",
                showlegend=False
            )
            
            return {
                'success': True,
                'graphiques': {
                    'evolution_ca': fig_ca,
                    'charge_postes': fig_charge,
                    'top_clients': fig_clients
                },
                'donnees': {
                    'evolution_ca': evolution_ca,
                    'charge_postes': charge_postes,
                    'top_clients': top_clients
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur création dashboard: {e}")
            return {'success': False, 'error': str(e)}


def show_assistant_ia_page(db):
    """Interface Streamlit pour l'assistant IA"""
    st.title("🤖 Assistant IA Claude")
    st.markdown("---")
    
    # Vérifier la configuration
    api_key = os.environ.get('CLAUDE_API_KEY') or st.session_state.get('claude_api_key')
    
    if not api_key:
        st.warning("⚠️ Configuration requise")
        st.info("""
        Pour utiliser l'assistant IA, vous devez configurer votre clé API Claude :
        
        1. Obtenez une clé API sur [console.anthropic.com](https://console.anthropic.com/)
        2. Ajoutez la variable d'environnement `CLAUDE_API_KEY`
        3. Ou entrez-la ci-dessous (temporaire)
        """)
        
        temp_key = st.text_input("Clé API Claude (temporaire)", type="password")
        if temp_key:
            st.session_state['claude_api_key'] = temp_key
            st.rerun()
        return
    
    # Initialiser l'assistant
    assistant = AssistantIAClaude(db, api_key)
    
    # Onglets principaux
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Tableau de bord IA",
        "💬 Chat Assistant", 
        "📈 Analyses",
        "🔮 Prévisions",
        "💡 Suggestions"
    ])
    
    with tab1:
        st.header("Tableau de bord intelligent")
        
        # Métriques rapides avec IA
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            projets_actifs = db.execute_query("SELECT COUNT(*) as nb FROM projects WHERE statut = 'EN COURS'")[0]['nb']
            st.metric("Projets actifs", projets_actifs)
        
        with col2:
            alertes_stock = db.execute_query("SELECT COUNT(*) as nb FROM inventory_items WHERE quantite_metric <= limite_minimale_metric")[0]['nb']
            st.metric("Alertes stock", alertes_stock, delta=None if alertes_stock == 0 else f"+{alertes_stock}", delta_color="inverse")
        
        with col3:
            ca_mois = db.execute_query("SELECT SUM(prix_estime) as ca FROM projects WHERE created_at >= date('now', 'start of month')")[0]['ca'] or 0
            st.metric("CA du mois", f"${ca_mois:,.0f}")
        
        with col4:
            employes_actifs = db.execute_query("SELECT COUNT(*) as nb FROM employees WHERE statut = 'ACTIF'")[0]['nb']
            st.metric("Employés actifs", employes_actifs)
        
        # Dashboard visuel
        with st.spinner("Création du dashboard intelligent..."):
            dashboard = assistant.creer_dashboard_insights()
            
            if dashboard['success']:
                # Graphiques
                col1, col2 = st.columns(2)
                
                with col1:
                    st.plotly_chart(dashboard['graphiques']['evolution_ca'], use_container_width=True)
                
                with col2:
                    st.plotly_chart(dashboard['graphiques']['charge_postes'], use_container_width=True)
                
                st.plotly_chart(dashboard['graphiques']['top_clients'], use_container_width=True)
                
                # Analyse IA globale
                if st.button("🧠 Générer analyse IA complète", type="primary"):
                    with st.spinner("Claude analyse vos données..."):
                        analyse = assistant.analyser_situation_globale()
                        
                        if analyse['success']:
                            st.success("✅ Analyse complétée")
                            
                            # Afficher l'analyse dans un container stylé
                            with st.container():
                                st.markdown("""
                                <div style='background-color: #f0f8ff; padding: 20px; border-radius: 10px; border-left: 5px solid #00A971;'>
                                """, unsafe_allow_html=True)
                                
                                st.markdown(analyse['analyse'])
                                
                                st.markdown("</div>", unsafe_allow_html=True)
                                
                                # Bouton pour télécharger l'analyse
                                st.download_button(
                                    label="📥 Télécharger le rapport",
                                    data=analyse['analyse'],
                                    file_name=f"analyse_ia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                    mime="text/plain"
                                )
                        else:
                            st.error(f"❌ {analyse['error']}")
    
    with tab2:
        st.header("Chat avec l'assistant IA")
        
        # Historique des conversations
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Zone de chat
        chat_container = st.container()
        
        with chat_container:
            # Afficher l'historique
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    st.markdown(f"**Vous:** {message['content']}")
                else:
                    with st.container():
                        st.markdown(f"**Claude:** {message['content']}")
                        st.markdown("---")
        
        # Zone de saisie
        col1, col2 = st.columns([5, 1])
        
        with col1:
            question = st.text_input("Posez votre question...", placeholder="Ex: Quel est le projet le plus rentable ce mois-ci?")
        
        with col2:
            if st.button("Envoyer", type="primary"):
                if question:
                    # Ajouter la question à l'historique
                    st.session_state.chat_history.append({'role': 'user', 'content': question})
                    
                    # Obtenir la réponse
                    with st.spinner("Claude réfléchit..."):
                        reponse = assistant.repondre_question(question)
                    
                    # Ajouter la réponse à l'historique
                    st.session_state.chat_history.append({'role': 'assistant', 'content': reponse})
                    
                    # Recharger pour afficher
                    st.rerun()
        
        # Bouton pour effacer l'historique
        if st.button("🗑️ Effacer la conversation"):
            st.session_state.chat_history = []
            st.rerun()
        
        # Questions suggérées
        st.subheader("💡 Questions suggérées")
        
        suggestions = [
            "Quels sont les projets les plus en retard?",
            "Analyse la performance de production de ce mois",
            "Quels articles d'inventaire nécessitent un réapprovisionnement urgent?",
            "Quelle est la charge de travail prévue pour les 2 prochaines semaines?",
            "Quels sont nos meilleurs clients en termes de rentabilité?"
        ]
        
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(suggestion, key=f"sugg_{i}"):
                    st.session_state.chat_history.append({'role': 'user', 'content': suggestion})
                    with st.spinner("Claude réfléchit..."):
                        reponse = assistant.repondre_question(suggestion)
                    st.session_state.chat_history.append({'role': 'assistant', 'content': reponse})
                    st.rerun()
    
    with tab3:
        st.header("Analyses approfondies")
        
        # Sélection du type d'analyse
        type_analyse = st.selectbox(
            "Type d'analyse",
            ["Projet spécifique", "Portefeuille clients", "Performance production", "Santé inventaire"]
        )
        
        if type_analyse == "Projet spécifique":
            # Liste des projets actifs
            projets = db.execute_query("""
                SELECT id, nom_projet, statut, client_nom_cache
                FROM projects
                WHERE statut IN ('EN COURS', 'À FAIRE')
                ORDER BY created_at DESC
            """)
            
            if projets:
                projet_selectionne = st.selectbox(
                    "Sélectionnez un projet",
                    options=projets,
                    format_func=lambda p: f"{p['nom_projet']} - {p['client_nom_cache']} ({p['statut']})"
                )
                
                if st.button("🔍 Analyser ce projet"):
                    with st.spinner("Analyse en cours..."):
                        analyse = assistant.analyser_projet_specifique(projet_selectionne['id'])
                        
                        if analyse['success']:
                            # Métriques du projet
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Heures prévues", f"{analyse['metriques']['heures_prevues']:.1f}h")
                            
                            with col2:
                                st.metric("Heures réelles", f"{analyse['metriques']['heures_reelles']:.1f}h")
                            
                            with col3:
                                ecart = ((analyse['metriques']['heures_reelles'] / analyse['metriques']['heures_prevues'] - 1) * 100) if analyse['metriques']['heures_prevues'] > 0 else 0
                                st.metric("Écart", f"{ecart:+.1f}%", delta=f"{ecart:.1f}%")
                            
                            with col4:
                                st.metric("Avancement", f"{analyse['metriques']['taux_avancement']:.0f}%")
                            
                            # Analyse IA
                            st.markdown("### 🧠 Analyse Claude")
                            st.markdown(analyse['analyse'])
                        else:
                            st.error(analyse['error'])
    
    with tab4:
        st.header("Analyses prévisionnelles")
        
        # Paramètres de prévision
        col1, col2 = st.columns(2)
        
        with col1:
            horizon = st.slider("Horizon de prévision (jours)", 7, 90, 30)
        
        with col2:
            st.info(f"Analyse sur {horizon} jours ({horizon/7:.1f} semaines)")
        
        if st.button("🔮 Générer prévisions", type="primary"):
            with st.spinner("Génération des prévisions..."):
                previsions = assistant.generer_rapport_previsionnel(horizon)
                
                if previsions['success']:
                    # Métriques prévisionnelles
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Projets à livrer", previsions['donnees']['projets_a_livrer'])
                    
                    with col2:
                        st.metric("Charge totale", f"{previsions['donnees']['charge_totale']:.0f}h")
                    
                    with col3:
                        st.metric("Capacité disponible", f"{previsions['donnees']['capacite_disponible']:.0f}h")
                    
                    with col4:
                        taux = previsions['donnees']['taux_charge']
                        color = "normal" if taux < 80 else "inverse" if taux < 100 else "off"
                        st.metric("Taux de charge", f"{taux:.0f}%", delta=None, delta_color=color)
                    
                    # Rapport IA
                    st.markdown("### 📊 Analyse prévisionnelle")
                    st.markdown(previsions['analyse'])
                    
                    # Graphique de charge
                    if taux > 0:
                        fig = go.Figure(go.Indicator(
                            mode="gauge+number+delta",
                            value=taux,
                            title={'text': "Taux de charge prévisionnel"},
                            domain={'x': [0, 1], 'y': [0, 1]},
                            gauge={
                                'axis': {'range': [None, 120]},
                                'bar': {'color': "#00A971" if taux < 80 else "#F59E0B" if taux < 100 else "#EF4444"},
                                'steps': [
                                    {'range': [0, 80], 'color': "#E8F5E9"},
                                    {'range': [80, 100], 'color': "#FFF3E0"},
                                    {'range': [100, 120], 'color': "#FFEBEE"}
                                ],
                                'threshold': {
                                    'line': {'color': "red", 'width': 4},
                                    'thickness': 0.75,
                                    'value': 100
                                }
                            }
                        ))
                        
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error(previsions['error'])
    
    with tab5:
        st.header("Suggestions et recommandations")
        
        # Générer les suggestions
        suggestions = assistant.generer_suggestions_quotidiennes()
        
        if suggestions:
            st.info(f"🎯 {len(suggestions)} suggestions identifiées")
            
            for i, suggestion in enumerate(suggestions):
                # Couleur selon priorité
                couleur = {
                    'critique': '#EF4444',
                    'haute': '#F59E0B',
                    'moyenne': '#3B82F6',
                    'basse': '#6B7280'
                }[suggestion['priorite']]
                
                # Afficher la suggestion
                with st.container():
                    st.markdown(f"""
                    <div style='background-color: {couleur}22; border-left: 4px solid {couleur}; 
                                padding: 15px; margin: 10px 0; border-radius: 5px;'>
                        <h4 style='margin: 0; color: {couleur};'>{suggestion['titre']}</h4>
                        <p style='margin: 5px 0;'>{suggestion['description']}</p>
                        <small style='color: #666;'>Priorité: {suggestion['priorite'].upper()}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(suggestion['action'], key=f"action_{i}"):
                        st.info(f"Redirection vers {suggestion['type']}...")
        else:
            st.success("✅ Aucune action urgente requise!")
            st.balloons()
        
        # Section insights automatiques
        st.subheader("🎯 Insights automatiques")
        
        if st.button("Générer de nouveaux insights"):
            with st.spinner("Recherche d'insights..."):
                # Ici on pourrait ajouter plus d'analyses automatiques
                st.info("Cette fonctionnalité sera enrichie avec plus d'analyses automatiques.")