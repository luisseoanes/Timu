import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import { api } from '@/api/client'
import type { Sesion, Usuario } from '@/types'

interface AuthState {
  usuario: Usuario | null
  cargando: boolean
  login: (email: string, password: string) => Promise<Usuario>
  /** Ingreso del portal: celular más el código que llegó por WhatsApp (F3-POR-07). */
  ingresarConCodigo: (telefono: string, codigo: string) => Promise<Usuario>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null)
  const [cargando, setCargando] = useState(true)

  // Con cookie httpOnly el frontend no puede inspeccionar la sesión: la única
  // forma de saber si sigue viva es preguntárselo al backend.
  useEffect(() => {
    api
      .get<Usuario>('/auth/me')
      .then((r) => setUsuario(r.data))
      .catch(() => setUsuario(null))
      .finally(() => setCargando(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    // OAuth2PasswordRequestForm espera form-urlencoded con username/password.
    const body = new URLSearchParams({ username: email, password })
    const { data } = await api.post('/auth/login', body, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    setUsuario(data.usuario)
    return data.usuario as Usuario
  }, [])

  const ingresarConCodigo = useCallback(async (telefono: string, codigo: string) => {
    const { data } = await api.post<Sesion>('/auth/codigo/verificacion', { telefono, codigo })
    setUsuario(data.usuario)
    return data.usuario
  }, [])

  const logout = useCallback(async () => {
    await api.post('/auth/logout').catch(() => undefined)
    setUsuario(null)
  }, [])

  const value = useMemo(
    () => ({ usuario, cargando, login, ingresarConCodigo, logout }),
    [usuario, cargando, login, ingresarConCodigo, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider')
  return ctx
}
