import React from 'react';

export default function Input({ label, ...props }) {
  return (
    <label className="input-label">
      {label}
      <input className="input-field" {...props} />
    </label>
  );
}
