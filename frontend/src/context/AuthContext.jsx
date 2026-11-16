import React, { createContext, useEffect, useState } from 'react';
import api from '../services/api';
export const AuthContext = createContext(null);
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => { let active = true; api.get('/auth/me').then(({data}) => { if(active) setUser(data.user); }).catch(() => {}).finally(() => { if(active) setLoading(false); }); return () => { active=false; }; }, []);
  async function signIn(credentials) { const {data} = await api.post('/auth/login', credentials); setUser(data.user); }
  async function signUp(credentials) { const {data} = await api.post('/auth/register', credentials); setUser(data.user); }
  async function signOut() { await api.post('/auth/logout'); setUser(null); }
  return <AuthContext.Provider value={{user, loading, isAuthenticated: !!user, signIn, signUp, signOut}}>{children}</AuthContext.Provider>;
}
