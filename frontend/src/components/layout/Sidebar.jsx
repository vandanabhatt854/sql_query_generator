import React from 'react';
import { NavLink } from 'react-router-dom';

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <NavLink to="/dashboard">Dashboard</NavLink>
      <NavLink to="/query-generator">Query Generator</NavLink>
      <NavLink to="/history">History</NavLink>
    </aside>
  );
}
