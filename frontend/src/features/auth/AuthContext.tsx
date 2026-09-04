import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import { api, tokenStorage } from '@/api/client'
import type { Usuario } from '@/types'

interface AuthState {
  usuario: Usuario | null
  cargando: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null)
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    if (!tokenStorage.get()) {
      setCargando(false)
      return
    }
    api
      .get<Usuario>('/auth/me')
      .then((r) => setUsuario(r.data))
      .catch(() => tokenStorage.clear())
      .finally(() => setCargando(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    // OAuth2PasswordRequestForm espera form-urlencoded con username/password.
    const body = new URLSearchParams({ username: email, password })
    const { data } = await api.post('/auth/login', body, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    tokenStorage.set(data.access_token)
    setUsuario(data.usuario)
  }, [])

  const logout = useCallback(() => {
    tokenStorage.clear()
    setUsuario(null)
  }, [])

  const value = useMemo(
    () => ({ usuario, cargando, login, logout }),
    [usuario, cargando, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider')
  return ctx
}
