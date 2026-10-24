import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { api } from '@/api/client'
import { Icono } from '@/components/Icono'
import { mensajeError } from '@/lib/errores'

import { AccesoLayout, MarcaTimu } from './AccesoLayout'

/** Pide el enlace de recuperación (F1-AUT-03). Responde igual exista o no la cuenta. */
export function RecuperarPage() {
  const [identificador, setIdentificador] = useState('')
  const pedir = useMutation({
    mutationFn: async () => (await api.post('/auth/recuperar', { identificador })).data,
  })

  return (
    <AccesoLayout>
      <div className="ingreso-panel">
        <MarcaTimu />
        <div className="ingreso-titulo">
          <h1>Recupera tu acceso</h1>
          <p>Escribe tu correo o celular y te enviaremos un enlace para crear una contraseña nueva.</p>
        </div>

        {pedir.isSuccess ? (
          <p className="aviso-ok" role="status">
            <Icono nombre="check" size={16} /> Si hay una cuenta con ese dato, en unos minutos te llega el
            enlace. Revisa también la carpeta de spam.
          </p>
        ) : (
          <form
            className="ingreso-form"
            onSubmit={(e) => {
              e.preventDefault()
              pedir.mutate()
            }}
          >
            <label className="campo">
              <span>Correo o celular</span>
              <span className="campo-adorno">
                <Icono nombre="usuario" size={18} />
                <input
                  className="input"
                  autoComplete="username"
                  value={identificador}
                  onChange={(e) => setIdentificador(e.target.value)}
                  required
                />
              </span>
            </label>
            {pedir.isError && (
              <p className="aviso-error" role="alert">
                {mensajeError(pedir.error, 'No pudimos enviar el enlace. Intenta de nuevo.')}
              </p>
            )}
            <button className="btn btn-primario btn-bloque btn-grande" type="submit" disabled={pedir.isPending}>
              {pedir.isPending ? 'Enviando…' : 'Enviar enlace'}
            </button>
          </form>
        )}

        <Link to="/login" className="btn btn-plano">
          <Icono nombre="volver" size={16} /> Volver al ingreso
        </Link>
      </div>
    </AccesoLayout>
  )
}

/**
 * Define la contraseña con el enlace recibido. El mismo formulario sirve para
 * recuperarla y para activar una cuenta nueva del portal: cambia sólo el texto.
 */
export function RestablecerPage({ modo }: { modo: 'restablecer' | 'activar' }) {
  const [params] = useSearchParams()
  const token = params.get('token') ?? ''
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [confirmacion, setConfirmacion] = useState('')
  const [visible, setVisible] = useState(false)
  const definir = useMutation({
    mutationFn: async () => {
      await api.post('/auth/restablecer', { token, password })
    },
  })

  const noCoinciden = confirmacion.length > 0 && confirmacion !== password
  const activar = modo === 'activar'

  return (
    <AccesoLayout>
      <div className="ingreso-panel">
        <MarcaTimu />
        <div className="ingreso-titulo">
          <h1>{activar ? 'Activa tu cuenta' : 'Crea una contraseña nueva'}</h1>
          <p>
            {activar
              ? 'Elige la contraseña con la que vas a ingresar a TIMU.'
              : 'Usa al menos 8 caracteres. Al guardarla se cierran las demás sesiones abiertas.'}
          </p>
        </div>

        {!token && (
          <p className="aviso-error" role="alert">
            El enlace está incompleto. Ábrelo de nuevo desde el mensaje que recibiste.
          </p>
        )}

        {definir.isSuccess ? (
          <>
            <p className="aviso-ok" role="status">
              <Icono nombre="check" size={16} /> Listo, tu contraseña quedó guardada.
            </p>
            <button className="btn btn-primario btn-bloque btn-grande" type="button" onClick={() => navigate('/login')}>
              Ir al ingreso
            </button>
          </>
        ) : (
          <form
            className="ingreso-form"
            onSubmit={(e) => {
              e.preventDefault()
              if (!noCoinciden) definir.mutate()
            }}
          >
            <label className="campo">
              <span>Contraseña nueva</span>
              <span className="campo-adorno">
                <Icono nombre="candado" size={18} />
                <input
                  className="input"
                  type={visible ? 'text' : 'password'}
                  autoComplete="new-password"
                  minLength={8}
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
            <label className="campo">
              <span>Confirma la contraseña</span>
              <span className="campo-adorno">
                <Icono nombre="candado" size={18} />
                <input
                  className="input"
                  type={visible ? 'text' : 'password'}
                  autoComplete="new-password"
                  value={confirmacion}
                  onChange={(e) => setConfirmacion(e.target.value)}
                  aria-invalid={noCoinciden}
                  required
                />
              </span>
            </label>
            {noCoinciden && <p className="error">Las contraseñas no coinciden.</p>}
            {definir.isError && (
              <p className="aviso-error" role="alert">
                {mensajeError(definir.error, 'El enlace no es válido o ya venció. Pide uno nuevo.')}
              </p>
            )}
            <button
              className="btn btn-primario btn-bloque btn-grande"
              type="submit"
              disabled={!token || noCoinciden || definir.isPending}
            >
              {definir.isPending ? 'Guardando…' : activar ? 'Activar cuenta' : 'Guardar contraseña'}
            </button>
          </form>
        )}
      </div>
    </AccesoLayout>
  )
}
