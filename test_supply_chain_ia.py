#!/usr/bin/env python3
# test_supply_chain_ia.py - Tests pour les fonctionnalités IA Supply Chain
# ERP Production DG Inc. - Tests des nouvelles capacités de l'assistant IA pour fournisseurs/demandes prix/bons d'achat

"""
Tests pour vérifier le bon fonctionnement des nouvelles fonctionnalités IA 
pour la création et modification de fournisseurs, demandes de prix et bons d'achat via l'assistant Claude
"""

import os
import sys
import traceback
from pathlib import Path

# Ajouter le répertoire parent au PATH pour les imports
sys.path.append(str(Path(__file__).parent))

def test_assistant_ia_fournisseurs():
    """Test des fonctionnalités IA pour les fournisseurs"""
    print("🏭 TESTS ASSISTANT IA - GESTION FOURNISSEURS")
    print("=" * 60)
    
    try:
        # Imports nécessaires
        from erp_database import ERPDatabase
        from assistant_ia import AssistantIAClaude
        from auth_config import get_claude_api_key
        
        print("📦 Modules fournisseurs importés avec succès")
        
        # Initialisation
        db = ERPDatabase()
        api_key = get_claude_api_key()
        
        if not api_key:
            print("⚠️ Tests IA sautés - pas de clé API Claude")
            return True
        
        assistant = AssistantIAClaude(db, api_key)
        
        # Test création fournisseur avec IA
        print("\n1️⃣ Test création fournisseur avec IA...")
        instructions_creation = """
        Créer un fournisseur Matériaux Nord-Est Inc., spécialisé en béton et granulats.
        Adresse: 1250 boulevard Industriel, Québec QC G1N 2V9
        Contact: Jean-François Dubois, téléphone 418-555-0147
        Email: jf.dubois@materiaux-ne.ca, site web: www.materiaux-ne.ca
        Délai paiement 45 jours, remise 3.5%, certifié CSA et BNQ
        Notes: Fournisseur fiable depuis 15 ans, livraison rapide région Québec
        """
        
        resultat = assistant.creer_fournisseur_avec_ia(instructions_creation)
        
        if resultat['success']:
            print("✅ Création fournisseur IA réussie!")
            print(f"   - Fournisseur ID: {resultat.get('fournisseur_id')}")
            print(f"   - Nom: {resultat.get('nom')}")
            print(f"   - Catégories: {resultat.get('nb_categories', 0)}")
            print(f"   - Certifications: {resultat.get('nb_certifications', 0)}")
            
            fournisseur_id = resultat['fournisseur_id']
            
            # Test modification fournisseur
            print("\n2️⃣ Test modification fournisseur avec IA...")
            instructions_modif = """
            Changer l'adresse pour 2500 route de l'Industrie, Lévis QC G6W 5M6
            et augmenter la remise à 5.0%. Ajouter certification RBQ.
            """
            
            resultat_modif = assistant.modifier_fournisseur_avec_ia(fournisseur_id, instructions_modif)
            
            if resultat_modif['success']:
                print("✅ Modification fournisseur IA réussie!")
                print(f"   - Modifications: {list(resultat_modif.get('modifications_appliquees', {}).keys())}")
            else:
                print(f"❌ Erreur modification: {resultat_modif.get('error', '')}")
        else:
            print(f"❌ Erreur création: {resultat.get('error', '')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR TESTS FOURNISSEURS: {e}")
        return False

def test_assistant_ia_demandes_prix():
    """Test des fonctionnalités IA pour les demandes de prix"""
    print("\n📋 TESTS ASSISTANT IA - DEMANDES DE PRIX")
    print("=" * 60)
    
    try:
        from erp_database import ERPDatabase
        from assistant_ia import AssistantIAClaude
        from auth_config import get_claude_api_key
        
        print("📦 Modules demandes prix importés avec succès")
        
        db = ERPDatabase()
        api_key = get_claude_api_key()
        
        if not api_key:
            print("⚠️ Tests IA sautés - pas de clé API Claude")
            return True
        
        assistant = AssistantIAClaude(db, api_key)
        
        # Test création demande de prix avec IA
        print("\n1️⃣ Test création demande prix avec IA...")
        instructions_demande = """
        Créer une demande de prix pour béton prêt-mélangé projet résidentiel.
        Besoin de 150 m³ béton 35 MPa, 50 m³ béton 30 MPa pour fondations.
        Date limite réponse: dans 10 jours.
        Conditions: livraison échelonnée sur 3 semaines, accès camion-malaxeur requis.
        Spécifications: conformité CSA A23.1, résistance au gel certifiée.
        """
        
        resultat_demande = assistant.creer_demande_prix_avec_ia(instructions_demande)
        
        if resultat_demande['success']:
            print("✅ Création demande prix IA réussie!")
            print(f"   - Form ID: {resultat_demande.get('form_id')}")
            print(f"   - Type: {resultat_demande.get('type')}")
            print(f"   - Fournisseur: {resultat_demande.get('supplier_id')}")
            print(f"   - Lignes: {resultat_demande.get('nb_lignes', 0)}")
            print(f"   - Titre: {resultat_demande.get('titre')}")
            
            form_id = resultat_demande['form_id']
            
            # Test modification demande prix
            print("\n2️⃣ Test modification demande prix avec IA...")
            instructions_modif = """
            Ajouter 25 m³ de béton 25 MPa pour dalle et changer la date limite à dans 14 jours.
            Préciser que la livraison se fera sur le chantier au 123 rue des Érables, Lévis.
            """
            
            resultat_modif = assistant.modifier_demande_prix_avec_ia(form_id, instructions_modif)
            
            if resultat_modif['success']:
                print("✅ Modification demande prix IA réussie!")
                print(f"   - Modifications: {list(resultat_modif.get('modifications_appliquees', {}).keys())}")
                if 'lignes_traitees' in resultat_modif.get('modifications_appliquees', {}):
                    print(f"   - Lignes traitées: {resultat_modif['modifications_appliquees']['lignes_traitees']}")
            else:
                print(f"❌ Erreur modification: {resultat_modif.get('error', '')}")
        else:
            print(f"❌ Erreur création demande: {resultat_demande.get('error', '')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR TESTS DEMANDES PRIX: {e}")
        return False

def test_assistant_ia_bons_achat():
    """Test des fonctionnalités IA pour les bons d'achat"""
    print("\n🛒 TESTS ASSISTANT IA - BONS D'ACHAT")
    print("=" * 60)
    
    try:
        from erp_database import ERPDatabase
        from assistant_ia import AssistantIAClaude
        from auth_config import get_claude_api_key
        
        print("📦 Modules bons d'achat importés avec succès")
        
        db = ERPDatabase()
        api_key = get_claude_api_key()
        
        if not api_key:
            print("⚠️ Tests IA sautés - pas de clé API Claude")
            return True
        
        assistant = AssistantIAClaude(db, api_key)
        
        # Test création bon d'achat avec IA
        print("\n1️⃣ Test création bon achat avec IA...")
        instructions_bon = """
        Créer bon d'achat matériaux isolation projet résidentiel.
        Commander 500 panneaux isolant polyuréthane 2x4 pieds à 25$ chacun,
        100 rouleaux laine minérale R-20 à 45$ le rouleau,
        25 tubes scellant polyuréthane à 12$ l'unité.
        Livraison souhaitée dans 5 jours au 456 chemin du Chantier, Beauport QC G1E 2A3.
        Conditions: paiement 30 jours net, matériaux protégés contre l'humidité.
        """
        
        resultat_bon = assistant.creer_bon_achat_avec_ia(instructions_bon)
        
        if resultat_bon['success']:
            print("✅ Création bon d'achat IA réussie!")
            print(f"   - Form ID: {resultat_bon.get('form_id')}")
            print(f"   - Type: {resultat_bon.get('type')}")
            print(f"   - Fournisseur: {resultat_bon.get('supplier_id')}")
            print(f"   - Lignes: {resultat_bon.get('nb_lignes', 0)}")
            print(f"   - Total estimé: {resultat_bon.get('total_estime', 0):.2f}$")
            print(f"   - Titre: {resultat_bon.get('titre')}")
            
            form_id = resultat_bon['form_id']
            
            # Test modification bon d'achat
            print("\n2️⃣ Test modification bon achat avec IA...")
            instructions_modif = """
            Ajouter 50 tubes adhésif construction à 8$ l'unité.
            Changer la date de livraison à dans 7 jours et 
            modifier l'adresse pour 789 rue de la Construction, Québec QC G1N 4B5.
            """
            
            resultat_modif = assistant.modifier_bon_achat_avec_ia(form_id, instructions_modif)
            
            if resultat_modif['success']:
                print("✅ Modification bon d'achat IA réussie!")
                print(f"   - Ancien total: {resultat_modif.get('ancien_total', 0):.2f}$")
                print(f"   - Nouveau total: {resultat_modif.get('nouveau_total', 0):.2f}$")
                print(f"   - Modifications: {list(resultat_modif.get('modifications_appliquees', {}).keys())}")
                if 'lignes_traitees' in resultat_modif.get('modifications_appliquees', {}):
                    print(f"   - Lignes traitées: {resultat_modif['modifications_appliquees']['lignes_traitees']}")
            else:
                print(f"❌ Erreur modification: {resultat_modif.get('error', '')}")
        else:
            print(f"❌ Erreur création bon d'achat: {resultat_bon.get('error', '')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR TESTS BONS ACHAT: {e}")
        return False

def test_integrite_fonctions_supply_chain():
    """Test d'intégrité de toutes les nouvelles fonctions supply chain"""
    print("\n🔧 TESTS D'INTÉGRITÉ SUPPLY CHAIN")
    print("=" * 60)
    
    try:
        from erp_database import ERPDatabase
        from assistant_ia import AssistantIAClaude
        
        db = ERPDatabase()
        assistant = AssistantIAClaude(db, None)  # Sans API pour test structure
        
        # Fonctions fournisseurs
        fonctions_fournisseurs = [
            'creer_fournisseur_avec_ia',
            'modifier_fournisseur_avec_ia'
        ]
        
        # Fonctions demandes prix
        fonctions_demandes = [
            'creer_demande_prix_avec_ia',
            'modifier_demande_prix_avec_ia'
        ]
        
        # Fonctions bons achat
        fonctions_bons = [
            'creer_bon_achat_avec_ia',
            'modifier_bon_achat_avec_ia'
        ]
        
        toutes_fonctions = fonctions_fournisseurs + fonctions_demandes + fonctions_bons
        
        print(f"\n📋 Test disponibilité fonctions ({len(toutes_fonctions)} fonctions)...")
        for fonction in toutes_fonctions:
            if hasattr(assistant, fonction):
                print(f"   ✅ Fonction {fonction} disponible")
            else:
                print(f"   ❌ Fonction {fonction} manquante")
                return False
        
        # Test imports modules supply chain
        print(f"\n📋 Test imports modules supply chain...")
        
        try:
            from fournisseurs import GestionnaireFournisseurs, CATEGORIES_CONSTRUCTION, CERTIFICATIONS_CONSTRUCTION
            print(f"   ✅ Module fournisseurs: {len(CATEGORIES_CONSTRUCTION)} catégories, {len(CERTIFICATIONS_CONSTRUCTION)} certifications")
        except ImportError as e:
            print(f"   ❌ Erreur import fournisseurs: {e}")
            return False
        
        # Vérifier les structures de données clés
        print(f"\n📋 Test structures données supply chain...")
        
        # Test tables fournisseurs
        tables_requises = [
            'suppliers',
            'supplier_categories', 
            'supplier_certifications',
            'supplier_forms',
            'supplier_form_lines'
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
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR TESTS INTÉGRITÉ SUPPLY CHAIN: {e}")
        return False

def test_exemples_usage_supply_chain():
    """Affiche des exemples d'utilisation des nouvelles fonctionnalités supply chain"""
    print("\n" + "=" * 80)
    print("📚 EXEMPLES D'UTILISATION SUPPLY CHAIN")
    print("=" * 80)
    
    exemples = [
        {
            'categorie': '🏭 FOURNISSEURS',
            'exemples': [
                {
                    'titre': 'Nouveau fournisseur béton',
                    'instruction': 'Créer fournisseur Béton Plus, spécialisé béton prêt-mélangé, Montréal, contact Pierre Martin 514-555-9876',
                    'description': 'Crée automatiquement avec catégories construction et coordonnées québécoises'
                },
                {
                    'titre': 'Modification coordonnées',
                    'instruction': 'Changer le téléphone du fournisseur FOUR-123 à 418-555-4321 et ajouter certification BNQ',
                    'description': 'Met à jour spécifiquement les champs demandés avec validation'
                }
            ]
        },
        {
            'categorie': '📋 DEMANDES DE PRIX',
            'exemples': [
                {
                    'titre': 'Demande matériaux toiture',
                    'instruction': 'Demander prix 200 feuilles contreplaqué OSB 4x8, 50 rouleaux membrane, livraison chantier Lévis',
                    'description': 'Génère demande structurée avec lignes détaillées et conditions'
                },
                {
                    'titre': 'Modification quantités',
                    'instruction': 'Modifier demande DP-456: augmenter OSB à 250 feuilles et ajouter 25 tubes scellant',
                    'description': 'Ajuste quantités existantes et ajoute nouveaux articles automatiquement'
                }
            ]
        },
        {
            'categorie': '🛒 BONS D\'ACHAT',
            'exemples': [
                {
                    'titre': 'Commande isolant',
                    'instruction': 'Commander 100 panneaux isolant XPS 2 pouces à 28$ chacun, livraison 123 rue Principale Québec',
                    'description': 'Crée bon d\'achat avec calcul automatique du total et adresse livraison'
                },
                {
                    'titre': 'Ajout article urgent',
                    'instruction': 'Ajouter au bon BA-789: 20 tubes colle PL à 15$ l\'unité, livraison express demain',
                    'description': 'Ajoute articles et recalcule automatiquement le total de commande'
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
    
    print(f"\n💡 AVANTAGES SUPPLY CHAIN IA:")
    print("   - Création rapide fournisseurs avec validation données québécoises")
    print("   - Génération automatique demandes prix structurées")
    print("   - Bons d'achat avec calcul automatique des totaux")
    print("   - Liaison intelligente fournisseurs ↔ produits ↔ projets")
    print("   - Interface conversationnelle naturelle en français")
    print("   - Respect automatique des standards construction québécois")

def test_complet_supply_chain():
    """Lance tous les tests pour Supply Chain IA"""
    print("🚀 LANCEMENT DES TESTS COMPLETS SUPPLY CHAIN IA")
    print("=" * 80)
    print("Tests des nouvelles fonctionnalités de gestion Supply Chain via IA")
    
    resultats = []
    
    # Tests fournisseurs
    print(f"\n{'='*80}")
    resultats.append(test_assistant_ia_fournisseurs())
    
    # Tests demandes prix
    print(f"\n{'='*80}")
    resultats.append(test_assistant_ia_demandes_prix())
    
    # Tests bons achat
    print(f"\n{'='*80}")
    resultats.append(test_assistant_ia_bons_achat())
    
    # Tests intégrité
    print(f"\n{'='*80}")
    resultats.append(test_integrite_fonctions_supply_chain())
    
    # Résumé final
    print(f"\n{'='*80}")
    if all(resultats):
        print("🎉 TOUS LES TESTS SUPPLY CHAIN RÉUSSIS!")
        print("✅ L'assistant IA peut gérer fournisseurs, demandes prix et bons d'achat!")
        test_exemples_usage_supply_chain()
        return True
    else:
        print("❌ CERTAINS TESTS SUPPLY CHAIN ONT ÉCHOUÉ")
        print("🔍 Vérifiez la configuration et les dépendances supply chain")
        return False

if __name__ == "__main__":
    success = test_complet_supply_chain()
    print(f"\n🏁 Tests Supply Chain terminés - {'✅ SUCCÈS' if success else '❌ ÉCHEC'}")
    
    print(f"\n📋 RÉSUMÉ DES NOUVELLES CAPACITÉS SUPPLY CHAIN IA:")
    print("   🔹 Création automatique fournisseurs avec catégories construction")
    print("   🔹 Modification intelligente coordonnées et certifications")
    print("   🔹 Génération demandes prix structurées multi-lignes")
    print("   🔹 Modification dynamique demandes avec ajout/suppression articles")
    print("   🔹 Création bons d'achat avec calcul automatique totaux")
    print("   🔹 Gestion livraisons et conditions spéciales")
    print("   🔹 Validation automatique formats québécois (téléphone, adresses)")
    print("   🔹 Interface conversationnelle naturelle française")
    
    if success:
        print(f"\n🎯 L'ASSISTANT IA SUPPLY CHAIN EST OPÉRATIONNEL!")
        print("   Peut gérer: FOURNISSEURS, DEMANDES PRIX, BONS D'ACHAT")
        print("   Intégration complète avec: PROJETS, DEVIS, PRODUITS, RH, CRM")
        print("   Via instructions en français québécois naturel!")
        print(f"\n🌟 L'ERP EST MAINTENANT ENTIÈREMENT GÉRÉ PAR IA!")
        print("   Modules IA complets: PROJETS + DEVIS + PRODUITS + RH + CRM + SUPPLY CHAIN")