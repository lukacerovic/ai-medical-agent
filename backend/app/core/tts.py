import pyttsx3
from io import BytesIO
import tempfile
import os
from app.core.config import settings

class TextToSpeech:
    """Text-to-Speech engine"""
    
    def __init__(self):
        if settings.tts_engine == "pyttsx3":
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)  # Speed
            self.engine.setProperty('volume', 0.9)  # Volume
        else:
            self.engine = None
    
    def synthesize(self, text: str) -> bytes:
        """Convert text to speech bytes"""
        try:
            if settings.tts_engine == "pyttsx3":
                return self._pyttsx3_synthesize(text)
            else:
                return b""  # Fallback
        except Exception as e:
            print(f"TTS error: {e}")
            return b""
    
    def _pyttsx3_synthesize(self, text: str) -> bytes:
        """Use pyttsx3 for TTS"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            temp_file = f.name
        
        try:
            self.engine.save_to_file(text, temp_file)
            self.engine.runAndWait()
            
            with open(temp_file, "rb") as f:
                audio_bytes = f.read()
            
            return audio_bytes
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)