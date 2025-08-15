#!/usr/bin/env python3
"""
Script d'analyse de la structure de la base de données SQLite
Identifie les tables, colonnes, index et relations
"""

import sqlite3
import os
import sys
from pathlib import Path

def analyze_database_structure(db_path):
    """Analyse la structure complète de la base de données SQLite"""
    
    print(f"=== ANALYSE DE LA BASE DE DONNÉES ===")
    print(f"Chemin: {db_path}")
    print(f"Existe: {os.path.exists(db_path)}")
    
    if not os.path.exists(db_path):
        print("❌ Base de données non trouvée!")
        return None
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Informations générales
        print(f"\n=== INFORMATIONS GÉNÉRALES ===")
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        print(f"Nombre de tables: {table_count}")
        
        # 2. Lister toutes les tables
        print(f"\n=== TABLES EXISTANTES ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            print(f"\n📋 TABLE: {table_name}")
            
            # Informations sur les colonnes
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print("   Colonnes:")
            for col in columns:
                col_id, name, data_type, not_null, default_val, pk = col
                constraints = []
                if pk:
                    constraints.append("PRIMARY KEY")
                if not_null:
                    constraints.append("NOT NULL")
                if default_val:
                    constraints.append(f"DEFAULT {default_val}")
                
                constraint_str = f" ({', '.join(constraints)})" if constraints else ""
                print(f"     - {name}: {data_type}{constraint_str}")
            
            # Clés étrangères
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = cursor.fetchall()
            
            if foreign_keys:
                print("   Clés étrangères:")
                for fk in foreign_keys:
                    fk_id, seq, table_ref, from_col, to_col, on_update, on_delete, match = fk
                    print(f"     - {from_col} → {table_ref}({to_col})")
            
            # Index
            cursor.execute(f"PRAGMA index_list({table_name})")
            indexes = cursor.fetchall()
            
            if indexes:
                print("   Index:")
                for idx in indexes:
                    seq, name, unique, origin, partial = idx
                    unique_str = " (UNIQUE)" if unique else ""
                    print(f"     - {name}{unique_str}")
        
        # 3. Vérification spécifique de formulaire_bt_id
        print(f"\n=== VÉRIFICATION COLONNE formulaire_bt_id ===")
        tables_with_bt_id = []
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                if col[1] == 'formulaire_bt_id':
                    tables_with_bt_id.append(table_name)
                    print(f"✅ {table_name} contient formulaire_bt_id")
        
        if not tables_with_bt_id:
            print("❌ Aucune table ne contient la colonne formulaire_bt_id")
        
        # 4. Analyse des relations avec formulaires
        print(f"\n=== RELATIONS AVEC TABLE formulaires ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='formulaires'")
        if cursor.fetchone():
            print("✅ Table formulaires existe")
            
            # Structure de la table formulaires
            cursor.execute("PRAGMA table_info(formulaires)")
            formulaires_cols = cursor.fetchall()
            print("   Colonnes de formulaires:")
            for col in formulaires_cols:
                print(f"     - {col[1]}: {col[2]}")
        else:
            print("❌ Table formulaires n'existe pas")
        
        # 5. Vérifier les contraintes de clés étrangères
        print(f"\n=== CONTRAINTES CLÉS ÉTRANGÈRES ===")
        for table_name in tables_with_bt_id:
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = cursor.fetchall()
            
            bt_fk_found = False
            for fk in foreign_keys:
                if fk[3] == 'formulaire_bt_id':  # from_col
                    bt_fk_found = True
                    print(f"✅ {table_name}.formulaire_bt_id → {fk[2]}({fk[4]})")
            
            if not bt_fk_found and table_name in tables_with_bt_id:
                print(f"⚠️  {table_name}.formulaire_bt_id sans contrainte FK")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def create_database_if_missing():
    """Crée la base de données si elle n'existe pas"""
    try:
        # Importer le module de base de données local
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from erp_database import ERPDatabase
        
        db_path = "erp_production_dg.db"
        print(f"Création de la base de données: {db_path}")
        
        # Créer la base de données
        db = ERPDatabase(db_path)
        print("✅ Base de données créée avec succès")
        
        return db_path
        
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    # Chemins possibles pour la base de données
    possible_paths = [
        "erp_production_dg.db",
        os.path.join("data", "erp_production_dg.db"),
        "C:\\IA\\ERP AI\\erp_production_dg.db"
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("Base de données non trouvée, tentative de création...")
        db_path = create_database_if_missing()
    
    if db_path:
        analyze_database_structure(db_path)
    else:
        print("❌ Impossible d'analyser la structure de la base de données")