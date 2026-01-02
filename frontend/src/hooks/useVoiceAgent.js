import { useRef, useCallback, useState } from 'react';

const useVoiceAgent = (sessionId, onResponseReceived, onStatusChange) => {
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);
  const recordingTimerRef = useRef(null);
  const [isRecording, setIsRecording] = useState(false);

  const startVoiceCall = useCallback(async () => {
    try {
      console.log('\n' + '='.repeat(80));
      console.log('🎤 [MIC] Starting microphone recording...');
      console.log('='.repeat(80));
      
      onStatusChange('listening');

      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });
      streamRef.current = stream;
      console.log('✅ [MIC] Microphone access granted with echo cancellation');

      // Create MediaRecorder
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      // Collect audio chunks
      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
          console.log(`📦 [MIC] Audio chunk received: ${e.data.size} bytes`);
        }
      };

      // When recording stops, send to backend
      mediaRecorderRef.current.onstop = async () => {
        console.log('📎 [MIC] Recording stopped');
        console.log(`📊 [MIC] Total chunks: ${audioChunksRef.current.length}`);
        console.log('='.repeat(80) + '\n');
        
        if (audioChunksRef.current.length > 0) {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
          console.log(`🎵 [MIC] Audio blob size: ${audioBlob.size} bytes`);
          await sendAudioToBackend(audioBlob, sessionId, onStatusChange, onResponseReceived);
        } else {
          console.warn('⚠️ [MIC] No audio chunks recorded!');
        }
        
        // Clean up stream
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => {
            track.stop();
            console.log('🚫 [MIC] Microphone track stopped');
          });
          streamRef.current = null;
        }
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      console.log('▶️ [MIC] Recording started (30 second max)');
      console.log('='.repeat(80) + '\n');

      // EXTENDED: Auto-stop after 30 seconds (was 10)
      recordingTimerRef.current = setTimeout(() => {
        console.log('\n' + '-'.repeat(80));
        console.log('⏰ [MIC] 30 seconds elapsed - auto-stopping recording');
        console.log('-'.repeat(80) + '\n');
        
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          mediaRecorderRef.current.stop();
          setIsRecording(false);
        }
      }, 30000); // 30 seconds

    } catch (error) {
      console.error('\n' + '!'.repeat(80));
      console.error('❌ [MIC ERROR] Microphone error:', error);
      console.error('!'.repeat(80) + '\n');
      onStatusChange('error');
    }
  }, [sessionId, onStatusChange, onResponseReceived]);

  const stopVoiceCall = useCallback(() => {
    console.log('\n' + '-'.repeat(80));
    console.log('🛑 [MIC] Manually stopping voice call...');
    
    // Clear timer
    if (recordingTimerRef.current) {
      clearTimeout(recordingTimerRef.current);
      recordingTimerRef.current = null;
      console.log('✅ [MIC] Recording timer cleared');
    }
    
    // Stop recording
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      console.log('✅ [MIC] MediaRecorder stopped');
    }
    
    // Stop all tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => {
        track.stop();
        console.log('🚫 [MIC] Track stopped:', track.kind);
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
    console.log(`📝 [BACKEND] Transcription received: "${data.text}"`);
    console.log('='.repeat(80) + '\n');

    if (data.text && data.text.trim().length > 0) {
      // Got transcription, now send as text message
      await sendTextMessage(data.text, sessionId, onStatusChange, onResponseReceived);
    } else {
      console.warn('⚠️ [BACKEND] Empty transcription received');
      onStatusChange('idle');
    }

  } catch (error) {
    console.error('\n' + '!'.repeat(80));
    console.error('❌ [BACKEND ERROR] Audio send error:', error);
    console.error('!'.repeat(80) + '\n');
    onStatusChange('error');
  }
};

const sendTextMessage = async (text, sessionId, onStatusChange, onResponseReceived) => {
  try {
    console.log('\n' + '='.repeat(80));
    console.log('💬 [CHAT] Sending text to AI...');
    console.log('='.repeat(80));
    console.log(`📝 [CHAT] User message: "${text}"`);
    console.log(`🎫 [CHAT] Session ID: ${sessionId}`);
    
    const response = await fetch(
      `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/chat`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, text })
      }
    );

    const data = await response.json();
    console.log(`🤖 [CHAT] AI response received: "${data.assistant_response}"`);
    console.log('='.repeat(80) + '\n');

    if (data.assistant_response) {
      // CRITICAL: Only call onResponseReceived - App.js handles TTS
      // DO NOT play audio here - it causes duplication!
      console.log('✅ [CHAT] Passing response to App.js (App.js will handle TTS)');
      onResponseReceived(data.assistant_response);
      onStatusChange('idle');
    }

  } catch (error) {
    console.error('\n' + '!'.repeat(80));
    console.error('❌ [CHAT ERROR] Chat error:', error);
    console.error('!'.repeat(80) + '\n');
    onStatusChange('error');
  }
};

export default useVoiceAgent;
