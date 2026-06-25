import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from '../pages/Home';
import Login from '../pages/Login';
import Register from '../pages/Register';
import Dashboard from '../pages/Dashboard';
import QueryGenerator from '../pages/QueryGenerator';
import QueryHistory from '../pages/QueryHistory';
import QueryResults from '../pages/QueryResults';
import SchemaViewer from '../pages/SchemaViewer';
import Profile from '../pages/Profile';
import NotFound from '../pages/NotFound';
import ProtectedRoute from './ProtectedRoute';

export default function AppRoutes() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/query-generator" element={<ProtectedRoute><QueryGenerator /></ProtectedRoute>} />
        <Route path="/history" element={<ProtectedRoute><QueryHistory /></ProtectedRoute>} />
        <Route path="/results" element={<ProtectedRoute><QueryResults /></ProtectedRoute>} />
        <Route path="/schema" element={<ProtectedRoute><SchemaViewer /></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  );
}
