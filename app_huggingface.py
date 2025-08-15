#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Point d'entrée principal pour Hugging Face Spaces
Initialise la persistance et lance l'application ERP
"""

import streamlit as st
import sys
import os

# Configuration Streamlit pour HF
st.set_page_config(
    page_title="🏭 ERP Constructo AI - Hugging Face",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_huggingface_environment():
    """Initialise l'environnement Hugging Face"""
    
    # Ajouter le répertoire actuel au path Python
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Vérifier et initialiser la persistence
    try:
        from huggingface_setup import setup_huggingface_persistence
        
        with st.spinner("🔧 Initialisation Hugging Face..."):
            setup_success = setup_huggingface_persistence()
        
        if setup_success:
            st.success("✅ Environnement Hugging Face initialisé")
        else:
            st.warning("⚠️ Initialisation partielle - certaines données peuvent être temporaires")
            
        return setup_success
        
    except ImportError as e:
        st.error(f"❌ Erreur d'importation: {e}")
        st.info("L'application va démarrer avec la configuration par défaut")
        return False
    except Exception as e:
        st.error(f"❌ Erreur d'initialisation: {e}")
        st.info("L'application va démarrer avec la configuration par défaut")
        return False

def show_huggingface_info():
    """Affiche les informations spécifiques à Hugging Face"""
    
    try:
        from database_config import get_database_path, detect_environment
        
        environment = detect_environment()
        db_path = get_database_path()
        
        with st.expander("ℹ️ Informations Hugging Face", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Environnement:**", environment)
                st.write("**Base de données:**", db_path)
                st.write("**Stockage persistant:**", "✅ OUI" if "/data" in db_path else "❌ TEMPORAIRE")
            
            with col2:
                if "/tmp" in db_path or "EPHEMERAL" in environment:
                    st.error("🚨 **ATTENTION**: Stockage temporaire détecté")
                    st.warning("Les données seront perdues au redémarrage de l'espace")
                    st.info("💡 Pour la persistance, configurez un volume persistant dans les paramètres HF")
                else:
                    st.success("✅ Configuration persistante active")
                
                st.info("📧 Support: [GitHub Issues](https://github.com/Estimation79/gestion-projets-dg/issues)")
    
    except Exception as e:
        st.error(f"Erreur affichage info HF: {e}")

def main():
    """Fonction principale pour Hugging Face"""
    
    # Titre principal
    st.title("🏭 ERP Production - Constructo AI Inc.")
    st.markdown("---")
    
    # Initialisation Hugging Face
    if 'hf_initialized' not in st.session_state:
        st.session_state.hf_initialized = initialize_huggingface_environment()
    
    # Informations HF
    show_huggingface_info()
    
    # Choix de l'application
    st.markdown("## 🚀 Applications disponibles")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🏗️ ERP Principal", use_container_width=True, type="primary"):
            st.session_state.selected_app = "erp_main"
    
    with col2:
        if st.button("🤖 Assistant IA", use_container_width=True):
            st.session_state.selected_app = "ai_assistant"
    
    with col3:
        if st.button("🔐 ERP avec Auth", use_container_width=True):
            st.session_state.selected_app = "erp_auth"
    
    # Lancer l'application sélectionnée
    if hasattr(st.session_state, 'selected_app'):
        st.markdown("---")
        
        try:
            if st.session_state.selected_app == "erp_main":
                st.info("🔄 Chargement ERP Principal...")
                # Importer et exécuter app.py
                import importlib.util
                spec = importlib.util.spec_from_file_location("app_main", "app.py")
                if spec and spec.loader:
                    app_main = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(app_main)
                else:
                    st.error("❌ Impossible de charger app.py")
            
            elif st.session_state.selected_app == "ai_assistant":
                st.info("🔄 Chargement Assistant IA...")
                # Importer et exécuter ai_expert_app.py
                import importlib.util
                spec = importlib.util.spec_from_file_location("ai_expert", "ai_expert_app.py")
                if spec and spec.loader:
                    ai_expert = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(ai_expert)
                else:
                    st.error("❌ Impossible de charger ai_expert_app.py")
            
            elif st.session_state.selected_app == "erp_auth":
                st.info("🔄 Chargement ERP avec Authentification...")
                # Importer et exécuter app_with_auth.py
                import importlib.util
                spec = importlib.util.spec_from_file_location("app_auth", "app_with_auth.py")
                if spec and spec.loader:
                    app_auth = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(app_auth)
                else:
                    st.error("❌ Impossible de charger app_with_auth.py")
        
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement: {e}")
            st.code(str(e))
            
            # Bouton pour retour
            if st.button("🏠 Retour au menu principal"):
                if 'selected_app' in st.session_state:
                    del st.session_state.selected_app
                st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        🏗️ ERP Constructo AI Inc. | Hébergé sur Hugging Face Spaces<br>
        © 2025 Desmarais & Gagné - Développé par Sylvain Leduc
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()