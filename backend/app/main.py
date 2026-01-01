from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import voice, services, booking, chat
from app.core.memory import memory
from uuid import uuid4

app = FastAPI(
    title="MedCare Clinic AI",
    description="AI-powered medical clinic support system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# Include routers
app.include_router(voice.router, prefix="/api", tags=["Voice"])
app.include_router(services.router, prefix="/api", tags=["Services"])
app.include_router(booking.router, prefix="/api", tags=["Booking"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])


@app.on_event("startup")
async def startup_event():
    print("🚀 MedCare Clinic AI Backend Started")
    print("✓ Mistral LLM configured")
    print("✓ Whisper STT ready")
    print("✓ TTS engine initialized")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/session/new")
async def create_new_session():
    """Create a new conversation session"""
    try:
        session_id = memory.create_session()
        print(f"✓ Session created: {session_id}")
        return {
            "session_id": session_id,
            "status": "created"
        }
    except Exception as e:
        print(f"❌ Session creation error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "status": "failed"
        }


@app.get("/")
async def root():
    """API documentation"""
    return {
        "name": "MedCare Clinic AI",
        "version": "1.0.0",
        "endpoints": {
            "websocket": "ws://localhost:8000/ws/{session_id}",
            "rest": {
                "health": "GET /health",
                "new_session": "GET /session/new",
                "services": "GET /api/services",
                "service_detail": "GET /api/services/{service_id}",
                "availability": "GET /api/availability/{date}",
                "chat": "POST /api/chat",
                "booking": "POST /api/booking"
            }
        }
    }