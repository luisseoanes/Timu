import axios from 'axios'
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import { api } from '@/api/client'
import { esErrorPasajero } from '@/lib/errores'
import type { Sesion, Usuario } from '@/types'

/** Esperas entre intentos cuando el backend no pudo contestar si hay sesión. */
const ESPERAS_SESION_MS = [1000, 3000, 9000]
/** Tope para un Retry-After largo: la ventana del limitador puede pedir hasta 60 s. */
const ESPERA_MAXIMA_MS = 15000

const dormir = (ms: number) => new Promise((r) => setTimeout(r, ms))

function esperaPedida(error: unknown): number | null {
  if (!axios.isAxiosError(error)) return null
  const segundos = Number(error.response?.headers?.['retry-after'])
  return Number.isFinite(segundos) && segundos > 0 ? segundos * 1000 : null
}

/**
 * Pregunta al backend si hay sesión. Un 429 (límite de peticiones), un 5xx o la red caída
 * no dicen nada de la sesión, así que se reintenta; una respuesta firme (401) es que no la
 * hay. Devuelve `error` si tras los reintentos sigue sin respuesta.
 */
async function comprobarSesion(sigue: () => boolean): Promise<{ usuario: Usuario | null; error?: unknown }> {
  for (let intento = 0; ; intento++) {
    try {
      return { usuario: (await api.get<Usuario>('/auth/me')).data }
    } catch (error) {
      // Una respuesta firme (401, o cualquier 4xx que no sea pasajero) es «sin sesión».
      if (!esErrorPasajero(error)) return { usuario: null }
      const espera = ESPERAS_SESION_MS[intento]
      if (espera === undefined || !sigue()) return { usuario: null, error }
      await dormir(Math.min(esperaPedida(error) ?? espera, ESPERA_MAXIMA_MS))
      if (!sigue()) return { usuario: null, error }
    }
  }
}

interface AuthState {
  usuario: Usuario | null
  cargando: boolean
  /** No se pudo comprobar la sesión (no es que no la haya): se ofrece reintentar. */
  errorSesion: boolean
  reintentarSesion: () => void
  login: (email: string, password: string) => Promise<Usuario>
  /** Ingreso del portal: celular más el código que llegó por WhatsApp (F3-POR-07). */
  ingresarConCodigo: (telefono: string, codigo: string) => Promise<Usuario>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null)
  const [cargando, setCargando] = useState(true)
  const [errorSesion, setErrorSesion] = useState(false)
  const [intentos, setIntentos] = useState(0)

  // Con cookie httpOnly el frontend no puede inspeccionar la sesión: la única
  // forma de saber si sigue viva es preguntárselo al backend.
  useEffect(() => {
    let vigente = true
    comprobarSesion(() => vigente).then(({ usuario: u, error }) => {
      if (!vigente) return
      setUsuario(u)
      setErrorSesion(error !== undefined)
      setCargando(false)
    })
    return () => {
      vigente = false
    }
  }, [intentos])

  const reintentarSesion = useCallback(() => {
    setCargando(true)
    setErrorSesion(false)
    setIntentos((n) => n + 1)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    // OAuth2PasswordRequestForm espera form-urlencoded con username/password.
    const body = new URLSearchParams({ username: email, password })
    const { data } = await api.post('/auth/login', body, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    setUsuario(data.usuario)
    setErrorSesion(false)
    return data.usuario as Usuario
  }, [])

  const ingresarConCodigo = useCallback(async (telefono: string, codigo: string) => {
    const { data } = await api.post<Sesion>('/auth/codigo/verificacion', { telefono, codigo })
    setUsuario(data.usuario)
    setErrorSesion(false)
    return data.usuario
  }, [])

  const logout = useCallback(async () => {
    await api.post('/auth/logout').catch(() => undefined)
    setUsuario(null)
  }, [])

  const value = useMemo(
    () => ({ usuario, cargando, errorSesion, reintentarSesion, login, ingresarConCodigo, logout }),
    [usuario, cargando, errorSesion, reintentarSesion, login, ingresarConCodigo, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider')
  return ctx
}
