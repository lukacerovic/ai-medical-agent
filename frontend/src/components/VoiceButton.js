import React from 'react';

const VoiceButton = ({ onClick, disabled }) => {
  const handleClick = () => {
    console.log('VoiceButton clicked!');
    if (onClick) {
      onClick();
    }
  };

  return (
    <button
      className="voice-button"
      onClick={handleClick}
      disabled={disabled}
      type="button"
    >
      <span className="icon">🎤</span>
      <span className="text">Start Conversation</span>
    </button>
  );
};

export default VoiceButton;
