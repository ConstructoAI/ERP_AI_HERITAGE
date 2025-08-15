"""
Configuration de la base de données pour différents environnements
Gère automatiquement les chemins pour local, Render et Hugging Face
"""

import os
import sys

def detect_environment():
    """
    Détecte l'environnement d'exécution
    """
    if os.environ.get('RENDER'):
        return 'RENDER'
    elif os.environ.get('SPACE_ID') or '/home/user' in os.getcwd() or 'spaces' in os.getcwd().lower():
        return 'HUGGINGFACE'
    else:
        return 'LOCAL'

def get_database_path():
    """
    Retourne le chemin correct de la base de données selon l'environnement
    """
    db_filename = "erp_production_dg.db"
    environment = detect_environment()
    
    print(f"[Database Config] Environnement détecté: {environment}")
    
    if environment == 'RENDER':
        # Sur Render avec persistent disk
        possible_paths = [
            os.path.join("/opt/render/project/data", db_filename),
            os.path.join("../data", db_filename),
            os.path.join(os.path.expanduser("~"), "project", "data", db_filename),
            os.path.join("/opt/render/project/src/data", db_filename),
            os.path.join("data", db_filename),
            db_filename
        ]
        default_dir = "/opt/render/project/data"
        
    elif environment == 'HUGGINGFACE':
        # Sur Hugging Face - utiliser /tmp pour éviter les erreurs de permissions
        # ET vérifier si un volume persistant est disponible
        possible_paths = [
            os.path.join("/data", db_filename),  # Volume persistant HF (si configuré)
            os.path.join("/home/user/app/data", db_filename),  # Répertoire app persistant
            os.path.join(os.getcwd(), "data", db_filename),  # Sous-dossier data
            os.path.join(os.getcwd(), db_filename),  # Répertoire courant
            os.path.join("/tmp", db_filename)  # Fallback temporaire
        ]
        # Priorité au volume persistant si disponible
        if os.path.exists("/data") and os.access("/data", os.W_OK):
            default_dir = "/data"
            print(f"[Database Config] Volume persistant HF détecté: /data")
        elif os.access(os.getcwd(), os.W_OK):
            default_dir = os.path.join(os.getcwd(), "data")
            print(f"[Database Config] Utilisation répertoire app: {default_dir}")
        else:
            default_dir = "/tmp"
            print(f"[Database Config] ⚠️ ATTENTION: Utilisation stockage temporaire /tmp")
            print(f"[Database Config] 🚨 Les données seront perdues au redémarrage!")
        
    else:  # LOCAL
        possible_paths = [
            db_filename,
            os.path.join("data", db_filename)
        ]
        default_dir = "."
    
    # Chercher le fichier existant
    for path in possible_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            print(f"[Database Config] Base de données trouvée: {abs_path}")
            return abs_path
    
    # Si non trouvé, retourner le chemin par défaut
    if not os.path.exists(default_dir):
        try:
            os.makedirs(default_dir, exist_ok=True)
            print(f"[Database Config] Répertoire créé: {default_dir}")
        except Exception as e:
            print(f"[Database Config] Impossible de créer le répertoire: {e}")
    
    default_path = os.path.join(default_dir, db_filename)
    print(f"[Database Config] Base de données non trouvée, chemin par défaut: {default_path}")
    return default_path

def get_attachments_path():
    """
    Retourne le chemin correct pour les pièces jointes
    """
    environment = detect_environment()
    
    if environment == 'RENDER':
        base_dir = "/opt/render/project/data"
    elif environment == 'HUGGINGFACE':
        # Prioriser le volume persistant si disponible
        if os.path.exists("/data") and os.access("/data", os.W_OK):
            base_dir = "/data"
        elif os.access(os.getcwd(), os.W_OK):
            base_dir = os.getcwd()
        else:
            base_dir = "/tmp"
            print("[Attachments] ⚠️ Utilisation stockage temporaire pour pièces jointes")
    else:  # LOCAL
        base_dir = "."
    
    attachments_dir = os.path.join(base_dir, "attachments")
    try:
        os.makedirs(attachments_dir, exist_ok=True)
    except PermissionError:
        print(f"[Attachments] Erreur permission: {attachments_dir}, utilisation /tmp")
        attachments_dir = "/tmp/attachments"
        os.makedirs(attachments_dir, exist_ok=True)
    
    return attachments_dir

def get_backup_path():
    """
    Retourne le chemin correct pour les sauvegardes
    """
    environment = detect_environment()
    
    if environment == 'RENDER':
        base_dir = "/opt/render/project/data"
    elif environment == 'HUGGINGFACE':
        # Prioriser le volume persistant si disponible
        if os.path.exists("/data") and os.access("/data", os.W_OK):
            base_dir = "/data"
        elif os.access(os.getcwd(), os.W_OK):
            base_dir = os.getcwd()
        else:
            base_dir = "/tmp"
            print("[Backups] ⚠️ Utilisation stockage temporaire pour sauvegardes")
    else:  # LOCAL
        base_dir = "."
    
    backup_dir = os.path.join(base_dir, "backups")
    try:
        os.makedirs(backup_dir, exist_ok=True)
    except PermissionError:
        print(f"[Backups] Erreur permission: {backup_dir}, utilisation /tmp")
        backup_dir = "/tmp/backups"
        os.makedirs(backup_dir, exist_ok=True)
    
    return backup_dir

# Variable globale pour le chemin de la base de données
DATABASE_PATH = get_database_path()

# Test au chargement du module
if __name__ == "__main__":
    print("=== Configuration Base de Données ===")
    environment = detect_environment()
    print(f"Environnement: {environment}")
    print(f"Répertoire de travail: {os.getcwd()}")
    print(f"Chemin base de données: {DATABASE_PATH}")
    print(f"Base de données existe: {os.path.exists(DATABASE_PATH)}")
    print(f"Chemin pièces jointes: {get_attachments_path()}")
    print(f"Chemin sauvegardes: {get_backup_path()}")
    
    # Avertissement pour Hugging Face
    if environment == 'HUGGINGFACE':
        if "/tmp" in DATABASE_PATH:
            print("🚨 ATTENTION: Base de données en stockage temporaire!")
            print("💡 Pour la persistance, configurez un volume persistant HF")
        else:
            print("✅ Configuration persistante détectée")
    
    # Test de lecture si le fichier existe
    if os.path.exists(DATABASE_PATH):
        try:
            import sqlite3
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            conn.close()
            print(f"Base de données valide avec {table_count} tables")
        except Exception as e:
            print(f"Erreur lors de la lecture de la DB: {e}")