#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT DE MIGRATION - CONSTRUCTO AI INC.
Migration des employés DG Inc. vers Constructo AI Inc.
"""

import sqlite3
import os

def migrate_employees_to_constructo_ai():
    """Migre la base de données vers les employés Constructo AI Inc."""
    
    db_path = "erp_production_dg.db"
    
    if not os.path.exists(db_path):
        print("❌ Base de données non trouvée :", db_path)
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Début de la migration...")
        
        # 1. Supprimer les anciennes données
        print("🗑️ Suppression des anciennes données...")
        cursor.execute("DELETE FROM project_assignments WHERE employee_id IN (SELECT id FROM employees)")
        cursor.execute("DELETE FROM employee_competences WHERE employee_id IN (SELECT id FROM employees)")  
        cursor.execute("DELETE FROM employees")
        
        # 2. Insérer les nouveaux employés Constructo AI Inc.
        print("👥 Insertion des employés Constructo AI Inc...")
        
        employees_data = [
            # Chantier et Gros Œuvre
            (1, 'Alexandre', 'Dubois', 'alexandre.dubois@constructo-ai.ca', '450-555-0101', 'Manoeuvre spécialisé', 'CHANTIER', 'ACTIF', 'CDI', '2020-03-15', 51000, 23, 85, 'Spécialiste manutention et montage - Certification CNESST'),
            (2, 'François', 'Tremblay', 'francois.tremblay@constructo-ai.ca', '450-555-0102', 'Charpentier-menuisier', 'CHARPENTE_BOIS', 'ACTIF', 'CDI', '2018-06-01', 70000, 23, 90, 'Charpentier certifié CCQ - Spécialiste ossature bois'),
            (3, 'André', 'Johnson', 'andre.johnson@constructo-ai.ca', '450-555-0103', 'Maçon', 'STRUCTURE_BÉTON', 'ACTIF', 'CDI', '2019-09-15', 75000, 23, 88, 'Maçon spécialisé brique et pierre - Compagnon CCQ'),
            (4, 'Denis', 'Bergeron', 'denis.bergeron@constructo-ai.ca', '450-555-0104', 'Dessinateur-projeteur', 'INGÉNIERIE', 'ACTIF', 'CDI', '2015-01-20', 83000, 24, 95, 'Technologue architecture - Expert AutoCAD et Revit'),
            (5, 'Luc', 'Côté', 'luc.cote@constructo-ai.ca', '450-555-0105', 'Coffreur', 'STRUCTURE_BÉTON', 'ACTIF', 'CDI', '2017-11-01', 67000, 23, 87, 'Coffreur expérimenté, spécialiste fondations et dalles'),
            (6, 'Daniel', 'Roy', 'daniel.roy@constructo-ai.ca', '450-555-0106', 'Manoeuvre général', 'CHANTIER', 'ACTIF', 'CDI', '2021-04-12', 47000, 23, 82, 'Manoeuvre polyvalent - Spécialiste nettoyage chantier'),
            (7, 'Denis', 'Mercier', 'denis.mercier@constructo-ai.ca', '450-555-0107', 'Coffreur-ferrailleur', 'STRUCTURE_BÉTON', 'ACTIF', 'CDI', '2016-08-15', 69000, 23, 90, 'Expert coffrage complexe et armature béton'),
            (8, 'Maxime', 'Lavoie', 'maxime.lavoie@constructo-ai.ca', '450-555-0108', 'Plombier', 'MÉCANIQUE_BÂTIMENT', 'ACTIF', 'CDI', '2019-02-20', 74000, 24, 89, 'Plombier certifié, spécialiste résidentiel/commercial'),
            (9, 'Nicolas', 'Bouchard', 'nicolas.bouchard@constructo-ai.ca', '450-555-0109', 'Opérateur machinerie lourde', 'CHANTIER', 'ACTIF', 'CDI', '2018-10-05', 72000, 23, 86, 'Opérateur excavatrice et grue mobile certifié'),
            (10, 'Louis', 'Gonzalez', 'louis.gonzalez@constructo-ai.ca', '450-555-0110', 'Manoeuvre général', 'CHARPENTE_BOIS', 'ACTIF', 'CDI', '2020-07-10', 49000, 23, 84, 'Trilingue (français/anglais/espagnol)'),
            
            # Équipe technique et supervision  
            (11, 'Pierre', 'Lafleur', 'pierre.lafleur@constructo-ai.ca', '450-555-0111', 'Contremaître général', 'DIRECTION', 'ACTIF', 'CDI', '2012-05-01', 95000, None, 100, 'Contremaître principal chantier - 12 ans expérience'),
            (12, 'William', 'Cédrick', 'william.cedrick@constructo-ai.ca', '450-555-0112', 'Charpentier général', 'CHARPENTE_BOIS', 'ACTIF', 'CDI', '2021-01-15', 58000, 23, 86, 'Charpentier junior en formation avancée'),
            (13, 'Martin', 'Leblanc', 'martin.leblanc@constructo-ai.ca', '450-555-0113', 'Manoeuvre général', 'CHARPENTE_BOIS', 'ACTIF', 'CDI', '2019-05-20', 52000, 23, 88, 'Manoeuvre expérimenté, polyvalent'),
            (14, 'Roxanne', 'Bertrand', 'roxanne.bertrand@constructo-ai.ca', '450-555-0114', 'Inspecteur qualité construction', 'QUALITÉ_CONFORMITÉ', 'ACTIF', 'CDI', '2017-09-01', 66000, 24, 85, 'Responsable qualité et conformité RBQ'),
            (15, 'Samuel', 'Turcotte', 'samuel.turcotte@constructo-ai.ca', '450-555-0115', 'Manoeuvre général', 'CHARPENTE_BOIS', 'ACTIF', 'CDI', '2022-03-10', 46000, 23, 80, 'Manoeuvre récent, apprentissage rapide'),
            (16, 'Éric', 'Brisebois', 'eric.brisebois@constructo-ai.ca', '450-555-0116', 'Charpentier général', 'CHARPENTE_BOIS', 'ACTIF', 'CDI', '2016-04-15', 72000, 23, 91, 'Charpentier senior, mentor pour juniors'),
            
            # Commercial et Administration
            (17, 'Jovick', 'Desrochers', 'jovick.desrochers@constructo-ai.ca', '450-555-0117', 'Chargé de projet construction', 'COMMERCIAL', 'ACTIF', 'CDI', '2019-03-01', 78000, 24, 95, 'Développement projets résidentiels et commerciaux'),
            (18, 'Sylvain', 'Leduc', 'sylvain.leduc@constructo-ai.ca', '450-555-0118', 'Estimateur construction', 'COMMERCIAL', 'ACTIF', 'CDI', '2017-08-15', 85000, 24, 98, 'Estimateur senior et intégration ERP'),
            (19, 'Myriam', 'Girouard', 'myriam.girouard@constructo-ai.ca', '450-555-0119', 'Adjointe administrative', 'ADMINISTRATION', 'ACTIF', 'CDI', '2018-11-20', 51000, 24, 85, 'Administration générale et coordination'),
            (20, 'Cindy', 'Julien', 'cindy.julien@constructo-ai.ca', '450-555-0120', 'Coordonnateur chantier', 'ADMINISTRATION', 'ACTIF', 'CDI', '2020-02-10', 62000, 24, 80, 'Marketing et coordination projets web'),
            
            # Direction
            (23, 'Jean-Pierre', 'Contremaître', 'jp.contremaitre@constructo-ai.ca', '450-555-0123', 'Surintendant chantier', 'DIRECTION', 'ACTIF', 'CDI', '2010-01-15', 95000, 24, 100, 'Surintendant principal - Responsable chantiers'),
            (24, 'Marie-Claude', 'Directrice', 'mc.directrice@constructo-ai.ca', '450-555-0124', 'Directeur construction', 'DIRECTION', 'ACTIF', 'CDI', '2008-05-01', 110000, None, 100, 'Directrice générale Constructo AI Inc.')
        ]
        
        # Insérer les employés
        cursor.executemany("""
            INSERT INTO employees (
                id, prenom, nom, email, telephone, poste, departement, 
                statut, type_contrat, date_embauche, salaire, manager_id, 
                charge_travail, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, employees_data)
        
        print("✅ 22 employés Constructo AI Inc. insérés")
        
        # 3. Insérer quelques compétences de base
        print("🎯 Ajout des compétences de base...")
        competences_data = [
            # Compétences communes
            (1, 'CNESST', 'AVANCÉ', 1, '2020-03-15'),
            (1, 'Manutention matériaux construction', 'EXPERT', 1, '2020-03-15'),
            (2, 'Charpenterie résidentielle', 'EXPERT', 1, '2018-06-01'),
            (2, 'Certification CCQ Charpentier', 'EXPERT', 1, '2018-06-01'),
            (3, 'Maçonnerie brique', 'EXPERT', 1, '2019-09-15'),
            (3, 'Maçonnerie pierre', 'AVANCÉ', 1, '2019-09-15'),
            (4, 'AutoCAD', 'EXPERT', 1, '2015-01-20'),
            (4, 'Revit', 'AVANCÉ', 1, '2015-01-20'),
            (5, 'Coffrage de fondations', 'EXPERT', 1, '2017-11-01'),
            (8, 'Plomberie résidentielle', 'EXPERT', 1, '2019-02-20'),
            (9, 'Excavatrice', 'EXPERT', 1, '2018-10-05'),
        ]
        
        cursor.executemany("""
            INSERT INTO employee_competences (employee_id, nom_competence, niveau, certifie, date_obtention)
            VALUES (?, ?, ?, ?, ?)
        """, competences_data)
        
        conn.commit()
        conn.close()
        
        print("🎉 Migration terminée avec succès !")
        print("📊 22 employés Constructo AI Inc. avec compétences construction")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration : {e}")
        return False

if __name__ == "__main__":
    print("🏗️ MIGRATION CONSTRUCTO AI INC.")
    print("=" * 50)
    migrate_employees_to_constructo_ai()