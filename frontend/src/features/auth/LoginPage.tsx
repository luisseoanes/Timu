import * as Tabs from '@radix-ui/react-tabs'
import { isAxiosError } from 'axios'
import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

import { api } from '@/api/client'
import { Icono } from '@/components/Icono'
import { mensajeError } from '@/lib/errores'
import { telefono as formatoTelefono } from '@/lib/formato'
import { inicioDeRol } from '@/lib/permisos'
import type { Usuario } from '@/types'

import { AccesoLayout } from './AccesoLayout'
import { useAuth } from './AuthContext'
import { CampoClave } from './CampoClave'

/**
 * Ingreso. El equipo (y la clínica aliada) entra con correo y contraseña; las familias, con
 * su celular y un código que les llega por WhatsApp o, si activaron su cuenta, con su
 * contraseña. Quien llega desde una ruta del portal encuentra abierta la pestaña Familias.
 */
export function LoginPage() {
  const { usuario, cargando } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const desde = (location.state as { from?: string } | null)?.from

  if (!cargando && usuario) return <Navigate to={inicioDeRol(usuario.rol)} replace />

  function entrar(usuario: Usuario) {
    navigate(desde ?? inicioDeRol(usuario.rol), { replace: true })
  }

  return (
    <AccesoLayout>
      <h1>Hola de nuevo</h1>

      <Tabs.Root defaultValue={desde?.startsWith('/portal') ? 'familia' : 'equipo'} className="ingreso-form">
        <Tabs.List className="segmento" aria-label="Quién ingresa">
          <Tabs.Trigger value="equipo" className="segmento-opcion">
            {/* Entran el equipo de TIMU y las clínicas aliadas, con correo y contraseña (DEU-6). */}
            <Icono nombre="clinica" size={16} /> Equipo y aliadas
          </Tabs.Trigger>
          <Tabs.Trigger value="familia" className="segmento-opcion">
            <Icono nombre="huella" size={16} /> Familias
          </Tabs.Trigger>
        </Tabs.List>
        <Tabs.Content value="equipo">
          <IngresoConClave etiqueta="Correo" tipo="email" ejemplo="nombre@timu.co" onEntrar={entrar} />
        </Tabs.Content>
        <Tabs.Content value="familia">
          <IngresoFamilia onEntrar={entrar} />
        </Tabs.Content>
      </Tabs.Root>
    </AccesoLayout>
  )
}

function IngresoConClave({
  etiqueta,
  tipo,
  ejemplo,
  onEntrar,
}: {
  etiqueta: string
  tipo: 'email' | 'text'
  ejemplo?: string
  onEntrar: (u: Usuario) => void
}) {
  const { login } = useAuth()
  const [identificador, setIdentificador] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setEnviando(true)
    setError(null)
    try {
      onEntrar(await login(identificador, password))
    } catch (err) {
      // 401 es credenciales: se dice en palabras propias. Bloqueo o caída, con su causa.
      setError(
        isAxiosError(err) && err.response?.status === 401
          ? `${tipo === 'email' ? 'El correo' : 'El dato'} o la contraseña no coinciden. Intenta de nuevo.`
          : mensajeError(err, 'No fue posible ingresar. Intenta de nuevo en un momento.'),
      )
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form className="ingreso-form" onSubmit={onSubmit}>
      <div className="campo">
        <label htmlFor="ingreso-identificador">{etiqueta}</label>
        <span className="campo-adorno">
          <Icono nombre={tipo === 'email' ? 'correo' : 'usuario'} size={18} />
          <input
            id="ingreso-identificador"
            className="input"
            type={tipo}
            autoComplete="username"
            placeholder={ejemplo}
            value={identificador}
            onChange={(e) => setIdentificador(e.target.value)}
            aria-invalid={error ? true : undefined}
            required
          />
        </span>
      </div>

      <CampoClave
        id="clave-ingreso"
        etiqueta="Contraseña"
        autoComplete="current-password"
        valor={password}
        onCambio={setPassword}
        invalido={Boolean(error)}
      />

      <div className="ingreso-ayuda">
        <Link to="/recuperar">¿Olvidaste tu contraseña?</Link>
      </div>

      {error && (
        <p className="aviso-error" role="alert">
          <Icono nombre="alerta" size={16} /> {error}
        </p>
      )}

      <button className="btn btn-primario btn-bloque btn-grande" type="submit" disabled={enviando}>
        {enviando ? 'Ingresando…' : 'Ingresar'}
      </button>
    </form>
  )
}

function IngresoFamilia({ onEntrar }: { onEntrar: (u: Usuario) => void }) {
  const [conClave, setConClave] = useState(false)
  if (conClave) {
    return (
      <div className="ingreso-form">
        <IngresoConClave etiqueta="Correo o celular" tipo="text" onEntrar={onEntrar} />
        <button className="btn btn-plano" type="button" onClick={() => setConClave(false)}>
          <Icono nombre="mensaje" size={16} /> Recibir un código por WhatsApp
        </button>
      </div>
    )
  }
  return <IngresoConCodigo onEntrar={onEntrar} onConClave={() => setConClave(true)} />
}

function IngresoConCodigo({ onEntrar, onConClave }: { onEntrar: (u: Usuario) => void; onConClave: () => void }) {
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
        <div className="campo">
          <label htmlFor="ingreso-celular">Celular registrado</label>
          <span className="campo-adorno">
            <Icono nombre="telefono" size={18} />
            <input
              id="ingreso-celular"
              className="input"
              type="tel"
              inputMode="tel"
              autoComplete="tel"
              placeholder="300 123 4567"
              value={telefono}
              onChange={(e) => setTelefono(e.target.value)}
              aria-describedby="ingreso-celular-ayuda"
              required
            />
          </span>
          <span id="ingreso-celular-ayuda" className="campo-ayuda">
            Te enviamos un código de un solo uso por WhatsApp.
          </span>
        </div>
        {error && (
          <p className="aviso-error" role="alert">
            <Icono nombre="alerta" size={16} /> {error}
          </p>
        )}
        <button className="btn btn-primario btn-bloque btn-grande" type="submit" disabled={enviando}>
          {enviando ? 'Enviando…' : 'Recibir código'}
        </button>
        <button className="btn btn-plano" type="button" onClick={onConClave}>
          <Icono nombre="candado" size={16} /> Ingresar con contraseña
        </button>
      </form>
    )
  }

  return (
    <form className="ingreso-form" onSubmit={verificar}>
      <p className="aviso-ok" role="status">
        <Icono nombre="mensaje" size={16} />
        <span>
          Enviamos un código por WhatsApp al <span className="sin-cortes">{formatoTelefono(telefono.trim())}</span>.
        </span>
      </p>
      <div className="campo">
        <label htmlFor="ingreso-codigo">Código</label>
        <input
          id="ingreso-codigo"
          className="input codigo-input"
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={6}
          value={codigo}
          onChange={(e) => setCodigo(e.target.value.replace(/\D/g, ''))}
          aria-invalid={error ? true : undefined}
          required
        />
      </div>
      {error && (
        <p className="aviso-error" role="alert">
          <Icono nombre="alerta" size={16} /> {error}
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
