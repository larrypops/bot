import whisper
import torch
import librosa
import soundfile as sf
from pydub import AudioSegment
from loguru import logger
import os
from typing import Dict, List, Tuple
import numpy as np
from langdetect import detect

class AudioTranscriber:
    """Classe principale pour la transcription audio avec Whisper"""
    
    def __init__(self, model_name: str = "base"):
        """
        Initialise le transcriber avec le modèle Whisper spécifié
        
        Args:
            model_name: Nom du modèle Whisper (tiny, base, small, medium, large)
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Initialisation de Whisper avec le modèle {model_name} sur {self.device}")
        
        try:
            self.model = whisper.load_model(model_name, device=self.device)
            logger.info("Modèle Whisper chargé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle Whisper: {e}")
            raise
    
    def convert_to_wav(self, input_path: str, output_path: str) -> str:
        """
        Convertit n'importe quel format audio en WAV
        
        Args:
            input_path: Chemin du fichier audio d'entrée
            output_path: Chemin du fichier WAV de sortie
            
        Returns:
            Chemin du fichier WAV converti
        """
        try:
            logger.info(f"Conversion de {input_path} vers WAV")
            
            # Conversion avec pydub
            audio = AudioSegment.from_file(input_path)
            
            # Normalisation du volume
            audio = audio.normalize()
            
            # Export en WAV
            audio.export(output_path, format="wav", parameters=["-ar", "16000"])
            
            logger.info(f"Conversion terminée: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la conversion audio: {e}")
            raise
    
    def detect_language(self, audio_path: str) -> str:
        """
        Détecte la langue de l'audio
        
        Args:
            audio_path: Chemin du fichier audio
            
        Returns:
            Code de la langue détectée (ex: 'fr', 'en')
        """
        try:
            # Charge l'audio
            audio = whisper.load_audio(audio_path)
            
            # Détecte la langue avec Whisper
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(self.device)
            
            _, probs = self.model.detect_language(mel)
            detected_lang = max(probs, key=probs.get)
            
            logger.info(f"Langue détectée: {detected_lang} ({probs[detected_lang]:.2f})")
            return detected_lang
            
        except Exception as e:
            logger.warning(f"Erreur lors de la détection de langue: {e}")
            return "fr"  # Langue par défaut
    
    def transcribe_with_timestamps(self, audio_path: str, language: str = None) -> Dict:
        """
        Transcrit l'audio avec les timestamps détaillés
        
        Args:
            audio_path: Chemin du fichier audio
            language: Langue cible (optionnel)
            
        Returns:
            Dictionnaire contenant la transcription et les métadonnées
        """
        try:
            logger.info(f"Début de la transcription de {audio_path}")
            
            # Options de transcription
            options = {
                "task": "transcribe",
                "word_timestamps": True,
                "verbose": False
            }
            
            if language:
                options["language"] = language
            
            # Transcription
            result = self.model.transcribe(audio_path, **options)
            
            # Traitement des segments
            segments = []
            for segment in result["segments"]:
                segment_data = {
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip(),
                    "words": []
                }
                
                # Ajout des mots avec timestamps si disponibles
                if "words" in segment:
                    for word in segment["words"]:
                        segment_data["words"].append({
                            "start": word["start"],
                            "end": word["end"],
                            "word": word["word"].strip(),
                            "confidence": word.get("probability", 0.0)
                        })
                
                segments.append(segment_data)
            
            # Métadonnées
            metadata = {
                "language": result.get("language", "unknown"),
                "duration": result.get("duration", 0),
                "text": result["text"].strip(),
                "segments": segments,
                "word_count": len(result["text"].split()),
                "model_used": self.model_name
            }
            
            logger.info(f"Transcription terminée: {metadata['word_count']} mots, {metadata['duration']:.2f}s")
            return metadata
            
        except Exception as e:
            logger.error(f"Erreur lors de la transcription: {e}")
            raise
    
    def analyze_audio_quality(self, audio_path: str) -> Dict:
        """
        Analyse la qualité de l'audio
        
        Args:
            audio_path: Chemin du fichier audio
            
        Returns:
            Dictionnaire avec les métriques de qualité
        """
        try:
            # Charge l'audio avec librosa
            y, sr = librosa.load(audio_path, sr=None)
            
            # Calcule les métriques
            duration = librosa.get_duration(y=y, sr=sr)
            rms_energy = np.sqrt(np.mean(y**2))
            zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(y)[0])
            
            # Détection de silence
            silence_threshold = 0.01
            silent_frames = np.sum(np.abs(y) < silence_threshold)
            silence_percentage = (silent_frames / len(y)) * 100
            
            quality_metrics = {
                "duration": duration,
                "sample_rate": sr,
                "rms_energy": float(rms_energy),
                "zero_crossing_rate": float(zero_crossing_rate),
                "silence_percentage": float(silence_percentage),
                "quality_score": self._calculate_quality_score(rms_energy, silence_percentage)
            }
            
            logger.info(f"Analyse qualité: score {quality_metrics['quality_score']:.2f}/10")
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de qualité: {e}")
            return {"quality_score": 5.0}
    
    def _calculate_quality_score(self, rms_energy: float, silence_percentage: float) -> float:
        """
        Calcule un score de qualité (0-10)
        
        Args:
            rms_energy: Énergie RMS
            silence_percentage: Pourcentage de silence
            
        Returns:
            Score de qualité
        """
        # Score basé sur l'énergie et le pourcentage de silence
        energy_score = min(rms_energy * 10, 5)  # Max 5 points pour l'énergie
        silence_score = max(5 - (silence_percentage / 20), 0)  # Max 5 points pour peu de silence
        
        return round(energy_score + silence_score, 2)
    
    def process_audio_file(self, file_path: str, language: str = None) -> Dict:
        """
        Traite complètement un fichier audio
        
        Args:
            file_path: Chemin du fichier audio
            language: Langue cible (optionnel)
            
        Returns:
            Dictionnaire complet avec transcription et analyses
        """
        try:
            # Conversion en WAV si nécessaire
            wav_path = file_path
            if not file_path.endswith('.wav'):
                wav_path = file_path.rsplit('.', 1)[0] + '_converted.wav'
                wav_path = self.convert_to_wav(file_path, wav_path)
            
            # Détection de la langue si non spécifiée
            if not language:
                language = self.detect_language(wav_path)
            
            # Analyse de qualité
            quality = self.analyze_audio_quality(wav_path)
            
            # Transcription
            transcription = self.transcribe_with_timestamps(wav_path, language)
            
            # Nettoyage du fichier temporaire
            if wav_path != file_path and os.path.exists(wav_path):
                os.remove(wav_path)
            
            # Assemblage du résultat
            result = {
                **transcription,
                "quality_metrics": quality,
                "processing_info": {
                    "model": self.model_name,
                    "device": self.device,
                    "language_detected": language
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du fichier audio: {e}")
            raise
