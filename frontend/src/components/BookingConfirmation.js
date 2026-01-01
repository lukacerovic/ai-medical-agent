import React from 'react';

const BookingConfirmation = ({ booking, onClose }) => {
  if (!booking) return null;

  return (
    <div className="confirmation-overlay">
      <div className="confirmation-card">
        <div className="confirmation-header">
          <h3>✓ Booking Confirmed!</h3>
        </div>
        <div className="confirmation-details">
          <p>
            <strong>Service:</strong> {booking.service}
          </p>
          <p>
            <strong>Date:</strong> {booking.date}
          </p>
          <p>
            <strong>Time:</strong> {booking.time}
          </p>
          {booking.notes && (
            <p>
              <strong>Notes:</strong> {booking.notes}
            </p>
          )}
        </div>
        <button
          className="btn-primary"
          onClick={onClose}
        >
          Done
        </button>
      </div>
    </div>
  );
};

export default BookingConfirmation;
