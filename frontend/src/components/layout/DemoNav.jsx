import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import useAuth from '../../hooks/useAuth';
export default function DemoNav() {
 const {user,signOut}=useAuth(); const navigate=useNavigate();
 const [error,setError]=React.useState('');
 return <><nav className="demo-nav" aria-label="Main navigation"><NavLink to="/">Query Generator</NavLink><NavLink to="/history">History</NavLink><NavLink to="/schema">Database Schema</NavLink>{user ? <><NavLink to="/profile">{user.name}</NavLink><button onClick={async()=>{try{await signOut();navigate('/');}catch{setError('Could not sign out. Please try again.');}}}>Sign out</button></> : <NavLink to="/login">Sign in</NavLink>}</nav>{error && <p role="alert" className="error-banner">{error}</p>}</>;
}
