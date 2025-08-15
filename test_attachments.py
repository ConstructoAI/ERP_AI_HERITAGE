#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour le système de pièces jointes - Version Local Windows
ERP Production DG Inc.
"""

import os
import sys
from pathlib import Path

def test_attachments_structure():
    """Teste la structure des dossiers de pièces jointes"""
    
    print("🧪 Test Structure Pièces Jointes - ERP Local Windows")
    print("=" * 60)
    
    # Dossiers requis
    required_folders = [
        "attachments",
        "attachments/2025",
        "attachments/2025/08",
        "backup_json",
        "data",
        "data/backups"
    ]
    
    print("📁 Vérification des dossiers requis:")
    all_good = True
    
    for folder in required_folders:
        folder_path = Path(folder)
        if folder_path.exists():
            print(f"  ✅ {folder}")
        else:
            print(f"  ❌ {folder} - MANQUANT")
            all_good = False
            # Créer le dossier manquant
            try:
                folder_path.mkdir(parents=True, exist_ok=True)
                print(f"     🔧 Créé automatiquement: {folder}")
                all_good = True
            except Exception as e:
                print(f"     ❌ Impossible de créer: {e}")
    
    print()
    print("🔍 Vérification des permissions:")
    
    # Test d'écriture dans attachments
    test_file = Path("attachments/test_write.txt")
    try:
        test_file.write_text("Test d'écriture")
        print("  ✅ Écriture dans attachments/ - OK")
        test_file.unlink()  # Supprimer le fichier test
    except Exception as e:
        print(f"  ❌ Écriture dans attachments/ - Erreur: {e}")
        all_good = False
    
    # Test d'écriture dans backup_json
    test_backup = Path("backup_json/test_backup.json")
    try:
        test_backup.write_text('{"test": "backup"}')
        print("  ✅ Écriture dans backup_json/ - OK")
        test_backup.unlink()
    except Exception as e:
        print(f"  ❌ Écriture dans backup_json/ - Erreur: {e}")
        all_good = False
    
    print()
    print("📊 Informations système:")
    print(f"  🖥️  Plateforme: {sys.platform}")
    print(f"  📁 Répertoire courant: {os.getcwd()}")
    print(f"  🐍 Python: {sys.version}")
    
    print()
    if all_good:
        print("🎉 SUCCÈS! Structure des pièces jointes prête")
        print("   Vous pouvez maintenant uploader des fichiers PDF")
        print("   dans votre application ERP !")
    else:
        print("⚠️  ATTENTION! Certains problèmes détectés")
        print("   Vérifiez les permissions ou créez manuellement")
        print("   les dossiers manquants")
    
    print("=" * 60)
    return all_good

def create_sample_readme():
    """Crée un README dans le dossier attachments"""
    readme_content = """# Dossier Pièces Jointes - ERP Production DG Inc.

## Structure des Dossiers

```
attachments/
├── 2025/          # Année courante
│   ├── 01/        # Janvier
│   ├── 02/        # Février
│   └── ...
└── [autres années]/

backup_json/       # Sauvegardes JSON
data/
└── backups/       # Sauvegardes base de données
```

## Types de Fichiers Supportés

### Documents 📄
- PDF, DOC, DOCX, XLS, XLSX
- TXT, RTF, ODT, ODS
- CSV, JSON, XML, MD

### Images 📷
- JPG, JPEG, PNG, GIF, BMP
- TIFF, SVG, WEBP

### Techniques 📐
- DWG, DXF, STEP, STP
- IGES, IGS, STL, OBJ

### Archives 📦
- ZIP, RAR, 7Z, TAR

### Média 🎬
- MP4, AVI, MOV, MP3, WAV

## Sécurité

- Taille max: 50 MB par fichier
- Vérification des types de fichiers
- Hachage MD5 pour éviter les doublons
- Stockage sécurisé avec noms uniques

---
Généré automatiquement par test_attachments.py
"""
    
    readme_path = Path("attachments/README.md")
    readme_path.write_text(readme_content, encoding='utf-8')
    print(f"📝 README créé: {readme_path}")

if __name__ == "__main__":
    success = test_attachments_structure()
    
    if success:
        create_sample_readme()
        print()
        print("🚀 PRÊT! Lancez votre application ERP:")
        print("   python -m streamlit run app.py")
        print()
        print("💡 Puis testez l'upload de fichiers PDF dans un projet!")
    
    input("\n📋 Appuyez sur Entrée pour terminer...")