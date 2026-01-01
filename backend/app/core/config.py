from typing import Optional
from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str
    whisper_model: str = "base"
    
    # Mistral
    mistral_local: bool = True
    mistral_api_url: str = "http://localhost:11434"
    mistral_model: str = "mistral:instruct"
    mistral_api_key: Optional[str] = None
    
    # FastAPI
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:3000"
    
    # TTS
    tts_engine: str = "pyttsx3"  # pyttsx3 or gtts
    
    # Paths
    data_dir: Path = Path(__file__).parent.parent / "data"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()