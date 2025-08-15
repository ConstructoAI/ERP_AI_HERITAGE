#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de debug pour tester la persistance des données ERP
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from database_config import DATABASE_PATH
from erp_database import ERPDatabase

def debug_persistence():
    """Teste la persistance des données"""
    
    print("🔍 DEBUG PERSISTANCE - ERP Production DG Inc.")
    print("=" * 60)
    
    # 1. Vérifier les chemins
    print(f"📁 Répertoire courant: {os.getcwd()}")
    print(f"📄 DATABASE_PATH configuré: {DATABASE_PATH}")
    print(f"📊 Fichier DB existe: {os.path.exists(DATABASE_PATH)}")
    print(f"📏 Taille du fichier: {os.path.getsize(DATABASE_PATH) if os.path.exists(DATABASE_PATH) else 0} bytes")
    
    print("\n🔍 Recherche de tous les fichiers .db:")
    for db_file in Path(".").glob("**/*.db"):
        print(f"  📄 {db_file} ({db_file.stat().st_size} bytes)")
    
    # 2. Connecter à la base de données principale
    print(f"\n🔗 Connexion à: {DATABASE_PATH}")
    try:
        db = ERPDatabase(DATABASE_PATH)
        print(f"✅ Connexion réussie")
        print(f"📍 Chemin DB dans l'objet: {db.db_path}")
        
        # 3. Compter les projets existants
        projets_count = db.execute_query("SELECT COUNT(*) as count FROM projects")
        companies_count = db.execute_query("SELECT COUNT(*) as count FROM companies") 
        
        print(f"\n📊 DONNÉES ACTUELLES:")
        print(f"  👥 Clients: {companies_count[0]['count'] if companies_count else 0}")
        print(f"  🏢 Projets: {projets_count[0]['count'] if projets_count else 0}")
        
        # 4. Lister les derniers projets
        if projets_count and projets_count[0]['count'] > 0:
            derniers_projets = db.execute_query("""
                SELECT p.id, p.nom_projet, p.statut, p.created_at, c.nom as client_nom
                FROM projects p
                LEFT JOIN companies c ON p.client_company_id = c.id
                ORDER BY p.created_at DESC
                LIMIT 5
            """)
            
            print(f"\n📋 DERNIERS PROJETS:")
            for i, projet in enumerate(derniers_projets, 1):
                print(f"  {i}. {projet.get('nom_projet', 'N/A')} - {projet.get('client_nom', 'N/A')} ({projet.get('statut', 'N/A')})")
        
        # 5. Test de création d'un projet temporaire
        print(f"\n🧪 TEST DE PERSISTANCE:")
        test_client_id = db.execute_insert("""
            INSERT INTO companies (nom, secteur, type_entreprise, created_at)
            VALUES (?, 'Construction', 'CLIENT', datetime('now'))
        """, (f"CLIENT_TEST_{datetime.now().strftime('%H%M%S')}",))
        
        if test_client_id:
            print(f"  ✅ Client test créé avec ID: {test_client_id}")
            
            test_project_data = {
                'nom_projet': f"PROJET_TEST_{datetime.now().strftime('%H%M%S')}",
                'client_company_id': test_client_id,
                'statut': 'À FAIRE',
                'priorite': 'MOYEN',
                'tache': '1.1 Test persistance',
                'date_soumis': datetime.now().isoformat(),
                'prix_estime': 1000.0,
                'description': 'Projet de test pour vérifier la persistance'
            }
            
            test_project_id = db.create_project(test_project_data)
            
            if test_project_id:
                print(f"  ✅ Projet test créé avec ID: {test_project_id}")
                
                # Vérification immédiate
                verification = db.execute_query("SELECT COUNT(*) as count FROM projects WHERE id = ?", (test_project_id,))
                print(f"  🔍 Vérification immédiate: {verification[0]['count'] if verification else 0} projet trouvé")
                
                # Vérifier la taille du fichier après insertion
                print(f"  📏 Nouvelle taille fichier: {os.path.getsize(DATABASE_PATH)} bytes")
                
                print(f"\n💾 POUR TESTER LA PERSISTANCE:")
                print(f"  1. Notez l'ID du projet test: {test_project_id}")
                print(f"  2. Redémarrez l'application ERP")
                print(f"  3. Vérifiez si le projet {test_project_data['nom_projet']} existe toujours")
                
            else:
                print(f"  ❌ Échec création projet test")
        else:
            print(f"  ❌ Échec création client test")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)

if __name__ == "__main__":
    debug_persistence()