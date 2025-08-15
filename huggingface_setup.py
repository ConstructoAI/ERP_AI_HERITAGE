#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'initialisation pour Hugging Face Spaces
Copie la base de données depuis GitHub Releases si nécessaire
"""

import os
import sys
import requests
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

def is_huggingface_environment():
    """Détecte si on est sur Hugging Face"""
    return (os.environ.get('SPACE_ID') or 
            '/home/user' in os.getcwd() or 
            'spaces' in os.getcwd().lower())

def get_database_info():
    """Récupère les informations sur la base de données"""
    from database_config import get_database_path, detect_environment
    
    db_path = get_database_path()
    environment = detect_environment()
    
    return {
        'path': db_path,
        'exists': os.path.exists(db_path),
        'environment': environment,
        'is_temp': '/tmp' in db_path
    }

def download_backup_from_github():
    """Télécharge la dernière sauvegarde depuis GitHub Releases"""
    
    # Configuration GitHub (ajustez selon votre repo)
    github_repo = "Estimation79/gestion-projets-dg"  # À ajuster
    github_api_url = "https://api.github.com"
    
    print("🔍 Recherche de la dernière sauvegarde GitHub...")
    
    try:
        # Récupérer la liste des releases
        releases_url = f"{github_api_url}/repos/{github_repo}/releases"
        response = requests.get(releases_url, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Erreur accès GitHub: {response.status_code}")
            return None
        
        releases = response.json()
        
        # Chercher les releases de backup
        backup_releases = [r for r in releases if r['tag_name'].startswith('backup-')]
        
        if not backup_releases:
            print("❌ Aucune sauvegarde trouvée sur GitHub")
            return None
        
        # Prendre la plus récente
        latest_release = backup_releases[0]
        print(f"📦 Dernière sauvegarde trouvée: {latest_release['name']}")
        
        # Chercher le fichier ZIP de backup
        backup_asset = None
        for asset in latest_release.get('assets', []):
            if asset['name'].endswith('.zip') and 'backup' in asset['name']:
                backup_asset = asset
                break
        
        if not backup_asset:
            print("❌ Fichier de sauvegarde non trouvé dans la release")
            return None
        
        download_url = backup_asset['browser_download_url']
        backup_filename = backup_asset['name']
        
        print(f"⬇️ Téléchargement: {backup_filename} ({backup_asset['size']} bytes)")
        
        # Télécharger le fichier
        download_response = requests.get(download_url, timeout=120)
        
        if download_response.status_code != 200:
            print(f"❌ Erreur téléchargement: {download_response.status_code}")
            return None
        
        # Sauvegarder temporairement
        temp_zip_path = f"/tmp/{backup_filename}"
        with open(temp_zip_path, 'wb') as f:
            f.write(download_response.content)
        
        print(f"✅ Sauvegarde téléchargée: {temp_zip_path}")
        return temp_zip_path
        
    except Exception as e:
        print(f"❌ Erreur téléchargement GitHub: {e}")
        return None

def extract_database_from_backup(zip_path, target_db_path):
    """Extrait la base de données du fichier ZIP"""
    
    import zipfile
    
    try:
        print(f"📂 Extraction de la base de données...")
        
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            # Chercher le fichier .db dans le ZIP
            db_files = [f for f in zipf.namelist() if f.endswith('.db')]
            
            if not db_files:
                print("❌ Aucun fichier .db trouvé dans la sauvegarde")
                return False
            
            db_file = db_files[0]  # Prendre le premier fichier .db
            print(f"📄 Fichier trouvé: {db_file}")
            
            # Extraire vers le chemin cible
            target_dir = os.path.dirname(target_db_path)
            os.makedirs(target_dir, exist_ok=True)
            
            # Extraire et renommer
            zipf.extract(db_file, target_dir)
            extracted_path = os.path.join(target_dir, db_file)
            
            if extracted_path != target_db_path:
                shutil.move(extracted_path, target_db_path)
            
            print(f"✅ Base de données restaurée: {target_db_path}")
            
            # Vérifier l'intégrité
            return verify_database_integrity(target_db_path)
            
    except Exception as e:
        print(f"❌ Erreur extraction: {e}")
        return False

def verify_database_integrity(db_path):
    """Vérifie l'intégrité de la base de données"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test d'intégrité SQLite
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()
        
        # Compter les tables
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        
        conn.close()
        
        if integrity_result[0] == 'ok' and table_count > 0:
            print(f"✅ Base intègre: {table_count} tables")
            return True
        else:
            print(f"❌ Problème intégrité: {integrity_result[0]}, {table_count} tables")
            return False
            
    except Exception as e:
        print(f"❌ Erreur vérification: {e}")
        return False

def setup_huggingface_persistence():
    """Configuration principale pour Hugging Face"""
    
    print("🚀 SETUP HUGGING FACE - ERP CONSTRUCTO AI")
    print("=" * 60)
    
    if not is_huggingface_environment():
        print("❌ Ce script est conçu pour Hugging Face Spaces")
        return False
    
    # Informations sur la base de données
    db_info = get_database_info()
    
    print(f"📊 Environnement: {db_info['environment']}")
    print(f"📁 Chemin DB: {db_info['path']}")
    print(f"💾 Existe: {db_info['exists']}")
    print(f"⚠️ Temporaire: {db_info['is_temp']}")
    
    # Si la base existe déjà et n'est pas temporaire, tout va bien
    if db_info['exists'] and not db_info['is_temp']:
        print("✅ Base de données persistante déjà configurée")
        return True
    
    # Si la base n'existe pas ou est temporaire, essayer de restaurer depuis GitHub
    if not db_info['exists'] or db_info['is_temp']:
        print("🔄 Tentative de restauration depuis GitHub...")
        
        backup_zip = download_backup_from_github()
        
        if backup_zip:
            success = extract_database_from_backup(backup_zip, db_info['path'])
            
            # Nettoyage
            try:
                os.remove(backup_zip)
            except:
                pass
            
            if success:
                print("🎉 Restauration réussie depuis GitHub!")
                return True
        
        print("⚠️ Impossible de restaurer depuis GitHub")
        print("💡 L'application va créer une nouvelle base de données")
        
        if db_info['is_temp']:
            print("🚨 ATTENTION: Stockage temporaire - données perdues au redémarrage")
    
    return True

def create_hf_requirements():
    """Crée un fichier requirements.txt optimisé pour HF si nécessaire"""
    
    if os.path.exists("requirements.txt"):
        return  # Le fichier existe déjà
    
    hf_requirements = """
streamlit>=1.28.0
pandas>=1.5.0
plotly>=5.15.0
sqlite3
anthropic>=0.5.0
requests>=2.28.0
Pillow>=9.0.0
PyPDF2>=3.0.0
python-docx>=0.8.11
schedule>=1.2.0
pytz>=2023.3
beautifulsoup4>=4.11.0
""".strip()
    
    with open("requirements.txt", "w") as f:
        f.write(hf_requirements)
    
    print("✅ requirements.txt créé pour Hugging Face")

def main():
    """Fonction principale"""
    try:
        create_hf_requirements()
        return setup_huggingface_persistence()
    except Exception as e:
        print(f"❌ Erreur setup: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)