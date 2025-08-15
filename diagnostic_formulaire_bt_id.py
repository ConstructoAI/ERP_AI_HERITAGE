#!/usr/bin/env python3
"""
Script de diagnostic complet pour la colonne formulaire_bt_id
Analyse le code source et identifie tous les usages
"""

import os
import re
import sys
from pathlib import Path

def find_formulaire_bt_id_usage():
    """Trouve tous les usages de formulaire_bt_id dans les fichiers Python"""
    
    print("=== DIAGNOSTIC COLONNE formulaire_bt_id ===\n")
    
    # Dossier courant
    current_dir = Path(".")
    python_files = list(current_dir.glob("*.py"))
    
    print(f"Fichiers Python à analyser: {len(python_files)}\n")
    
    usages = {
        'SELECT': [],
        'INSERT': [],
        'UPDATE': [], 
        'DELETE': [],
        'ALTER_TABLE': [],
        'CREATE_TABLE': [],
        'JOIN': [],
        'WHERE': [],
        'OTHER': []
    }
    
    # Patterns de recherche
    patterns = {
        'SELECT': r'SELECT.*formulaire_bt_id',
        'INSERT': r'INSERT.*formulaire_bt_id',
        'UPDATE': r'UPDATE.*formulaire_bt_id',
        'DELETE': r'DELETE.*formulaire_bt_id',
        'ALTER_TABLE': r'ALTER\s+TABLE.*formulaire_bt_id',
        'CREATE_TABLE': r'CREATE\s+TABLE.*formulaire_bt_id',
        'JOIN': r'JOIN.*formulaire_bt_id',
        'WHERE': r'WHERE.*formulaire_bt_id',
    }
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
                
                # Chercher les occurrences
                for line_num, line in enumerate(lines, 1):
                    if 'formulaire_bt_id' in line:
                        # Catégoriser l'usage
                        categorized = False
                        for category, pattern in patterns.items():
                            if re.search(pattern, line, re.IGNORECASE):
                                usages[category].append({
                                    'file': str(py_file),
                                    'line': line_num,
                                    'content': line.strip()
                                })
                                categorized = True
                                break
                        
                        if not categorized:
                            usages['OTHER'].append({
                                'file': str(py_file),
                                'line': line_num,
                                'content': line.strip()
                            })
                            
        except Exception as e:
            print(f"Erreur lecture {py_file}: {e}")
    
    # Affichage des résultats
    total_usages = sum(len(usage_list) for usage_list in usages.values())
    print(f"TOTAL OCCURRENCES: {total_usages}\n")
    
    for category, usage_list in usages.items():
        if usage_list:
            print(f"=== {category} ({len(usage_list)} occurrences) ===")
            for usage in usage_list:
                print(f"  📁 {usage['file']}:{usage['line']}")
                print(f"     {usage['content']}")
                print()
            print()
    
    return usages

def analyze_table_definitions():
    """Analyse les définitions de tables dans erp_database.py"""
    
    print("=== ANALYSE DÉFINITIONS DE TABLES ===\n")
    
    try:
        with open("erp_database.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Chercher les CREATE TABLE
        create_table_pattern = r'CREATE\s+TABLE[^(]*\([^)]*formulaire_bt_id[^)]*\)'
        matches = re.finditer(create_table_pattern, content, re.IGNORECASE | re.DOTALL)
        
        print("Tables définies avec formulaire_bt_id:")
        for match in matches:
            table_def = match.group(0)
            # Extraire le nom de la table
            table_name_match = re.search(r'CREATE\s+TABLE[^(]*?(\w+)\s*\(', table_def, re.IGNORECASE)
            if table_name_match:
                table_name = table_name_match.group(1)
                print(f"✅ {table_name}")
                
                # Analyser la définition de la colonne
                bt_col_pattern = r'formulaire_bt_id[^,\n]*'
                bt_match = re.search(bt_col_pattern, table_def, re.IGNORECASE)
                if bt_match:
                    print(f"   Définition: {bt_match.group(0).strip()}")
                print()
        
        # Chercher les ALTER TABLE ADD COLUMN
        alter_pattern = r'ALTER\s+TABLE[^"]*formulaire_bt_id[^"]*'
        alter_matches = re.finditer(alter_pattern, content, re.IGNORECASE)
        
        print("Modifications ALTER TABLE pour formulaire_bt_id:")
        for match in alter_matches:
            print(f"  {match.group(0).strip()}")
        print()
        
    except FileNotFoundError:
        print("❌ Fichier erp_database.py non trouvé")
    except Exception as e:
        print(f"❌ Erreur analyse erp_database.py: {e}")

def check_schema_migrations():
    """Vérifie les migrations de schéma"""
    
    print("=== MIGRATIONS DE SCHÉMA ===\n")
    
    try:
        with open("erp_database.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Chercher les migrations v3 et v4 (qui ajoutent formulaire_bt_id)
        migration_pattern = r'if from_version < [34]:.*?formulaire_bt_id.*?except'
        matches = re.finditer(migration_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for i, match in enumerate(matches, 1):
            print(f"Migration #{i}:")
            print(match.group(0)[:300] + "..." if len(match.group(0)) > 300 else match.group(0))
            print()
            
    except Exception as e:
        print(f"❌ Erreur analyse migrations: {e}")

def generate_fix_sql():
    """Génère le SQL de correction"""
    
    print("=== SQL DE CORRECTION RECOMMANDÉ ===\n")
    
    sql_fixes = [
        "-- Vérification de l'existence de la colonne formulaire_bt_id",
        "PRAGMA table_info(time_entries);",
        "PRAGMA table_info(operations);",
        "",
        "-- Si la colonne n'existe pas, l'ajouter:",
        "ALTER TABLE time_entries ADD COLUMN formulaire_bt_id INTEGER;",
        "ALTER TABLE operations ADD COLUMN formulaire_bt_id INTEGER;",
        "",
        "-- Créer les index pour performance:",
        "CREATE INDEX IF NOT EXISTS idx_time_entries_bt ON time_entries(formulaire_bt_id);",
        "CREATE INDEX IF NOT EXISTS idx_operations_bt ON operations(formulaire_bt_id);",
        "",
        "-- Créer les contraintes de clé étrangère (si nécessaire):",
        "-- Note: SQLite ne permet pas d'ajouter des FK après coup facilement",
        "",
        "-- Vérifier les données:",
        "SELECT COUNT(*) FROM time_entries WHERE formulaire_bt_id IS NOT NULL;",
        "SELECT COUNT(*) FROM operations WHERE formulaire_bt_id IS NOT NULL;"
    ]
    
    for line in sql_fixes:
        print(line)
    
    print("\n=== SCRIPT DE VÉRIFICATION ===\n")
    
    verification_sql = [
        "-- Vérifier que les colonnes existent maintenant:",
        "SELECT sql FROM sqlite_master WHERE name IN ('time_entries', 'operations');",
        "",
        "-- Vérifier les index:",
        "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%bt%';",
        "",
        "-- Test de requête avec formulaire_bt_id:",
        "SELECT COUNT(*) FROM time_entries te LEFT JOIN formulaires f ON te.formulaire_bt_id = f.id;"
    ]
    
    for line in verification_sql:
        print(line)

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("DIAGNOSTIC COMPLET - COLONNE formulaire_bt_id")
    print("=" * 50)
    print()
    
    # 1. Analyse des usages dans le code
    usages = find_formulaire_bt_id_usage()
    
    # 2. Analyse des définitions de tables
    analyze_table_definitions()
    
    # 3. Vérification des migrations
    check_schema_migrations()
    
    # 4. Génération du SQL de correction
    generate_fix_sql()
    
    print("\n=== RÉSUMÉ DU DIAGNOSTIC ===")
    print("1. La colonne formulaire_bt_id est utilisée dans plusieurs fichiers")
    print("2. Elle devrait être présente dans les tables 'time_entries' et 'operations'")
    print("3. Le système de migration automatique devrait l'ajouter")
    print("4. Si l'erreur persiste, utiliser le SQL de correction ci-dessus")
    print("\nRecommandation: Exécuter le module erp_database.py pour déclencher les migrations automatiques")