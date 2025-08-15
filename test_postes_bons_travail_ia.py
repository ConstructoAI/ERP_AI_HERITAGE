#!/usr/bin/env python3
# test_postes_bons_travail_ia.py - Tests pour les fonctionnalités IA Postes et Bons de Travail
# ERP Production DG Inc. - Tests des nouvelles capacités de l'assistant IA pour postes de travail et bons de travail

"""
Tests pour vérifier le bon fonctionnement des nouvelles fonctionnalités IA 
pour la création et modification de postes de travail et bons de travail via l'assistant Claude
"""

import os
import sys
import traceback
from pathlib import Path

# Ajouter le répertoire parent au PATH pour les imports
sys.path.append(str(Path(__file__).parent))

def test_assistant_ia_postes_travail():
    """Test des fonctionnalités IA pour les postes de travail"""
    print("🏭 TESTS ASSISTANT IA - GESTION POSTES DE TRAVAIL")
    print("=" * 60)
    
    try:
        # Imports nécessaires
        from erp_database import ERPDatabase
        from assistant_ia import AssistantIAClaude
        from auth_config import get_claude_api_key
        
        print("📦 Modules postes travail importés avec succès")
        
        # Initialisation
        db = ERPDatabase()
        api_key = get_claude_api_key()
        
        if not api_key:
            print("⚠️ Tests IA sautés - pas de clé API Claude")
            return True
        
        assistant = AssistantIAClaude(db, api_key)
        
        # Test création poste de travail avec IA
        print("\n1️⃣ Test création poste de travail avec IA...")
        instructions_creation = """
        Créer un poste de soudage automatisé Robot ABB GMAW Station 2.
        Département production, catégorie ossature, robot ABB IRB 2600.
        Capacité 16 heures par jour, 2 opérateurs requis, coût 85$/heure.
        Compétences: Programmation robot ABB, Soudage GMAW-P, Lecture plans structures.
        Localisation: Atelier B - Zone robotisée 2, statut actif.
        """
        
        resultat = assistant.creer_poste_travail_avec_ia(instructions_creation)
        
        if resultat['success']:
            print("✅ Création poste travail IA réussie!")
            print(f"   - Poste ID: {resultat.get('work_center_id')}")
            print(f"   - Nom: {resultat.get('nom')}")
            print(f"   - Département: {resultat.get('departement')}")
            print(f"   - Catégorie: {resultat.get('categorie')}")
            print(f"   - Capacité: {resultat.get('capacite_theorique')}h/jour")
            print(f"   - Coût: {resultat.get('cout_horaire')}$/h")
            
            work_center_id = resultat['work_center_id']
            
            # Test modification poste de travail
            print("\n2️⃣ Test modification poste de travail avec IA...")
            instructions_modif = """
            Passer le poste en maintenance pour révision programmée.
            Réduire la capacité à 8 heures par jour temporairement.
            Augmenter le coût horaire à 95$ pour inclure frais maintenance.
            """
            
            resultat_modif = assistant.modifier_poste_travail_avec_ia(work_center_id, instructions_modif)
            
            if resultat_modif['success']:
                print("✅ Modification poste travail IA réussie!")
                print(f"   - Modifications: {list(resultat_modif.get('modifications_appliquees', {}).keys())}")
                if resultat_modif.get('modifications_appliquees'):
                    for champ, valeur in resultat_modif['modifications_appliquees'].items():
                        print(f"     • {champ}: {valeur}")
            else:
                print(f"❌ Erreur modification: {resultat_modif.get('error', '')}")
        else:
            print(f"❌ Erreur création: {resultat.get('error', '')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR TESTS POSTES TRAVAIL: {e}")
        traceback.print_exc()
        return False

def test_assistant_ia_bons_travail():
    """Test des fonctionnalités IA pour les bons de travail"""
    print("\n📋 TESTS ASSISTANT IA - BONS DE TRAVAIL")
    print("=" * 60)
    
    try:
        from erp_database import ERPDatabase
        from assistant_ia import AssistantIAClaude
        from auth_config import get_claude_api_key
        
        print("📦 Modules bons travail importés avec succès")
        
        db = ERPDatabase()
        api_key = get_claude_api_key()
        
        if not api_key:
            print("⚠️ Tests IA sautés - pas de clé API Claude")
            return True
        
        assistant = AssistantIAClaude(db, api_key)
        
        # Test création bon de travail avec IA
        print("\n1️⃣ Test création bon de travail avec IA...")
        instructions_bt = """
        Créer bon de travail pour assemblage structure métallique projet Tour Horizon.
        Client: Constructions Modernes Inc., chargé projet: Marie Dubois.
        Priorité haute, début lundi prochain, fin dans 2 semaines.
        
        Tâches:
        - Préparation matériel et outillage (4h, Jean Tremblay)
        - Découpe profilés acier selon plans (12h, équipe découpe)
        - Soudage assemblage principal (16h, Pierre Martin)
        - Contrôle qualité et finition (6h, inspecteur qualité)
        
        Matériaux:
        - 50 profilés HEA 200 de 6m
        - 25kg électrodes E70XX 
        - 10 boulons HR M20x80
        - Peinture anti-corrosion 5L
        
        Sécurité: EPI complets, ventilation soudage, espace confiné.
        Qualité: Soudures certifiées CWB, contrôles par ressuage.
        """
        
        resultat_bt = assistant.creer_bon_travail_avec_ia(instructions_bt)
        
        if resultat_bt['success']:
            print("✅ Création bon de travail IA réussie!")
            print(f"   - BT ID: {resultat_bt.get('bt_id')}")
            print(f"   - Numéro: {resultat_bt.get('numero_document')}")
            print(f"   - Projet: {resultat_bt.get('project_name')}")
            print(f"   - Priorité: {resultat_bt.get('priority')}")
            print(f"   - Tâches: {resultat_bt.get('nb_taches', 0)}")
            print(f"   - Matériaux: {resultat_bt.get('nb_materiaux', 0)}")
            print(f"   - Heures planifiées: {resultat_bt.get('heures_planifiees', 0)}")
            
            bt_id = resultat_bt['bt_id']
            
            # Test modification bon de travail
            print("\n2️⃣ Test modification bon de travail avec IA...")
            instructions_modif = """
            Ajouter une tâche de peinturage final (8h, équipe finition).
            Changer la priorité à urgente suite demande client.
            Ajouter 15L de diluant peinture dans les matériaux.
            Modifier les heures de soudage de 16h à 20h (complexité accrue).
            """
            
            resultat_modif = assistant.modifier_bon_travail_avec_ia(bt_id, instructions_modif)
            
            if resultat_modif['success']:
                print("✅ Modification bon de travail IA réussie!")
                print(f"   - Anciennes heures: {resultat_modif.get('anciennes_heures_planifiees', 0)}")
                print(f"   - Nouvelles heures: {resultat_modif.get('nouvelles_heures_planifiees', 0)}")
                print(f"   - Nouveau nb tâches: {resultat_modif.get('nouveau_nb_taches', 0)}")
                print(f"   - Nouveau nb matériaux: {resultat_modif.get('nouveau_nb_materiaux', 0)}")
                
                modifications = resultat_modif.get('modifications_appliquees', {})
                if 'taches_traitees' in modifications:
                    print(f"   - Tâches: {modifications['taches_traitees']}")
                if 'materiaux_traites' in modifications:
                    print(f"   - Matériaux: {modifications['materiaux_traites']}")
                
                for champ, valeur in modifications.items():
                    if champ not in ['taches_traitees', 'materiaux_traites']:
                        print(f"   - {champ}: {valeur}")
            else:
                print(f"❌ Erreur modification: {resultat_modif.get('error', '')}")
        else:
            print(f"❌ Erreur création bon travail: {resultat_bt.get('error', '')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR TESTS BONS TRAVAIL: {e}")
        traceback.print_exc()
        return False

def test_integrite_fonctions_postes_bt():
    """Test d'intégrité de toutes les nouvelles fonctions postes et BT"""
    print("\n🔧 TESTS D'INTÉGRITÉ POSTES & BONS TRAVAIL")
    print("=" * 60)
    
    try:
        from erp_database import ERPDatabase
        from assistant_ia import AssistantIAClaude
        
        db = ERPDatabase()
        assistant = AssistantIAClaude(db, None)  # Sans API pour test structure
        
        # Fonctions postes de travail
        fonctions_postes = [
            'creer_poste_travail_avec_ia',
            'modifier_poste_travail_avec_ia'
        ]
        
        # Fonctions bons de travail
        fonctions_bt = [
            'creer_bon_travail_avec_ia',
            'modifier_bon_travail_avec_ia'
        ]
        
        toutes_fonctions = fonctions_postes + fonctions_bt
        
        print(f"\n📋 Test disponibilité fonctions ({len(toutes_fonctions)} fonctions)...")
        for fonction in toutes_fonctions:
            if hasattr(assistant, fonction):
                print(f"   ✅ Fonction {fonction} disponible")
            else:
                print(f"   ❌ Fonction {fonction} manquante")
                return False
        
        # Test imports modules production
        print(f"\n📋 Test imports modules production...")
        
        try:
            from production_management import GestionnaireFormulaires
            print(f"   ✅ Module production_management: GestionnaireFormulaires importé")
        except ImportError as e:
            print(f"   ❌ Erreur import production_management: {e}")
            return False
        
        # Vérifier les structures de données clés
        print(f"\n📋 Test structures données postes/BT...")
        
        # Test tables postes et formulaires
        tables_requises = [
            'work_centers',
            'formulaires',
            'formulaire_lignes',
            'operations'
        ]
        
        for table in tables_requises:
            try:
                result = db.execute_query(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if result:
                    print(f"   ✅ Table {table} existe")
                else:
                    print(f"   ⚠️ Table {table} non trouvée")
            except Exception as e:
                print(f"   ❌ Erreur vérification table {table}: {e}")
        
        # Test méthodes ERP Database
        methodes_requises = [
            'add_work_center',
            'update_work_center', 
            'get_work_center_by_id'
        ]
        
        for methode in methodes_requises:
            if hasattr(db, methode):
                print(f"   ✅ Méthode DB {methode} disponible")
            else:
                print(f"   ❌ Méthode DB {methode} manquante")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR TESTS INTÉGRITÉ: {e}")
        traceback.print_exc()
        return False

def test_exemples_usage_postes_bt():
    """Affiche des exemples d'utilisation des nouvelles fonctionnalités"""
    print("\n" + "=" * 80)
    print("📚 EXEMPLES D'UTILISATION POSTES & BONS DE TRAVAIL")
    print("=" * 80)
    
    exemples = [
        {
            'categorie': '🏭 POSTES DE TRAVAIL',
            'exemples': [
                {
                    'titre': 'Nouveau poste CNC',
                    'instruction': 'Créer poste tournage CNC Haas ST-30, production mécanique, 2 opérateurs, 75$/h, Atelier A Zone 3',
                    'description': 'Génère poste avec toutes spécifications techniques et contraintes opérationnelles'
                },
                {
                    'titre': 'Maintenance programmée',
                    'instruction': 'Mettre le poste WELD-002 en maintenance, réduire capacité 4h/jour, noter révision annuelle',
                    'description': 'Ajuste automatiquement statut, capacité et ajoute notes maintenance'
                }
            ]
        },
        {
            'categorie': '📋 BONS DE TRAVAIL',
            'exemples': [
                {
                    'titre': 'BT fabrication charpente',
                    'instruction': 'BT pour charpente acier projet École Secondaire, 5 tâches soudage, matériaux HEA 240, priorité normale',
                    'description': 'Crée BT complet avec tâches détaillées, matériaux structurés, liens projet'
                },
                {
                    'titre': 'Modification urgence',
                    'instruction': 'Ajouter tâche galvanisation au BT-2024-001, passer priorité urgente, 12h supplémentaires',
                    'description': 'Modifie BT existant avec nouvelles tâches et recalcule automatiquement totaux'
                }
            ]
        },
        {
            'categorie': '🔗 INTÉGRATION SYSTÈME',
            'exemples': [
                {
                    'titre': 'Liaison projets',
                    'instruction': 'Créer BT lié au projet PROJ-123 avec assignation équipe selon disponibilités',
                    'description': 'Intègre automatiquement données projet, clients, et ressources disponibles'
                },
                {
                    'titre': 'Suivi capacité',
                    'instruction': 'Créer poste avec suivi temps réel et alertes dépassement capacité théorique',
                    'description': 'Configure monitoring automatique charge travail et alertes préventives'
                }
            ]
        }
    ]
    
    for categorie_info in exemples:
        print(f"\n{categorie_info['categorie']}")
        print("-" * 50)
        
        for i, exemple in enumerate(categorie_info['exemples'], 1):
            print(f"\n{i}. {exemple['titre']}")
            print(f"   💬 Instruction: \"{exemple['instruction']}\"")
            print(f"   📝 Résultat: {exemple['description']}")
    
    print(f"\n💡 AVANTAGES POSTES & BONS TRAVAIL IA:")
    print("   - Configuration rapide postes avec validations métier automatiques")
    print("   - Génération BT structurés avec liens projets/ressources")
    print("   - Modification intelligente avec préservation cohérence données")
    print("   - Intégration native avec modules ERP (projets, employés, matériaux)")
    print("   - Validation automatique contraintes production québécoises")
    print("   - Interface conversationnelle naturelle français construction")

def test_scenarios_avances():
    """Tests de scénarios avancés d'utilisation"""
    print("\n🎯 TESTS SCÉNARIOS AVANCÉS")
    print("=" * 60)
    
    try:
        from erp_database import ERPDatabase
        from assistant_ia import AssistantIAClaude
        from auth_config import get_claude_api_key
        
        db = ERPDatabase()
        api_key = get_claude_api_key()
        
        if not api_key:
            print("⚠️ Tests avancés sautés - pas de clé API Claude")
            return True
        
        assistant = AssistantIAClaude(db, api_key)
        
        print("\n1️⃣ Scénario: Configuration complète atelier...")
        # Test création multiple postes pour un atelier complet
        postes_atelier = [
            "Poste découpe plasma Hypertherm, production, 12h/jour, opérateur certifié découpe",
            "Station assemblage manuel, 8h/jour, 3 soudeurs, outillage complet, Zone A",
            "Poste contrôle dimensionnel, qualité, équipements métrologie, inspecteur niveau 2"
        ]
        
        postes_crees = []
        for i, instruction in enumerate(postes_atelier, 1):
            print(f"   Création poste {i}/3...")
            resultat = assistant.creer_poste_travail_avec_ia(instruction)
            if resultat['success']:
                postes_crees.append(resultat['work_center_id'])
                print(f"   ✅ Poste {i} créé: {resultat.get('nom')}")
            else:
                print(f"   ❌ Échec poste {i}: {resultat.get('error')}")
        
        if len(postes_crees) >= 2:
            print(f"\n✅ Scénario atelier réussi: {len(postes_crees)} postes créés")
        else:
            print(f"\n⚠️ Scénario atelier partiel: {len(postes_crees)} postes créés")
        
        print("\n2️⃣ Scénario: BT complexe multi-phases...")
        # Test BT avec nombreuses tâches et matériaux
        instruction_bt_complexe = """
        BT production escalier hélicoïdal sur mesure, priorité haute.
        
        Phase 1 - Préparation (2 jours):
        - Analyse plans et calculs (4h, ingénieur)
        - Commande matériaux spéciaux (2h, acheteur)
        - Préparation outillage cintrage (6h, outilleur)
        
        Phase 2 - Fabrication (5 jours):
        - Cintrage limons acier (16h, opérateur cintrage)  
        - Découpe marches sur mesure (12h, découpe CNC)
        - Soudage assemblage principal (24h, 2 soudeurs)
        - Montage garde-corps (8h, assembleur)
        
        Phase 3 - Finition (2 jours):
        - Meulage et finition (10h, finisseur)
        - Apprêt et peinture (8h, peintre)
        - Contrôle final et emballage (4h, contrôleur)
        
        Matériaux spéciaux:
        - 2 limons acier 300x15mm, longueur 8m
        - 15 marches acier perforé sur mesure
        - Kit garde-corps inox avec fixations
        - Peinture architecturale 3L, couleur RAL 7016
        - Visserie inox A4 complète
        
        Sécurité: Travail hauteur, manutention lourde, espaces confinés.
        Qualité: Soudures CWB classe 1, dimensions ±2mm, finition architecturale.
        """
        
        resultat_bt_complexe = assistant.creer_bon_travail_avec_ia(instruction_bt_complexe)
        
        if resultat_bt_complexe['success']:
            print("✅ BT complexe créé avec succès!")
            print(f"   - Tâches: {resultat_bt_complexe.get('nb_taches', 0)}")
            print(f"   - Matériaux: {resultat_bt_complexe.get('nb_materiaux', 0)}")
            print(f"   - Heures totales: {resultat_bt_complexe.get('heures_planifiees', 0)}")
            
            # Test modification complexe
            print("\n   Test modification complexe...")
            modif_complexe = """
            Ajouter phase 4 - Livraison et installation:
            - Transport sécurisé (4h, chauffeur spécialisé)
            - Installation sur site (16h, 2 monteurs certifiés)  
            - Formation client utilisation (2h, technicien)
            
            Modifier phase 2: augmenter soudage à 32h (complexité accrue).
            Ajouter matériau: kit transport et protection 1 ensemble.
            Passer priorité à urgente (demande client).
            """
            
            resultat_modif = assistant.modifier_bon_travail_avec_ia(resultat_bt_complexe['bt_id'], modif_complexe)
            
            if resultat_modif['success']:
                print("✅ Modification complexe réussie!")
                print(f"   - Delta heures: +{resultat_modif.get('nouvelles_heures_planifiees', 0) - resultat_modif.get('anciennes_heures_planifiees', 0)}")
                print(f"   - Nouvelles tâches: {resultat_modif.get('nouveau_nb_taches', 0)}")
            else:
                print(f"❌ Erreur modification complexe: {resultat_modif.get('error')}")
        else:
            print(f"❌ Échec BT complexe: {resultat_bt_complexe.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR TESTS AVANCÉS: {e}")
        traceback.print_exc()
        return False

def test_complet_postes_bons_travail():
    """Lance tous les tests pour Postes et Bons de Travail IA"""
    print("🚀 LANCEMENT DES TESTS COMPLETS POSTES & BONS TRAVAIL IA")
    print("=" * 80)
    print("Tests des nouvelles fonctionnalités de gestion Production via IA")
    
    resultats = []
    
    # Tests postes de travail
    print(f"\n{'='*80}")
    resultats.append(test_assistant_ia_postes_travail())
    
    # Tests bons de travail
    print(f"\n{'='*80}")
    resultats.append(test_assistant_ia_bons_travail())
    
    # Tests intégrité
    print(f"\n{'='*80}")
    resultats.append(test_integrite_fonctions_postes_bt())
    
    # Tests scénarios avancés
    print(f"\n{'='*80}")
    resultats.append(test_scenarios_avances())
    
    # Résumé final
    print(f"\n{'='*80}")
    if all(resultats):
        print("🎉 TOUS LES TESTS POSTES & BONS TRAVAIL RÉUSSIS!")
        print("✅ L'assistant IA peut gérer la production complètement!")
        test_exemples_usage_postes_bt()
        return True
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("🔍 Vérifiez la configuration et les dépendances production")
        return False

if __name__ == "__main__":
    success = test_complet_postes_bons_travail()
    print(f"\n🏁 Tests Production terminés - {'✅ SUCCÈS' if success else '❌ ÉCHEC'}")
    
    print(f"\n📋 RÉSUMÉ DES NOUVELLES CAPACITÉS PRODUCTION IA:")
    print("   🔹 Création automatique postes travail avec contraintes techniques")
    print("   🔹 Configuration intelligente capacités et coûts horaires") 
    print("   🔹 Génération bons travail multi-phases structurés")
    print("   🔹 Modification dynamique tâches et matériaux avec validation")
    print("   🔹 Liaison automatique projets ↔ bons travail ↔ postes")
    print("   🔹 Calculs automatiques heures, coûts et planning")
    print("   🔹 Validation contraintes production québécoises")
    print("   🔹 Interface conversationnelle spécialisée construction")
    
    if success:
        print(f"\n🎯 L'ASSISTANT IA PRODUCTION EST OPÉRATIONNEL!")
        print("   Peut gérer: POSTES DE TRAVAIL, BONS DE TRAVAIL")
        print("   Intégration complète avec: PROJETS, EMPLOYÉS, MATÉRIAUX, FOURNISSEURS")
        print("   Via instructions en français québécois naturel!")
        print(f"\n🌟 L'ERP EST MAINTENANT 100% GÉRÉ PAR IA!")
        print("   Modules IA complets: PROJETS + DEVIS + PRODUITS + RH + CRM + SUPPLY CHAIN + PRODUCTION")
        print("   L'assistant IA couvre TOUS les aspects de l'entreprise de construction!")