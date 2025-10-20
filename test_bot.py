#!/usr/bin/env python3
"""
Script de test pour le bot Telegram de transcription audio
"""

import os
import sys
import asyncio
import tempfile
from pathlib import Path

# Ajoute le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from audio_transcriber import AudioTranscriber
from srt_generator import SRTGenerator
from tone_analyzer import ToneAnalyzer

class BotTester:
    """Classe de test pour le bot"""
    
    def __init__(self):
        self.transcriber = None
        self.srt_generator = None
        self.tone_analyzer = None
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Enregistre le résultat d'un test"""
        status = "✅" if success else "❌"
        self.test_results.append({
            'name': test_name,
            'success': success,
            'message': message
        })
        print(f"{status} {test_name}")
        if message:
            print(f"   {message}")
    
    async def test_configuration(self):
        """Test la configuration"""
        try:
            Config.validate()
            self.log_test("Configuration", True, f"Token configuré: {Config.TELEGRAM_TOKEN[:10]}...")
        except Exception as e:
            self.log_test("Configuration", False, str(e))
    
    async def test_audio_transcriber(self):
        """Test le transcriber audio"""
        try:
            self.transcriber = AudioTranscriber("tiny")  # Utilise le modèle tiny pour les tests
            self.log_test("Transcriber Audio", True, f"Modèle {self.transcriber.model_name} chargé")
        except Exception as e:
            self.log_test("Transcriber Audio", False, str(e))
    
    async def test_srt_generator(self):
        """Test le générateur SRT"""
        try:
            self.srt_generator = SRTGenerator()
            
            # Test avec des données factices
            test_data = {
                'segments': [
                    {'text': 'Bonjour, comment allez-vous ?', 'start': 0.0, 'end': 2.5},
                    {'text': 'Je vais bien, merci !', 'start': 3.0, 'end': 5.0}
                ],
                'duration': 5.0
            }
            
            srt_content = self.srt_generator.generate_srt(test_data)
            
            if srt_content and "Bonjour" in srt_content:
                self.log_test("Générateur SRT", True, "SRT généré avec succès")
            else:
                self.log_test("Générateur SRT", False, "Contenu SRT invalide")
                
        except Exception as e:
            self.log_test("Générateur SRT", False, str(e))
    
    async def test_tone_analyzer(self):
        """Test l'analyseur de ton"""
        try:
            self.tone_analyzer = ToneAnalyzer()
            
            # Test avec un texte simple
            test_text = "Je suis très heureux aujourd'hui !"
            emotion = self.tone_analyzer.analyze_text_emotion(test_text)
            
            if emotion and 'dominant_emotion' in emotion:
                self.log_test("Analyseur de Ton", True, f"Émotion détectée: {emotion['dominant_emotion']}")
            else:
                self.log_test("Analyseur de Ton", False, "Pas d'émotion détectée")
                
        except Exception as e:
            self.log_test("Analyseur de Ton", False, str(e))
    
    async def test_full_workflow(self):
        """Test le workflow complet avec un fichier audio de test"""
        try:
            if not self.transcriber or not self.srt_generator:
                self.log_test("Workflow Complet", False, "Composants non initialisés")
                return
            
            # Crée un fichier audio de test (silence de 1 seconde)
            import wave
            import numpy as np
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
                
                # Crée un fichier WAV silencieux de 1 seconde
                sample_rate = 16000
                duration = 1.0
                samples = int(sample_rate * duration)
                
                with wave.open(temp_path, 'w') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(sample_rate)
                    
                    # Écrit des échantillons silencieux
                    silence = np.zeros(samples, dtype=np.int16)
                    wav_file.writeframes(silence.tobytes())
            
            # Test de transcription
            try:
                transcription = self.transcriber.process_audio_file(temp_path)
                
                if transcription and 'segments' in transcription:
                    self.log_test("Workflow - Transcription", True, f"Durée: {transcription.get('duration', 0):.2f}s")
                    
                    # Test de génération SRT
                    if self.tone_analyzer:
                        transcription = self.tone_analyzer.enhance_transcription_with_tone(transcription)
                    
                    srt_path = temp_path.replace('.wav', '.srt')
                    self.srt_generator.generate_srt_file(transcription, srt_path)
                    
                    if os.path.exists(srt_path):
                        self.log_test("Workflow - Génération SRT", True, "Fichier SRT créé")
                        
                        # Nettoyage
                        os.unlink(srt_path)
                    else:
                        self.log_test("Workflow - Génération SRT", False, "Fichier SRT non créé")
                else:
                    self.log_test("Workflow - Transcription", False, "Pas de transcription générée")
                    
            except Exception as e:
                self.log_test("Workflow Complet", False, f"Erreur workflow: {str(e)}")
            finally:
                # Nettoyage
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            self.log_test("Workflow Complet", False, str(e))
    
    async def test_file_formats(self):
        """Test la compatibilité des formats de fichiers"""
        try:
            supported_formats = Config.SUPPORTED_FORMATS
            
            if supported_formats:
                self.log_test("Formats Supportés", True, f"{len(supported_formats)} formats: {', '.join(supported_formats)}")
            else:
                self.log_test("Formats Supportés", False, "Aucun format configuré")
                
        except Exception as e:
            self.log_test("Formats Supportés", False, str(e))
    
    async def run_all_tests(self):
        """Exécute tous les tests"""
        print("🧪 Démarrage des tests du Bot Telegram de Transcription Audio")
        print("=" * 60)
        
        tests = [
            ("Configuration", self.test_configuration),
            ("Transcriber Audio", self.test_audio_transcriber),
            ("Générateur SRT", self.test_srt_generator),
            ("Analyseur de Ton", self.test_tone_analyzer),
            ("Formats de Fichiers", self.test_file_formats),
            ("Workflow Complet", self.test_full_workflow),
        ]
        
        for test_name, test_func in tests:
            print(f"\n📋 Test: {test_name}")
            try:
                await test_func()
            except Exception as e:
                self.log_test(test_name, False, f"Erreur inattendue: {str(e)}")
        
        # Résultats finaux
        print("\n" + "=" * 60)
        print("📊 Résultats des tests")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['name']}")
            if result['message'] and not result['success']:
                print(f"   Erreur: {result['message']}")
        
        print(f"\n🎯 Résultat: {passed}/{total} tests réussis")
        
        if passed == total:
            print("🎉 Tous les tests sont réussis ! Le bot est prêt à être utilisé.")
        else:
            print("⚠️ Certains tests ont échoué. Veuillez vérifier la configuration.")
        
        return passed == total

async def main():
    """Fonction principale"""
    try:
        tester = BotTester()
        success = await tester.run_all_tests()
        return success
        
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrompus par l'utilisateur")
        return False
    except Exception as e:
        print(f"\n❌ Erreur fatale lors des tests: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
