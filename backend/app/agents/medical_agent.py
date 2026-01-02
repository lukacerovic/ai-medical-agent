import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from app.core.llm import MistralLLM
from app.core.memory import memory
from app.core.config import settings
from pathlib import Path

class MedicalAgent:
    """Main AI Agent for medical clinic interactions"""
    
    def __init__(self):
        print("\n" + "="*80)
        print("🏥 MEDICAL AGENT INITIALIZATION")
        print("="*80)
        self.llm = MistralLLM()
        self.services = self._load_services()
        self.availability = self._load_availability()
        self.bookings = self._load_bookings()
        print(f"✅ Services loaded: {len(self.services)}")
        print(f"✅ Availability loaded: {len(self.availability)} dates")
        print(f"✅ Bookings loaded: {len(self.bookings)}")
        print("="*80 + "\n")
    
    def _load_services(self) -> Dict[str, Dict]:
        """Load services from JSON"""
        try:
            with open(settings.data_dir / "services.json") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Warning: Could not load services.json: {e}")
            return {}
    
    def _load_availability(self) -> Dict:
        """Load availability schedule"""
        try:
            with open(settings.data_dir / "availability.json") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Warning: Could not load availability.json: {e}")
            return {}
    
    def _load_bookings(self) -> list:
        """Load existing bookings"""
        try:
            with open(settings.data_dir / "bookings.json") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Warning: Could not load bookings.json: {e}")
            return []
    
    def _save_booking(self, booking: Dict):
        """Save booking to file"""
        self.bookings.append(booking)
        try:
            with open(settings.data_dir / "bookings.json", "w") as f:
                json.dump(self.bookings, f, indent=2)
        except Exception as e:
            print(f"Error saving booking: {e}")
    
    async def process_user_input(self, session_id: str, user_input: str) -> str:
        """Process user input and generate appropriate response"""
        
        print(f"\n" + "#"*80)
        print(f"💬 NEW USER INPUT")
        print(f"#"*80)
        print(f"📱 Session ID: {session_id}")
        print(f"👤 User says: {user_input}")
        print(f"#"*80 + "\n")
        
        # Add user message to memory
        memory.add_message(session_id, "user", user_input)
        session = memory.get_session(session_id)
        
        # Detect intent
        print("🔍 Starting intent detection...")
        intent_data = await self.llm.detect_intent(user_input)
        intent = intent_data.get("intent", "other")
        confidence = intent_data.get("confidence", 0.0)
        
        print(f"\n🎯 INTENT DETECTED: '{intent}' (confidence: {confidence})")
        print(f"   Full intent data: {intent_data}")
        
        memory.set_current_intent(session_id, intent)
        
        # Route to appropriate handler
        print(f"\n🔀 ROUTING TO HANDLER: {intent}")
        
        if intent == "book_appointment":
            print("   → Booking intent handler")
            response = await self._handle_booking_intent(session_id, user_input)
        elif intent == "describe_symptoms":
            print("   → Symptom intent handler")
            response = await self._handle_symptom_intent(session_id, user_input)
        elif intent == "ask_about_service":
            print("   → Service info handler")
            response = await self._handle_service_info_intent(session_id, user_input)
        elif intent == "ask_price_duration":
            print("   → Price intent handler")
            response = await self._handle_price_intent(session_id, user_input)
        elif intent == "ask_preparation":
            print("   → Preparation handler")
            response = await self._handle_preparation_intent(session_id, user_input)
        else:
            print("   → General intent handler")
            response = await self._handle_general_intent(session_id, user_input)
        
        # Check if response is empty
        print(f"\n📤 FINAL RESPONSE CHECK:")
        print(f"   Response length: {len(response)}")
        print(f"   Response empty: {not response or response.strip() == ''}")
        print(f"   Response preview: {response[:100] if response else 'EMPTY'}")
        
        # Add agent response to memory
        memory.add_message(session_id, "assistant", response)
        
        print(f"\n" + "#"*80)
        print(f"✅ RESPONSE COMPLETED")
        print(f"#"*80 + "\n")
        
        return response
    
    async def _handle_booking_intent(self, session_id: str, user_input: str) -> str:
        """Handle appointment booking"""
        print("\n📅 BOOKING INTENT HANDLER")
        session = memory.get_session(session_id)
        history = memory.get_conversation_history(session_id)
        
        print(f"   Conversation history length: {len(history)}")
        print(f"   Extracted info: {session.extracted_info}")
        
        prompt = f"""You are Anna, a warm and professional medical clinic receptionist.
        
Patient conversation history:
{history}

Patient just said: "{user_input}"

Current extracted info: {session.extracted_info}
User profile: {session.user_profile.dict()}

You are helping them book an appointment. Based on the conversation:
1. If they haven't specified a service, ask which service they need
2. If they have a service, ask for preferred date and time
3. If we have date/time, ask for their name and DOB
4. Once we have all info, confirm the booking

Be warm, natural, and conversational. Ask one question at a time.
Respond naturally in 1-2 sentences."""
        
        print(f"   Generating response...")
        response = await self.llm.generate(prompt, max_tokens=150)
        
        # Extract structured info from response
        await self._extract_booking_info(session_id, user_input)
        
        print(f"   ✅ Booking handler complete")
        return response
    
    async def _handle_symptom_intent(self, session_id: str, user_input: str) -> str:
        """Handle symptom description and service recommendation"""
        print("\n🩺 SYMPTOM INTENT HANDLER")
        session = memory.get_session(session_id)
        history = memory.get_conversation_history(session_id)
        
        # Ask clarifying questions
        prompt = f"""You are Anna, a medical clinic AI assistant.

Patient says: "{user_input}"

Ask follow-up questions about:
1. How long they've had this symptom
2. Severity (mild, moderate, severe)
3. Any other associated symptoms

Then recommend the most appropriate medical service.
IMPORTANT: Never diagnose. Always emphasize that a doctor will evaluate them.
Use phrases like 'Based on what you described...' and 'The doctor will evaluate further...'

Respond in 1-2 natural, warm sentences."""
        
        response = await self.llm.generate(prompt, max_tokens=150)
        
        # Extract symptoms and suggest service
        print("   Extracting symptoms...")
        symptoms = await self._extract_symptoms(user_input)
        suggested_service = self._suggest_service(symptoms)
        
        print(f"   Extracted symptoms: {symptoms}")
        print(f"   Suggested service: {suggested_service}")
        
        if suggested_service:
            memory.update_extracted_info(session_id, "symptoms", symptoms)
            memory.update_extracted_info(session_id, "suggested_service", suggested_service)
        
        print(f"   ✅ Symptom handler complete")
        return response
    
    async def _handle_service_info_intent(self, session_id: str, user_input: str) -> str:
        """Handle questions about specific services"""
        print("\nℹ️ SERVICE INFO HANDLER")
        
        prompt = f"""You are Anna helping a patient learn about our services.

Patient asks: "{user_input}"

Available services:
{json.dumps(self.services, indent=2)}

Provide friendly, accurate information about the service they're asking about.
If they ask about a service we don't have, politely let them know.
Keep response to 2-3 sentences."""
        
        response = await self.llm.generate(prompt, max_tokens=150)
        print(f"   ✅ Service info handler complete")
        return response
    
    async def _handle_price_intent(self, session_id: str, user_input: str) -> str:
        """Handle questions about pricing and duration"""
        print("\n💰 PRICE INTENT HANDLER")
        
        prompt = f"""You are Anna explaining service costs and duration.

Patient asks: "{user_input}"

Available services with pricing:
{json.dumps(self.services, indent=2)}

Provide the requested pricing/duration information clearly and warmly.
Keep response to 2-3 sentences."""
        
        response = await self.llm.generate(prompt, max_tokens=150)
        print(f"   ✅ Price handler complete")
        return response
    
    async def _handle_preparation_intent(self, session_id: str, user_input: str) -> str:
        """Handle preparation instructions"""
        print("\n📋 PREPARATION HANDLER")
        
        prompt = f"""You are Anna explaining preparation for appointments.

Patient asks: "{user_input}"

Available services with preparation info:
{json.dumps(self.services, indent=2)}

Provide clear preparation instructions if available.
Keep response to 2-3 sentences."""
        
        response = await self.llm.generate(prompt, max_tokens=150)
        print(f"   ✅ Preparation handler complete")
        return response
    
    async def _handle_general_intent(self, session_id: str, user_input: str) -> str:
        """Handle general conversation"""
        print("\n💬 GENERAL INTENT HANDLER")
        
        prompt = f"""You are Anna, a warm and professional medical clinic receptionist.
Patient says: "{user_input}"

Respond naturally and helpfully. You can help with:
- Booking appointments
- Answering questions about services, pricing, duration, preparation
- Suggesting services based on symptoms (without diagnosing)

Keep response to 2 sentences and be warm and professional."""
        
        response = await self.llm.generate(prompt, max_tokens=150)
        
        # Ensure response is not empty
        if not response or response.strip() == "":
            print("   ⚠️ WARNING: Empty response from LLM, using fallback")
            response = "I'm here to help! Could you please tell me more about what you need?"
        
        print(f"   ✅ General handler complete")
        return response.strip()

    
    async def _extract_booking_info(self, session_id: str, user_input: str):
        """Extract booking-related information"""
        # This would parse for dates, times, names, etc.
        # Simplified version - in production, use structured extraction
        pass
    
    async def _extract_symptoms(self, user_input: str) -> list:
        """Extract symptoms from user input"""
        prompt = f"""Extract medical symptoms from this text: "{user_input}"
        
        Return ONLY a JSON list of symptoms:
        ["symptom1", "symptom2", ...]"""
        
        response = await self.llm.generate(prompt, max_tokens=100)
        try:
            return json.loads(response)
        except:
            print(f"   ⚠️ Could not parse symptoms JSON: {response[:100]}")
            return []
    
    def _suggest_service(self, symptoms: list) -> Optional[str]:
        """Suggest appropriate service based on symptoms"""
        
        # Simple mapping - in production, use more sophisticated logic
        symptom_service_map = {
            "chest": "cardiology_consultation",
            "heart": "cardiology_consultation",
            "stomach": "gastroenterology_consultation",
            "gastro": "gastroenterology_consultation",
            "belly": "gastroenterology_consultation",
            "abdominal": "abdominal_ultrasound",
            "blood": "blood_analysis",
            "skin": "dermatology_checkup",
            "rash": "dermatology_checkup",
        }
        
        for symptom in symptoms:
            for key, service in symptom_service_map.items():
                if key.lower() in symptom.lower():
                    return service
        
        return None
    
    def check_availability(self, date: str, time: str) -> bool:
        """Check if time slot is available"""
        return self.availability.get(date, {}).get(time, True)
    
    def get_available_slots(self, date: str) -> list:
        """Get available time slots for a date"""
        slots = self.availability.get(date, {})
        available = [slot for slot, available in slots.items() if available]
        return sorted(available)
    
    def create_booking(self, session_id: str, service_id: str, date: str, 
                      time: str, name: str, dob: str, phone: Optional[str] = None) -> Dict:
        """Create an appointment booking"""
        
        booking = {
            "id": f"BK-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "session_id": session_id,
            "service_id": service_id,
            "user_name": name,
            "user_dob": dob,
            "user_phone": phone,
            "date": date,
            "time": time,
            "status": "confirmed",
            "created_at": datetime.now().isoformat(),
            "service_name": self.services.get(service_id, {}).get("name", ""),
            "service_duration": self.services.get(service_id, {}).get("duration_minutes", 30),
            "service_price": self.services.get(service_id, {}).get("price_eur", 0),
            "special_preparation": self.services.get(service_id, {}).get("special_preparation")
        }
        
        self._save_booking(booking)
        
        # Mark slot as unavailable
        if date in self.availability and time in self.availability[date]:
            self.availability[date][time] = False
            self._save_availability()
        
        return booking
    
    def _save_availability(self):
        """Save availability to file"""
        try:
            with open(settings.data_dir / "availability.json", "w") as f:
                json.dump(self.availability, f, indent=2)
        except Exception as e:
            print(f"Error saving availability: {e}")