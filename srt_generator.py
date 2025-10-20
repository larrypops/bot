import pysrt
import re
from datetime import timedelta
from typing import List, Dict, Tuple
from loguru import logger
import textwrap

class SRTGenerator:
    """Générateur professionnel de fichiers SRT avec détection intelligente des pauses"""
    
    def __init__(self, max_chars_per_line: int = 42, max_lines_per_subtitle: int = 2):
        """
        Initialise le générateur SRT
        
        Args:
            max_chars_per_line: Nombre maximum de caractères par ligne
            max_lines_per_subtitle: Nombre maximum de lignes par sous-titre
        """
        self.max_chars_per_line = max_chars_per_line
        self.max_lines_per_subtitle = max_lines_per_subtitle
        self.min_pause_duration = 0.5  # secondes
        
        # Ponctuation qui indique des pauses naturelles
        self.pause_punctuation = {
            '.': 1.0,    # Pause longue après un point
            '!': 0.8,    # Pause moyenne après exclamation
            '?': 0.8,    # Pause moyenne après question
            ';': 0.6,    # Pause courte après point-virgule
            ':': 0.4,    # Pause très courte après deux-points
            ',': 0.3,    # Pause très courte après virgule
        }
    
    def format_timestamp(self, seconds: float) -> str:
        """
        Convertit les secondes en format timestamp SRT (HH:MM:SS,mmm)
        
        Args:
            seconds: Temps en secondes
            
        Returns:
            Timestamp formaté
        """
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int((seconds - int(seconds)) * 1000)
        
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d},{milliseconds:03d}"
    
    def split_text_intelligently(self, text: str, max_chars: int) -> List[str]:
        """
        Divise le texte intelligemment en respectant les mots et la ponctuation
        
        Args:
            text: Texte à diviser
            max_chars: Nombre maximum de caractères par segment
            
        Returns:
            Liste des segments de texte
        """
        if len(text) <= max_chars:
            return [text]
        
        # Nettoyage du texte
        text = text.strip()
        
        # Essayons de diviser aux points de ponctuation naturels
        split_points = []
        for i, char in enumerate(text):
            if char in '.!?;:,' and i < len(text) - 1:
                # Vérifie si le segment jusqu'à ce point est dans la limite
                segment = text[:i+1].strip()
                if len(segment) <= max_chars * 0.9:  # Laisse une marge
                    split_points.append(i+1)
        
        # Si pas de points de division naturels, divise aux espaces
        if not split_points:
            words = text.split()
            current_line = ""
            lines = []
            
            for word in words:
                if len(current_line + " " + word) <= max_chars:
                    current_line += (" " if current_line else "") + word
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            return lines
        
        # Utilise les points de division naturels
        segments = []
        start = 0
        
        for point in split_points:
            segment = text[start:point].strip()
            if segment:
                segments.append(segment)
            start = point
        
        # Ajoute le reste
        if start < len(text):
            remaining = text[start:].strip()
            if remaining:
                segments.append(remaining)
        
        return segments
    
    def detect_pause_duration(self, text: str) -> float:
        """
        Détecte la durée de pause appropriée basée sur le texte
        
        Args:
            text: Texte du segment
            
        Returns:
            Durée de pause en secondes
        """
        if not text:
            return self.min_pause_duration
        
        # Vérifie la ponctuation finale
        last_char = text[-1] if text[-1] not in ' \n\t' else text[-2] if len(text) > 1 else ''
        
        base_pause = self.pause_punctuation.get(last_char, self.min_pause_duration)
        
        # Ajuste selon la longueur du texte
        if len(text) > 80:
            base_pause += 0.2
        elif len(text) > 120:
            base_pause += 0.4
        
        return max(base_pause, self.min_pause_duration)
    
    def create_subtitle_lines(self, text: str) -> List[str]:
        """
        Crée les lignes de sous-titre formatées
        
        Args:
            text: Texte à formater
            
        Returns:
            Liste des lignes formatées
        """
        # Nettoyage du texte
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Division en segments logiques
        segments = self.split_text_intelligently(text, self.max_chars_per_line)
        
        # Limitation du nombre de lignes
        if len(segments) > self.max_lines_per_subtitle:
            # Divise en plusieurs sous-titres
            lines = []
            current_subtitle = []
            current_length = 0
            
            for segment in segments:
                if len(current_subtitle) < self.max_lines_per_subtitle:
                    current_subtitle.append(segment)
                    current_length += len(segment)
                else:
                    lines.append(current_subtitle)
                    current_subtitle = [segment]
                    current_length = len(segment)
            
            if current_subtitle:
                lines.append(current_subtitle)
            
            # Retourne seulement le premier sous-titre pour cette méthode
            return lines[0] if lines else segments[:self.max_lines_per_subtitle]
        
        return segments
    
    def calculate_optimal_timing(self, segments: List[Dict], total_duration: float) -> List[Dict]:
        """
        Calcule les timings optimaux pour les segments
        
        Args:
            segments: Segments de transcription
            total_duration: Durée totale de l'audio
            
        Returns:
            Segments avec timings ajustés
        """
        if not segments:
            return []
        
        timed_segments = []
        current_time = 0
        
        for i, segment in enumerate(segments):
            text = segment['text']
            
            # Calcule la durée de lecture (basé sur la vitesse de parole moyenne)
            words = len(text.split())
            reading_duration = max(words * 0.4, 2.0)  # 0.4s par mot, minimum 2s
            
            # Ajoute la pause détectée
            pause_duration = self.detect_pause_duration(text)
            
            # Ajuste pour ne pas dépasser la durée totale
            if i < len(segments) - 1:
                segment_duration = reading_duration + pause_duration
            else:
                # Dernier segment : utilise le temps restant
                remaining_time = total_duration - current_time
                segment_duration = max(reading_duration, remaining_time)
            
            # S'assure que le segment ne dépasse pas la durée totale
            if current_time + segment_duration > total_duration:
                segment_duration = total_duration - current_time
            
            timed_segment = {
                **segment,
                'start': current_time,
                'end': current_time + segment_duration,
                'duration': segment_duration
            }
            
            timed_segments.append(timed_segment)
            current_time += segment_duration
            
            # Arrête si on atteint la durée totale
            if current_time >= total_duration:
                break
        
        return timed_segments
    
    def generate_srt(self, transcription_data: Dict) -> str:
        """
        Génère le contenu SRT complet
        
        Args:
            transcription_data: Données de transcription
            
        Returns:
            Contenu SRT formaté
        """
        try:
            segments = transcription_data.get('segments', [])
            duration = transcription_data.get('duration', 0)
            
            if not segments:
                logger.warning("Aucun segment à convertir en SRT")
                return ""
            
            # Calcule les timings optimaux
            timed_segments = self.calculate_optimal_timing(segments, duration)
            
            # Crée les sous-titres
            subs = pysrt.SubRipFile()
            
            for i, segment in enumerate(timed_segments):
                text = segment['text']
                
                # Formate le texte en lignes
                lines = self.create_subtitle_lines(text)
                formatted_text = '\n'.join(lines)
                
                # Crée le sous-titre
                sub = pysrt.SubRipItem(
                    index=i + 1,
                    start=pysrt.SubRipTime.from_ordinal(int(segment['start'] * 1000)),
                    end=pysrt.SubRipTime.from_ordinal(int(segment['end'] * 1000)),
                    text=formatted_text.replace('\n', ' | ')  # SRT format
                )
                
                subs.append(sub)
            
            logger.info(f"Génération SRT terminée: {len(subs)} sous-titres créés")
            return str(subs)
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération SRT: {e}")
            raise
    
    def generate_srt_file(self, transcription_data: Dict, output_path: str) -> str:
        """
        Génère et sauvegarde un fichier SRT
        
        Args:
            transcription_data: Données de transcription
            output_path: Chemin du fichier de sortie
            
        Returns:
            Chemin du fichier créé
        """
        try:
            srt_content = self.generate_srt(transcription_data)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            logger.info(f"Fichier SRT créé: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du fichier SRT: {e}")
            raise
    
    def get_statistics(self, transcription_data: Dict) -> Dict:
        """
        Génère des statistiques sur la transcription
        
        Args:
            transcription_data: Données de transcription
            
        Returns:
            Dictionnaire de statistiques
        """
        segments = transcription_data.get('segments', [])
        text = transcription_data.get('text', '')
        
        if not segments:
            return {}
        
        # Statistiques de base
        word_count = len(text.split())
        char_count = len(text)
        
        # Durée totale
        duration = transcription_data.get('duration', 0)
        
        # Durée moyenne par segment
        avg_segment_duration = sum(s.get('end', 0) - s.get('start', 0) for s in segments) / len(segments) if segments else 0
        
        # Vitesse de parole (mots par minute)
        speech_rate = (word_count / duration * 60) if duration > 0 else 0
        
        # Nombre de sous-titres estimés
        estimated_subtitles = len(self.generate_srt(transcription_data).split('\n\n')) if transcription_data else 0
        
        stats = {
            'duration': duration,
            'word_count': word_count,
            'char_count': char_count,
            'segment_count': len(segments),
            'estimated_subtitle_count': estimated_subtitles,
            'avg_segment_duration': avg_segment_duration,
            'speech_rate_wpm': round(speech_rate, 1),
            'language': transcription_data.get('language', 'unknown')
        }
        
        return stats
