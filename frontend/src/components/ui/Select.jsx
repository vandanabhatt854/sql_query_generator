import React from 'react';

export default function Select({ label, options = [], ...props }) {
  return (
    <label className="select-label">
      {label}
      <select className="select-field" {...props}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
