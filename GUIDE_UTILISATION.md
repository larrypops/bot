# Guide d'utilisation du Bot Telegram de Transcription Audio

## Table des matières

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Utilisation](#utilisation)
4. [Fonctionnalités avancées](#fonctionnalités-avancées)
5. [Dépannage](#dépannage)
6. [FAQ](#faq)

## Installation

### Prérequis

- Python 3.8 ou supérieur
- FFmpeg (obligatoire pour le traitement audio)
- Un token de bot Telegram

### Installation automatique (recommandée)

```bash
# Clonez ou téléchargez le projet
cd telegram_audio_transcriber

# Exécutez le script d'installation
python setup.py
```

Le script d'installation va :
- ✅ Vérifier Python et FFmpeg
- ✅ Créer un environnement virtuel
- ✅ Installer toutes les dépendances
- ✅ Télécharger les modèles Whisper
- ✅ Configurer les répertoires
- ✅ Exécuter les tests de validation

### Installation manuelle

1. **Créez un environnement virtuel**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

2. **Installez les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configurez FFmpeg**
- **Windows** : Téléchargez depuis [ffmpeg.org](https://ffmpeg.org/download.html#build-windows) et ajoutez au PATH
- **macOS** : `brew install ffmpeg`
- **Linux** : `sudo apt install ffmpeg`

4. **Créez le fichier de configuration**
```bash
cp .env.example .env
```

## Configuration

### 1. Créer un bot Telegram

1. Cherchez **@BotFather** sur Telegram
2. Envoyez `/newbot`
3. Suivez les instructions :
   - Nom du bot : `Transcription Audio Bot`
   - Username : `mon_transcripteur_bot` (doit finir par `_bot`)
4. Copiez le token reçu

### 2. Configurer le fichier .env

Éditez le fichier `.env` avec vos informations :

```env
# Token du bot (obligatoire)
TELEGRAM_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789

# Modèle Whisper (tiny, base, small, medium, large)
WHISPER_MODEL=base

# Langue par défaut (fr, en, es, de, etc.)
WHISPER_LANGUAGE=fr

# Analyse du ton (True/False)
ENABLE_TONE_ANALYSIS=True

# Niveau de logs (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

### 3. Tester l'installation

```bash
python test_bot.py
```

## Utilisation

### Démarrer le bot

```bash
# Avec l'environnement virtuel activé
python bot.py
```

Le bot démarrera et affichera :
```
✅ Bot démarré avec succès
🎙️ Bot Telegram de transcription audio initialisé
```

### Commandes disponibles

- `/start` - Message de bienvenue et instructions
- `/help` - Aide détaillée
- `/stats` - Statistiques d'utilisation du bot

### Envoyer un fichier audio

1. **Ouvrez une conversation** avec votre bot
2. **Envoyez un fichier audio** (clic sur l'icône 📎)
3. **Attendez le traitement** (progression affichée)
4. **Recevez le fichier SRT** avec statistiques

### Formats supportés

- **Audio** : MP3, WAV, M4A, OGG, FLAC, AAC
- **Voix** : Messages vocaux Telegram
- **Taille maximale** : 50MB
- **Durée recommandée** : Moins de 30 minutes

### Exemple de conversation

```
Vous: 📎 [audio_file.mp3]

Bot: ⏳ Traitement de votre fichier audio en cours...

Bot: 🎵 Analyse audio en cours...

Bot: 🎭 Analyse du ton et des émotions...

Bot: 📝 Génération du fichier SRT...

Bot: ✅ Transcription terminée ! Voici votre fichier SRT.

[📄 transcription_20241020_143022.srt]

📊 Statistiques de la transcription :
Durée : 2m30s
Mots : 185
Langue : FR
Ton général : neutre | Rythme : modéré | Pauses modérées
🎵 Qualité audio : 7.2/10
```

## Fonctionnalités avancées

### Analyse du ton et des émotions

Le bot peut analyser le ton et les émotions dans l'audio :

- **Émotions détectées** : joie, tristesse, colère, peur, surprise, etc.
- **Rythme de parole** : lent, modéré, rapide, très rapide
- **Patterns linguistiques** : questions, exclamations, hésitations
- **Niveau de formalité** : formel vs informel

### Qualité audio

Le bot évalue la qualité de l'audio :

- **Score de qualité** : 0-10
- **Énergie RMS** : puissance du signal
- **Pourcentage de silence** : détecte les silences
- **Taux de croisement zéro** : analyse du signal

### Formatage SRT professionnel

- **Pause intelligente** : détecte les pauses naturelles
- **Lignes limitées** : 42 caractères max par ligne
- **Maximum 2 lignes** par sous-titre
- **Timestamps précis** : au millième de seconde
- **Respect de la ponctuation** : ajuste les durées selon . ! ? ; :

## Dépannage

### Problèmes courants

#### "Token invalide"
```
❌ Veuillez configurer votre token Telegram dans le fichier .env
```

**Solution** : Vérifiez votre token dans `.env` et assurez-vous qu'il n'y a pas d'espaces.

#### "FFmpeg non trouvé"
```
❌ FFmpeg n'est pas installé
```

**Solution** : Installez FFmpeg et assurez-vous qu'il est dans le PATH de votre système.

#### "Modèle non trouvé"
```
❌ Erreur lors du chargement du modèle Whisper
```

**Solution** : Vérifiez votre connexion internet et réessayez. Le modèle sera téléchargé automatiquement.

#### "Fichier trop volumineux"
```
❌ Fichier trop volumineux. Taille maximale : 50MB
```

**Solution** : Compressez votre fichier audio ou divisez-le en plusieurs parties.

#### "Format non supporté"
```
❌ Format de fichier non supporté
```

**Solution** : Convertissez votre fichier en MP3, WAV, M4A, OGG ou FLAC.

### Logs et débogage

Les logs sont sauvegardés dans `bot.log` :

```bash
# Voir les logs en temps réel
tail -f bot.log

# Voir les erreurs
grep ERROR bot.log
```

### Performance

**Optimisations recommandées** :

- **Modèle Whisper** : Utilisez `base` pour un bon équilibre vitesse/précision
- **GPU** : Si vous avez une GPU NVIDIA, le bot l'utilisera automatiquement
- **Mémoire** : Minimum 4GB RAM recommandé
- **Espace disque** : 2GB pour les modèles

## FAQ

### Q : Le bot fonctionne-t-il hors ligne ?
R : Non, le bot nécessite une connexion internet pour télécharger les modèles et fonctionner.

### Q : Puis-je utiliser le bot pour des fichiers très longs ?
R : Oui, mais les fichiers de plus de 30 minutes peuvent prendre beaucoup de temps à traiter.

### Q : Le bot supporte-t-il d'autres langues que le français ?
R : Oui, le bot supporte 99 langues. Changez `WHISPER_LANGUAGE` dans `.env`.

### Q : Puis-je améliorer la précision de la transcription ?
R : Oui, utilisez un modèle plus grand (`medium` ou `large`) dans la configuration.

### Q : Le bot stocke-t-il mes fichiers ?
R : Non, les fichiers sont temporairement traités puis supprimés automatiquement.

### Q : Comment puis-je contribuer au projet ?
R : Vous pouvez reporter des bugs, suggérer des améliorations ou soumettre du code.

### Q : Le bot est-il gratuit ?
R : Oui, le bot est open source et gratuit. Seuls les coûts d'hébergement s'appliquent.

## Support technique

Pour toute question ou problème :

1. **Consultez les logs** : `bot.log`
2. **Exécutez les tests** : `python test_bot.py`
3. **Vérifiez la configuration** : `.env`
4. **Consultez la FAQ** ci-dessus

---

🎙️ **Bot Telegram de Transcription Audio** - Transcrivez vos fichiers audio en SRT professionnellement !
