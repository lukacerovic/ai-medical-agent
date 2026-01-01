import React, { useState, useRef, useEffect } from 'react';

const Transcript = ({ messages, onSendMessage }) => {
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isSending) {
      setIsSending(true);
      onSendMessage(input);
      setInput('');
      setTimeout(() => setIsSending(false), 1000);
    }
  };

  return (
    <div className="transcript-container">
      <div className="messages">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`message ${msg.role}`}
          >
            <div className="message-content">
              {msg.text}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={isSending}
          className="message-input"
        />
        <button
          type="submit"
          disabled={isSending || !input.trim()}
          className="send-button"
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default Transcript;
