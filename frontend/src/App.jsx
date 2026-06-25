import React from 'react'
import AppRoutes from './routes/AppRoutes'
import { AuthProvider } from './context/AuthContext'
import { QueryProvider } from './context/QueryContext'
import { ThemeProvider } from './context/ThemeContext'
import './styles/index.css'

export default function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <QueryProvider>
          <AppRoutes />
        </QueryProvider>
      </ThemeProvider>
    </AuthProvider>
  )
}
