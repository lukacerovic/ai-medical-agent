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

  // Initialize session
  useEffect(() => {
    const initializeSession = async () => {
      try {
        const response = await fetch(
          `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/session/new`
        );
        const data = await response.json();
        console.log('Session created:', data.session_id);
        setSessionId(data.session_id);
      } catch (error) {
        console.error('Failed to initialize session:', error);
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
    if (!sessionId) return;
    
    console.log('Starting phone call...');
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
    console.log('Ending call');
    stopVoiceCall();
    setIsInCall(false);
    setTranscript('');
    setStatus('idle');
    setIsListening(false);
    window.speechSynthesis.cancel();
  };

  return (
    <div className="app">
      <div className="container">
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
                <VoiceButton 
                  onClick={handleStartCall}
                  disabled={!sessionId}
                />
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
