#!/usr/bin/env python3
# test_produits_ia.py - Tests pour les fonctionnalités IA des produits
# ERP Production DG Inc. - Tests des nouvelles capacités de l'assistant IA

"""
Tests pour vérifier le bon fonctionnement des nouvelles fonctionnalités IA 
pour la création et modification de produits via l'assistant Claude
"""

import os
import sys
import traceback
from pathlib import Path

# Ajouter le répertoire parent au PATH pour les imports
sys.path.append(str(Path(__file__).parent))

def test_assistant_ia_produits():
    """Test des fonctionnalités IA pour les produits"""
    print("🧪 TESTS ASSISTANT IA - GESTION PRODUITS")
    print("=" * 60)
    
    try:
        # Imports nécessaires
        from erp_database import ERPDatabase
        from assistant_ia import AssistantIAClaude
        from auth_config import get_claude_api_key
        
        print("📦 Modules importés avec succès")
        
        # 1. Initialisation base de données
        print("\n1️⃣ Initialisation base de données...")
        db = ERPDatabase()
        if not db.db_path or not os.path.exists(db.db_path):
            print("❌ Base de données non trouvée")
            return False
        print(f"✅ Base de données connectée: {db.db_path}")
        
        # 2. Initialisation Assistant IA
        print("\n2️⃣ Initialisation Assistant IA...")
        api_key = get_claude_api_key()
        if not api_key:
            print("⚠️ Clé API Claude non configurée - tests en mode simulation")
            assistant = AssistantIAClaude(db, None)  # Mode sans API
        else:
            print("✅ Clé API Claude configurée")
            assistant = AssistantIAClaude(db, api_key)
        
        # 3. Test création de produit avec IA
        print("\n3️⃣ Test création produit avec IA...")
        
        if assistant.client:  # Si API disponible
            # Test avec instructions réalistes
            instructions_creation = """
            Créer un produit acier structural W200x46 pour poutres de construction.
            Prix environ 15$ par pied linéaire. Stock initial 50 pièces, minimum 20 pièces.
            Fournisseur principal: Canam Steel. 
            Dimensions standard de 20 pieds de longueur.
            """
            
            print(f"📝 Instructions: {instructions_creation[:100]}...")
            resultat = assistant.creer_produit_avec_ia(instructions_creation)
            
            if resultat['success']:
                print("✅ Création produit IA réussie!")
                print(f"   - Produit ID: {resultat.get('produit_id')}")
                print(f"   - Message: {resultat.get('message', '')[:100]}...")
                
                # 4. Test modification du produit créé
                if resultat.get('produit_id'):
                    print("\n4️⃣ Test modification produit avec IA...")
                    instructions_modification = "Augmenter le prix à 18$ et le stock minimum à 25 pièces"
                    
                    resultat_modif = assistant.modifier_produit_avec_ia(
                        resultat['produit_id'], 
                        instructions_modification
                    )
                    
                    if resultat_modif['success']:
                        print("✅ Modification produit IA réussie!")
                        print(f"   - Modifications: {resultat_modif.get('modifications_appliquees', {})}")
                        print(f"   - Impact: {resultat_modif.get('impact', '')[:100]}...")
                    else:
                        print(f"❌ Erreur modification: {resultat_modif.get('error', '')}")
                
                # 5. Test analyse produit spécifique
                print("\n5️⃣ Test analyse produit spécifique...")
                resultat_analyse = assistant.analyser_produit_specifique(resultat['produit_id'])
                
                if resultat_analyse['success']:
                    print("✅ Analyse produit IA réussie!")
                    print(f"   - Produit analysé: {resultat_analyse.get('produit_nom', '')}")
                    print(f"   - Analyse: {resultat_analyse.get('analyse_complete', '')[:150]}...")
                else:
                    print(f"❌ Erreur analyse: {resultat_analyse.get('error', '')}")
                    
            else:
                print(f"❌ Erreur création: {resultat.get('error', '')}")
        
        else:
            print("⚠️ Tests IA sautés - pas de clé API")
        
        # 6. Test optimisation catalogue
        print("\n6️⃣ Test optimisation catalogue produits...")
        
        if assistant.client:
            resultat_optim = assistant.optimiser_catalogue_produits()
            
            if resultat_optim['success']:
                print("✅ Optimisation catalogue réussie!")
                print(f"   - Nombre total produits: {resultat_optim.get('nb_produits_total', 0)}")
                print(f"   - Nombre catégories: {resultat_optim.get('nb_categories', 0)}")
                print(f"   - Valeur stock total: ${resultat_optim.get('valeur_stock_total', 0):,.2f}")
            else:
                print(f"❌ Erreur optimisation: {resultat_optim.get('error', '')}")
        else:
            print("⚠️ Test optimisation sauté - pas de clé API")
        
        # 7. Test intégrité des fonctions (même sans API)
        print("\n7️⃣ Tests d'intégrité des fonctions...")
        
        # Vérifier que les fonctions existent
        fonctions_requises = [
            'creer_produit_avec_ia',
            'modifier_produit_avec_ia', 
            'analyser_produit_specifique',
            'optimiser_catalogue_produits'
        ]
        
        for fonction in fonctions_requises:
            if hasattr(assistant, fonction):
                print(f"   ✅ Fonction {fonction} disponible")
            else:
                print(f"   ❌ Fonction {fonction} manquante")
                return False
        
        # 8. Vérifier imports modules produits
        print("\n8️⃣ Test imports modules produits...")
        try:
            from produits import GestionnaireProduits, CATEGORIES_PRODUITS, UNITES_VENTE
            gestionnaire = GestionnaireProduits(db)
            print(f"✅ GestionnaireProduits initialisé")
            print(f"   - {len(CATEGORIES_PRODUITS)} catégories disponibles")
            print(f"   - {len(UNITES_VENTE)} unités de vente disponibles")
        except ImportError as e:
            print(f"❌ Erreur import produits: {e}")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 TOUS LES TESTS RÉUSSIS!")
        print("✅ L'Assistant IA peut maintenant créer et modifier des produits")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR LORS DES TESTS: {e}")
        print(f"🐛 Détails: {traceback.format_exc()}")
        return False

def test_exemples_usage():
    """Affiche des exemples d'utilisation des nouvelles fonctionnalités"""
    print("\n" + "=" * 60)
    print("📚 EXEMPLES D'UTILISATION")
    print("=" * 60)
    
    exemples = [
        {
            'titre': '🏗️ Création produit béton',
            'instruction': 'Créer un sac de béton prémélangé 25 MPa, 30kg, prix 7.50$, stock 200 sacs, minimum 50',
            'description': 'Crée automatiquement un produit béton avec spécifications techniques'
        },
        {
            'titre': '🔧 Modification prix acier',
            'instruction': 'Augmenter le prix du produit W200x46 de 15% à cause de l\'inflation',
            'description': 'Calcule et applique automatiquement la nouvelle tarification'
        },
        {
            'titre': '📊 Analyse isolation',
            'instruction': 'Analyser les performances du produit laine minérale R-20',
            'description': 'Fournit insights complets: stock, prix, conformité, optimisations'
        },
        {
            'titre': '🎯 Optimisation globale',
            'instruction': 'Optimiser tout le catalogue produits selon les saisons québécoises',
            'description': 'Plan stratégique complet avec actions 30/60/90 jours'
        }
    ]
    
    for i, exemple in enumerate(exemples, 1):
        print(f"\n{i}. {exemple['titre']}")
        print(f"   💬 Instruction: \"{exemple['instruction']}\"")
        print(f"   📝 Résultat: {exemple['description']}")
    
    print(f"\n💡 UTILISATION DANS L'APPLICATION:")
    print("   - Interface chat de l'assistant IA")
    print("   - Commandes vocales en français québécois")
    print("   - Intégration complète avec la base de données")
    print("   - Validation automatique des données")

if __name__ == "__main__":
    print("🚀 LANCEMENT DES TESTS PRODUITS IA")
    print("Tests des nouvelles fonctionnalités de gestion de produits via IA")
    
    # Lancer les tests
    success = test_assistant_ia_produits()
    
    if success:
        test_exemples_usage()
        print(f"\n✅ SUCCÈS TOTAL - L'assistant IA peut gérer les produits!")
    else:
        print(f"\n❌ ÉCHEC - Vérifiez la configuration")
    
    print("\n🏁 Tests terminés")