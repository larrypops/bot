import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration du bot Telegram de transcription audio"""
    
    # Token du bot Telegram
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', 'VOTRE_TOKEN_ICI')
    
    # Configuration Whisper
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'base')  # tiny, base, small, medium, large
    WHISPER_LANGUAGE = os.getenv('WHISPER_LANGUAGE', 'fr')  # Langue par défaut
    
    # Configuration audio
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    SUPPORTED_FORMATS = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac']
    
    # Configuration SRT
    MAX_CHARS_PER_LINE = 42
    MAX_LINES_PER_SUBTITLE = 2
    MIN_PAUSE_DURATION = 0.5  # secondes
    
    # Analyse du ton
    ENABLE_TONE_ANALYSIS = os.getenv('ENABLE_TONE_ANALYSIS', 'True').lower() == 'true'
    TONE_MODEL = os.getenv('TONE_MODEL', 'cardiffnlp/twitter-roberta-base-emotion')
    
    # Configuration du serveur
    TEMP_DIR = 'temp'
    OUTPUT_DIR = 'output'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'bot.log'
    
    # Messages
    MESSAGES = {
        'welcome': "🎙️ Bienvenue ! Envoyez-moi un fichier audio et je générerai un fichier SRT professionnel pour vous.\n\nFormats supportés : MP3, WAV, M4A, OGG, FLAC",
        'processing': "⏳ Traitement de votre fichier audio en cours...",
        'error_format': "❌ Format de fichier non supporté. Veuillez envoyer un fichier audio valide.",
        'error_size': "❌ Fichier trop volumineux. Taille maximale : 50MB",
        'error_processing': "❌ Une erreur est survenue lors du traitement. Veuillez réessayer.",
        'success': "✅ Transcription terminée ! Voici votre fichier SRT.",
        'stats': "📊 Statistiques de la transcription :\n"
                "Durée : {duration}\n"
                "Mots : {words}\n"
                "Langue : {language}\n"
                "Ton dominant : {tone}"
    }
    
    @classmethod
    def validate(cls):
        """Valide la configuration"""
        if cls.TELEGRAM_TOKEN == 'VOTRE_TOKEN_ICI':
            raise ValueError("Veuillez configurer votre token Telegram dans le fichier .env")
        
        os.makedirs(cls.TEMP_DIR, exist_ok=True)
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
