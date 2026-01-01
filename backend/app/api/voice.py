from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from app.core.memory import memory
from app.core.whisper import WhisperTranscriber
from app.core.tts import TextToSpeech
from app.agents.medical_agent import MedicalAgent
import json
import tempfile
import os

router = APIRouter()
transcriber = WhisperTranscriber()
tts = TextToSpeech()
agent = MedicalAgent()

@router.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...), session_id: str = Form(...)):
    """Transcribe audio file to text using Whisper"""
    try:
        print(f"Received audio file for session: {session_id}")
        
        # Save uploaded audio to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        print(f"Audio file saved to: {tmp_path}")
        
        try:
            # Transcribe using Whisper
            print(f"Starting transcription...")
            audio_bytes = open(tmp_path, 'rb').read()
            text = await transcriber.transcribe(audio_bytes)
            
            print(f"Transcription result: '{text}'")
            
            if not text or text.strip() == "":
                print("WARNING: Transcription returned empty text")
                return {
                    "session_id": session_id,
                    "text": "",
                    "success": False,
                    "error": "Could not transcribe audio"
                }
            
            return {
                "session_id": session_id,
                "text": text,
                "success": True
            }
        
        finally:
            # Clean up temp file
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    print(f"Temp file deleted: {tmp_path}")
            except Exception as e:
                print(f"Error deleting temp file: {e}")
    
    except Exception as e:
        print(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for voice/text chat"""
    await websocket.accept()
    print(f"WebSocket connected for session: {session_id}")
    
    # Create session if doesn't exist
    if not memory.get_session(session_id):
        memory.create_session()
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            print(f"WebSocket message: {message_data}")
            
            # Handle text messages
            if message_data.get("type") == "text":
                user_text = message_data.get("text", "")
                
                # Add to memory
                memory.add_message(session_id, "user", user_text)
                
                # Get response from agent
                response = await agent.process_user_input(session_id, user_text)
                
                # Add to memory
                memory.add_message(session_id, "assistant", response)
                
                # Send response
                await websocket.send_text(json.dumps({
                    "type": "text",
                    "text": response,
                    "role": "assistant"
                }))
            
            # Handle audio messages
            elif message_data.get("type") == "audio":
                audio_bytes = bytes(message_data.get("audio", []))
                
                # Transcribe
                user_text = await transcriber.transcribe(audio_bytes)
                
                if user_text:
                    print(f"Transcribed: {user_text}")
                    
                    # Send transcription
                    await websocket.send_text(json.dumps({
                        "type": "transcription",
                        "text": user_text
                    }))
                    
                    # Add to memory
                    memory.add_message(session_id, "user", user_text)
                    
                    # Get response from agent
                    response = await agent.process_user_input(session_id, user_text)
                    
                    # Add to memory
                    memory.add_message(session_id, "assistant", response)
                    
                    # Generate audio
                    audio = tts.synthesize(response)
                    
                    # Send response
                    await websocket.send_text(json.dumps({
                        "type": "response",
                        "text": response,
                        "audio": list(audio) if audio else []
                    }))
    
    except WebSocketDisconnect:
        print(f"Client disconnected: {session_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e)
            }))
        except:
            pass
