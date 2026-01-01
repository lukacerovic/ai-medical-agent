import { useRef, useCallback, useState } from 'react';

const useVoiceAgent = (sessionId, onResponseReceived, onStatusChange) => {
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const [isRecording, setIsRecording] = useState(false);

  const startVoiceCall = useCallback(async () => {
    try {
      console.log('Starting voice call...');
      onStatusChange('listening');

      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      console.log('✓ Microphone access granted');

      // Create MediaRecorder
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      // Collect audio chunks
      mediaRecorderRef.current.ondataavailable = (e) => {
        audioChunksRef.current.push(e.data);
      };

      // When recording stops, send to backend
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await sendAudioToBackend(audioBlob, sessionId, onStatusChange, onResponseReceived);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);

      // Auto-stop after 10 seconds (or user clicks stop)
      setTimeout(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          mediaRecorderRef.current.stop();
          setIsRecording(false);
        }
      }, 10000);

    } catch (error) {
      console.error('Microphone error:', error);
      onStatusChange('error');
    }
  }, [sessionId, onStatusChange, onResponseReceived]);

  const stopVoiceCall = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, []);

  return {
    startVoiceCall,
    stopVoiceCall,
    isRecording
  };
};

const sendAudioToBackend = async (audioBlob, sessionId, onStatusChange, onResponseReceived) => {
  try {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'audio.wav');
    formData.append('session_id', sessionId);

    console.log('Sending audio to backend...');
    onStatusChange('thinking');

    const response = await fetch(
      `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/transcribe`,
      {
        method: 'POST',
        body: formData
      }
    );

    const data = await response.json();
    console.log('Transcription:', data);

    if (data.text) {
      // Got transcription, now send as text message
      await sendTextMessage(data.text, sessionId, onStatusChange, onResponseReceived);
    }

  } catch (error) {
    console.error('Audio send error:', error);
    onStatusChange('error');
  }
};

const sendTextMessage = async (text, sessionId, onStatusChange, onResponseReceived) => {
  try {
    const response = await fetch(
      `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/chat`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, text })
      }
    );

    const data = await response.json();
    console.log('AI Response:', data);

    if (data.assistant_response) {
      onResponseReceived(data.assistant_response);
      
      // Play audio response
      await playAudioResponse(data.assistant_response);
      
      onStatusChange('idle');
    }

  } catch (error) {
    console.error('Chat error:', error);
    onStatusChange('error');
  }
};

const playAudioResponse = async (text) => {
  try {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;
    
    return new Promise((resolve) => {
      utterance.onend = resolve;
      window.speechSynthesis.speak(utterance);
    });
  } catch (error) {
    console.error('Audio playback error:', error);
  }
};

export default useVoiceAgent;
