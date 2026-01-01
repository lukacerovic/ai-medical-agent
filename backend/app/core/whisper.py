import ssl
import urllib.request
import whisper
from app.core.config import settings
import tempfile
import os

# Fix Windows SSL certificate issue
ssl._create_default_https_context = ssl._create_unverified_context


class WhisperTranscriber:
    """Speech-to-text transcription using OpenAI Whisper"""
    
    def __init__(self):
        """Initialize Whisper model"""
        try:
            print("Loading Whisper model...")
            
            # Create models directory if it doesn't exist
            models_dir = settings.data_dir / "models"
            models_dir.mkdir(parents=True, exist_ok=True)
            
            # Load model with local cache
            self.model = whisper.load_model(
                "base",
                download_root=str(models_dir)
            )
            
            print("✓ Whisper model loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading Whisper model: {e}")
            raise
    
    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribe audio bytes to text using Whisper
        
        Args:
            audio_bytes: Audio file content as bytes
            
        Returns:
            Transcribed text string (empty if transcription fails)
        """
        try:
            if not audio_bytes or len(audio_bytes) == 0:
                print("❌ No audio data provided")
                return ""
            
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".wav"
            ) as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name
            
            print(f"Received audio file: {tmp_path} ({len(audio_bytes)} bytes)")
            
            try:
                print("Starting Whisper transcription...")
                
                # Transcribe audio using Whisper
                result = self.model.transcribe(tmp_path)
                text = result.get("text", "").strip()
                
                # Log result
                if text:
                    print(f"✓ Successfully transcribed: '{text}'")
                else:
                    print("⚠ Transcription returned empty text")
                
                return text
                
            finally:
                # Always clean up temporary file
                try:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                        print(f"Cleaned up temp file: {tmp_path}")
                except Exception as cleanup_error:
                    print(f"Warning: Failed to delete temp file: {cleanup_error}")
        
        except Exception as e:
            print(f"❌ Transcription error: {str(e)}")
            import traceback
            traceback.print_exc()
            return ""
