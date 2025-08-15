# -*- coding: utf-8 -*-
"""
Configuration des dossiers pour ERP Production DG Inc. - Version Windows Local
"""

import os
from pathlib import Path

def setup_erp_folders():
    """Configure tous les dossiers necessaires pour l'ERP"""
    
    print("Configuration ERP Production DG Inc. - Version Local Windows")
    print("=" * 60)
    
    # Dossiers requis
    folders_to_create = [
        "attachments",
        "attachments/2025",
        "attachments/2025/01", "attachments/2025/02", "attachments/2025/03",
        "attachments/2025/04", "attachments/2025/05", "attachments/2025/06", 
        "attachments/2025/07", "attachments/2025/08", "attachments/2025/09",
        "attachments/2025/10", "attachments/2025/11", "attachments/2025/12",
        "backup_json",
        "data",
        "data/backups",
        "logs"  # Pour les logs futurs
    ]
    
    print("Creation des dossiers:")
    created_count = 0
    
    for folder in folders_to_create:
        folder_path = Path(folder)
        if not folder_path.exists():
            try:
                folder_path.mkdir(parents=True, exist_ok=True)
                print(f"  [CREE] {folder}")
                created_count += 1
            except Exception as e:
                print(f"  [ERREUR] {folder}: {e}")
        else:
            print(f"  [EXISTE] {folder}")
    
    print()
    print("Test des permissions d'ecriture:")
    
    # Test attachments
    try:
        test_file = Path("attachments/test.txt")
        test_file.write_text("test")
        test_file.unlink()
        print("  [OK] Ecriture dans attachments/")
    except Exception as e:
        print(f"  [ERREUR] attachments/: {e}")
    
    # Test backup_json
    try:
        test_backup = Path("backup_json/test.json")
        test_backup.write_text('{"test": true}')
        test_backup.unlink()
        print("  [OK] Ecriture dans backup_json/")
    except Exception as e:
        print(f"  [ERREUR] backup_json/: {e}")
    
    print()
    print("Informations systeme:")
    print(f"  Repertoire: {os.getcwd()}")
    print(f"  Nombre dossiers crees: {created_count}")
    
    # Creer un fichier .gitignore pour les attachments
    gitignore_content = """# Fichiers uploadés - ne pas versionner
attachments/**/*
!attachments/README.md
!attachments/.gitkeep

# Sauvegardes
backup_json/*.json
data/backups/*.db
logs/*.log

# Base de données locale
*.db
*.sqlite
*.sqlite3

# Cache Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
desktop.ini
"""
    
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        gitignore_path.write_text(gitignore_content, encoding='utf-8')
        print("  [CREE] .gitignore")
    
    # Creer README dans attachments
    readme_content = """# Pieces Jointes ERP

Ce dossier contient les fichiers uploadés dans l'ERP.

Structure:
- YYYY/MM/ = Année/Mois
- Noms de fichiers sécurisés automatiquement
- Types supportés: PDF, DOC, XLS, IMG, DWG, etc.

Taille max: 50 MB par fichier
"""
    
    readme_path = Path("attachments/README.md")
    if not readme_path.exists():
        readme_path.write_text(readme_content, encoding='utf-8')
        print("  [CREE] attachments/README.md")
    
    print()
    print("=" * 60)
    print("CONFIGURATION TERMINEE!")
    print()
    print("Prochaines etapes:")
    print("1. Lancez l'ERP: python -m streamlit run app.py")
    print("2. Ou utilisez: Run.bat")
    print("3. Testez l'upload de fichiers PDF dans un projet")
    print()

if __name__ == "__main__":
    setup_erp_folders()
    input("Appuyez sur Entree pour continuer...")