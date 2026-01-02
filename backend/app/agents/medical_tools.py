"""Custom Tools for Medical Agents"""

from crewai_tools import BaseTool
from typing import Type, Any, Dict, List, Optional
from pydantic import BaseModel, Field
import json
import os
from datetime import datetime, timedelta
import re

class ServiceMatchingInput(BaseModel):
    """Input schema for Service Matching Tool."""
    symptoms: str = Field(..., description="Patient's described symptoms or medical concerns")

class ServiceMatchingTool(BaseTool):
    name: str = "Service Matching Tool"
    description: str = (
        "Matches patient symptoms to appropriate medical services. "
        "Input should be a description of symptoms. "
        "Returns matching services with details (name, price, duration, description)."
    )
    args_schema: Type[BaseModel] = ServiceMatchingInput
    
    def _run(self, symptoms: str) -> str:
        """
        Match symptoms to medical services.
        
        Args:
            symptoms: Patient's described symptoms
            
        Returns:
            JSON string with matching services
        """
        # Load services data
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        services_file = os.path.join(data_dir, 'services.json')
        
        try:
            with open(services_file, 'r', encoding='utf-8') as f:
                services = json.load(f)
        except FileNotFoundError:
            return json.dumps({"error": "Services data not found"})
        
        # Simple keyword matching (can be enhanced with ML)
        symptoms_lower = symptoms.lower()
        matched_services = []
        
        # Keyword mapping
        keyword_map = {
            "heart": ["cardiology_consultation"],
            "cardiac": ["cardiology_consultation"],
            "chest pain": ["cardiology_consultation"],
            "stomach": ["gastroenterology"],
            "digestive": ["gastroenterology"],
            "gastro": ["gastroenterology"],
            "blood": ["blood_analysis"],
            "test": ["blood_analysis"],
            "analysis": ["blood_analysis"],
        }
        
        # Find matches
        for keyword, service_ids in keyword_map.items():
            if keyword in symptoms_lower:
                for service_id in service_ids:
                    service = next((s for s in services if s["id"] == service_id), None)
                    if service and service not in matched_services:
                        matched_services.append(service)
        
        # If no specific match, return all services
        if not matched_services:
            matched_services = services
        
        return json.dumps({
            "matched_services": matched_services,
            "match_confidence": "high" if len(matched_services) <= 2 else "medium"
        }, indent=2)

class AvailabilityCheckerInput(BaseModel):
    """Input schema for Availability Checker Tool."""
    date: Optional[str] = Field(None, description="Specific date to check (YYYY-MM-DD format)")
    days_ahead: int = Field(7, description="Number of days ahead to check")

class AvailabilityCheckerTool(BaseTool):
    name: str = "Availability Checker Tool"
    description: str = (
        "Checks available appointment slots. "
        "Can check specific date or next N days. "
        "Returns available time slots with dates."
    )
    args_schema: Type[BaseModel] = AvailabilityCheckerInput
    
    def _run(self, date: Optional[str] = None, days_ahead: int = 7) -> str:
        """
        Check appointment availability.
        
        Args:
            date: Specific date to check (YYYY-MM-DD)
            days_ahead: Number of days to check from today
            
        Returns:
            JSON string with available slots
        """
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        availability_file = os.path.join(data_dir, 'availability.json')
        
        try:
            with open(availability_file, 'r', encoding='utf-8') as f:
                availability = json.load(f)
        except FileNotFoundError:
            return json.dumps({"error": "Availability data not found"})
        
        # Filter available slots
        available_slots = {}
        
        if date:
            # Check specific date
            if date in availability:
                slots = {k: v for k, v in availability[date].items() if v}
                if slots:
                    available_slots[date] = slots
        else:
            # Check next N days
            for date_key in list(availability.keys())[:days_ahead]:
                slots = {k: v for k, v in availability[date_key].items() if v}
                if slots:
                    available_slots[date_key] = slots
        
        return json.dumps({
            "available_slots": available_slots,
            "total_dates": len(available_slots)
        }, indent=2)

class BookingCreatorInput(BaseModel):
    """Input schema for Booking Creator Tool."""
    patient_name: str = Field(..., description="Full name of the patient")
    dob: str = Field(..., description="Date of birth (YYYY-MM-DD)")
    service_name: str = Field(..., description="Name of the medical service")
    date: str = Field(..., description="Appointment date (YYYY-MM-DD)")
    time: str = Field(..., description="Appointment time (HH:MM)")
    price: float = Field(..., description="Service price")

class BookingCreatorTool(BaseTool):
    name: str = "Booking Creator Tool"
    description: str = (
        "Creates a confirmed appointment booking. "
        "Requires: patient_name, dob, service_name, date, time, price. "
        "Returns booking confirmation with ID."
    )
    args_schema: Type[BaseModel] = BookingCreatorInput
    
    def _run(
        self,
        patient_name: str,
        dob: str,
        service_name: str,
        date: str,
        time: str,
        price: float
    ) -> str:
        """
        Create a new booking.
        
        Args:
            patient_name: Full patient name
            dob: Date of birth
            service_name: Service name
            date: Appointment date
            time: Appointment time
            price: Service price
            
        Returns:
            JSON string with booking confirmation
        """
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        bookings_file = os.path.join(data_dir, 'bookings.json')
        availability_file = os.path.join(data_dir, 'availability.json')
        
        # Generate booking ID
        booking_id = f"BK-{date.replace('-', '')}{time.replace(':', '')}"
        
        # Create booking record
        booking = {
            "id": booking_id,
            "patient_name": patient_name,
            "dob": dob,
            "service_name": service_name,
            "date": date,
            "time": time,
            "status": "confirmed",
            "price": price,
            "created_at": datetime.now().isoformat()
        }
        
        # Load existing bookings
        try:
            with open(bookings_file, 'r', encoding='utf-8') as f:
                bookings = json.load(f)
        except FileNotFoundError:
            bookings = []
        
        # Add new booking
        bookings.append(booking)
        
        # Save bookings
        with open(bookings_file, 'w', encoding='utf-8') as f:
            json.dump(bookings, f, indent=2)
        
        # Update availability
        try:
            with open(availability_file, 'r', encoding='utf-8') as f:
                availability = json.load(f)
            
            if date in availability and time in availability[date]:
                availability[date][time] = False
                
                with open(availability_file, 'w', encoding='utf-8') as f:
                    json.dump(availability, f, indent=2)
        except Exception as e:
            pass  # Non-critical if availability update fails
        
        return json.dumps({
            "status": "success",
            "booking": booking,
            "message": "Booking created successfully"
        }, indent=2)

class PatientInfoExtractorInput(BaseModel):
    """Input schema for Patient Info Extractor Tool."""
    text: str = Field(..., description="Patient's message or conversation text")

class PatientInfoExtractorTool(BaseTool):
    name: str = "Patient Info Extractor Tool"
    description: str = (
        "Extracts structured patient information from natural language. "
        "Can extract: name, date of birth, phone, email, preferred dates/times. "
        "Returns structured JSON with extracted fields."
    )
    args_schema: Type[BaseModel] = PatientInfoExtractorInput
    
    def _run(self, text: str) -> str:
        """
        Extract patient information from text.
        
        Args:
            text: Patient's message
            
        Returns:
            JSON string with extracted information
        """
        extracted = {}
        
        # Extract dates (various formats)
        date_patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
            r'(\d{2})/(\d{2})/(\d{4})',  # MM/DD/YYYY
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',  # Month DD, YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted["date_mentioned"] = match.group(0)
                break
        
        # Extract times
        time_pattern = r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?'
        time_match = re.search(time_pattern, text)
        if time_match:
            extracted["time_mentioned"] = time_match.group(0)
        
        # Extract names (simple heuristic - capitalized words)
        name_pattern = r'(?:my name is|I am|I\'m)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
        name_match = re.search(name_pattern, text, re.IGNORECASE)
        if name_match:
            extracted["name"] = name_match.group(1)
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            extracted["email"] = email_match.group(0)
        
        # Extract phone
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            extracted["phone"] = phone_match.group(0)
        
        return json.dumps({
            "extracted_info": extracted,
            "extraction_count": len(extracted)
        }, indent=2)
