import React from 'react';
import { Navigate } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
export default function ProtectedRoute({children}) { const {loading,isAuthenticated}=useAuth(); if(loading) return <p className="utility-page">Checking session...</p>; return isAuthenticated ? children : <Navigate to="/login" replace />; }
