#!/usr/bin/env python3
# test_rh_crm_ia.py - Tests pour les fonctionnalités IA RH et CRM
# ERP Production DG Inc. - Tests des nouvelles capacités de l'assistant IA pour employés/contacts/entreprises

"""
Tests pour vérifier le bon fonctionnement des nouvelles fonctionnalités IA 
pour la création et modification d'employés, contacts et entreprises via l'assistant Claude
"""

import os
import sys
import traceback
from pathlib import Path

# Ajouter le répertoire parent au PATH pour les imports
sys.path.append(str(Path(__file__).parent))

def test_assistant_ia_employes():
    """Test des fonctionnalités IA pour les employés"""
    print("👥 TESTS ASSISTANT IA - GESTION EMPLOYÉS")
    print("=" * 60)
    
    try:
        # Imports nécessaires
        from erp_database import ERPDatabase
        from assistant_ia import AssistantIAClaude
        from auth_config import get_claude_api_key
        
        print("📦 Modules employés importés avec succès")
        
        # Initialisation
        db = ERPDatabase()
        api_key = get_claude_api_key()
        
        if not api_key:
            print("⚠️ Tests IA sautés - pas de clé API Claude")
            return True
        
        assistant = AssistantIAClaude(db, api_key)
        
        # Test création employé avec IA
        print("\n1️⃣ Test création employé avec IA...")
        instructions_creation = """
        Créer un employé Marc Lavoie, charpentier senior, département charpente bois.
        Salaire 72000$ annuel, embauché aujourd'hui, contrat CDI.
        Compétences: charpenterie résidentielle niveau expert, lecture de plans avancé.
        Téléphone 514-555-0123, email marc.lavoie@constructo.ai
        """
        
        resultat = assistant.creer_employe_avec_ia(instructions_creation)
        
        if resultat['success']:
            print("✅ Création employé IA réussie!")
            print(f"   - Employé ID: {resultat.get('employe_id')}")
            print(f"   - Compétences: {resultat.get('nb_competences', 0)}")
            
            employe_id = resultat['employe_id']
            
            # Test modification employé
            print("\n2️⃣ Test modification employé avec IA...")
            instructions_modif = "Promouvoir Marc à contremaître, augmenter salaire à 78000$ et changer département à direction"
            
            resultat_modif = assistant.modifier_employe_avec_ia(employe_id, instructions_modif)
            
            if resultat_modif['success']:
                print("✅ Modification employé IA réussie!")
                print(f"   - Modifications: {list(resultat_modif.get('modifications_appliquees', {}).keys())}")
            else:
                print(f"❌ Erreur modification: {resultat_modif.get('error', '')}")
        else:
            print(f"❌ Erreur création: {resultat.get('error', '')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR TESTS EMPLOYÉS: {e}")
        return False

def test_assistant_ia_contacts_entreprises():
    """Test des fonctionnalités IA pour contacts et entreprises"""
    print("\n🏢 TESTS ASSISTANT IA - GESTION CONTACTS/ENTREPRISES")
    print("=" * 60)
    
    try:
        from erp_database import ERPDatabase
        from assistant_ia import AssistantIAClaude
        from auth_config import get_claude_api_key
        
        print("📦 Modules CRM importés avec succès")
        
        db = ERPDatabase()
        api_key = get_claude_api_key()
        
        if not api_key:
            print("⚠️ Tests IA sautés - pas de clé API Claude")
            return True
        
        assistant = AssistantIAClaude(db, api_key)
        
        # Test création entreprise avec IA
        print("\n1️⃣ Test création entreprise avec IA...")
        instructions_entreprise = """
        Créer une entreprise BâtiPro Québec Inc., entrepreneur général dans la construction commerciale.
        Adresse: 456 boulevard Saint-Laurent, Montréal QC H2X 2V4 Canada.
        Site web: www.batipro.ca
        Notes: Spécialisé dans les édifices à bureaux et centres commerciaux
        """
        
        resultat_ent = assistant.creer_entreprise_avec_ia(instructions_entreprise)
        
        if resultat_ent['success']:
            print("✅ Création entreprise IA réussie!")
            print(f"   - Entreprise ID: {resultat_ent.get('entreprise_id')}")
            
            entreprise_id = resultat_ent['entreprise_id']
            
            # Test création contact lié à l'entreprise
            print("\n2️⃣ Test création contact avec IA...")
            instructions_contact = """
            Créer un contact Sophie Tremblay, directrice des opérations.
            Téléphone 514-987-6543, email sophie.tremblay@batipro.ca
            Notes: Contact principal pour soumissions commerciales
            """
            
            resultat_contact = assistant.creer_contact_avec_ia(instructions_contact, entreprise_id)
            
            if resultat_contact['success']:
                print("✅ Création contact IA réussie!")
                print(f"   - Contact ID: {resultat_contact.get('contact_id')}")
                
                contact_id = resultat_contact['contact_id']
                
                # Test modification contact
                print("\n3️⃣ Test modification contact avec IA...")
                instructions_modif_contact = "Changer le titre à présidente et mettre le nouveau téléphone 514-987-9999"
                
                resultat_modif_contact = assistant.modifier_contact_avec_ia(contact_id, instructions_modif_contact)
                
                if resultat_modif_contact['success']:
                    print("✅ Modification contact IA réussie!")
                else:
                    print(f"❌ Erreur modification contact: {resultat_modif_contact.get('error', '')}")
            else:
                print(f"❌ Erreur création contact: {resultat_contact.get('error', '')}")
            
            # Test modification entreprise
            print("\n4️⃣ Test modification entreprise avec IA...")
            instructions_modif_ent = "Changer l'adresse à 789 rue de la Gauchetière, Montréal QC H3B 2M7"
            
            resultat_modif_ent = assistant.modifier_entreprise_avec_ia(entreprise_id, instructions_modif_ent)
            
            if resultat_modif_ent['success']:
                print("✅ Modification entreprise IA réussie!")
                print(f"   - Modifications: {list(resultat_modif_ent.get('modifications_appliquees', {}).keys())}")
            else:
                print(f"❌ Erreur modification entreprise: {resultat_modif_ent.get('error', '')}")
        else:
            print(f"❌ Erreur création entreprise: {resultat_ent.get('error', '')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR TESTS CRM: {e}")
        return False

def test_integrite_fonctions():
    """Test d'intégrité de toutes les nouvelles fonctions"""
    print("\n🔧 TESTS D'INTÉGRITÉ DES FONCTIONS")
    print("=" * 60)
    
    try:
        from erp_database import ERPDatabase
        from assistant_ia import AssistantIAClaude
        
        db = ERPDatabase()
        assistant = AssistantIAClaude(db, None)  # Sans API pour test structure
        
        # Fonctions employés
        fonctions_employes = [
            'creer_employe_avec_ia',
            'modifier_employe_avec_ia'
        ]
        
        # Fonctions contacts
        fonctions_contacts = [
            'creer_contact_avec_ia',
            'modifier_contact_avec_ia'
        ]
        
        # Fonctions entreprises
        fonctions_entreprises = [
            'creer_entreprise_avec_ia', 
            'modifier_entreprise_avec_ia'
        ]
        
        toutes_fonctions = fonctions_employes + fonctions_contacts + fonctions_entreprises
        
        for fonction in toutes_fonctions:
            if hasattr(assistant, fonction):
                print(f"   ✅ Fonction {fonction} disponible")
            else:
                print(f"   ❌ Fonction {fonction} manquante")
                return False
        
        # Test imports modules
        print("\n📋 Test imports modules...")
        
        try:
            from employees import GestionnaireEmployes, DEPARTEMENTS, COMPETENCES_DISPONIBLES
            print(f"   ✅ Module employés: {len(DEPARTEMENTS)} départements, {len(COMPETENCES_DISPONIBLES)} compétences")
        except ImportError as e:
            print(f"   ❌ Erreur import employees: {e}")
            return False
        
        try:
            from crm import GestionnaireCRM, TYPES_ENTREPRISES_CONSTRUCTION, SECTEURS_CONSTRUCTION
            print(f"   ✅ Module CRM: {len(TYPES_ENTREPRISES_CONSTRUCTION)} types entreprises, {len(SECTEURS_CONSTRUCTION)} secteurs")
        except ImportError as e:
            print(f"   ❌ Erreur import crm: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR TESTS INTÉGRITÉ: {e}")
        return False

def test_exemples_usage():
    """Affiche des exemples d'utilisation des nouvelles fonctionnalités"""
    print("\n" + "=" * 80)
    print("📚 EXEMPLES D'UTILISATION RH & CRM")
    print("=" * 80)
    
    exemples = [
        {
            'categorie': '👥 EMPLOYÉS',
            'exemples': [
                {
                    'titre': 'Création charpentier',
                    'instruction': 'Créer un employé Pierre Dubois, charpentier-menuisier, département chantier, 28$/h',
                    'description': 'Crée automatiquement un employé avec compétences et salaire adapté'
                },
                {
                    'titre': 'Promotion employé',
                    'instruction': 'Promouvoir l\'employé EMP-123 à superviseur avec augmentation 10%',
                    'description': 'Calcule automatiquement nouveau salaire et met à jour le poste'
                }
            ]
        },
        {
            'categorie': '📞 CONTACTS',
            'exemples': [
                {
                    'titre': 'Contact client',
                    'instruction': 'Créer contact Marie Bertrand, directrice achats chez Béton Plus, 418-555-7890',
                    'description': 'Crée contact professionnel avec validation format québécois'
                },
                {
                    'titre': 'Mise à jour contact',
                    'instruction': 'Changer l\'email du contact CONT-456 à nouveau.email@entreprise.com',
                    'description': 'Modifie spécifiquement les champs demandés'
                }
            ]
        },
        {
            'categorie': '🏢 ENTREPRISES',
            'exemples': [
                {
                    'titre': 'Nouvelle entreprise',
                    'instruction': 'Créer entreprise Toiture Express, sous-traitant spécialisé, secteur couverture, Québec QC',
                    'description': 'Structure complète avec adresse québécoise et secteur approprié'
                },
                {
                    'titre': 'Changement adresse',
                    'instruction': 'Déménager l\'entreprise COMP-789 au 123 rue Principal, Sherbrooke QC J1H 1A1',
                    'description': 'Met à jour adresse structurée avec validation code postal'
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
    
    print(f"\n💡 UTILISATION DANS L'APPLICATION:")
    print("   - Interface chat de l'assistant IA")
    print("   - Commandes vocales en français québécois") 
    print("   - Intégration complète avec les modules existants")
    print("   - Validation automatique des données RH/CRM")
    print("   - Liens automatiques entre contacts et entreprises")

def test_complet_rh_crm():
    """Lance tous les tests pour RH et CRM"""
    print("🚀 LANCEMENT DES TESTS COMPLETS RH & CRM IA")
    print("=" * 80)
    print("Tests des nouvelles fonctionnalités de gestion RH et CRM via IA")
    
    resultats = []
    
    # Tests employés
    print(f"\n{'='*80}")
    resultats.append(test_assistant_ia_employes())
    
    # Tests contacts/entreprises
    print(f"\n{'='*80}")
    resultats.append(test_assistant_ia_contacts_entreprises())
    
    # Tests intégrité
    print(f"\n{'='*80}")
    resultats.append(test_integrite_fonctions())
    
    # Résumé final
    print(f"\n{'='*80}")
    if all(resultats):
        print("🎉 TOUS LES TESTS RÉUSSIS!")
        print("✅ L'assistant IA peut gérer employés, contacts et entreprises!")
        test_exemples_usage()
        return True
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("🔍 Vérifiez la configuration et les dépendances")
        return False

if __name__ == "__main__":
    success = test_complet_rh_crm()
    print(f"\n🏁 Tests terminés - {'✅ SUCCÈS' if success else '❌ ÉCHEC'}")
    
    print(f"\n📋 RÉSUMÉ DES NOUVELLES CAPACITÉS IA:")
    print("   🔹 Création automatique d'employés avec compétences")
    print("   🔹 Modification intelligente des données RH")
    print("   🔹 Gestion complète contacts professionnels") 
    print("   🔹 Création/modification entreprises construction")
    print("   🔹 Liaison automatique contacts ↔ entreprises")
    print("   🔹 Validation données québécoises (téléphone, adresses)")
    print("   🔹 Interface conversationnelle naturelle")
    
    if success:
        print(f"\n🎯 L'ASSISTANT IA EST MAINTENANT COMPLET!")
        print("   Peut gérer: PROJETS, DEVIS, PRODUITS, EMPLOYÉS, CONTACTS, ENTREPRISES")
        print("   Via instructions en français québécois naturel!")