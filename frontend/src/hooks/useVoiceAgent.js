import { useRef, useCallback, useState } from 'react';

const useVoiceAgent = (sessionId, onResponseReceived, onStatusChange) => {
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);
  const recordingTimerRef = useRef(null);
  const vadTimerRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const [isRecording, setIsRecording] = useState(false);

  // VAD Configuration
  const VAD_CONFIG = {
    SILENCE_THRESHOLD: 0.01,      // Volume threshold (0-1, lower = more sensitive)
    SILENCE_DURATION: 1500,       // Milliseconds of silence before auto-stop (1.5 seconds)
    MIN_SPEECH_DURATION: 500,     // Minimum milliseconds of speech before VAD activates
    CHECK_INTERVAL: 100,          // How often to check audio level (ms)
    MAX_RECORDING_TIME: 30000,    // Maximum recording time (30 seconds)
  };

  const startVoiceCall = useCallback(async () => {
    try {
      console.log('\n' + '='.repeat(80));
      console.log('🎤 [VAD] Starting Voice Activity Detection...');
      console.log('='.repeat(80));
      
      onStatusChange('listening');

      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        } 
      });
      streamRef.current = stream;
      console.log('✅ [VAD] Microphone access granted');

      // Setup Audio Context for VAD
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      analyserRef.current.fftSize = 512;
      
      console.log('✅ [VAD] Audio analyzer initialized');
      console.log(`🎯 [VAD] Silence threshold: ${VAD_CONFIG.SILENCE_THRESHOLD}`);
      console.log(`⏱️ [VAD] Auto-stop after ${VAD_CONFIG.SILENCE_DURATION}ms of silence`);

      // Create MediaRecorder
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];
      let speechStartTime = null;
      let lastSpeechTime = Date.now();

      // Collect audio chunks
      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
          console.log(`📦 [VAD] Audio chunk: ${e.data.size} bytes`);
        }
      };

      // When recording stops, send to backend
      mediaRecorderRef.current.onstop = async () => {
        console.log('\n' + '-'.repeat(80));
        console.log('📍 [VAD] Recording stopped');
        console.log(`📊 [VAD] Total chunks: ${audioChunksRef.current.length}`);
        console.log('-'.repeat(80) + '\n');
        
        // Clean up VAD timer
        if (vadTimerRef.current) {
          clearInterval(vadTimerRef.current);
          vadTimerRef.current = null;
        }
        
        // Clean up audio context
        if (audioContextRef.current) {
          audioContextRef.current.close();
          audioContextRef.current = null;
          analyserRef.current = null;
        }
        
        if (audioChunksRef.current.length > 0) {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
          console.log(`🎵 [VAD] Sending ${audioBlob.size} bytes to backend`);
          await sendAudioToBackend(audioBlob, sessionId, onStatusChange, onResponseReceived);
        } else {
          console.warn('⚠️ [VAD] No audio recorded!');
          onStatusChange('idle');
        }
        
        // Clean up stream
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => {
            track.stop();
            console.log('🚫 [VAD] Track stopped:', track.kind);
          });
          streamRef.current = null;
        }
      };

      // Start recording
      mediaRecorderRef.current.start(100); // Collect data every 100ms
      setIsRecording(true);
      console.log('▶️ [VAD] Recording started');
      console.log('='.repeat(80) + '\n');

      // 🎯 SMART VAD: Monitor audio levels
      vadTimerRef.current = setInterval(() => {
        if (!analyserRef.current) return;

        const bufferLength = analyserRef.current.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyserRef.current.getByteFrequencyData(dataArray);

        // Calculate average volume (0-1)
        const average = dataArray.reduce((a, b) => a + b, 0) / bufferLength / 255;

        const isSpeaking = average > VAD_CONFIG.SILENCE_THRESHOLD;

        if (isSpeaking) {
          if (!speechStartTime) {
            speechStartTime = Date.now();
            console.log('🗣️ [VAD] Speech detected!');
          }
          lastSpeechTime = Date.now();
        } else {
          // Check if we've had enough speech before checking for silence
          const speechDuration = speechStartTime ? Date.now() - speechStartTime : 0;
          
          if (speechDuration >= VAD_CONFIG.MIN_SPEECH_DURATION) {
            const silenceDuration = Date.now() - lastSpeechTime;
            
            if (silenceDuration >= VAD_CONFIG.SILENCE_DURATION) {
              console.log('\n' + '🔴'.repeat(40));
              console.log(`⏸️ [VAD] Silence detected for ${silenceDuration}ms - auto-stopping!`);
              console.log('🔴'.repeat(40) + '\n');
              
              if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
                mediaRecorderRef.current.stop();
                setIsRecording(false);
              }
            }
          }
        }

        // Debug: Show volume level
        if (Math.random() < 0.1) { // Log 10% of the time to avoid spam
          console.log(`🔊 [VAD] Volume: ${(average * 100).toFixed(1)}% | Speaking: ${isSpeaking ? '✅' : '❌'}`);
        }
      }, VAD_CONFIG.CHECK_INTERVAL);

      // Safety: Max recording time
      recordingTimerRef.current = setTimeout(() => {
        console.log('\n' + '⚠️'.repeat(40));
        console.log(`⏰ [VAD] Maximum recording time (${VAD_CONFIG.MAX_RECORDING_TIME / 1000}s) reached`);
        console.log('⚠️'.repeat(40) + '\n');
        
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          mediaRecorderRef.current.stop();
          setIsRecording(false);
        }
      }, VAD_CONFIG.MAX_RECORDING_TIME);

    } catch (error) {
      console.error('\n' + '!'.repeat(80));
      console.error('❌ [VAD ERROR] Microphone error:', error);
      console.error('!'.repeat(80) + '\n');
      onStatusChange('error');
    }
  }, [sessionId, onStatusChange, onResponseReceived, VAD_CONFIG]);

  const stopVoiceCall = useCallback(() => {
    console.log('\n' + '-'.repeat(80));
    console.log('🛑 [VAD] Manually stopping recording...');
    
    // Clear timers
    if (recordingTimerRef.current) {
      clearTimeout(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
    
    if (vadTimerRef.current) {
      clearInterval(vadTimerRef.current);
      vadTimerRef.current = null;
    }
    
    // Stop recording
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      console.log('✅ [VAD] Recording stopped');
    }
    
    // Clean up audio context
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
      analyserRef.current = null;
    }
    
    // Stop all tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => {
        track.stop();
        console.log('🚫 [VAD] Track stopped:', track.kind);
      });
      streamRef.current = null;
    }
    
    console.log('-'.repeat(80) + '\n');
  }, []);

  return {
    startVoiceCall,
    stopVoiceCall,
    isRecording
  };
};

const sendAudioToBackend = async (audioBlob, sessionId, onStatusChange, onResponseReceived) => {
  try {
    console.log('\n' + '='.repeat(80));
    console.log('📤 [BACKEND] Sending audio to backend...');
    console.log('='.repeat(80));
    
    const formData = new FormData();
    formData.append('audio', audioBlob, 'audio.wav');
    formData.append('session_id', sessionId);

    console.log(`📦 [BACKEND] Audio size: ${audioBlob.size} bytes`);
    console.log(`🎫 [BACKEND] Session ID: ${sessionId}`);
    
    onStatusChange('thinking');

    const response = await fetch(
      `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/transcribe`,
      {
        method: 'POST',
        body: formData
      }
    );

    const data = await response.json();
    console.log(`📝 [BACKEND] Transcription: "${data.text}"`);
    console.log('='.repeat(80) + '\n');

    if (data.text && data.text.trim().length > 0) {
      await sendTextMessage(data.text, sessionId, onStatusChange, onResponseReceived);
    } else {
      console.warn('⚠️ [BACKEND] Empty transcription');
      onStatusChange('idle');
    }

  } catch (error) {
    console.error('\n' + '!'.repeat(80));
    console.error('❌ [BACKEND ERROR]:', error);
    console.error('!'.repeat(80) + '\n');
    onStatusChange('error');
  }
};

const sendTextMessage = async (text, sessionId, onStatusChange, onResponseReceived) => {
  try {
    console.log('\n' + '='.repeat(80));
    console.log('💬 [CHAT] Sending to AI...');
    console.log('='.repeat(80));
    console.log(`📝 [CHAT] Message: "${text}"`);
    
    const response = await fetch(
      `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/chat`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, text })
      }
    );

    const data = await response.json();
    console.log(`🤖 [CHAT] AI: "${data.assistant_response}"`);
    console.log('='.repeat(80) + '\n');

    if (data.assistant_response) {
      console.log('✅ [CHAT] Passing to App.js for TTS');
      onResponseReceived(data.assistant_response);
      onStatusChange('idle');
    }

  } catch (error) {
    console.error('\n' + '!'.repeat(80));
    console.error('❌ [CHAT ERROR]:', error);
    console.error('!'.repeat(80) + '\n');
    onStatusChange('error');
  }
};

export default useVoiceAgent;
