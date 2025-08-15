@echo off
echo === ANALYSE DE LA STRUCTURE DE LA BASE DE DONNEES ===
echo.

set DB_PATH=erp_production_dg.db

if not exist "%DB_PATH%" (
    echo Base de donnees non trouvee: %DB_PATH%
    echo Tentative de creation...
    python analyze_db_structure.py
    if not exist "%DB_PATH%" (
        echo Echec de la creation de la base de donnees
        pause
        exit /b 1
    )
)

echo Base de donnees trouvee: %DB_PATH%
echo.

echo === TABLES EXISTANTES ===
sqlite3 "%DB_PATH%" ".tables"
echo.

echo === STRUCTURE TABLE time_entries ===
sqlite3 "%DB_PATH%" ".schema time_entries"
echo.

echo === STRUCTURE TABLE operations ===
sqlite3 "%DB_PATH%" ".schema operations"
echo.

echo === STRUCTURE TABLE formulaires ===
sqlite3 "%DB_PATH%" ".schema formulaires"
echo.

echo === VERIFICATION COLONNE formulaire_bt_id ===
echo Table time_entries:
sqlite3 "%DB_PATH%" "PRAGMA table_info(time_entries);" | findstr formulaire_bt_id
if %ERRORLEVEL% neq 0 echo - Colonne formulaire_bt_id NON TROUVEE

echo Table operations:
sqlite3 "%DB_PATH%" "PRAGMA table_info(operations);" | findstr formulaire_bt_id
if %ERRORLEVEL% neq 0 echo - Colonne formulaire_bt_id NON TROUVEE

echo.
echo === INDEX EXISTANTS ===
sqlite3 "%DB_PATH%" "SELECT name, sql FROM sqlite_master WHERE type='index' AND name LIKE '%bt%';"

echo.
pause