import React, { useState, useEffect } from 'react';
import './App.css';
import VoiceButton from './components/VoiceButton';
import Waveform from './components/Waveform';
import StatusIndicator from './components/StatusIndicator';
import ServiceDetails from './components/ServiceDetails';
import useVoiceAgent from './hooks/useVoiceAgent';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [status, setStatus] = useState('idle');
  const [isInCall, setIsInCall] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [sessionError, setSessionError] = useState(null);

  // Initialize session
  useEffect(() => {
    const initializeSession = async () => {
      try {
        console.log('🔄 Initializing session...');
        const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        console.log(`📡 API URL: ${apiUrl}/session/new`);
        
        const response = await fetch(`${apiUrl}/session/new`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
        console.log('📥 Response status:', response.status);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✅ Session created:', data);
        
        if (data.session_id) {
          setSessionId(data.session_id);
          setSessionError(null);
          console.log('✅ Session ID set:', data.session_id);
        } else {
          throw new Error('No session_id in response');
        }
      } catch (error) {
        console.error('❌ Failed to initialize session:', error);
        setSessionError(error.message);
        // Set a dummy session ID so button works anyway
        const fallbackId = `fallback-${Date.now()}`;
        console.log('⚠️ Using fallback session ID:', fallbackId);
        setSessionId(fallbackId);
      }
    };

    initializeSession();
  }, []);

  // Handle AI responses
  const handleResponseReceived = (responseText) => {
    console.log('AI Response received:', responseText);
    setTranscript(responseText);
    setIsListening(false);
    setStatus('speaking');
    
    // Play audio
    playVoiceResponse(responseText);
  };

  // Use voice hook
  const { startVoiceCall, stopVoiceCall, isRecording } = useVoiceAgent(
    sessionId,
    handleResponseReceived,
    setStatus
  );

  const playVoiceResponse = (text) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;
    
    utterance.onstart = () => {
      setStatus('speaking');
    };
    
    utterance.onend = () => {
      // After AI speaks, listen again
      setTimeout(() => {
        setStatus('listening');
        setIsListening(true);
        startVoiceCall();
      }, 500);
    };
    
    window.speechSynthesis.speak(utterance);
  };

  const handleStartCall = () => {
    console.log('🎤 Start call button clicked');
    console.log('📋 Current sessionId:', sessionId);
    
    if (!sessionId) {
      console.error('❌ No session ID available!');
      return;
    }
    
    console.log('✅ Starting phone call...');
    setIsInCall(true);
    setTranscript('');
    setStatus('idle');
    
    // Wait a moment then greet
    setTimeout(() => {
      const greeting = `Hello! I'm Anna, your medical clinic AI assistant. I can help you with information about our services, book appointments, and answer health-related questions. How can I help you today?`;
      
      setTranscript(greeting);
      playVoiceResponse(greeting);
    }, 500);
  };

  const handleEndCall = () => {
    console.log('🛑 EMERGENCY STOP: Killing conversation');
    
    // Stop all voice processing
    stopVoiceCall();
    
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();
    
    // Reset all states
    setIsInCall(false);
    setTranscript('');
    setStatus('idle');
    setIsListening(false);
    
    console.log('✅ Conversation terminated');
  };

  return (
    <div className="app">
      <div className="container">
        {/* EMERGENCY KILL BUTTON - Always visible */}
        {isInCall && (
          <button 
            className="emergency-kill-btn"
            onClick={handleEndCall}
            title="Emergency Stop"
            style={{
              position: 'fixed',
              top: '20px',
              right: '20px',
              zIndex: 9999,
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '50%',
              width: '60px',
              height: '60px',
              fontSize: '24px',
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(220, 53, 69, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.target.style.transform = 'scale(1.1)';
              e.target.style.boxShadow = '0 6px 16px rgba(220, 53, 69, 0.6)';
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'scale(1)';
              e.target.style.boxShadow = '0 4px 12px rgba(220, 53, 69, 0.4)';
            }}
          >
            🛑
          </button>
        )}

        <header className="header">
          <div className="logo">
            <span className="icon">🏥</span>
            <h1>MedCare Clinic</h1>
          </div>
          <p className="subtitle">AI Voice Assistant</p>
        </header>

        <main className="main">
          <div className="content">
            {!isInCall ? (
              // IDLE SCREEN - Just the button
              <div className="greeting">
                <h2>Welcome to MedCare Clinic</h2>
                <p>Click to start a voice call with Anna</p>
                
                {/* Debug info */}
                {sessionError && (
                  <div style={{color: 'orange', fontSize: '12px', margin: '10px 0'}}>
                    ⚠️ Session warning: {sessionError}
                  </div>
                )}
                
                {sessionId && (
                  <div style={{color: 'green', fontSize: '12px', margin: '10px 0'}}>
                    ✅ Ready (Session: {sessionId.substring(0, 8)}...)
                  </div>
                )}
                
                <VoiceButton 
                  onClick={handleStartCall}
                  disabled={!sessionId}
                />
                
                {!sessionId && (
                  <p style={{color: 'gray', fontSize: '14px', marginTop: '10px'}}>
                    Initializing session...
                  </p>
                )}
              </div>
            ) : (
              // CALL SCREEN - Pure voice interface
              <div className="call-interface">
                {/* Header with status */}
                <div className="call-header">
                  <StatusIndicator status={status} />
                </div>

                {/* Main call area - Waveform animation */}
                <div className="call-main">
                  <Waveform isActive={isRecording || isListening} />
                  
                  {/* Transcript display */}
                  <div className="transcript-display">
                    {transcript && (
                      <div className="transcript-text">
                        <p>{transcript}</p>
                      </div>
                    )}
                  </div>

                  {/* Status message */}
                  <div className="status-message">
                    {status === 'listening' && <p>🎤 Listening...</p>}
                    {status === 'thinking' && <p>⏳ Processing...</p>}
                    {status === 'speaking' && <p>🔊 Speaking...</p>}
                    {status === 'idle' && <p>Ready to listen...</p>}
                  </div>
                </div>

                {/* Footer - End call button */}
                <div className="call-footer">
                  <button 
                    className="btn-end-call"
                    onClick={handleEndCall}
                  >
                    ✕ End Call
                  </button>
                </div>
              </div>
            )}
          </div>

          {!isInCall && (
            <aside className="sidebar">
              <ServiceDetails />
            </aside>
          )}
        </main>

        <footer className="footer">
          <p>MedCare Clinic © 2025 | Powered by Voice AI</p>
        </footer>
      </div>
    </div>
  );
}

export default App;
