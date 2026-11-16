import React from 'react';
import useAuth from '../hooks/useAuth';
export default function Profile(){const {user}=useAuth();return <main className="utility-page"><section className="panel utility-card"><h1>Your account</h1><p>Name: {user.name}</p><p>Email: {user.email}</p><p>Demo data and query history are shared locally. This account does not isolate database records.</p></section></main>;}
