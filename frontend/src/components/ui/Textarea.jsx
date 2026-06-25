import React from 'react';

export default function Textarea({ label, ...props }) {
  return (
    <label className="textarea-label">
      {label}
      <textarea className="textarea-field" {...props} />
    </label>
  );
}
