import React from 'react';

export default function Modal({ title, children, onClose }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <header className="modal-header">
          <h2>{title}</h2>
          <button onClick={onClose}>Close</button>
        </header>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}
