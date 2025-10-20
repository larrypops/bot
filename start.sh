#!/bin/bash

echo "========================================"
echo "  Bot Telegram de Transcription Audio"
echo "========================================"
echo

# Vérifie si l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Erreur lors de la création de l'environnement virtuel"
        exit 1
    fi
fi

# Active l'environnement virtuel
echo "🔄 Activation de l'environnement virtuel..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de l'activation de l'environnement virtuel"
    exit 1
fi

# Vérifie si les dépendances sont installées
echo "📋 Vérification des dépendances..."
python -c "import telegram" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installation des dépendances..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Erreur lors de l'installation des dépendances"
        exit 1
    fi
fi

# Vérifie la configuration
echo "⚙️ Vérification de la configuration..."
python -c "from config import Config; Config.validate()" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Configuration invalide. Veuillez vérifier le fichier .env"
    echo "   1. Créez un bot avec @BotFather sur Telegram"
    echo "   2. Copiez le token dans le fichier .env"
    exit 1
fi

echo "✅ Configuration valide"
echo
echo "🚀 Démarrage du bot..."
echo
echo "Appuyez sur Ctrl+C pour arrêter le bot"
echo "========================================"
echo

python bot.py

echo
echo "Bot arrêté."
