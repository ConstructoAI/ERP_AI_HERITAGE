#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple pour les nouvelles fonctionnalites devis de l'assistant IA
"""

import os
import sys
from database_config import get_database_path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_simple():
    print("TEST - Assistant IA Devis")
    print("=" * 30)
    
    try:
        from erp_database import ERPDatabase
        from assistant_ia import AssistantIAClaude
        
        db_path = get_database_path()
        print(f"DB: {db_path}")
        
        db = ERPDatabase(db_path)
        print("DB OK")
        
        api_key = os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('CLAUDE_API_KEY')
        assistant = AssistantIAClaude(db, api_key)
        print("Assistant OK")
        
        # Test collecte donnees devis
        print("\nTest collecte devis...")
        donnees = assistant._collecter_donnees_devis()
        print(f"Devis recents: {donnees.get('nb_devis_recents', 0)}")
        
        # Test recherche devis existants
        print("\nRecherche devis existants...")
        devis = db.execute_query("SELECT COUNT(*) as nb FROM formulaires WHERE type_formulaire = 'EST'")
        nb_devis = devis[0]['nb'] if devis else 0
        print(f"Devis total: {nb_devis}")
        
        if nb_devis > 0:
            # Test avec premier devis
            premier_devis = db.execute_query("SELECT id FROM formulaires WHERE type_formulaire = 'EST' LIMIT 1")
            if premier_devis and api_key:
                devis_id = premier_devis[0]['id']
                print(f"Test analyse devis #{devis_id}...")
                
                try:
                    analyse = assistant.analyser_devis_specifique(str(devis_id))
                    if analyse['success']:
                        print("Analyse OK")
                        print(f"Metriques: {analyse.get('metriques', {})}")
                    else:
                        print(f"Erreur: {analyse.get('error', 'Inconnue')}")
                except Exception as e:
                    print(f"Exception analyse: {e}")
        
        print("\nTests termines!")
        return True
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_simple()