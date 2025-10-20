import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from loguru import logger
import re
from typing import Dict, List, Tuple
import numpy as np
from collections import Counter

class ToneAnalyzer:
    """Analyseur de ton et d'émotions pour améliorer la transcription"""
    
    def __init__(self, model_name: str = "cardiffnlp/twitter-roberta-base-emotion"):
        """
        Initialise l'analyseur de ton
        
        Args:
            model_name: Nom du modèle de classification d'émotions
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        try:
            # Initialisation du pipeline de classification d'émotions
            self.emotion_classifier = pipeline(
                "text-classification",
                model=model_name,
                tokenizer=model_name,
                device=0 if self.device == "cuda" else -1
            )
            
            # Mapping des émotions en français
            self.emotion_labels = {
                'joy': 'joie',
                'sadness': 'tristesse',
                'anger': 'colère',
                'fear': 'peur',
                'surprise': 'surprise',
                'disgust': 'dégoût',
                'neutral': 'neutre',
                'love': 'amour',
                'optimism': 'optimisme',
                'pessimism': 'pessimisme'
            }
            
            logger.info(f"Analyseur de ton initialisé avec {model_name}")
            
        except Exception as e:
            logger.warning(f"Impossible de charger le modèle d'émotions: {e}")
            self.emotion_classifier = None
    
    def analyze_text_emotion(self, text: str) -> Dict:
        """
        Analyse l'émotion dominante d'un texte
        
        Args:
            text: Texte à analyser
            
        Returns:
            Dictionnaire avec les émotions détectées
        """
        if not self.emotion_classifier or not text.strip():
            return self._get_default_emotion()
        
        try:
            # Nettoyage du texte
            clean_text = self._clean_text_for_analysis(text)
            
            if len(clean_text.split()) < 2:
                return self._get_default_emotion()
            
            # Classification
            results = self.emotion_classifier(clean_text)
            
            # Traitement des résultats
            emotions = {}
            dominant_emotion = None
            max_score = 0
            
            for result in results:
                emotion = result['label'].lower()
                score = result['score']
                
                # Traduction en français si disponible
                emotion_fr = self.emotion_labels.get(emotion, emotion)
                emotions[emotion_fr] = score
                
                if score > max_score:
                    max_score = score
                    dominant_emotion = emotion_fr
            
            return {
                'dominant_emotion': dominant_emotion,
                'confidence': max_score,
                'all_emotions': emotions,
                'text_length': len(text),
                'word_count': len(text.split())
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse d'émotion: {e}")
            return self._get_default_emotion()
    
    def _clean_text_for_analysis(self, text: str) -> str:
        """
        Nettoie le texte pour l'analyse
        
        Args:
            text: Texte à nettoyer
            
        Returns:
            Texte nettoyé
        """
        # Supprime les caractères spéciaux excessifs
        text = re.sub(r'[^\w\s\.\!\?\,\;\:\-\']', ' ', text)
        
        # Supprime les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Limite la longueur pour éviter les problèmes avec le modèle
        if len(text) > 512:
            text = text[:512] + "..."
        
        return text.strip()
    
    def _get_default_emotion(self) -> Dict:
        """
        Retourne une émotion par défaut
        
        Returns:
            Dictionnaire d'émotion par défaut
        """
        return {
            'dominant_emotion': 'neutre',
            'confidence': 0.5,
            'all_emotions': {'neutre': 0.5},
            'text_length': 0,
            'word_count': 0
        }
    
    def detect_speech_patterns(self, text: str) -> Dict:
        """
        Détecte les patterns de parole
        
        Args:
            text: Texte à analyser
            
        Returns:
            Dictionnaire des patterns détectés
        """
        if not text:
            return {}
        
        patterns = {
            'questions': 0,
            'exclamations': 0,
            'hesitations': 0,
            'formal_level': 0,
            'complexity_score': 0
        }
        
        # Compte les questions
        patterns['questions'] = text.count('?')
        
        # Compte les exclamations
        patterns['exclamations'] = text.count('!')
        
        # Détecte les hésitations
        hesitation_words = ['euh', 'ben', 'donc', 'alors', 'voilà', 'enfin']
        for word in hesitation_words:
            patterns['hesitations'] += text.lower().split().count(word)
        
        # Évalue le niveau de formalité
        formal_indicators = ['vous', 'monsieur', 'madame', 'cher', 'chère']
        informal_indicators = ['tu', 'ton', 'ta', 'tes', 'mec', 'meuf', 'fréro']
        
        formal_count = sum(1 for word in formal_indicators if word in text.lower())
        informal_count = sum(1 for word in informal_indicators if word in text.lower())
        
        total_words = len(text.split())
        if total_words > 0:
            patterns['formal_level'] = (formal_count - informal_count) / total_words
        
        # Évalue la complexité
        avg_word_length = np.mean([len(word) for word in text.split()]) if text.split() else 0
        sentence_count = len(re.split(r'[.!?]+', text))
        avg_sentence_length = total_words / sentence_count if sentence_count > 0 else 0
        
        patterns['complexity_score'] = (avg_word_length + avg_sentence_length / 10) / 2
        
        return patterns
    
    def analyze_pauses_and_rhythm(self, segments: List[Dict]) -> Dict:
        """
        Analyse les pauses et le rythme de parole
        
        Args:
            segments: Segments de transcription avec timestamps
            
        Returns:
            Analyse du rythme et des pauses
        """
        if len(segments) < 2:
            return {}
        
        pause_durations = []
        speech_durations = []
        word_counts = []
        
        for i, segment in enumerate(segments):
            # Durée du segment
            duration = segment.get('end', 0) - segment.get('start', 0)
            speech_durations.append(duration)
            
            # Nombre de mots
            word_count = len(segment.get('text', '').split())
            word_counts.append(word_count)
            
            # Pause avant le segment (sauf le premier)
            if i > 0:
                pause = segment.get('start', 0) - segments[i-1].get('end', 0)
                if pause > 0:
                    pause_durations.append(pause)
        
        # Statistiques
        analysis = {
            'avg_pause_duration': np.mean(pause_durations) if pause_durations else 0,
            'max_pause_duration': np.max(pause_durations) if pause_durations else 0,
            'avg_speech_duration': np.mean(speech_durations) if speech_durations else 0,
            'avg_words_per_segment': np.mean(word_counts) if word_counts else 0,
            'speech_rate_variability': np.std(speech_durations) if len(speech_durations) > 1 else 0,
            'pause_frequency': len(pause_durations) / len(segments) if segments else 0
        }
        
        # Classification du rythme
        if analysis['avg_pause_duration'] > 2.0:
            rhythm_type = 'lent_réfléchi'
        elif analysis['avg_pause_duration'] > 1.0:
            rhythm_type = 'modéré'
        elif analysis['avg_pause_duration'] > 0.5:
            rhythm_type = 'rapide'
        else:
            rhythm_type = 'très_rapide'
        
        analysis['rhythm_type'] = rhythm_type
        
        return analysis
    
    def generate_tone_markers(self, text: str, emotion_data: Dict) -> List[str]:
        """
        Génère des marqueurs de ton pour améliorer la transcription
        
        Args:
            text: Texte original
            emotion_data: Données d'émotion
            
        Returns:
            Liste des marqueurs de ton suggérés
        """
        markers = []
        
        if not emotion_data:
            return markers
        
        dominant_emotion = emotion_data.get('dominant_emotion', 'neutre')
        confidence = emotion_data.get('confidence', 0.5)
        
        # Ajoute des marqueurs basés sur l'émotion dominante
        if confidence > 0.7:
            if dominant_emotion == 'joie':
                markers.append('[ton enjoué]')
            elif dominant_emotion == 'colère':
                markers.append('[ton irrité]')
            elif dominant_emotion == 'tristesse':
                markers.append('[ton mélancolique]')
            elif dominant_emotion == 'surprise':
                markers.append('[ton surpris]')
            elif dominant_emotion == 'peur':
                markers.append('[ton angoissé]')
        
        # Analyse des patterns de parole
        patterns = self.detect_speech_patterns(text)
        
        if patterns.get('questions', 0) > 0:
            markers.append('[interrogatif]')
        
        if patterns.get('exclamations', 0) > 0:
            markers.append('[exclamatif]')
        
        if patterns.get('hesitations', 0) > 2:
            markers.append('[hésitant]')
        
        if patterns.get('formal_level', 0) > 0.1:
            markers.append('[formel]')
        elif patterns.get('formal_level', 0) < -0.1:
            markers.append('[informel]')
        
        return markers
    
    def enhance_transcription_with_tone(self, transcription_data: Dict) -> Dict:
        """
        Enrichit la transcription avec des informations de ton
        
        Args:
            transcription_data: Données de transcription originales
            
        Returns:
            Transcription enrichie avec analyse de ton
        """
        enhanced_data = transcription_data.copy()
        
        # Analyse de l'émotion globale
        full_text = transcription_data.get('text', '')
        global_emotion = self.analyze_text_emotion(full_text)
        
        # Analyse par segment
        segments = transcription_data.get('segments', [])
        enhanced_segments = []
        
        for segment in segments:
            segment_text = segment.get('text', '')
            segment_emotion = self.analyze_text_emotion(segment_text)
            patterns = self.detect_speech_patterns(segment_text)
            markers = self.generate_tone_markers(segment_text, segment_emotion)
            
            enhanced_segment = {
                **segment,
                'emotion': segment_emotion,
                'speech_patterns': patterns,
                'tone_markers': markers
            }
            
            enhanced_segments.append(enhanced_segment)
        
        # Analyse du rythme global
        rhythm_analysis = self.analyze_pauses_and_rhythm(segments)
        
        # Assemblage des données enrichies
        enhanced_data.update({
            'segments': enhanced_segments,
            'global_emotion': global_emotion,
            'rhythm_analysis': rhythm_analysis,
            'tone_analysis_enabled': True
        })
        
        return enhanced_data
    
    def get_tone_summary(self, enhanced_transcription: Dict) -> str:
        """
        Génère un résumé de l'analyse de ton
        
        Args:
            enhanced_transcription: Transcription enrichie
            
        Returns:
            Résumé textuel de l'analyse
        """
        if not enhanced_transcription.get('tone_analysis_enabled'):
            return "Analyse de ton non disponible"
        
        global_emotion = enhanced_transcription.get('global_emotion', {})
        rhythm = enhanced_transcription.get('rhythm_analysis', {})
        
        summary_parts = []
        
        # Émotion dominante
        dominant = global_emotion.get('dominant_emotion', 'neutre')
        confidence = global_emotion.get('confidence', 0)
        
        if confidence > 0.6:
            summary_parts.append(f"Ton général : {dominant}")
        else:
            summary_parts.append("Ton général : neutre/mixte")
        
        # Rythme
        rhythm_type = rhythm.get('rhythm_type', 'modéré')
        rhythm_map = {
            'lent_réfléchi': 'lent et réfléchi',
            'modéré': 'modéré',
            'rapide': 'rapide',
            'très_rapide': 'très rapide'
        }
        summary_parts.append(f"Rythme : {rhythm_map.get(rhythm_type, rhythm_type)}")
        
        # Durée moyenne des pauses
        avg_pause = rhythm.get('avg_pause_duration', 0)
        if avg_pause > 1.5:
            summary_parts.append("Pauses longues (réflexion)")
        elif avg_pause < 0.5:
            summary_parts.append("Pauses courtes (flux rapide)")
        else:
            summary_parts.append("Pauses modérées")
        
        return " | ".join(summary_parts)
