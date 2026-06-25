'use client'

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { api } from './api'

export type User = {
  id: number
  username: string
  email: string
  phone?: string
  role: string
}

type AuthContextType = {
  user: User | null
  token: string | null
  isLoggedIn: boolean
  isSeller: boolean
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string, isSeller?: boolean, phone?: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loaded, setLoaded] = useState(false)
  const router = useRouter()

  useEffect(() => {
    const t = localStorage.getItem('ikobiz_token')
    if (t) {
      setToken(t)
      const u = localStorage.getItem('ikobiz_user')
      if (u) {
        try { setUser(JSON.parse(u)) } catch { /* ignore */ }
      }
    }
    setLoaded(true)
  }, [])

  useEffect(() => {
    if (loaded && token && !user) {
      api.get('/auth/me', true).then(u => {
        setUser(u)
        localStorage.setItem('ikobiz_user', JSON.stringify(u))
      }).catch(() => logout())
    }
  }, [loaded, token])

  const login = useCallback(async (username: string, password: string) => {
    const data = await api.post('/auth/login', { username, password })
    localStorage.setItem('ikobiz_token', data.access_token)
    setToken(data.access_token)
    const u = await api.get('/auth/me', true)
    setUser(u)
    localStorage.setItem('ikobiz_user', JSON.stringify(u))
  }, [])

  const register = useCallback(async (username: string, email: string, password: string, isSeller = false, phone?: string) => {
    const body: Record<string, unknown> = { username, email, password, is_seller: isSeller }
    if (phone) body.phone = phone
    await api.post('/auth/register', body)
    await login(username, password)
  }, [login])

  const logout = useCallback(() => {
    localStorage.removeItem('ikobiz_token')
    localStorage.removeItem('ikobiz_user')
    setToken(null)
    setUser(null)
    router.push('/auth/login')
  }, [router])

  const refreshUser = useCallback(async () => {
    try {
      const u = await api.get('/auth/me', true)
      setUser(u)
      localStorage.setItem('ikobiz_user', JSON.stringify(u))
    } catch { /* ignore */ }
  }, [])

  return (
    <AuthContext.Provider value={{
      user, token, isLoggedIn: !!token, isSeller: !!(user && (user.role === 'seller' || user.role === 'admin')),
      login, register, logout, refreshUser,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
