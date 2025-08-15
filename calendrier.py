# calendrier.py - Version 100% Native Streamlit
# ERP Production DG Inc. - Calendrier entièrement basé sur les composants Streamlit
# ✅ AUCUN HTML PERSONNALISÉ - COMPOSANTS STREAMLIT UNIQUEMENT

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import calendar

# NOUVELLE ARCHITECTURE : Import SQLite Database et Gestionnaires
from erp_database import ERPDatabase
from app import GestionnaireProjetSQL  # Import depuis app.py

def load_external_css():
    """Charge le fichier CSS externe pour un design uniforme"""
    try:
        with open('style.css', 'r', encoding='utf-8') as f:
            css_content = f.read()
        st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
        return True
    except FileNotFoundError:
        st.warning("⚠️ Fichier style.css non trouvé. Utilisation du style par défaut.")
        return False
    except Exception as e:
        st.warning(f"⚠️ Erreur chargement CSS: {e}")
        return False

def display_calendar_native_streamlit(year, month, month_events):
    """Calendrier avec le style CSS du programme ERP"""
    
    # Nom du mois en français
    month_names_fr = ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
                     "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    
    # Titre du calendrier avec style CSS du programme
    with st.container():
        st.markdown(f"""
        <div style='text-align: center; padding: 20px; 
                    background: var(--lustrous-primary); 
                    border-radius: var(--border-radius-lg); 
                    margin-bottom: 20px;
                    box-shadow: var(--shadow-primary);'>
            <h2 style='color: white; margin: 0; font-size: 1.8em; font-family: var(--font-family);'>
                📅 {month_names_fr[month]} {year}
            </h2>
        </div>
        """, unsafe_allow_html=True)
    
    # En-têtes des jours de la semaine avec variables CSS
    days_fr = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    header_cols = st.columns(7)
    
    for i, day_name in enumerate(days_fr):
        with header_cols[i]:
            weekend_color = "var(--error-color)" if i >= 5 else "var(--primary-color)"
            st.markdown(f"""
            <div style='text-align: center; font-weight: bold; color: {weekend_color}; 
                        font-size: 1.1em; padding: 10px; font-family: var(--font-family);'>
                {day_name}
            </div>
            """, unsafe_allow_html=True)
    
    # Obtenir le calendrier du mois
    cal = calendar.monthcalendar(year, month)
    today = date.today()
    selected_date = st.session_state.selected_date
    
    # Afficher chaque semaine dans un conteneur stylé
    for week_index, week in enumerate(cal):
        with st.container():
            week_cols = st.columns(7)
            
            for day_index, day in enumerate(week):
                with week_cols[day_index]:
                    if day == 0:
                        # Jour vide avec espacement
                        st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
                    else:
                        current_date = date(year, month, day)
                        
                        # Vérifier les événements pour ce jour
                        day_events = month_events.get(current_date, [])
                        num_events = len(day_events)
                        
                        # Style de conteneur selon le contexte
                        is_today = current_date == today
                        is_selected = current_date == selected_date
                        is_weekend = day_index >= 5
                        has_events = num_events > 0
                        
                        # CSS dynamique avec variables du style.css
                        if is_today:
                            cell_style = """background: var(--lustrous-warning); color: white; font-weight: bold;
                                           box-shadow: var(--shadow-warning);"""
                            day_icon = "🌟"
                        elif is_selected:
                            cell_style = """background: var(--lustrous-success); color: white; font-weight: bold;
                                           box-shadow: var(--shadow-success);"""
                            day_icon = "✅"
                        elif has_events:
                            cell_style = """background: var(--lustrous-blue); color: white;
                                           box-shadow: var(--shadow-blue);"""
                            day_icon = "📅"
                        elif is_weekend:
                            cell_style = """background: var(--background-gray); color: var(--text-color-lighter); 
                                           border: 1px solid var(--border-color);"""
                            day_icon = "🏠"
                        else:
                            cell_style = """background: var(--background-white); color: var(--text-color); 
                                           border: 1px solid var(--border-color-light);
                                           box-shadow: var(--shadow-xs);"""
                            day_icon = ""
                        
                        # Créer la cellule du jour avec style CSS uniforme
                        cell_content = f"""
                        <div style='text-align: center; padding: 8px; 
                                    border-radius: var(--border-radius-md); margin: 2px; 
                                    min-height: 70px; cursor: pointer; 
                                    transition: all var(--animation-speed) ease;
                                    font-family: var(--font-family);
                                    {cell_style}'>
                            <div style='font-size: 1.2em; margin-bottom: 5px;'>{day_icon} {day}</div>
                        """
                        
                        # Ajouter les indicateurs d'événements
                        if num_events > 0:
                            cell_content += f"<div style='font-size: 0.8em; opacity: 0.9;'>• {num_events} événement(s)</div>"
                            
                            # Afficher les types d'événements
                            event_icons = []
                            for event in day_events[:3]:
                                event_type = event.get('type', 'N/A')
                                if event_type == 'Début':
                                    event_icons.append("🚀")
                                elif event_type == 'Fin Prévue':
                                    event_icons.append("🏁")
                                else:
                                    event_icons.append("📋")
                            
                            if event_icons:
                                cell_content += f"<div style='margin-top: 3px;'>{''.join(event_icons[:3])}</div>"
                        
                        cell_content += "</div>"
                        
                        # Afficher la cellule avec bouton cliquable
                        button_type = "primary" if is_today else "secondary" if is_selected else "tertiary"
                        
                        if st.button(
                            f"{day_icon} {day}" + (f" ({num_events})" if num_events > 0 else ""),
                            key=f"day_{year}_{month}_{day}_{week_index}_{day_index}",
                            help=f"📅 {day} {month_names_fr[month]} {year}\n🎯 {num_events} événement(s)",
                            type=button_type,
                            use_container_width=True
                        ):
                            st.session_state.selected_date = current_date
                            st.rerun()
                        
                        # Aperçu compact des événements
                        if num_events > 0:
                            for i, event in enumerate(day_events[:2]):
                                event_type = event.get('type', 'N/A')
                                event_name = event.get('nom_projet', 'Projet')[:15]
                                
                                if event_type == 'Début':
                                    st.caption(f"🚀 {event_name}")
                                elif event_type == 'Fin Prévue':
                                    st.caption(f"🏁 {event_name}")
                                else:
                                    st.caption(f"📋 {event_name}")
                            
                            if num_events > 2:
                                st.caption(f"... et {num_events - 2} autre(s)")

def display_day_details_native_streamlit(selected_date, month_events, gestionnaire=None):
    """Affiche les détails du jour sélectionné avec le style CSS du programme"""
    
    # En-tête du jour sélectionné
    day_name_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    day_name = day_name_fr[selected_date.weekday()]
    month_name = ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
                 "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    
    # Conteneur avec style CSS du programme
    with st.container():
        # En-tête avec style CSS uniforme
        st.markdown(f"""
        <div style='background: var(--lustrous-primary); 
                    padding: 15px; border-radius: var(--border-radius-lg); 
                    margin-bottom: 20px; text-align: center;
                    box-shadow: var(--shadow-primary);'>
            <h3 style='color: white; margin: 0; font-size: 1.4em; font-family: var(--font-family);'>
                📅 {day_name} {selected_date.day} {month_name[selected_date.month]} {selected_date.year}
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Vérifier s'il y a des événements pour cette date
        day_events = month_events.get(selected_date, [])
        
        if not day_events:
            # Design avec style CSS du programme pour journée libre
            st.markdown("""
            <div style='background: var(--lustrous-success); 
                        padding: 20px; border-radius: var(--border-radius-lg); 
                        text-align: center; margin: 10px 0;
                        box-shadow: var(--shadow-success);'>
                <h4 style='color: white; margin: 0; font-family: var(--font-family);'>🌟 Journée Libre</h4>
                <p style='color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-family: var(--font-family);'>
                    Aucun événement planifié pour cette journée
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Suggestions pour journée libre avec style CSS
            with st.expander("💡 Suggestions d'activités", expanded=False):
                suggestions = [
                    "🔧 Maintenance préventive des équipements",
                    "📊 Révision des indicateurs de performance",
                    "👥 Formation du personnel",
                    "📋 Planification des projets futurs",
                    "🔍 Audit qualité des processus",
                    "💼 Prospection commerciale"
                ]
                for suggestion in suggestions:
                    st.write(f"• {suggestion}")
        else:
            # En-tête pour journée avec événements - style CSS uniforme
            st.markdown(f"""
            <div style='background: var(--lustrous-blue); 
                        padding: 15px; border-radius: var(--border-radius-lg); 
                        text-align: center; margin-bottom: 15px;
                        box-shadow: var(--shadow-blue);'>
                <h4 style='color: white; margin: 0; font-family: var(--font-family);'>
                    📋 {len(day_events)} Événement(s) Planifié(s)
                </h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Affichage des événements avec design amélioré
            for i, event in enumerate(day_events):
                event_type = event.get('type', 'N/A')
                event_id = event.get('id', '?')
                event_name = event.get('nom_projet', 'N/A')
                
                # Couleur selon le type d'événement avec variables CSS
                if event_type == 'Début':
                    header_color = "background: var(--lustrous-success);"
                    icon = "🚀"
                elif event_type == 'Fin Prévue':
                    header_color = "background: var(--lustrous-error);"
                    icon = "🏁"
                else:
                    header_color = "background: var(--lustrous-warning);"
                    icon = "📋"
                
                with st.expander(f"{icon} Projet #{event_id} - {event_name}", expanded=i==0):
                    # Conteneur avec design CSS uniforme
                    st.markdown(f"""
                    <div style='{header_color} 
                                padding: 10px; border-radius: var(--border-radius-md); 
                                margin-bottom: 15px; box-shadow: var(--shadow-sm);'>
                        <h5 style='color: white; margin: 0; text-align: center; font-family: var(--font-family);'>
                            {icon} {event_type.upper()}
                        </h5>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Informations principales avec colonnes
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            label="🆔 ID Projet", 
                            value=f"#{event_id}",
                            help="Identifiant unique du projet"
                        )
                    
                    with col2:
                        st.metric(
                            label="🏷️ Type", 
                            value=event_type,
                            help="Type d'événement dans le planning"
                        )
                    
                    with col3:
                        st.metric(
                            label="📝 Projet", 
                            value=event_name[:20] + "..." if len(event_name) > 20 else event_name,
                            help=f"Nom complet: {event_name}"
                        )
                    
                    # Détails additionnels
                    if event.get('tache'):
                        st.markdown("**🎯 Tâche associée:**")
                        st.info(event.get('tache'))
                    
                    # Actions disponibles
                    col_action1, col_action2 = st.columns(2)
                    
                    with col_action1:
                        if st.button(
                            "🔍 Détails Complets", 
                            key=f"details_btn_{event_id}_{i}",
                            type="primary",
                            use_container_width=True,
                            help="Voir toutes les informations du projet"
                        ):
                            # Trouver le projet dans les données SQLite
                            if gestionnaire:
                                projet = next((p for p in gestionnaire.projets if p.get('id') == event_id), None)
                                if projet:
                                    st.session_state.selected_project_id = event_id
                                    st.session_state.selected_project = projet
                                    st.session_state.show_project_details = True
                                    st.rerun()
                                else:
                                    st.error(f"Projet #{event_id} non trouvé dans la base de données")
                    
                    with col_action2:
                        if st.button(
                            "📊 Analyse Projet", 
                            key=f"analyze_btn_{event_id}_{i}",
                            type="secondary",
                            use_container_width=True,
                            help="Analyser les métriques du projet"
                        ):
                            st.info("🚧 Fonctionnalité d'analyse en développement")

def get_events_for_month(year, month, gestionnaire):
    """Récupère tous les événements pour le mois donné - VERSION SQLITE."""
    events = {}
    
    # Déterminer la plage de dates du mois
    _, last_day = calendar.monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)
    
    # Parcourir les projets depuis SQLite
    for projet in gestionnaire.projets:
        proj_id = projet.get('id')
        proj_nom = projet.get('nom_projet', 'N/A')
        
        # Vérifier la date de début
        try:
            date_debut_str = projet.get('date_soumis')
            if date_debut_str:
                date_debut = datetime.strptime(date_debut_str, "%Y-%m-%d").date()
                if start_date <= date_debut <= end_date:
                    if date_debut not in events:
                        events[date_debut] = []
                    events[date_debut].append({
                        'id': proj_id,
                        'nom_projet': proj_nom,
                        'type': 'Début',
                        'tache': projet.get('tache', 'N/A')
                    })
        except (ValueError, TypeError):
            pass
        
        # Vérifier la date de fin
        try:
            date_fin_str = projet.get('date_prevu')
            if date_fin_str:
                date_fin = datetime.strptime(date_fin_str, "%Y-%m-%d").date()
                if start_date <= date_fin <= end_date:
                    if date_fin not in events:
                        events[date_fin] = []
                    events[date_fin].append({
                        'id': proj_id,
                        'nom_projet': proj_nom,
                        'type': 'Fin Prévue',
                        'tache': projet.get('tache', 'N/A')
                    })
        except (ValueError, TypeError):
            pass
    
    return events

def display_navigation_native(current_year, current_month):
    """Navigation avec composants Streamlit natifs et design élégant"""
    month_names_fr = ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
                     "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    
    # Conteneur de navigation avec style
    with st.container():
        st.markdown("""
        <div style='background: linear-gradient(90deg, #f8fafc, #e2e8f0); 
                    padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation principale avec colonnes équilibrées
        col_nav1, col_nav2, col_nav3, col_nav4, col_nav5 = st.columns([1, 1, 2, 1, 1])
        
        with col_nav1:
            if st.button("⏪ Année -1", key="nav_prev_year", use_container_width=True, help="Année précédente"):
                st.session_state.view_year = current_year - 1
                st.rerun()
        
        with col_nav2:
            if st.button("◀️ Mois -1", key="nav_prev", use_container_width=True, help="Mois précédent"):
                if current_month == 1:
                    st.session_state.view_month = 12
                    st.session_state.view_year = current_year - 1
                else:
                    st.session_state.view_month = current_month - 1
                st.rerun()
        
        with col_nav3:
            # Titre central avec gradient
            st.markdown(f"""
            <div style='text-align: center; padding: 10px; 
                        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
                        border-radius: 8px; margin: 0 10px;'>
                <h3 style='color: white; margin: 0; font-size: 1.3em;'>
                    {month_names_fr[current_month]} {current_year}
                </h3>
            </div>
            """, unsafe_allow_html=True)
        
        with col_nav4:
            if st.button("Mois +1 ▶️", key="nav_next", use_container_width=True, help="Mois suivant"):
                if current_month == 12:
                    st.session_state.view_month = 1
                    st.session_state.view_year = current_year + 1
                else:
                    st.session_state.view_month = current_month + 1
                st.rerun()
        
        with col_nav5:
            if st.button("Année +1 ⏩", key="nav_next_year", use_container_width=True, help="Année suivante"):
                st.session_state.view_year = current_year + 1
                st.rerun()
        
        # Ligne de raccourcis
        st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)
        col_shortcut1, col_shortcut2, col_shortcut3 = st.columns([1, 1, 1])
        
        with col_shortcut1:
            if st.button("📅 Aujourd'hui", key="nav_today", type="primary", use_container_width=True, help="Retour à la date actuelle"):
                today = datetime.now().date()
                st.session_state.view_month = today.month
                st.session_state.view_year = today.year
                st.session_state.selected_date = today
                st.rerun()
        
        with col_shortcut2:
            if st.button("🏠 Début d'année", key="nav_year_start", use_container_width=True, help="Aller à janvier"):
                st.session_state.view_month = 1
                st.rerun()
        
        with col_shortcut3:
            if st.button("🎯 Fin d'année", key="nav_year_end", use_container_width=True, help="Aller à décembre"):
                st.session_state.view_month = 12
                st.rerun()

def show_project_details_native():
    """Affichage des détails d'un projet avec composants natifs"""
    projet_id = st.session_state.selected_project_id
    projet = st.session_state.selected_project
    
    with st.container():
        st.markdown("---")
        st.header(f"📁 Détails du Projet #{projet_id}")
        
        # Informations principales
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Nom du Projet", projet.get('nom_projet', 'Sans Nom'))
            st.metric("Client", projet.get('client_nom_cache', 'N/A'))
        
        with col2:
            st.metric("Statut", projet.get('statut', 'N/A'))
            st.metric("Priorité", projet.get('priorite', 'N/A'))
        
        with col3:
            st.metric("Prix Estimé", f"{projet.get('prix_estime', 'N/A')}")
            st.metric("BD-FT Estimé", f"{projet.get('bd_ft_estime', 'N/A')}h")
        
        # Dates
        st.subheader("📅 Planification")
        date_col1, date_col2 = st.columns(2)
        
        with date_col1:
            st.metric("Date de Début", projet.get('date_soumis', 'N/A'))
        
        with date_col2:
            st.metric("Date de Fin Prévue", projet.get('date_prevu', 'N/A'))
        
        # Description
        if projet.get('description'):
            st.subheader("📝 Description")
            st.write(projet.get('description'))
        
        # Bouton fermer
        if st.button("✖️ Fermer les Détails", type="secondary", use_container_width=True):
            st.session_state.show_project_details = False
            st.rerun()

def app():
    """Application calendrier principale - STYLE CSS UNIFORME DU PROGRAMME"""
    
    # Charger le CSS si disponible
    css_loaded = load_external_css()
    
    # En-tête principal avec style CSS du programme
    st.markdown("""
    <div style='background: var(--lustrous-primary); 
                padding: 20px; border-radius: var(--border-radius-xl); 
                margin-bottom: 25px; text-align: center;
                box-shadow: var(--shadow-xl);'>
        <h1 style='color: white; margin: 0; font-size: 2.2em; 
                   text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                   font-family: var(--font-family);'>
            📅 Calendrier ERP Constructo AI
        </h1>
        <p style='color: rgba(255,255,255,0.9); margin: 10px 0 0 0; 
                  font-size: 1.1em; font-family: var(--font-family);'>
            Interface Native avec Style CSS Uniforme - Base SQLite Unifiée
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # INITIALISATION SQLITE
    if 'erp_db' not in st.session_state:
        from database_config import get_database_path
        db_path = get_database_path()
        st.session_state.erp_db = ERPDatabase(db_path)
    
    if 'gestionnaire' not in st.session_state:
        st.session_state.gestionnaire = GestionnaireProjetSQL(st.session_state.erp_db)
    
    gestionnaire = st.session_state.gestionnaire
    
    # Bannière de statut avec variables CSS
    if css_loaded:
        status_style = "background: var(--lustrous-success); box-shadow: var(--shadow-success);"
        status_icon = "✅"
        status_text = "Style CSS externe chargé"
    else:
        status_style = "background: var(--lustrous-warning); box-shadow: var(--shadow-warning);"
        status_icon = "⚠️"
        status_text = "Style CSS par défaut utilisé"
    
    st.markdown(f"""
    <div style='{status_style} 
                padding: 10px; border-radius: var(--border-radius-md); 
                margin-bottom: 20px; text-align: center;'>
        <p style='color: white; margin: 0; font-weight: bold; font-family: var(--font-family);'>
            {status_icon} Calendrier Style CSS Uniforme - {status_text}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialisation des variables de session
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = datetime.now().date()
    if 'view_month' not in st.session_state:
        st.session_state.view_month = datetime.now().month
    if 'view_year' not in st.session_state:
        st.session_state.view_year = datetime.now().year
    if 'show_project_details' not in st.session_state:
        st.session_state.show_project_details = False
    
    # Sidebar avec style CSS uniforme du programme
    with st.sidebar:
        # En-tête sidebar avec style CSS
        st.markdown("""
        <div style='background: var(--lustrous-blue); 
                    padding: 15px; border-radius: var(--border-radius-lg); 
                    margin-bottom: 20px; text-align: center;
                    box-shadow: var(--shadow-blue);'>
            <h3 style='color: white; margin: 0; font-size: 1.3em; font-family: var(--font-family);'>
                📊 Tableau de Bord
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Vue d'ensemble avec expander
        with st.expander("📈 Vue d'Ensemble", expanded=True):
            try:
                total_projects_sql = st.session_state.erp_db.get_table_count('projects')
                total_companies = st.session_state.erp_db.get_table_count('companies')
                
                # Métriques avec colonnes
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📋 Projets", total_projects_sql, help="Total des projets en base")
                with col2:
                    st.metric("🏢 Entreprises", total_companies, help="Clients enregistrés")
                
                # Indicateur de santé avec style CSS
                if total_projects_sql == 0:
                    st.markdown("""
                    <div style='background: var(--lustrous-warning); 
                                padding: 10px; border-radius: var(--border-radius-md); 
                                text-align: center; box-shadow: var(--shadow-warning);'>
                        <p style='color: white; margin: 0; font-weight: bold; font-family: var(--font-family);'>
                            ⚠️ Base Vide
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.caption("💡 Créez des projets pour voir les événements")
                else:
                    st.markdown(f"""
                    <div style='background: var(--lustrous-success); 
                                padding: 10px; border-radius: var(--border-radius-md); 
                                text-align: center; box-shadow: var(--shadow-success);'>
                        <p style='color: white; margin: 0; font-weight: bold; font-family: var(--font-family);'>
                            ✅ {total_projects_sql} Projets Actifs
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Erreur: {e}")
        
        # Date sélectionnée avec style CSS uniforme
        with st.expander("📍 Date Sélectionnée", expanded=True):
            selected_date = st.session_state.selected_date
            day_name_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
            day_name = day_name_fr[selected_date.weekday()]
            
            st.markdown(f"""
            <div style='background: var(--lustrous-success); 
                        padding: 15px; border-radius: var(--border-radius-md); 
                        text-align: center; box-shadow: var(--shadow-success);'>
                <h4 style='color: white; margin: 0; font-family: var(--font-family);'>{day_name}</h4>
                <p style='color: rgba(255,255,255,0.9); margin: 5px 0 0 0; 
                          font-size: 1.1em; font-family: var(--font-family);'>
                    📅 {selected_date.strftime('%d/%m/%Y')}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Navigation rapide avec style CRM
        with st.expander("🚀 Navigation Rapide", expanded=True):
            # Retour ERP avec style
            if st.button("🏠 Retour ERP Principal", use_container_width=True, type="primary"):
                st.switch_page("app.py")
            
            # Raccourcis de dates
            if st.button("📅 Semaine Actuelle", use_container_width=True):
                today = datetime.now().date()
                st.session_state.view_month = today.month
                st.session_state.view_year = today.year
                st.session_state.selected_date = today
                st.rerun()
            
            if st.button("🗓️ Mois Prochain", use_container_width=True):
                current_month = st.session_state.view_month
                current_year = st.session_state.view_year
                if current_month == 12:
                    st.session_state.view_month = 1
                    st.session_state.view_year = current_year + 1
                else:
                    st.session_state.view_month = current_month + 1
                st.rerun()
        
        # Aide et informations avec style
        with st.expander("ℹ️ Aide & Infos", expanded=False):
            st.markdown("""
            **🎯 Navigation:**
            - Cliquez sur un jour pour le sélectionner
            - Utilisez les boutons de navigation
            - Les jours avec événements sont colorés
            
            **📊 Événements:**
            - 🚀 Début de projet
            - 🏁 Fin prévue
            - 📋 Autre événement
            
            **💡 Conseil:**
            Créez des projets dans l'ERP principal pour voir les événements apparaître dans le calendrier.
            """)
            
            st.markdown("""
            <div style='background: var(--background-gray); 
                        padding: 10px; border-radius: var(--border-radius-md); 
                        text-align: center; margin-top: 10px;
                        border: 1px solid var(--border-color);'>
                <p style='margin: 0; font-size: 0.9em; color: var(--text-color-lighter);
                          font-family: var(--font-family);'>
                    🏗️ ERP Constructo AI<br>
                    Version Calendrier Style CSS Uniforme
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    # Variables pour le mois/année actuels
    current_month = st.session_state.view_month
    current_year = st.session_state.view_year
    
    # Navigation
    display_navigation_native(current_year, current_month)
    
    st.markdown("---")
    
    # Récupérer les événements pour le mois
    month_events = get_events_for_month(current_year, current_month, gestionnaire)
    
    # Afficher le nombre total d'événements du mois avec style CSS uniforme
    total_events = sum(len(events) for events in month_events.values())
    
    if total_events > 0:
        st.markdown(f"""
        <div style='background: var(--lustrous-blue); 
                    padding: 15px; border-radius: var(--border-radius-lg); 
                    text-align: center; margin-bottom: 20px;
                    box-shadow: var(--shadow-blue);'>
            <h4 style='color: white; margin: 0; font-family: var(--font-family);'>
                📅 {total_events} Événement(s) ce Mois
            </h4>
            <p style='color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-family: var(--font-family);'>
                Activités planifiées dans votre calendrier
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background: var(--lustrous-warning); 
                    padding: 15px; border-radius: var(--border-radius-lg); 
                    text-align: center; margin-bottom: 20px;
                    box-shadow: var(--shadow-warning);'>
            <h4 style='color: white; margin: 0; font-family: var(--font-family);'>📅 Mois Libre</h4>
            <p style='color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-family: var(--font-family);'>
                Aucun événement planifié ce mois-ci
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Layout principal avec colonnes natives et séparateur élégant
    st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)
    
    col_cal, col_details = st.columns([3, 2], gap="large")
    
    with col_cal:
        # En-tête de section avec style CSS uniforme
        st.markdown("""
        <div style='background: var(--gradient-primary-soft); 
                    padding: 10px; border-radius: var(--border-radius-md); 
                    margin-bottom: 15px; text-align: center;
                    border: 1px solid var(--border-color);'>
            <h4 style='margin: 0; color: var(--text-color); font-family: var(--font-family);'>
                🗓️ Vue Calendrier
            </h4>
        </div>
        """, unsafe_allow_html=True)
        
        display_calendar_native_streamlit(current_year, current_month, month_events)
    
    with col_details:
        # En-tête de section avec style CSS uniforme
        st.markdown("""
        <div style='background: var(--gradient-primary-soft); 
                    padding: 10px; border-radius: var(--border-radius-md); 
                    margin-bottom: 15px; text-align: center;
                    border: 1px solid var(--border-color);'>
            <h4 style='margin: 0; color: var(--text-color); font-family: var(--font-family);'>
                📋 Détails du Jour
            </h4>
        </div>
        """, unsafe_allow_html=True)
        
        display_day_details_native_streamlit(st.session_state.selected_date, month_events, gestionnaire)
    
    # Modal pour les détails du projet (uniquement si activée)
    if st.session_state.get('show_project_details'):
        show_project_details_native()

if __name__ == "__main__":
    app()