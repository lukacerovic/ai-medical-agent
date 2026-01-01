import React, { useState, useEffect } from 'react';

const Waveform = ({ isActive }) => {
  const [bars, setBars] = useState(Array(20).fill(0));

  useEffect(() => {
    if (!isActive) {
      setBars(Array(20).fill(0));
      return;
    }

    const interval = setInterval(() => {
      setBars(prev => prev.map(() => Math.random() * 100));
    }, 100);

    return () => clearInterval(interval);
  }, [isActive]);

  return (
    <div className={`waveform ${isActive ? 'active' : ''}`}>
      {bars.map((height, i) => (
        <div
          key={i}
          className="bar"
          style={{
            height: `${Math.max(10, height)}%`,
            backgroundColor: isActive ? '#32b8c6' : '#ccc'
          }}
        />
      ))}
    </div>
  );
};

export default Waveform;
