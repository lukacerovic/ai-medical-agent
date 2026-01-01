import requests
import json
from typing import Dict, List, Any
from app.core.config import settings

class MistralLLM:
    """Mistral LLM interface (local or API)"""
    
    def __init__(self):
        self.api_url = settings.mistral_api_url
        self.model = settings.mistral_model
        self.local = settings.mistral_local
    
    async def generate(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate response from Mistral"""
        try:
            if self.local:
                return self._local_generate(prompt, max_tokens)
            else:
                return self._api_generate(prompt, max_tokens)
        except Exception as e:
            print(f"LLM error: {e}")
            return "I apologize, I'm having difficulty processing that. Could you repeat?"
    
    def _local_generate(self, prompt: str, max_tokens: int = 500) -> str:
        """Use local Ollama instance"""
        try:
            response = requests.post(
                f"{self.api_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": max_tokens
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            return ""
        except Exception as e:
            print(f"Local Ollama error: {e}")
            return ""
    
    def _api_generate(self, prompt: str, max_tokens: int = 500) -> str:
        """Use Mistral API"""
        try:
            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.mistral_api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": max_tokens
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            return ""
        except Exception as e:
            print(f"Mistral API error: {e}")
            return ""
    
    async def detect_intent(self, user_input: str) -> Dict[str, Any]:
        """Detect user intent from input"""
        prompt = f"""Analyze this patient message and extract the intent.

Patient message: "{user_input}"

Respond ONLY with a JSON object (no markdown, no explanation):
{{
  "intent": "book_appointment|ask_about_service|describe_symptoms|ask_preparation|ask_price_duration|other",
  "confidence": 0.0-1.0,
  "entities": {{}}
}}"""
        
        response = await self.generate(prompt, max_tokens=200)
        try:
            return json.loads(response)
        except:
            return {"intent": "other", "confidence": 0.5, "entities": {}}
