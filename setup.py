#!/usr/bin/env python3
"""
Script d'installation et de configuration du bot Telegram de transcription audio
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Vérifie la version de Python"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 ou supérieur est requis")
        print(f"Version actuelle : {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} détecté")
    return True

def check_ffmpeg():
    """Vérifie si FFmpeg est installé"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg est installé")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ FFmpeg n'est pas installé")
    print("Veuillez installer FFmpeg :")
    print("  Windows : https://ffmpeg.org/download.html#build-windows")
    print("  macOS : brew install ffmpeg")
    print("  Linux : sudo apt install ffmpeg")
    return False

def create_virtual_env():
    """Crée un environnement virtuel"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ L'environnement virtuel existe déjà")
        return True
    
    print("📦 Création de l'environnement virtuel...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], 
                      check=True, capture_output=True)
        print("✅ Environnement virtuel créé")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la création de l'environnement virtuel : {e}")
        return False

def install_dependencies():
    """Installe les dépendances"""
    venv_python = Path("venv/Scripts/python.exe") if sys.platform == "win32" else Path("venv/bin/python")
    
    if not venv_python.exists():
        print("❌ Environnement virtuel non trouvé")
        return False
    
    print("📦 Installation des dépendances...")
    try:
        subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        subprocess.run([str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        
        print("✅ Dépendances installées")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation des dépendances : {e}")
        return False

def setup_environment():
    """Configure l'environnement"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ Fichier .env existe déjà")
        return True
    
    if not env_example.exists():
        print("❌ Fichier .env.example non trouvé")
        return False
    
    print("⚙️ Création du fichier .env...")
    try:
        shutil.copy(env_example, env_file)
        print("✅ Fichier .env créé")
        print("📝 Veuillez éditer le fichier .env et ajouter votre token Telegram")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la création du fichier .env : {e}")
        return False

def create_directories():
    """Crée les répertoires nécessaires"""
    directories = ["temp", "output", "logs"]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            print(f"✅ Répertoire {directory} créé")
        else:
            print(f"✅ Répertoire {directory} existe déjà")

def download_whisper_models():
    """Télécharge les modèles Whisper de base"""
    venv_python = Path("venv/Scripts/python.exe") if sys.platform == "win32" else Path("venv/bin/python")
    
    print("🎵 Téléchargement du modèle Whisper de base...")
    try:
        test_script = f"""
import whisper
import sys

try:
    model = whisper.load_model("base")
    print("✅ Modèle Whisper base téléchargé avec succès")
    sys.exit(0)
except Exception as e:
    print(f"❌ Erreur lors du téléchargement du modèle : {{e}}")
    sys.exit(1)
"""
        
        result = subprocess.run([str(venv_python), "-c", test_script], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout.strip())
            return True
        else:
            print(result.stderr.strip())
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du téléchargement du modèle : {e}")
        return False

def run_tests():
    """Exécute les tests de base"""
    venv_python = Path("venv/Scripts/python.exe") if sys.platform == "win32" else Path("venv/bin/python")
    
    print("🧪 Exécution des tests de base...")
    
    test_script = """
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import Config
    from audio_transcriber import AudioTranscriber
    from srt_generator import SRTGenerator
    
    print("✅ Modules importés avec succès")
    
    # Test de configuration
    Config.validate()
    print("✅ Configuration validée")
    
    print("✅ Tous les tests passés")
    sys.exit(0)
    
except Exception as e:
    print(f"❌ Erreur lors des tests : {e}")
    sys.exit(1)
"""
    
    try:
        result = subprocess.run([str(venv_python), "-c", test_script], 
                              capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print(result.stdout.strip())
            return True
        else:
            print(result.stderr.strip())
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution des tests : {e}")
        return False

def main():
    """Fonction principale d'installation"""
    print("🚀 Installation du Bot Telegram de Transcription Audio")
    print("=" * 60)
    
    steps = [
        ("Vérification de Python", check_python_version),
        ("Vérification de FFmpeg", check_ffmpeg),
        ("Création de l'environnement virtuel", create_virtual_env),
        ("Installation des dépendances", install_dependencies),
        ("Configuration de l'environnement", setup_environment),
        ("Création des répertoires", create_directories),
        ("Téléchargement des modèles", download_whisper_models),
        ("Exécution des tests", run_tests),
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        if not step_func():
            failed_steps.append(step_name)
    
    print("\n" + "=" * 60)
    
    if failed_steps:
        print("❌ Installation terminée avec des erreurs")
        print(f"Étapes échouées : {', '.join(failed_steps)}")
        print("\nVeuillez corriger les erreurs et relancer l'installation")
        return False
    else:
        print("✅ Installation terminée avec succès !")
        print("\n📝 Prochaines étapes :")
        print("1. Éditez le fichier .env et ajoutez votre token Telegram")
        print("2. Créez un bot avec @BotFather sur Telegram")
        print("3. Démarrez le bot avec : python bot.py")
        print("\n🎙️ Votre bot est prêt à transcrire des fichiers audio !")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
