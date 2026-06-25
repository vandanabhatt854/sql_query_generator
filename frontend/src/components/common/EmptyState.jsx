import React from 'react';

export default function EmptyState({ title, description }) {
  return (
    <div className="empty-state">
      <h2>{title || 'No data available'}</h2>
      <p>{description || 'Try adjusting your filters or refresh the page.'}</p>
    </div>
  );
}
