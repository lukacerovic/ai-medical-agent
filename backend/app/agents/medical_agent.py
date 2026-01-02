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
        print("🏭 MEDICAL AGENT INITIALIZATION")
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
        
        # 📌 EXTRACT CONTEXT FROM CONVERSATION
        print(f"\n📊 ANALYZING CONVERSATION CONTEXT...")
        context = await self._analyze_context(session_id, user_input)
        print(f"✅ Context extracted: {json.dumps(context, indent=2)}")
        
        # Route to appropriate handler
        print(f"\n🔀 ROUTING TO HANDLER: {intent}")
        
        if intent == "book_appointment":
            print("   → Booking intent handler")
            response = await self._handle_booking_intent(session_id, user_input, context)
        elif intent == "describe_symptoms":
            print("   → Symptom intent handler")
            response = await self._handle_symptom_intent(session_id, user_input, context)
        elif intent == "ask_about_service":
            print("   → Service info handler")
            response = await self._handle_service_info_intent(session_id, user_input, context)
        elif intent == "ask_price_duration":
            print("   → Price intent handler")
            response = await self._handle_price_intent(session_id, user_input, context)
        elif intent == "ask_preparation":
            print("   → Preparation handler")
            response = await self._handle_preparation_intent(session_id, user_input, context)
        else:
            print("   → General intent handler")
            response = await self._handle_general_intent(session_id, user_input, context)
        
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
    
    async def _analyze_context(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Analyze conversation context and extract structured information"""
        session = memory.get_session(session_id)
        history = memory.get_conversation_history(session_id)
        
        # Extract keywords
        keywords = ["heart", "cardio", "chest", "cardiac", "stomach", "gastro", 
                    "blood", "test", "ultrasound", "consultation", "appointment", 
                    "book", "available", "slot", "time", "date"]
        
        mentioned_keywords = [kw for kw in keywords if kw.lower() in user_input.lower() or kw.lower() in history.lower()]
        
        # Identify mentioned service category
        service_category = None
        if any(kw in mentioned_keywords for kw in ["heart", "cardio", "chest", "cardiac"]):
            service_category = "cardiology"
        elif any(kw in mentioned_keywords for kw in ["stomach", "gastro"]):
            service_category = "gastroenterology"
        elif "blood" in mentioned_keywords:
            service_category = "blood_test"
        
        # Check booking stage
        booking_stage = "initial"
        if session.extracted_info.get("service_id"):
            booking_stage = "service_selected"
        if session.extracted_info.get("date") and session.extracted_info.get("time"):
            booking_stage = "datetime_selected"
        if session.extracted_info.get("name") and session.extracted_info.get("dob"):
            booking_stage = "ready_to_confirm"
        
        return {
            "service_category": service_category,
            "mentioned_keywords": mentioned_keywords,
            "booking_stage": booking_stage,
            "has_symptom_description": any(kw in mentioned_keywords for kw in ["heart", "stomach", "pain", "problem"]),
            "asks_about_availability": any(kw in mentioned_keywords for kw in ["available", "slot", "time", "when"]),
            "wants_to_book": any(kw in mentioned_keywords for kw in ["book", "appointment", "schedule", "reserve"])
        }
    
    async def _handle_booking_intent(self, session_id: str, user_input: str, context: Dict) -> str:
        """Handle appointment booking with smart workflow"""
        print("\n📅 BOOKING INTENT HANDLER")
        session = memory.get_session(session_id)
        history = memory.get_conversation_history(session_id)
        
        print(f"   Booking stage: {context['booking_stage']}")
        print(f"   Service category: {context['service_category']}")
        print(f"   Extracted info: {session.extracted_info}")
        
        # 🎯 STAGE 1: Identify service
        if not session.extracted_info.get("service_id") and context["service_category"]:
            # Suggest relevant services
            relevant_services = self._get_services_by_category(context["service_category"])
            
            if relevant_services:
                service_list = "\n".join([f"- {s['name']} (€{s['price_eur']}, {s['duration_minutes']} min)" 
                                          for s in relevant_services[:3]])
                
                prompt = f"""You are Anna, a warm medical clinic receptionist.

Patient mentioned: "{user_input}"
They are interested in {context['service_category']} services.

Here are our recommended services:
{service_list}

Suggest these services naturally and ask which one they'd prefer.
Keep response to 2-3 sentences, warm and friendly."""
                
                response = await self.llm.generate(prompt, max_tokens=150)
                return response
        
        # 🎯 STAGE 2: Show availability
        if session.extracted_info.get("service_id") and context["asks_about_availability"]:
            # Show available slots
            available_dates = list(self.availability.keys())[:5]
            date_list = "\n".join([f"- {date}" for date in available_dates])
            
            prompt = f"""You are Anna helping book an appointment.

Patient wants to book a service and asked about availability.

Available dates:
{date_list}

List these dates warmly and ask which one works best for them.
Keep response to 2-3 sentences."""
            
            response = await self.llm.generate(prompt, max_tokens=150)
            return response
        
        # 🎯 STAGE 3: Get patient details
        if context["booking_stage"] == "datetime_selected":
            prompt = f"""You are Anna confirming appointment details.

Patient has selected a date and time.

Now ask for:
1. Their full name
2. Date of birth

Be warm and explain we need this for their medical records.
Keep response to 2 sentences."""
            
            response = await self.llm.generate(prompt, max_tokens=150)
            return response
        
        # 🎯 STAGE 4: Confirm booking
        if context["booking_stage"] == "ready_to_confirm":
            # Create booking
            booking = self.create_booking(
                session_id=session_id,
                service_id=session.extracted_info["service_id"],
                date=session.extracted_info["date"],
                time=session.extracted_info["time"],
                name=session.extracted_info["name"],
                dob=session.extracted_info["dob"]
            )
            
            prompt = f"""You are Anna confirming a booked appointment.

Booking details:
- Service: {booking['service_name']}
- Date: {booking['date']}
- Time: {booking['time']}
- Price: €{booking['service_price']}

Confirm the booking warmly and remind them to arrive 10 minutes early.
Keep response to 2-3 sentences."""
            
            response = await self.llm.generate(prompt, max_tokens=150)
            return response
        
        # Default: Guide toward service selection
        prompt = f"""You are Anna, a medical clinic receptionist.

Patient says: "{user_input}"

Ask what type of service they need or what symptoms they're experiencing.
Be warm and helpful. Keep response to 2 sentences."""
        
        response = await self.llm.generate(prompt, max_tokens=150)
        print(f"   ✅ Booking handler complete")
        return response
    
    def _get_services_by_category(self, category: str) -> list:
        """Get services matching a category"""
        category_keywords = {
            "cardiology": ["cardio", "heart", "ecg"],
            "gastroenterology": ["gastro", "stomach", "abdominal"],
            "blood_test": ["blood", "analysis"]
        }
        
        keywords = category_keywords.get(category, [])
        matching_services = []
        
        for service_id, service_data in self.services.items():
            service_name = service_data.get("name", "").lower()
            if any(kw in service_name for kw in keywords):
                matching_services.append({**service_data, "id": service_id})
        
        return matching_services
    
    async def _handle_symptom_intent(self, session_id: str, user_input: str, context: Dict) -> str:
        """Handle symptom description and service recommendation"""
        print("\n🩺 SYMPTOM INTENT HANDLER")
        
        # Extract symptoms
        symptoms = await self._extract_symptoms(user_input)
        print(f"   Symptoms: {symptoms}")
        
        # Suggest service based on symptoms
        if context["service_category"]:
            relevant_services = self._get_services_by_category(context["service_category"])
            
            if relevant_services:
                service_list = "\n".join([f"- {s['name']} (€{s['price_eur']}, {s['duration_minutes']} min)" 
                                          for s in relevant_services[:2]])
                
                prompt = f"""You are Anna, a caring medical receptionist (NOT a doctor).

Patient described: "{user_input}"

Based on what they described, these services might help:
{service_list}

IMPORTANT:
- Be empathetic and acknowledge their concern
- NEVER diagnose - say "the doctor will evaluate"
- Suggest the service naturally
- Ask if they'd like to book

Keep response to 2-3 sentences, warm and supportive."""
                
                response = await self.llm.generate(prompt, max_tokens=150)
                
                # Store symptoms
                memory.update_extracted_info(session_id, "symptoms", symptoms)
                
                return response
        
        # Fallback: Ask for more details
        prompt = f"""You are Anna, a caring medical receptionist.

Patient mentioned: "{user_input}"

Ask 1-2 gentle follow-up questions about:
- How long they've had this
- How severe it is

Be empathetic. Keep response to 2 sentences."""
        
        response = await self.llm.generate(prompt, max_tokens=150)
        print(f"   ✅ Symptom handler complete")
        return response
    
    async def _handle_service_info_intent(self, session_id: str, user_input: str, context: Dict) -> str:
        """Handle questions about specific services"""
        print("\nℹ️ SERVICE INFO HANDLER")
        
        # Find relevant service
        if context["service_category"]:
            services = self._get_services_by_category(context["service_category"])
            service_list = "\n".join([f"- {s['name']}: {s.get('description', 'N/A')}" for s in services[:3]])
        else:
            service_list = "\n".join([f"- {s['name']}: {s.get('description', 'N/A')}" 
                                      for s in list(self.services.values())[:5]])
        
        prompt = f"""You are Anna explaining our services.

Patient asks: "{user_input}"

Our services:
{service_list}

Provide friendly, accurate information about what they asked.
Keep response to 2-3 sentences."""
        
        response = await self.llm.generate(prompt, max_tokens=150)
        print(f"   ✅ Service info handler complete")
        return response
    
    async def _handle_price_intent(self, session_id: str, user_input: str, context: Dict) -> str:
        """Handle questions about pricing and duration"""
        print("\n💰 PRICE INTENT HANDLER")
        
        if context["service_category"]:
            services = self._get_services_by_category(context["service_category"])
            price_list = "\n".join([f"- {s['name']}: €{s['price_eur']} ({s['duration_minutes']} minutes)" 
                                    for s in services[:3]])
        else:
            price_list = "\n".join([f"- {s['name']}: €{s['price_eur']} ({s['duration_minutes']} minutes)" 
                                    for s in list(self.services.values())[:5]])
        
        prompt = f"""You are Anna explaining pricing.

Patient asks: "{user_input}"

Pricing:
{price_list}

Provide the information clearly and warmly.
Keep response to 2-3 sentences."""
        
        response = await self.llm.generate(prompt, max_tokens=150)
        print(f"   ✅ Price handler complete")
        return response
    
    async def _handle_preparation_intent(self, session_id: str, user_input: str, context: Dict) -> str:
        """Handle preparation instructions"""
        print("\n📋 PREPARATION HANDLER")
        
        prompt = f"""You are Anna explaining appointment preparation.

Patient asks: "{user_input}"

Provide clear, helpful preparation instructions if available.
Keep response to 2-3 sentences."""
        
        response = await self.llm.generate(prompt, max_tokens=150)
        print(f"   ✅ Preparation handler complete")
        return response
    
    async def _handle_general_intent(self, session_id: str, user_input: str, context: Dict) -> str:
        """Handle general conversation"""
        print("\n💬 GENERAL INTENT HANDLER")
        
        prompt = f"""You are Anna, a warm and professional medical clinic receptionist.
Patient says: "{user_input}"

Respond naturally and helpfully. You can help with:
- Booking appointments
- Answering questions about services, pricing, duration
- Suggesting services based on symptoms (without diagnosing)

Keep response to 2 sentences and be warm and professional."""
        
        response = await self.llm.generate(prompt, max_tokens=150)
        
        # Ensure response is not empty
        if not response or response.strip() == "":
            print("   ⚠️ WARNING: Empty response from LLM, using fallback")
            response = "I'm here to help! Could you please tell me more about what you need?"
        
        print(f"   ✅ General handler complete")
        return response.strip()
    
    async def _extract_symptoms(self, user_input: str) -> list:
        """Extract symptoms from user input"""
        # Simple keyword extraction
        symptom_keywords = ["pain", "ache", "hurt", "problem", "issue", "chest", "heart", 
                           "stomach", "dizzy", "nausea", "fever", "cough", "short of breath"]
        
        found_symptoms = [kw for kw in symptom_keywords if kw.lower() in user_input.lower()]
        return found_symptoms if found_symptoms else ["general discomfort"]
    
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