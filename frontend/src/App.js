import React, { useState, useEffect, useRef } from 'react';
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
  const isSpeakingRef = useRef(false);

  // Initialize session
  useEffect(() => {
    const initializeSession = async () => {
      try {
        console.log('🔄 [SESSION] Initializing session...');
        const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        console.log(`📡 [SESSION] API URL: ${apiUrl}/session/new`);
        
        const response = await fetch(`${apiUrl}/session/new`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
        console.log(`📥 [SESSION] Response status: ${response.status}`);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✅ [SESSION] Session created:', data);
        
        if (data.session_id) {
          setSessionId(data.session_id);
          setSessionError(null);
          console.log('✅ [SESSION] Session ID set:', data.session_id);
        } else {
          throw new Error('No session_id in response');
        }
      } catch (error) {
        console.error('❌ [SESSION] Failed to initialize session:', error);
        setSessionError(error.message);
        const fallbackId = `fallback-${Date.now()}`;
        console.log('⚠️ [SESSION] Using fallback session ID:', fallbackId);
        setSessionId(fallbackId);
      }
    };

    initializeSession();
  }, []);

  // Handle AI responses
  const handleResponseReceived = (responseText) => {
    console.log('\n' + '='.repeat(80));
    console.log('📥 [RESPONSE] AI Response received');
    console.log('='.repeat(80));
    console.log(`📝 [RESPONSE] Text: ${responseText}`);
    console.log(`🔇 [RESPONSE] Stopping microphone to prevent echo`);
    
    // CRITICAL: Stop listening before AI speaks
    stopVoiceCall();
    setIsListening(false);
    
    setTranscript(responseText);
    setStatus('speaking');
    
    console.log(`🔊 [RESPONSE] Starting speech synthesis`);
    console.log('='.repeat(80) + '\n');
    
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
    console.log('\n' + '-'.repeat(80));
    console.log('🔊 [TTS] Starting Text-to-Speech');
    console.log('-'.repeat(80));
    
    isSpeakingRef.current = true;
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;
    
    utterance.onstart = () => {
      console.log('▶️ [TTS] Speech started');
      setStatus('speaking');
    };
    
    utterance.onend = () => {
      console.log('⏹️ [TTS] Speech ended');
      isSpeakingRef.current = false;
      console.log('-'.repeat(80));
      console.log('🎤 [LISTENING] Waiting 1 second before listening again...');
      console.log('-'.repeat(80) + '\n');
      
      // Wait 1 second after AI finishes speaking before listening again
      setTimeout(() => {
        console.log('\n' + '='.repeat(80));
        console.log('🎤 [LISTENING] Starting microphone');
        console.log('='.repeat(80));
        console.log('✅ [LISTENING] Ready to listen for user input');
        console.log('='.repeat(80) + '\n');
        
        setStatus('listening');
        setIsListening(true);
        startVoiceCall();
      }, 1000);
    };
    
    window.speechSynthesis.speak(utterance);
  };

  const handleStartCall = () => {
    console.log('\n' + '#'.repeat(80));
    console.log('📞 [CALL] START CALL BUTTON CLICKED');
    console.log('#'.repeat(80));
    console.log(`📋 [CALL] Session ID: ${sessionId}`);
    
    if (!sessionId) {
      console.error('❌ [CALL] No session ID available!');
      console.log('#'.repeat(80) + '\n');
      return;
    }
    
    console.log('✅ [CALL] Starting phone call...');
    console.log('#'.repeat(80) + '\n');
    
    setIsInCall(true);
    setTranscript('');
    setStatus('idle');
    
    // Wait a moment then greet
    setTimeout(() => {
      const greeting = `Hello! I'm Anna, your medical clinic AI assistant. I can help you with information about our services, book appointments, and answer health-related questions. How can I help you today?`;
      
      console.log('\n' + '='.repeat(80));
      console.log('👋 [GREETING] Playing initial greeting');
      console.log('='.repeat(80) + '\n');
      
      setTranscript(greeting);
      playVoiceResponse(greeting);
    }, 500);
  };

  const handleEndCall = () => {
    console.log('\n' + '!'.repeat(80));
    console.log('🛑 [EMERGENCY] EMERGENCY STOP: Killing conversation');
    console.log('!'.repeat(80));
    
    // Stop all voice processing
    stopVoiceCall();
    console.log('✅ [EMERGENCY] Voice call stopped');
    
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();
    console.log('✅ [EMERGENCY] Speech synthesis cancelled');
    
    // Reset all states
    setIsInCall(false);
    setTranscript('');
    setStatus('idle');
    setIsListening(false);
    isSpeakingRef.current = false;
    
    console.log('✅ [EMERGENCY] All states reset');
    console.log('✅ [EMERGENCY] Conversation terminated');
    console.log('!'.repeat(80) + '\n');
  };

  // ✨ NEW: Stop listening manually (for VAD)
  const handleStopListening = () => {
    console.log('\n' + '■'.repeat(80));
    console.log('⏸️ [MANUAL STOP] User manually stopped listening');
    console.log('■'.repeat(80));
    
    stopVoiceCall();
    setIsListening(false);
    setStatus('thinking');
    
    console.log('✅ [MANUAL STOP] Voice recording stopped');
    console.log('🔄 [MANUAL STOP] Processing audio...');
    console.log('■'.repeat(80) + '\n');
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
                    {status === 'thinking' && <p>⌛ Processing...</p>}
                    {status === 'speaking' && <p>🔊 Speaking...</p>}
                    {status === 'idle' && <p>Ready to listen...</p>}
                  </div>
                </div>

                {/* Footer - End Listening & End Call buttons */}
                <div className="call-footer">
                  {/* ✨ NEW: Stop Listening Button (only when listening) */}
                  {isListening && (
                    <button 
                      className="btn-stop-listening"
                      onClick={handleStopListening}
                      style={{
                        backgroundColor: '#ff9800',
                        color: 'white',
                        border: 'none',
                        borderRadius: '25px',
                        padding: '12px 24px',
                        fontSize: '16px',
                        fontWeight: '600',
                        cursor: 'pointer',
                        marginRight: '12px',
                        boxShadow: '0 2px 8px rgba(255, 152, 0, 0.3)',
                        transition: 'all 0.2s ease',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}
                      onMouseEnter={(e) => {
                        e.target.style.transform = 'scale(1.05)';
                        e.target.style.boxShadow = '0 4px 12px rgba(255, 152, 0, 0.4)';
                      }}
                      onMouseLeave={(e) => {
                        e.target.style.transform = 'scale(1)';
                        e.target.style.boxShadow = '0 2px 8px rgba(255, 152, 0, 0.3)';
                      }}
                    >
                      <span>⏸️</span>
                      <span>Stop Listening</span>
                    </button>
                  )}
                  
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
