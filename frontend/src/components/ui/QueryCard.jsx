import React from 'react';
import Card from './Card';

export default function QueryCard({ query, description }) {
  return (
    <Card className="query-card">
      <pre>{query}</pre>
      <p>{description}</p>
    </Card>
  );
}
