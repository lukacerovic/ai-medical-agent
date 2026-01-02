"""Custom Tools for Medical Clinic Agents."""
from crewai_tools import BaseTool
from typing import Type, List, Dict, Any
from pydantic import BaseModel, Field
import json
from datetime import datetime, timedelta
import os


class ServiceLookupInput(BaseModel):
    """Input for Service Lookup Tool."""
    keywords: str = Field(..., description="Keywords describing symptoms or medical condition")


class ServiceLookupTool(BaseTool):
    name: str = "service_lookup"
    description: str = "Searches available medical services based on symptoms or keywords. "\
                       "Returns matching services with details (name, price, duration, description)."
    args_schema: Type[BaseModel] = ServiceLookupInput

    def _run(self, keywords: str) -> str:
        """Search for services matching keywords.
        
        Args:
            keywords: Search terms for service matching
            
        Returns:
            JSON string of matching services
        """
        services = self._load_services()
        keywords_lower = keywords.lower()
        
        # Match services based on keywords
        matches = []
        for service in services:
            service_text = f"{service['name']} {service['description']}".lower()
            
            # Simple keyword matching
            if any(keyword in service_text for keyword in keywords_lower.split()):
                matches.append(service)
        
        if not matches:
            # Return all services if no matches
            matches = services[:3]  # Return top 3 services
        
        return json.dumps(matches, indent=2)

    def _load_services(self) -> List[Dict]:
        """Load services from JSON file."""
        services_path = os.path.join("backend", "app", "data", "services.json")
        
        if os.path.exists(services_path):
            with open(services_path, 'r') as f:
                return json.load(f)
        
        # Default services if file doesn't exist
        return [
            {
                "id": "cardiology_consultation",
                "name": "Cardiology Consultation",
                "price": 120,
                "duration": "45 min",
                "description": "Expert consultation for cardiac issues, heart problems, chest pain"
            },
            {
                "id": "gastroenterology",
                "name": "Gastroenterology Consultation",
                "price": 110,
                "duration": "40 min",
                "description": "Digestive system consultation for stomach, intestinal issues"
            },
            {
                "id": "blood_analysis",
                "name": "Blood Analysis",
                "price": 50,
                "duration": "20 min",
                "description": "Comprehensive blood test and health screening"
            },
            {
                "id": "dermatology",
                "name": "Dermatology Consultation",
                "price": 100,
                "duration": "30 min",
                "description": "Skin condition consultation, rashes, acne, skin problems"
            },
            {
                "id": "general_practice",
                "name": "General Practice",
                "price": 80,
                "duration": "30 min",
                "description": "General health concerns and checkups"
            }
        ]


class AvailabilityCheckInput(BaseModel):
    """Input for Availability Check Tool."""
    service_id: str = Field(..., description="ID of the medical service")
    preferred_date: str = Field(default="", description="Optional preferred date (YYYY-MM-DD)")


class AvailabilityCheckTool(BaseTool):
    name: str = "check_availability"
    description: str = "Checks available appointment slots for a specific service. "\
                       "Returns available dates and times for the next 7 days."
    args_schema: Type[BaseModel] = AvailabilityCheckInput

    def _run(self, service_id: str, preferred_date: str = "") -> str:
        """Check availability for service.
        
        Args:
            service_id: ID of service to check
            preferred_date: Optional preferred date
            
        Returns:
            JSON string of available slots
        """
        availability = self._load_availability()
        
        # Get next 7 days of availability
        available_slots = {}
        start_date = datetime.now().date()
        
        for i in range(7):
            check_date = start_date + timedelta(days=i)
            date_str = check_date.strftime("%Y-%m-%d")
            
            if date_str in availability:
                # Filter only available slots (value = true)
                available_times = [
                    time for time, is_available in availability[date_str].items()
                    if is_available
                ]
                if available_times:
                    available_slots[date_str] = available_times
        
        if not available_slots:
            # Generate default slots if none exist
            available_slots = self._generate_default_slots(start_date)
        
        return json.dumps(available_slots, indent=2)

    def _load_availability(self) -> Dict:
        """Load availability from JSON file."""
        availability_path = os.path.join("backend", "app", "data", "availability.json")
        
        if os.path.exists(availability_path):
            with open(availability_path, 'r') as f:
                return json.load(f)
        
        return {}

    def _generate_default_slots(self, start_date) -> Dict:
        """Generate default available slots."""
        slots = {}
        times = ["09:00", "09:30", "10:00", "10:30", "11:00", "14:00", "14:30", "15:00"]
        
        for i in range(7):
            date = start_date + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            slots[date_str] = times[:5]  # 5 slots per day
        
        return slots


class BookingCreationInput(BaseModel):
    """Input for Booking Creation Tool."""
    patient_name: str = Field(..., description="Patient's full name")
    dob: str = Field(..., description="Patient's date of birth (YYYY-MM-DD)")
    service_id: str = Field(..., description="ID of the medical service")
    service_name: str = Field(..., description="Name of the medical service")
    date: str = Field(..., description="Appointment date (YYYY-MM-DD)")
    time: str = Field(..., description="Appointment time (HH:MM)")
    price: float = Field(..., description="Service price")


class BookingCreationTool(BaseTool):
    name: str = "create_booking"
    description: str = "Creates a new appointment booking and updates availability. "\
                       "Returns confirmation with booking ID and all details."
    args_schema: Type[BaseModel] = BookingCreationInput

    def _run(self, patient_name: str, dob: str, service_id: str, service_name: str,
             date: str, time: str, price: float) -> str:
        """Create a new booking.
        
        Args:
            patient_name: Patient's full name
            dob: Date of birth
            service_id: Service ID
            service_name: Service name
            date: Appointment date
            time: Appointment time
            price: Service price
            
        Returns:
            JSON confirmation of booking
        """
        # Generate booking ID
        booking_id = f"BK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create booking record
        booking = {
            "id": booking_id,
            "patient_name": patient_name,
            "dob": dob,
            "service_id": service_id,
            "service_name": service_name,
            "date": date,
            "time": time,
            "price": price,
            "status": "confirmed",
            "created_at": datetime.now().isoformat()
        }
        
        # Save booking
        self._save_booking(booking)
        
        # Update availability
        self._update_availability(date, time)
        
        return json.dumps({
            "success": True,
            "booking": booking,
            "message": f"Appointment confirmed for {patient_name} on {date} at {time}"
        }, indent=2)

    def _save_booking(self, booking: Dict):
        """Save booking to JSON file."""
        bookings_path = os.path.join("backend", "app", "data", "bookings.json")
        os.makedirs(os.path.dirname(bookings_path), exist_ok=True)
        
        bookings = []
        if os.path.exists(bookings_path):
            with open(bookings_path, 'r') as f:
                bookings = json.load(f)
        
        bookings.append(booking)
        
        with open(bookings_path, 'w') as f:
            json.dump(bookings, f, indent=2)

    def _update_availability(self, date: str, time: str):
        """Mark slot as unavailable."""
        availability_path = os.path.join("backend", "app", "data", "availability.json")
        
        availability = {}
        if os.path.exists(availability_path):
            with open(availability_path, 'r') as f:
                availability = json.load(f)
        
        if date not in availability:
            availability[date] = {}
        
        availability[date][time] = False
        
        os.makedirs(os.path.dirname(availability_path), exist_ok=True)
        with open(availability_path, 'w') as f:
            json.dump(availability, f, indent=2)


def get_medical_tools() -> List[BaseTool]:
    """Get all medical clinic tools.
    
    Returns:
        List of initialized tools
    """
    return [
        ServiceLookupTool(),
        AvailabilityCheckTool(),
        BookingCreationTool()
    ]
