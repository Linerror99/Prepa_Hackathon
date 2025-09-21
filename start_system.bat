@echo off
echo 🚀 DÉMARRAGE SYSTÈME IoT+IA COMPLET
echo ====================================

REM Vérifier que Python est installé
python --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Python n'est pas installé ou pas dans le PATH
    pause
    exit /b 1
)

REM Vérifier que Docker est installé
docker --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Docker n'est pas installé ou pas démarré
    echo Installez Docker Desktop et assurez-vous qu'il est démarré
    pause
    exit /b 1
)

echo ✅ Python et Docker détectés
echo.

REM Changer vers le dossier du projet
cd /d "%~dp0"

REM Lancer le système
echo 🚀 Lancement du système complet...
python start_system.py

echo.
echo 👋 Système arrêté

echo 1️⃣ Démarrage du Backend IA...
cd /d "%PROJECT_DIR%\backend"
start "Backend IA" cmd /k "python main.py"

echo    ⏳ Attente du démarrage du backend (10 secondes)...
timeout /t 10 /nobreak >nul

echo 2️⃣ Démarrage du Simulateur IoT...
cd /d "%PROJECT_DIR%\simulator"
start "Simulateur IoT" cmd /k "python machine_simulator.py --machines 3 --mqtt-broker localhost"

echo    ⏳ Attente du démarrage du simulateur (5 secondes)...
timeout /t 5 /nobreak >nul

echo 3️⃣ Démarrage du Dashboard...
cd /d "%PROJECT_DIR%\dashboard"
start "Dashboard" cmd /k "python run_dashboard.py"

echo.
echo 🎉 SYSTÈME COMPLET DÉMARRÉ !
echo ==========================
echo 🧠 Backend IA:     http://localhost:8000
echo 📊 Dashboard:      http://localhost:8501
echo 🏭 Simulateur:     3 machines actives
echo.
echo 💡 Ouvrez http://localhost:8501 dans votre navigateur
echo.
echo 🛑 Pour arrêter: Fermez les fenêtres de commande ouvertes
echo.

REM Ouvrir automatiquement le dashboard dans le navigateur
echo 🌐 Ouverture du dashboard dans le navigateur...
timeout /t 3 /nobreak >nul
start http://localhost:8501

pause