# Bot Telegram Transcription Audio vers SRT

Un bot Telegram professionnel qui transcrit les fichiers audio (MP3, WAV, etc.) en fichiers SRT avec détection automatique des pauses, respect du ton et du contexte.

## Fonctionnalités

- 🎁 Support multiple formats audio (MP3, WAV, M4A, OGG, FLAC)
- 🎯 Transcription précise avec Whisper d'OpenAI
- ⏱️ Détection automatique des pauses et silences
- 🎭 Analyse du ton et de l'émotion
- 📝 Génération de fichiers SRT formatés
- 🌍 Support multilingue
- 📊 Statistiques de transcription
- 🔧 Interface utilisateur intuitive

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

1. Créer un bot Telegram avec @BotFather
2. Copier le token dans `config.py`
3. Configurer les clés API nécessaires

## Utilisation

1. Démarrer le bot: `python bot.py`
2. Envoyer un fichier audio au bot
3. Recevoir le fichier SRT généré
