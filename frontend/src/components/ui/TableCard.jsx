import React from 'react';
import Card from './Card';

export default function TableCard({ title, children }) {
  return (
    <Card className="table-card">
      <h3>{title}</h3>
      {children}
    </Card>
  );
}
