from fastapi import APIRouter
from app.agents.medical_agent import MedicalAgent

router = APIRouter()
agent = MedicalAgent()

@router.get("/services")
async def get_all_services():
    """Get all available medical services"""
    return {"services": agent.services}

@router.get("/services/{service_id}")
async def get_service(service_id: str):
    """Get specific service details"""
    service = agent.services.get(service_id)
    if not service:
        return {"error": "Service not found"}, 404
    return {"service": service}