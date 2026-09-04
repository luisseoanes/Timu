import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { Icono } from '@/components/Icono'

import { useAuth } from './AuthContext'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setEnviando(true)
    setError(null)
    try {
      await login(email, password)
      const destino = (location.state as { from?: string } | null)?.from ?? '/'
      navigate(destino, { replace: true })
    } catch {
      setError('El correo o la contraseña no coinciden. Intenta de nuevo.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="login">
      <div className="login-tarjeta">
        <aside className="login-lado">
          <h2>Bienvenido</h2>
          <div className="login-arte" aria-hidden="true">
            <IlustracionPanel />
          </div>
          <p className="pie">Plataforma de gestión y operación TIMU</p>
        </aside>

        <form className="login-form" onSubmit={onSubmit}>
          <h1>Ingresar</h1>

          <label className="campo campo-icono">
            <span>Correo</span>
            <input
              className="input input-linea"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Icono nombre="usuario" size={18} />
          </label>

          <label className="campo campo-icono">
            <span>Contraseña</span>
            <input
              className="input input-linea"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <Icono nombre="llave" size={18} />
          </label>

          {error && <p className="error">{error}</p>}

          <button className="btn btn-primario btn-bloque" type="submit" disabled={enviando}>
            {enviando ? 'Ingresando…' : 'Ingresar'}
          </button>

          <div className="login-pie">
            <a href="#recuperar">Olvidé mi contraseña</a>
            <a href="#ayuda">Ayuda</a>
          </div>
        </form>
      </div>
    </div>
  )
}

/** Ilustración plana del panel, en la línea isométrica de la referencia. */
function IlustracionPanel() {
  return (
    <svg width="200" height="180" viewBox="0 0 200 180" fill="none">
      <ellipse cx="100" cy="150" rx="78" ry="14" fill="#ffffff" opacity=".16" />
      <rect x="46" y="26" width="108" height="112" rx="14" fill="#ffffff" opacity=".95" />
      <rect x="60" y="42" width="52" height="7" rx="3.5" fill="var(--verde-500)" opacity=".5" />
      <rect x="60" y="58" width="80" height="5" rx="2.5" fill="var(--apagado)" opacity=".35" />
      <rect x="60" y="96" width="14" height="28" rx="4" fill="var(--verde-400)" />
      <rect x="82" y="82" width="14" height="42" rx="4" fill="var(--verde-500)" />
      <rect x="104" y="90" width="14" height="34" rx="4" fill="var(--verde-300)" />
      <rect x="126" y="72" width="14" height="52" rx="4" fill="var(--verde-600)" />
      <circle cx="152" cy="40" r="16" fill="#ffffff" opacity=".9" />
      <path d="M146 40.5l4.5 4.5 8-9" stroke="var(--verde-600)" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
