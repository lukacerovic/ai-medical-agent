from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.agents.medical_agent import MedicalAgent

router = APIRouter()
agent = MedicalAgent()

class BookingRequest(BaseModel):
    session_id: str
    service_id: str
    date: str
    time: str
    name: str
    dob: str
    phone: Optional[str] = None

@router.post("/booking")
async def create_booking(request: BookingRequest):
    """Create a new appointment booking"""
    
    # Check availability
    if not agent.check_availability(request.date, request.time):
        raise HTTPException(status_code=400, detail="Time slot not available")
    
    # Create booking
    booking = agent.create_booking(
        session_id=request.session_id,
        service_id=request.service_id,
        date=request.date,
        time=request.time,
        name=request.name,
        dob=request.dob,
        phone=request.phone
    )
    
    return {"booking": booking}

@router.get("/availability/{date}")
async def get_availability(date: str):
    """Get available time slots for a date"""
    slots = agent.get_available_slots(date)
    return {"date": date, "available_slots": slots}

@router.get("/bookings/{session_id}")
async def get_bookings(session_id: str):
    """Get bookings for a session"""
    bookings = [b for b in agent.bookings if b.get("session_id") == session_id]
    return {"bookings": bookings}