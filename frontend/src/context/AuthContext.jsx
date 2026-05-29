import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

const TOKEN_KEY = 'la_token'
const PROFESSOR_KEY = 'la_professor'

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY))
  const [professor, setProfessor] = useState(() => {
    try { return JSON.parse(localStorage.getItem(PROFESSOR_KEY)) } catch { return null }
  })
  const [loading, setLoading] = useState(false)

  const login = useCallback((accessToken, professorData) => {
    localStorage.setItem(TOKEN_KEY, accessToken)
    localStorage.setItem(PROFESSOR_KEY, JSON.stringify(professorData))
    setToken(accessToken)
    setProfessor(professorData)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(PROFESSOR_KEY)
    setToken(null)
    setProfessor(null)
  }, [])

  // Valida token ao iniciar — descarta se expirado
  useEffect(() => {
    if (!token) return
    setLoading(true)
    api.get('/auth/me', { headers: { Authorization: `Bearer ${token}` } })
      .then(({ data }) => setProfessor(data))
      .catch(() => logout())
      .finally(() => setLoading(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <AuthContext.Provider value={{ professor, token, login, logout, loading, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth deve ser usado dentro de AuthProvider')
  return ctx
}
