import * as Tabs from '@radix-ui/react-tabs'
import { isAxiosError } from 'axios'
import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

import { api } from '@/api/client'
import { Icono } from '@/components/Icono'
import { mensajeError } from '@/lib/errores'
import { inicioDeRol } from '@/lib/permisos'
import type { Usuario } from '@/types'

import { AccesoLayout, MarcaTimu } from './AccesoLayout'
import { useAuth } from './AuthContext'

/**
 * Ingreso. El equipo entra con correo y contraseña; las familias afiliadas, con su
 * celular y un código que les llega por WhatsApp, sin contraseña que recordar.
 */
export function LoginPage() {
  const { usuario, cargando } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  if (!cargando && usuario) return <Navigate to={inicioDeRol(usuario.rol)} replace />

  function entrar(usuario: Usuario) {
    const desde = (location.state as { from?: string } | null)?.from
    navigate(desde ?? inicioDeRol(usuario.rol), { replace: true })
  }

  return (
    <AccesoLayout>
      <div className="ingreso-panel">
        <MarcaTimu />
        <div className="ingreso-titulo">
          <h1>Bienvenido de nuevo</h1>
          <p>Ingresa para gestionar visitas, historias clínicas y afiliaciones.</p>
        </div>

        <Tabs.Root defaultValue="equipo" className="ingreso-form">
          <Tabs.List className="segmento" aria-label="Tipo de ingreso">
            <Tabs.Trigger value="equipo" className="segmento-opcion">
              <Icono nombre="clinica" size={16} /> Equipo TIMU
            </Tabs.Trigger>
            <Tabs.Trigger value="familia" className="segmento-opcion">
              <Icono nombre="huella" size={16} /> Familias
            </Tabs.Trigger>
          </Tabs.List>
          <Tabs.Content value="equipo">
            <IngresoEquipo onEntrar={entrar} />
          </Tabs.Content>
          <Tabs.Content value="familia">
            <IngresoFamilia onEntrar={entrar} />
          </Tabs.Content>
        </Tabs.Root>

        <p className="ingreso-pie">
          <Icono nombre="escudo" size={16} /> Conexión cifrada · tu sesión vive sólo en este navegador
        </p>
      </div>
    </AccesoLayout>
  )
}

function IngresoEquipo({ onEntrar }: { onEntrar: (u: Usuario) => void }) {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [visible, setVisible] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setEnviando(true)
    setError(null)
    try {
      onEntrar(await login(email, password))
    } catch (err) {
      // 401 es credenciales: se dice en palabras propias. Bloqueo o caída, con su causa.
      setError(
        isAxiosError(err) && err.response?.status === 401
          ? 'El correo o la contraseña no coinciden. Intenta de nuevo.'
          : mensajeError(err, 'No fue posible ingresar. Intenta de nuevo en un momento.'),
      )
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form className="ingreso-form" onSubmit={onSubmit}>
      <label className="campo">
        <span>Correo</span>
        <span className="campo-adorno">
          <Icono nombre="correo" size={18} />
          <input
            className="input"
            type="email"
            autoComplete="username"
            placeholder="nombre@timu.co"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </span>
      </label>

      <label className="campo">
        <span>Contraseña</span>
        <span className="campo-adorno">
          <Icono nombre="candado" size={18} />
          <input
            className="input"
            type={visible ? 'text' : 'password'}
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button
            type="button"
            className="campo-accion"
            aria-label={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}
            aria-pressed={visible}
            onClick={() => setVisible((v) => !v)}
          >
            <Icono nombre={visible ? 'ojo-cerrado' : 'ojo'} size={18} />
          </button>
        </span>
      </label>

      <div className="ingreso-ayuda">
        <Link to="/recuperar">¿Olvidaste tu contraseña?</Link>
      </div>

      {error && (
        <p className="aviso-error" role="alert">
          {error}
        </p>
      )}

      <button className="btn btn-primario btn-bloque btn-grande" type="submit" disabled={enviando}>
        {enviando ? 'Ingresando…' : 'Ingresar'}
      </button>
    </form>
  )
}

function IngresoFamilia({ onEntrar }: { onEntrar: (u: Usuario) => void }) {
  const { ingresarConCodigo } = useAuth()
  const [telefono, setTelefono] = useState('')
  const [codigo, setCodigo] = useState('')
  const [enviado, setEnviado] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function pedirCodigo(e: React.FormEvent) {
    e.preventDefault()
    setEnviando(true)
    setError(null)
    try {
      await api.post('/auth/codigo', { telefono })
      setEnviado(true)
    } catch (err) {
      setError(mensajeError(err, 'No pudimos enviar el código. Revisa el número e intenta de nuevo.'))
    } finally {
      setEnviando(false)
    }
  }

  async function verificar(e: React.FormEvent) {
    e.preventDefault()
    setEnviando(true)
    setError(null)
    try {
      onEntrar(await ingresarConCodigo(telefono, codigo))
    } catch (err) {
      setError(mensajeError(err, 'El código no es válido o ya venció. Pide uno nuevo.'))
    } finally {
      setEnviando(false)
    }
  }

  if (!enviado) {
    return (
      <form className="ingreso-form" onSubmit={pedirCodigo}>
        <label className="campo">
          <span>Celular registrado</span>
          <span className="campo-adorno">
            <Icono nombre="telefono" size={18} />
            <input
              className="input"
              type="tel"
              inputMode="tel"
              autoComplete="tel"
              placeholder="300 123 4567"
              value={telefono}
              onChange={(e) => setTelefono(e.target.value)}
              required
            />
          </span>
        </label>
        <p className="apagado">Te enviaremos un código de un solo uso por WhatsApp.</p>
        {error && (
          <p className="aviso-error" role="alert">
            {error}
          </p>
        )}
        <button className="btn btn-primario btn-bloque btn-grande" type="submit" disabled={enviando}>
          {enviando ? 'Enviando…' : 'Recibir código'}
        </button>
      </form>
    )
  }

  return (
    <form className="ingreso-form" onSubmit={verificar}>
      <p className="aviso-ok" role="status">
        <Icono nombre="mensaje" size={16} /> Enviamos un código por WhatsApp al {telefono}.
      </p>
      <label className="campo">
        <span>Código</span>
        <input
          className="input codigo-input"
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={6}
          value={codigo}
          onChange={(e) => setCodigo(e.target.value.replace(/\D/g, ''))}
          required
        />
      </label>
      {error && (
        <p className="aviso-error" role="alert">
          {error}
        </p>
      )}
      <button className="btn btn-primario btn-bloque btn-grande" type="submit" disabled={enviando}>
        {enviando ? 'Verificando…' : 'Entrar al portal'}
      </button>
      <button
        className="btn btn-plano"
        type="button"
        onClick={() => {
          setEnviado(false)
          setCodigo('')
          setError(null)
        }}
      >
        Cambiar número
      </button>
    </form>
  )
}
