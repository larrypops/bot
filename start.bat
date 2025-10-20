@echo off
echo ========================================
echo   Bot Telegram de Transcription Audio
echo ========================================
echo.

REM Vérifie si l'environnement virtuel existe
if not exist "venv" (
    echo 📦 Creation de l'environnement virtuel...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Erreur lors de la creation de l'environnement virtuel
        pause
        exit /b 1
    )
)

REM Active l'environnement virtuel
echo 🔄 Activation de l'environnement virtuel...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Erreur lors de l'activation de l'environnement virtuel
    pause
    exit /b 1
)

REM Vérifie si les dépendances sont installées
echo 📋 Verification des dependances...
python -c "import telegram" 2>nul
if errorlevel 1 (
    echo 📦 Installation des dependances...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Erreur lors de l'installation des dependances
        pause
        exit /b 1
    )
)

REM Vérifie la configuration
echo ⚙️ Verification de la configuration...
python -c "from config import Config; Config.validate()" 2>nul
if errorlevel 1 (
    echo ❌ Configuration invalide. Veuillez verifier le fichier .env
    echo    1. Creez un bot avec @BotFather sur Telegram
    echo    2. Copiez le token dans le fichier .env
    pause
    exit /b 1
)

echo ✅ Configuration valide
echo.
echo 🚀 Demarrage du bot...
echo.
echo Appuyez sur Ctrl+C pour arreter le bot
echo ========================================
echo.

python bot.py

echo.
echo Bot arrete. Appuyez sur une touche pour quitter...
pause
