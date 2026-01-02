import json
import re
from typing import Dict, Any, Optional, Tuple, List
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
                content = f.read().strip()
                if not content or content == "[]":
                    return []
                return json.loads(content)
        except Exception as e:
            print(f"⚠️ Warning: Could not load bookings.json: {e}")
            return []
    
    def _save_booking(self, booking: Dict):
        """Save booking to file and update availability"""
        print("\n" + "💾".repeat(40))
        print("💾 SAVING BOOKING TO FILE")
        print("💾".repeat(40))
        
        self.bookings.append(booking)
        
        try:
            # Save booking
            with open(settings.data_dir / "bookings.json", "w") as f:
                json.dump(self.bookings, f, indent=2)
            print(f"✅ Booking saved: {booking['id']}")
            print(f"📝 Service: {booking['service_name']}")
            print(f"📅 Date: {booking['date']} at {booking['time']}")
            print(f"👤 Patient: {booking['user_name']}")
            
            # Mark slot as unavailable
            date = booking['date']
            time = booking['time']
            
            if date in self.availability and time in self.availability[date]:
                self.availability[date][time] = False
                
                # Save updated availability
                with open(settings.data_dir / "availability.json", "w") as f:
                    json.dump(self.availability, f, indent=2)
                
                print(f"✅ Slot marked as unavailable: {date} {time}")
            
            print("💾".repeat(40) + "\n")
            
        except Exception as e:
            print(f"❌ Error saving booking: {e}")
            import traceback
            traceback.print_exc()
            print("💾".repeat(40) + "\n")
    
    def _save_availability(self):
        """Save availability to file"""
        try:
            with open(settings.data_dir / "availability.json", "w") as f:
                json.dump(self.availability, f, indent=2)
        except Exception as e:
            print(f"Error saving availability: {e}")
    
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
        
        # 📌 EXTRACT CONTEXT FROM FULL CONVERSATION HISTORY
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
        """Analyze FULL conversation context and extract structured information"""
        session = memory.get_session(session_id)
        history = memory.get_conversation_history(session_id)
        
        print(f"📋 FULL CONVERSATION HISTORY:")
        print(f"{history}")
        print(f"-" * 80)
        
        # Combine current input with full history
        full_context = history + f"Patient: {user_input}\n"
        
        # Extract keywords from FULL conversation, not just current message
        keywords = ["heart", "cardio", "chest", "cardiac", "stomach", "gastro", 
                    "blood", "test", "ultrasound", "consultation", "appointment", 
                    "book", "available", "slot", "time", "date", "schedule",
                    "january", "february", "march", "april", "may", "june",
                    "09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
        
        mentioned_keywords = [kw for kw in keywords if kw.lower() in full_context.lower()]
        
        # Identify mentioned service category from FULL history
        service_category = None
        if any(kw in mentioned_keywords for kw in ["heart", "cardio", "chest", "cardiac"]):
            service_category = "cardiology"
        elif any(kw in mentioned_keywords for kw in ["stomach", "gastro"]):
            service_category = "gastroenterology"
        elif "blood" in mentioned_keywords:
            service_category = "blood_test"
        
        # 📅 EXTRACT DATE AND TIME from user input
        date_match = self._extract_date(user_input)
        time_match = self._extract_time(user_input)
        
        if date_match:
            memory.update_extracted_info(session_id, "date", date_match)
            print(f"📅 Extracted date: {date_match}")
        
        if time_match:
            memory.update_extracted_info(session_id, "time", time_match)
            print(f"⏰ Extracted time: {time_match}")
        
        # 👤 EXTRACT NAME AND DOB from user input
        name_match = self._extract_name(user_input, history)
        dob_match = self._extract_dob(user_input)
        
        if name_match:
            memory.update_extracted_info(session_id, "name", name_match)
            print(f"👤 Extracted name: {name_match}")
        
        if dob_match:
            memory.update_extracted_info(session_id, "dob", dob_match)
            print(f"🎂 Extracted DOB: {dob_match}")
        
        # Check what's already been discussed
        already_discussed = {
            "services_suggested": "cardiology consultation" in history.lower() or "€120" in history,
            "asked_about_slots": "available" in user_input.lower() and "slot" in user_input.lower(),
            "user_confirmed_service": any(phrase in user_input.lower() for phrase in ["i'd like", "yes", "book a consultation", "schedule"]),
            "assistant_already_listed_services": "cardiology consultation" in history.lower(),
            "user_explicitly_asks_for_availability": "available" in user_input.lower() or "slot" in user_input.lower() or "when" in user_input.lower(),
            "dates_shown": any(date in history for date in self.availability.keys()),
            "user_selected_date": date_match is not None,
            "user_selected_time": time_match is not None,
            "asked_for_patient_details": "full name" in history.lower() or "date of birth" in history.lower(),
            "user_provided_name": name_match is not None,
            "user_provided_dob": dob_match is not None
        }
        
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
            "asks_about_availability": "available" in user_input.lower() or "slot" in user_input.lower() or "when" in user_input.lower(),
            "wants_to_book": any(kw in user_input.lower() for kw in ["book", "appointment", "schedule", "reserve", "i'd like", "yes"]),
            "already_discussed": already_discussed,
            "conversation_history": history,
            "extracted_date": date_match,
            "extracted_time": time_match,
            "extracted_name": name_match,
            "extracted_dob": dob_match
        }
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from text (format: YYYY-MM-DD)"""
        # Check if date exists in availability
        for date_key in self.availability.keys():
            if date_key.lower() in text.lower():
                return date_key
        
        # Try to match patterns like "January 6" or "Jan 6"
        month_map = {
            "january": "01", "jan": "01",
            "february": "02", "feb": "02",
            "march": "03", "mar": "03",
            "april": "04", "apr": "04",
            "may": "05",
            "june": "06", "jun": "06"
        }
        
        text_lower = text.lower()
        for month_name, month_num in month_map.items():
            if month_name in text_lower:
                # Extract day number
                import re
                day_match = re.search(rf"{month_name}\s+(\d{{1,2}})", text_lower)
                if day_match:
                    day = day_match.group(1).zfill(2)
                    potential_date = f"2025-{month_num}-{day}"
                    # Check if this date exists in availability
                    if potential_date in self.availability:
                        return potential_date
        
        return None
    
    def _extract_time(self, text: str) -> Optional[str]:
        """Extract time from text (format: HH:MM)"""
        import re
        
        # Match patterns like "10:00", "10 AM", "10:30"
        time_patterns = [
            r"(\d{1,2}:\d{2})",  # 10:00
            r"(\d{1,2})\s*(?:am|pm)",  # 10 AM
            r"(\d{1,2})\s*o'?clock"  # 10 o'clock
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text.lower())
            if match:
                time_str = match.group(1)
                
                # Convert to 24-hour format if needed
                if ":" in time_str:
                    return time_str
                else:
                    # Convert hour to HH:00 format
                    hour = int(time_str)
                    if "pm" in text.lower() and hour < 12:
                        hour += 12
                    return f"{hour:02d}:00"
        
        return None
    
    def _extract_name(self, text: str, history: str) -> Optional[str]:
        """Extract full name from text"""
        import re
        
        # Check if AI asked for name in previous message
        if "full name" not in history.lower():
            return None
        
        # Remove common phrases
        text_clean = text.lower()
        text_clean = re.sub(r"(my name is|i'm|i am|it's|name:)", "", text_clean).strip()
        
        # Match pattern: "FirstName LastName" (2-4 words, capitalized)
        name_pattern = r"\b([A-Z][a-z]+(?: [A-Z][a-z]+){1,3})\b"
        match = re.search(name_pattern, text)
        
        if match:
            return match.group(1)
        
        # Fallback: Extract 2-3 consecutive words after cleaning
        words = text_clean.split()
        if 2 <= len(words) <= 4:
            # Capitalize properly
            return " ".join(word.capitalize() for word in words)
        
        return None
    
    def _extract_dob(self, text: str) -> Optional[str]:
        """Extract date of birth from text (format: YYYY-MM-DD)"""
        import re
        
        # Pattern 1: YYYY-MM-DD
        pattern1 = r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})"
        match1 = re.search(pattern1, text)
        if match1:
            year, month, day = match1.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Pattern 2: MM/DD/YYYY or DD/MM/YYYY
        pattern2 = r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})"
        match2 = re.search(pattern2, text)
        if match2:
            first, second, year = match2.groups()
            # Assume DD/MM/YYYY (European format)
            return f"{year}-{second.zfill(2)}-{first.zfill(2)}"
        
        # Pattern 3: "15th May 1990" or "May 15, 1990"
        month_map = {
            "january": "01", "jan": "01",
            "february": "02", "feb": "02",
            "march": "03", "mar": "03",
            "april": "04", "apr": "04",
            "may": "05",
            "june": "06", "jun": "06",
            "july": "07", "jul": "07",
            "august": "08", "aug": "08",
            "september": "09", "sep": "09", "sept": "09",
            "october": "10", "oct": "10",
            "november": "11", "nov": "11",
            "december": "12", "dec": "12"
        }
        
        text_lower = text.lower()
        for month_name, month_num in month_map.items():
            if month_name in text_lower:
                # Extract day and year
                pattern = rf"(\d{{1,2}})(?:st|nd|rd|th)?\s*{month_name}\s*(\d{{4}})"
                match = re.search(pattern, text_lower)
                if match:
                    day, year = match.groups()
                    return f"{year}-{month_num}-{day.zfill(2)}"
                
                # Reverse: "May 15, 1990"
                pattern2 = rf"{month_name}\s*(\d{{1,2}})(?:st|nd|rd|th)?,?\s*(\d{{4}})"
                match2 = re.search(pattern2, text_lower)
                if match2:
                    day, year = match2.groups()
                    return f"{year}-{month_num}-{day.zfill(2)}"
        
        return None
    
    async def _handle_booking_intent(self, session_id: str, user_input: str, context: Dict) -> str:
        """Handle appointment booking with smart workflow and NO REPETITION"""
        print("\n📅 BOOKING INTENT HANDLER")
        session = memory.get_session(session_id)
        
        print(f"   Booking stage: {context['booking_stage']}")
        print(f"   Service category: {context['service_category']}")
        print(f"   Already discussed: {context['already_discussed']}")
        print(f"   Extracted info: {session.extracted_info}")
        
        # 🎯 STAGE: User provided name and DOB - Confirm booking
        if context["booking_stage"] == "ready_to_confirm":
            print("➡️ STAGE: Confirming booking")
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
- Patient: {booking['user_name']}

Confirm the booking warmly and remind them to arrive 10 minutes early.
Keep response to 2-3 sentences."""
            
            response = await self.llm.generate(prompt, max_tokens=150)
            return response
        
        # 🎯 STAGE: Date & Time selected - Ask for patient details
        if (context["already_discussed"]["user_selected_date"] and 
            context["already_discussed"]["user_selected_time"] and
            not context["already_discussed"]["asked_for_patient_details"]):
            
            date = context["extracted_date"]
            time = context["extracted_time"]
            
            # Validate availability
            if not self.check_availability(date, time):
                prompt = f"""You are Anna.

Patient selected {date} at {time}, but that slot is no longer available.

Apologize and show these available times for {date}:
{', '.join(self.get_available_slots(date))}

Keep response to 2 sentences."""
                
                response = await self.llm.generate(prompt, max_tokens=150)
                return response
            
            # Slot is available - ask for patient details
            print(f"✅ Slot {date} {time} is available!")
            
            prompt = f"""You are Anna confirming the appointment slot.

Patient selected: {date} at {time}

Say you've reserved that time and now need their:
1. Full name
2. Date of birth (for medical records)

Be warm and friendly. Keep response to 2 sentences."""
            
            response = await self.llm.generate(prompt, max_tokens=150)
            return response
        
        # 🚫 CRITICAL: If user CONFIRMED service and asked for slots, SHOW AVAILABILITY
        if (context["already_discussed"]["user_confirmed_service"] and 
            context["already_discussed"]["user_explicitly_asks_for_availability"] and
            context["already_discussed"]["services_suggested"] and
            not context["already_discussed"]["dates_shown"]):
            
            print("✅ User confirmed service AND asked for availability - showing slots!")
            
            # Show available dates with times
            available_info = []
            for date in list(self.availability.keys())[:3]:  # Show first 3 dates
                slots = self.get_available_slots(date)
                if slots:
                    available_info.append(f"{date}: {', '.join(slots[:4])}")
            
            date_list = "\n".join(available_info)
            
            # Store selected service
            if not session.extracted_info.get("service_id"):
                memory.update_extracted_info(session_id, "service_id", "cardiology_consultation")
            
            prompt = f"""You are Anna helping book an appointment.

Patient confirmed they want to book and asked: "{user_input}"

Available dates and times:
{date_list}

List these options warmly and ask which date and time they prefer.
DO NOT repeat service details they already know.
Keep response to 2-3 sentences."""
            
            response = await self.llm.generate(prompt, max_tokens=200)
            return response
        
        # 🎯 STAGE 1: Service NOT discussed yet - Suggest services
        if not context["already_discussed"]["assistant_already_listed_services"] and context["service_category"]:
            print("➡️ STAGE 1: Suggesting services for first time")
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
        
        # Default: If they want to book but services not suggested yet
        if context["wants_to_book"] and not context["already_discussed"]["services_suggested"]:
            print("➡️ DEFAULT: Asking what service they need")
            prompt = f"""You are Anna, a medical clinic receptionist.

Patient says: "{user_input}"

Ask what type of service or specialist they need.
Keep response to 1-2 sentences."""
            
            response = await self.llm.generate(prompt, max_tokens=150)
            return response
        
        # Absolute fallback
        print("⚠️ FALLBACK: Using generic booking response")
        prompt = f"""You are Anna.

Patient says: "{user_input}"

Conversation so far:
{context['conversation_history']}

Respond naturally based on where they are in the conversation.
DO NOT repeat information already discussed.
Keep response to 2 sentences."""
        
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
        return self.availability.get(date, {}).get(time, False)
    
    def get_available_slots(self, date: str) -> list:
        """Get available time slots for a date"""
        slots = self.availability.get(date, {})
        available = [slot for slot, is_available in slots.items() if is_available]
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
        
        return booking