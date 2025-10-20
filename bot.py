import os
import asyncio
import tempfile
from datetime import datetime
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError

from loguru import logger
import aiofiles

from config import Config, MESSAGES
from audio_transcriber import AudioTranscriber
from srt_generator import SRTGenerator
from tone_analyzer import ToneAnalyzer

class TelegramAudioBot:
    """Bot Telegram pour la transcription audio en SRT"""
    
    def __init__(self):
        """Initialise le bot et tous les composants"""
        
        # Validation de la configuration
        Config.validate()
        
        # Initialisation des composants
        self.audio_transcriber = None
        self.srt_generator = None
        self.tone_analyzer = None
        
        # Statistiques du bot
        self.stats = {
            'total_processed': 0,
            'total_duration': 0,
            'start_time': datetime.now()
        }
        
        logger.info("Bot Telegram de transcription audio initialisé")
    
    async def initialize_components(self):
        """Initialise les composants de traitement de manière asynchrone"""
        try:
            logger.info("Initialisation des composants de traitement...")
            
            # Initialisation dans un thread séparé pour ne pas bloquer
            loop = asyncio.get_event_loop()
            
            # Transcriber audio
            self.audio_transcriber = await loop.run_in_executor(
                None, lambda: AudioTranscriber(Config.WHISPER_MODEL)
            )
            
            # Générateur SRT
            self.srt_generator = SRTGenerator(
                Config.MAX_CHARS_PER_LINE,
                Config.MAX_LINES_PER_SUBTITLE
            )
            
            # Analyseur de ton (si activé)
            if Config.ENABLE_TONE_ANALYSIS:
                self.tone_analyzer = await loop.run_in_executor(
                    None, lambda: ToneAnalyzer(Config.TONE_MODEL)
                )
            
            logger.info("Tous les composants initialisés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation des composants: {e}")
            raise
    
    def format_duration(self, seconds: float) -> str:
        """Formate la durée en format lisible"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m{secs:.0f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h{minutes}m"
    
    def create_stats_message(self, transcription_data: dict) -> str:
        """Crée un message de statistiques formaté"""
        
        # Statistiques de base
        duration = transcription_data.get('duration', 0)
        word_count = transcription_data.get('word_count', 0)
        language = transcription_data.get('language', 'unknown')
        
        # Qualité audio
        quality = transcription_data.get('quality_metrics', {})
        quality_score = quality.get('quality_score', 0)
        
        # Ton et rythme
        tone_summary = ""
        if self.tone_analyzer and transcription_data.get('tone_analysis_enabled'):
            tone_summary = self.tone_analyzer.get_tone_summary(transcription_data)
        
        stats_text = MESSAGES['stats'].format(
            duration=self.format_duration(duration),
            words=word_count,
            language=language.upper(),
            tone=tone_summary if tone_summary else "Non analysé"
        )
        
        # Ajoute la qualité audio
        stats_text += f"\n🎵 Qualité audio : {quality_score:.1f}/10"
        
        return stats_text
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la commande /start"""
        await update.message.reply_text(
            MESSAGES['welcome'],
            parse_mode='HTML'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère la commande /help"""
        help_text = """
🎙️ <b>Bot de Transcription Audio vers SRT</b>

<b>Comment utiliser :</b>
1. Envoyez-moi un fichier audio (MP3, WAV, M4A, OGG, FLAC)
2. Je le transcris et génère un fichier SRT professionnel
3. Recevez le fichier SRT avec les statistiques

<b>Formats supportés :</b>
• MP3, WAV, M4A, OGG, FLAC, AAC
• Taille maximale : 50MB

<b>Fonctionnalités :</b>
• Transcription précise avec Whisper
• Détection automatique des pauses
• Analyse du ton et des émotions
• Formatage SRT professionnel
• Support multilingue

<b>Commandes :</b>
/start - Message de bienvenue
/help - Cette aide
/stats - Statistiques du bot

<b>Conseils :</b>
• Audio clair = meilleure transcription
• Parlez distinctement
• Évitez les bruits de fond
        """
        
        await update.message.reply_text(help_text, parse_mode='HTML')
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Affiche les statistiques du bot"""
        uptime = datetime.now() - self.stats['start_time']
        uptime_str = self.format_duration(uptime.total_seconds())
        
        stats_text = f"""
📊 <b>Statistiques du Bot</b>

🎯 Fichiers traités : {self.stats['total_processed']}
⏱️ Durée totale traitée : {self.format_duration(self.stats['total_duration'])}
⏳ Temps de fonctionnement : {uptime_str}
🤖 Modèle utilisé : {Config.WHISPER_MODEL}
🎵 Analyse de ton : {'Activée' if Config.ENABLE_TONE_ANALYSIS else 'Désactivée'}
        """
        
        await update.message.reply_text(stats_text, parse_mode='HTML')
    
    async def handle_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère les fichiers audio reçus"""
        
        # Vérifie si les composants sont initialisés
        if not self.audio_transcriber:
            await update.message.reply_text(
                "🔄 Le bot est en cours d'initialisation. Veuillez réessayer dans quelques instants..."
            )
            return
        
        try:
            # Message de traitement
            processing_msg = await update.message.reply_text(
                MESSAGES['processing'],
                parse_mode='HTML'
            )
            
            # Télécharge le fichier
            audio_file = await update.message.audio.get_file()
            file_name = audio_file.file_path.split('/')[-1] if audio_file.file_path else f"audio_{datetime.now().timestamp()}"
            
            # Vérifie le format
            file_ext = Path(file_name).suffix.lower()
            if file_ext not in Config.SUPPORTED_FORMATS:
                await processing_msg.edit_text(MESSAGES['error_format'])
                return
            
            # Vérifie la taille
            if update.message.audio.file_size > Config.MAX_FILE_SIZE:
                await processing_msg.edit_text(MESSAGES['error_size'])
                return
            
            # Téléchargement du fichier
            temp_dir = Config.TEMP_DIR
            os.makedirs(temp_dir, exist_ok=True)
            
            local_path = os.path.join(temp_dir, f"{datetime.now().timestamp()}_{file_name}")
            await audio_file.download_to_drive(local_path)
            
            logger.info(f"Fichier téléchargé: {local_path}")
            
            # Met à jour le message de traitement
            await processing_msg.edit_text("🎵 Analyse audio en cours...")
            
            # Transcription
            transcription_data = await asyncio.get_event_loop().run_in_executor(
                None, self.audio_transcriber.process_audio_file, local_path, Config.WHISPER_LANGUAGE
            )
            
            # Analyse du ton si activée
            if self.tone_analyzer:
                await processing_msg.edit_text("🎭 Analyse du ton et des émotions...")
                transcription_data = await asyncio.get_event_loop().run_in_executor(
                    None, self.tone_analyzer.enhance_transcription_with_tone, transcription_data
                )
            
            # Génération SRT
            await processing_msg.edit_text("📝 Génération du fichier SRT...")
            
            output_dir = Config.OUTPUT_DIR
            os.makedirs(output_dir, exist_ok=True)
            
            srt_filename = f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.srt"
            srt_path = os.path.join(output_dir, srt_filename)
            
            await asyncio.get_event_loop().run_in_executor(
                None, self.srt_generator.generate_srt_file, transcription_data, srt_path
            )
            
            # Met à jour les statistiques
            self.stats['total_processed'] += 1
            self.stats['total_duration'] += transcription_data.get('duration', 0)
            
            # Envoie le fichier SRT
            await processing_msg.edit_text("✅ Transcription terminée ! Envoi du fichier...")
            
            with open(srt_path, 'rb') as srt_file:
                await update.message.reply_document(
                    document=srt_file,
                    filename=srt_filename,
                    caption=MESSAGES['success'] + "\n\n" + self.create_stats_message(transcription_data),
                    parse_mode='HTML'
                )
            
            # Nettoyage
            try:
                os.remove(local_path)
                os.remove(srt_path)
            except:
                pass
            
            # Supprime le message de traitement
            await processing_msg.delete()
            
            logger.info(f"Transcription réussie pour {file_name}")
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'audio: {e}")
            
            try:
                await processing_msg.edit_text(MESSAGES['error_processing'])
            except:
                await update.message.reply_text(MESSAGES['error_processing'])
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère les messages vocaux"""
        await update.message.reply_text(
            "🎤 Les messages vocaux sont supportés ! Je les traite comme des fichiers audio."
        )
        
        # Convertit le message vocal en fichier audio
        voice_file = await update.message.voice.get_file()
        
        # Crée un objet audio-like pour le traitement
        class VoiceAudio:
            def __init__(self, voice_file, file_size):
                self.file_path = voice_file.file_path
                self.file_size = file_size
                self.get_file = lambda: voice_file
        
        # Simule un message audio
        update.message.audio = VoiceAudio(voice_file, update.message.voice.file_size)
        await self.handle_audio(update, context)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gère les erreurs du bot"""
        logger.error(f"Erreur {context.error} dans la mise à jour {update}")
        
        if update and update.message:
            await update.message.reply_text(
                "❌ Une erreur inattendue est survenue. L'équipe technique a été notifiée."
            )
    
    async def run(self):
        """Démarre le bot"""
        try:
            # Initialisation des composants
            await self.initialize_components()
            
            # Création de l'application
            application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
            
            # Handlers
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CommandHandler("help", self.help_command))
            application.add_handler(CommandHandler("stats", self.stats_command))
            
            # Messages audio
            application.add_handler(MessageHandler(filters.AUDIO, self.handle_audio))
            application.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
            
            # Gestionnaire d'erreurs
            application.add_error_handler(self.error_handler)
            
            logger.info("Bot démarré avec succès")
            
            # Démarrage du bot
            await application.run_polling(drop_pending_updates=True)
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du bot: {e}")
            raise

async def main():
    """Fonction principale"""
    try:
        # Configuration du logging
        logger.add(
            Config.LOG_FILE,
            rotation="10 MB",
            level=Config.LOG_LEVEL,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )
        
        logger.info("Démarrage du bot Telegram de transcription audio")
        
        # Création et démarrage du bot
        bot = TelegramAudioBot()
        await bot.run()
        
    except KeyboardInterrupt:
        logger.info("Arrêt du bot demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
