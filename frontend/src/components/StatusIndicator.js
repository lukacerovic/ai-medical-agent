import React from 'react';

const StatusIndicator = ({ status }) => {
  const statusMessages = {
    idle: 'Ready to chat',
    listening: 'Listening...',
    thinking: 'Thinking...',
    speaking: 'Speaking...'
  };

  const statusColors = {
    idle: '#95a5a6',
    listening: '#e74c3c',
    thinking: '#f39c12',
    speaking: '#27ae60'
  };

  return (
    <div className="status-indicator">
      <div
        className="status-dot"
        style={{ backgroundColor: statusColors[status] }}
      />
      <span className="status-text">{statusMessages[status]}</span>
    </div>
  );
};

export default StatusIndicator;
