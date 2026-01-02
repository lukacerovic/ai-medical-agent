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
app.include_router(voice.router, prefix="/api", tags=["Voice"])
app.include_router(services.router, prefix="/api", tags=["Services"])
app.include_router(booking.router, prefix="/api", tags=["Booking"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])


@app.on_event("startup")
async def startup_event():
    print("\n" + "="*80)
    print("🚀 MedCare Clinic AI Backend Started")
    print("="*80)
    print("✅ Mistral LLM configured")
    print("✅ Whisper STT ready")
    print("✅ TTS engine initialized")
    print("✅ CORS enabled for all origins")
    print(f"🌍 API running on: http://localhost:8000")
    print(f"📝 Docs available at: http://localhost:8000/docs")
    print("="*80 + "\n")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    print("❤️ Health check pinged")
    return {"status": "healthy", "message": "Backend is running"}

@app.get("/session/new")
async def create_new_session():
    """Create a new conversation session"""
    print("\n" + "-"*80)
    print("🆕 NEW SESSION REQUEST")
    print("-"*80)
    try:
        session_id = memory.create_session()
        print(f"✅ Session created successfully: {session_id}")
        print(f"💾 Session stored in memory")
        print("-"*80 + "\n")
        return {
            "session_id": session_id,
            "status": "created"
        }
    except Exception as e:
        print(f"❌ Session creation error: {e}")
        import traceback
        traceback.print_exc()
        print("-"*80 + "\n")
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
        "status": "running",
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
