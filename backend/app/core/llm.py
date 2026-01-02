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
        print(f"🤖 LLM Initialized:")
        print(f"   Mode: {'LOCAL (Ollama)' if self.local else 'API'}")
        print(f"   Model: {self.model}")
        print(f"   URL: {self.api_url}")
    
    async def generate(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate response from Mistral"""
        print(f"\n{'='*80}")
        print(f"🔄 GENERATE REQUEST")
        print(f"{'='*80}")
        print(f"📝 Prompt (first 200 chars): {prompt[:200]}...")
        print(f"🎯 Max tokens: {max_tokens}")
        
        try:
            if self.local:
                result = self._local_generate(prompt, max_tokens)
            else:
                result = self._api_generate(prompt, max_tokens)
            
            print(f"\n✅ RESPONSE RECEIVED:")
            print(f"   Length: {len(result)} characters")
            print(f"   Empty: {not result or result.strip() == ''}")
            print(f"   Content (first 200 chars): {result[:200] if result else 'EMPTY/NONE'}")
            print(f"{'='*80}\n")
            
            return result
            
        except Exception as e:
            print(f"\n❌ GENERATE ERROR: {e}")
            print(f"   Exception type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            print(f"{'='*80}\n")
            return "I apologize, I'm having difficulty processing that. Could you repeat?"
    
    def _local_generate(self, prompt: str, max_tokens: int = 500) -> str:
        """Use local Ollama instance"""
        print(f"\n🏠 LOCAL OLLAMA REQUEST")
        print(f"   Endpoint: {self.api_url}/api/generate")
        print(f"   Model: {self.model}")
        
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": max_tokens
            }
            
            print(f"   Sending request...")
            response = requests.post(
                f"{self.api_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("response", "").strip()
                print(f"   ✅ Success")
                print(f"   Response keys: {list(result.keys())}")
                print(f"   Generated length: {len(generated_text)}")
                return generated_text
            else:
                print(f"   ❌ Non-200 status code")
                print(f"   Response: {response.text[:500]}")
                return ""
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️ TIMEOUT: Ollama took longer than 30 seconds")
            return ""
        except requests.exceptions.ConnectionError as e:
            print(f"   🔌 CONNECTION ERROR: Cannot reach Ollama")
            print(f"   Is Ollama running? Try: ollama serve")
            print(f"   Error: {e}")
            return ""
        except Exception as e:
            print(f"   ❌ Local Ollama error: {e}")
            print(f"   Exception type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _api_generate(self, prompt: str, max_tokens: int = 500) -> str:
        """Use Mistral API"""
        print(f"\n☁️ MISTRAL API REQUEST")
        print(f"   Model: {self.model}")
        
        try:
            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.mistral_api_key[:10]}..."},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": max_tokens
                },
                timeout=30
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result["choices"][0]["message"]["content"]
                print(f"   ✅ Success")
                print(f"   Generated length: {len(generated_text)}")
                return generated_text
            else:
                print(f"   ❌ Non-200 status code")
                print(f"   Response: {response.text[:500]}")
                return ""
                
        except Exception as e:
            print(f"   ❌ Mistral API error: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    async def detect_intent(self, user_input: str) -> Dict[str, Any]:
        """Detect user intent from input"""
        print(f"\n🎯 INTENT DETECTION")
        print(f"   User input: {user_input}")
        
        prompt = f"""Analyze this patient message and extract the intent.

Patient message: "{user_input}"

Respond ONLY with a JSON object (no markdown, no explanation):
{{
  "intent": "book_appointment|ask_about_service|describe_symptoms|ask_preparation|ask_price_duration|other",
  "confidence": 0.0-1.0,
  "entities": {{}}
}}"""
        
        response = await self.generate(prompt, max_tokens=200)
        
        print(f"\n   Raw intent response: {response[:200]}")
        
        try:
            intent_data = json.loads(response)
            print(f"   ✅ Intent parsed successfully: {intent_data.get('intent')}")
            print(f"   Confidence: {intent_data.get('confidence')}")
            return intent_data
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON PARSE ERROR: {e}")
            print(f"   Defaulting to 'other' intent")
            return {"intent": "other", "confidence": 0.5, "entities": {}}
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return {"intent": "other", "confidence": 0.5, "entities": {}}
