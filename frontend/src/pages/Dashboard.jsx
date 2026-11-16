import React from 'react';
import {Link} from 'react-router-dom';
import useAuth from '../hooks/useAuth';
export default function Dashboard(){const {user}=useAuth();return <main className="utility-page"><section className="panel utility-card"><h1>Welcome, {user.name}</h1><p>Ask a database question in English, review the SQL, then execute it.</p><div className="demo-nav"><Link to="/">Generate a query</Link><Link to="/history">View history</Link><Link to="/schema">Explore the schema</Link></div></section></main>;}
