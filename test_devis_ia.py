#!/usr/bin/env python3
"""
Script de test pour les nouvelles fonctionnalités devis de l'assistant IA
"""

import os
import sys
from database_config import get_database_path

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_assistant_ia_devis():
    """Test des nouvelles fonctionnalités devis"""
    
    print("TEST - Assistant IA Devis")
    print("=" * 50)
    
    try:
        # Importer les modules
        from erp_database import ERPDatabase
        from assistant_ia import AssistantIAClaude
        
        # Initialiser la base de données
        db_path = get_database_path()
        print(f"Base de donnees: {db_path}")
        
        db = ERPDatabase(db_path)
        print("Base de donnees initialisee")
        
        # Initialiser l'assistant IA
        api_key = os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('CLAUDE_API_KEY')
        if not api_key:
            print("Cle API Claude non configuree - tests limites")
            
        assistant = AssistantIAClaude(db, api_key)
        print("Assistant IA initialise")
        
        # Test 1: Collecte des données devis
        print("\nTest 1: Collecte des donnees devis")
        donnees_devis = assistant._collecter_donnees_devis()
        
        if donnees_devis:
            print(f"✅ Données collectées:")
            print(f"   - Devis récents: {donnees_devis.get('nb_devis_recents', 0)}")
            print(f"   - Statuts: {len(donnees_devis.get('devis_par_statut', []))}")
            print(f"   - Top produits: {len(donnees_devis.get('top_produits', []))}")
            if donnees_devis.get('taux_conversion'):
                taux = donnees_devis['taux_conversion']
                conversion_rate = (taux.get('devis_approuves', 0) / max(taux.get('total_devis', 1), 1) * 100)
                print(f"   - Taux de conversion: {conversion_rate:.1f}%")
        else:
            print("❌ Aucune donnée de devis collectée")
        
        # Test 2: Recherche de devis existants
        print("\n🔍 Test 2: Recherche de devis existants")
        devis_existants = db.execute_query("""
            SELECT id, numero_document, statut, total_ht, created_at
            FROM formulaires 
            WHERE type_formulaire = 'EST'
            LIMIT 3
        """)
        
        if devis_existants:
            print(f"✅ {len(devis_existants)} devis trouvés dans la base:")
            for devis in devis_existants:
                devis_dict = dict(devis)
                print(f"   - #{devis_dict['id']}: {devis_dict['numero_document']} - {devis_dict['statut']} - ${float(devis_dict.get('total_ht', 0)):,.2f}")
            
            # Test 3: Analyse d'un devis spécifique
            if api_key:
                print("\n🔬 Test 3: Analyse d'un devis spécifique")
                devis_a_analyser = devis_existants[0]
                analyse = assistant.analyser_devis_specifique(str(devis_a_analyser['id']))
                
                if analyse['success']:
                    print("✅ Analyse réussie:")
                    print(f"   - Métriques: {analyse.get('metriques', {})}")
                    print(f"   - Analyse: {analyse['analyse'][:200]}..." if len(analyse['analyse']) > 200 else f"   - Analyse: {analyse['analyse']}")
                else:
                    print(f"❌ Erreur d'analyse: {analyse.get('error', 'Inconnue')}")
            else:
                print("⚠️ Test 3 sauté - pas de clé API")
        else:
            print("❌ Aucun devis existant trouvé")
        
        # Test 4: Création d'un devis avec IA (test de la structure)
        print("\n🆕 Test 4: Test création devis avec IA")
        if api_key:
            instructions_test = """
            Créer un devis pour des matériaux de construction:
            - 100 sacs de ciment Portland à 15$ chacun
            - 50 m³ de gravier à 30$ le m³
            - 200 blocs de béton à 5$ l'unité
            Validité 45 jours, paiement net 30 jours
            """
            
            resultat_creation = assistant.creer_devis_avec_ia(instructions_test, company_id=1)
            
            if resultat_creation['success']:
                print("✅ Test de création réussi:")
                if resultat_creation.get('devis_id'):
                    print(f"   - Devis créé: #{resultat_creation['devis_id']}")
                    print(f"   - Total: ${resultat_creation.get('total_ht', 0):,.2f}")
                    print(f"   - Articles: {resultat_creation.get('nb_articles', 0)}")
                else:
                    print(f"   - Analyse: {resultat_creation.get('analyse_creation', '')[:150]}...")
            else:
                print(f"❌ Erreur de création: {resultat_creation.get('error', 'Inconnue')}")
        else:
            print("⚠️ Test 4 sauté - pas de clé API")
        
        # Test 5: Conversation naturelle avec contexte devis
        print("\n💬 Test 5: Conversation naturelle avec devis")
        if api_key:
            message_test = "Comment vont nos devis ce mois-ci ? Y a-t-il des devis en attente qu'il faudrait relancer ?"
            
            try:
                reponse = assistant.conversation_naturelle(message_test)
                print("✅ Conversation réussie:")
                print(f"   - Réponse: {reponse[:200]}..." if len(reponse) > 200 else f"   - Réponse: {reponse}")
            except Exception as e:
                print(f"❌ Erreur conversation: {e}")
        else:
            print("⚠️ Test 5 sauté - pas de clé API")
        
        print("\n🎉 Tests terminés avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_assistant_ia_devis()
    sys.exit(0 if success else 1)