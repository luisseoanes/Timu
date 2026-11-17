import { useMutation } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { api } from '@/api/client'
import { AccesoLayout } from '@/components/AccesoLayout'
import { Icono } from '@/components/Icono'
import { esErrorPasajero, mensajeError } from '@/lib/errores'
import { diaISO, fechaCortaConDia, hora, hoyISO } from '@/lib/formato'
import { inicioDeRol } from '@/lib/permisos'
import type { EstadoEnlace } from '@/types'

import { useEstadoEnlace } from './api'
import { useAuth } from './AuthContext'
import { CampoClave } from './CampoClave'

/** Pide el enlace de recuperación (F1-AUT-03). Responde igual exista o no la cuenta. */
export function RecuperarPage() {
  const [identificador, setIdentificador] = useState('')
  const pedir = useMutation({
    mutationFn: async () => (await api.post('/auth/recuperar', { identificador })).data,
  })

  return (
    <AccesoLayout>
      {pedir.isSuccess ? (
        <div className="ingreso-titulo">
          <h1>Revisa tu correo o tu WhatsApp</h1>
          <p role="status">
            Si hay una cuenta con {identificador}, en unos minutos te llega un enlace para crear tu contraseña
            nueva. Si no lo ves, revisa también la carpeta de spam.
          </p>
        </div>
      ) : (
        <>
          <div className="ingreso-titulo">
            <h1>Recupera tu acceso</h1>
            <p>Escribe tu correo o tu celular y te enviamos un enlace para crear una contraseña nueva.</p>
          </div>
          <form
            className="ingreso-form"
            onSubmit={(e) => {
              e.preventDefault()
              pedir.mutate()
            }}
          >
            <div className="campo">
              <label htmlFor="recuperar-identificador">Correo o celular</label>
              <span className="campo-adorno">
                <Icono nombre="usuario" size={18} />
                <input
                  id="recuperar-identificador"
                  className="input"
                  autoComplete="username"
                  value={identificador}
                  onChange={(e) => setIdentificador(e.target.value)}
                  required
                />
              </span>
            </div>
            {pedir.isError && (
              <p className="aviso-error" role="alert">
                <Icono nombre="alerta" size={16} />{' '}
                {mensajeError(pedir.error, 'No pudimos enviar el enlace. Intenta de nuevo.')}
              </p>
            )}
            <button className="btn btn-primario btn-bloque btn-grande" type="submit" disabled={pedir.isPending}>
              {pedir.isPending ? 'Enviando…' : 'Enviar enlace'}
            </button>
          </form>
        </>
      )}

      <Link to="/login" className="btn btn-plano ingreso-volver">
        <Icono nombre="volver" size={16} /> Volver al ingreso
      </Link>
    </AccesoLayout>
  )
}

/** Lo que se le dice a quien abre un enlace que ya no sirve. */
const ENLACE_QUE_NO_SIRVE: Record<Exclude<EstadoEnlace['estado'], 'vigente'>, { titulo: string; texto: string }> = {
  usado: {
    titulo: 'Este enlace ya se usó',
    texto:
      'Cada enlace sirve una sola vez, y uno nuevo reemplaza a los anteriores. Si ya creaste tu contraseña, ingresa con ella; si no, pide otro enlace.',
  },
  vencido: {
    titulo: 'Este enlace venció',
    texto: 'Por seguridad, los enlaces vencen. Pide otro y ábrelo en cuanto te llegue.',
  },
  invalido: {
    titulo: 'Este enlace no sirve',
    texto: 'Puede que esté incompleto o que la cuenta ya no esté activa. Ábrelo de nuevo desde el mensaje que recibiste o pide otro.',
  },
}

/**
 * Define la contraseña con el enlace recibido y entra. El mismo formulario sirve para
 * recuperarla y para activar una cuenta del portal: la API dice para qué es el enlace, si
 * sirve y a quién saludar, antes de pedir nada.
 */
export function RestablecerPage({ modo }: { modo: 'restablecer' | 'activar' }) {
  const [params] = useSearchParams()
  const token = params.get('token') ?? ''
  const enlace = useEstadoEnlace(token)
  const frase = modo === 'activar' ? 'Te damos la bienvenida a la manada TIMU.' : undefined

  let contenido
  if (!token) {
    contenido = <EnlaceQueNoSirve titulo="El enlace está incompleto" texto={ENLACE_QUE_NO_SIRVE.invalido.texto} />
  } else if (enlace.isPending) {
    contenido = (
      <div className="esqueleto ingreso-esqueleto" role="status">
        <span className="sr-only">Comprobando el enlace…</span>
        <span className="esqueleto-linea" aria-hidden="true" />
        <span className="esqueleto-linea" aria-hidden="true" />
        <span className="esqueleto-linea" aria-hidden="true" />
      </div>
    )
  } else if (enlace.isError) {
    contenido = (
      <>
        <div className="ingreso-titulo">
          <h1>No pudimos comprobar el enlace</h1>
        </div>
        <p className="aviso-error" role="alert">
          <Icono nombre="alerta" size={16} />{' '}
          {mensajeError(enlace.error, 'El servidor no respondió. Intenta de nuevo en un momento.')}
        </p>
        {esErrorPasajero(enlace.error) && (
          <button className="btn btn-primario btn-bloque btn-grande" type="button" onClick={() => enlace.refetch()}>
            Reintentar
          </button>
        )}
      </>
    )
  } else if (enlace.data.estado !== 'vigente') {
    contenido = <EnlaceQueNoSirve {...ENLACE_QUE_NO_SIRVE[enlace.data.estado]} />
  } else {
    contenido = <DefinirClave token={token} enlace={enlace.data} />
  }

  return <AccesoLayout frase={frase}>{contenido}</AccesoLayout>
}

function EnlaceQueNoSirve({ titulo, texto }: { titulo: string; texto: string }) {
  return (
    <>
      <div className="ingreso-titulo">
        <h1>{titulo}</h1>
        <p>{texto}</p>
      </div>
      <Link to="/recuperar" className="btn btn-primario btn-bloque btn-grande">
        Pedir un enlace nuevo
      </Link>
      <Link to="/login" className="btn btn-plano ingreso-volver">
        <Icono nombre="volver" size={16} /> Ir al ingreso
      </Link>
    </>
  )
}

/** «Este enlace sirve hasta hoy a las 10:42 a. m.»: la vigencia la da la API. */
function vigencia(expira: string): string {
  const dia = diaISO(expira)
  return `Este enlace sirve hasta ${dia === hoyISO() ? 'hoy' : `el ${fechaCortaConDia(dia)}`} a las ${hora(expira)}.`
}

function DefinirClave({ token, enlace }: { token: string; enlace: EstadoEnlace }) {
  const { entrarConEnlace } = useAuth()
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [confirmacion, setConfirmacion] = useState('')
  const definir = useMutation({
    mutationFn: () => entrarConEnlace(token, password),
    onSuccess: (usuario) => navigate(inicioDeRol(usuario.rol), { replace: true }),
  })

  const noCoinciden = confirmacion.length > 0 && confirmacion !== password
  const activar = enlace.proposito === 'activacion'
  // Un 400 es el enlace, que se usó o venció mientras la pantalla estaba abierta.
  const enlaceCaducado = isAxiosError(definir.error) && definir.error.response?.status === 400

  return (
    <>
      <div className="ingreso-titulo">
        <h1>Hola, {enlace.nombre}</h1>
        <p>
          {activar
            ? 'Elige la contraseña con la que vas a entrar a TIMU.'
            : 'Crea tu contraseña nueva. Al guardarla se cierran las sesiones que tengas abiertas en otros equipos.'}
          {enlace.expira_en && <> {vigencia(enlace.expira_en)}</>}
        </p>
      </div>

      <form
        className="ingreso-form"
        onSubmit={(e) => {
          e.preventDefault()
          if (!noCoinciden) definir.mutate()
        }}
      >
        <CampoClave
          id="clave-nueva"
          etiqueta="Contraseña nueva"
          autoComplete="new-password"
          minLength={8}
          valor={password}
          onCambio={setPassword}
          ayuda="Al menos 8 caracteres."
        />
        <div className="campo">
          <label htmlFor="clave-confirmacion">Confirma la contraseña</label>
          <span className="campo-adorno">
            <Icono nombre="candado" size={18} />
            <input
              id="clave-confirmacion"
              className="input"
              type="password"
              autoComplete="new-password"
              value={confirmacion}
              onChange={(e) => setConfirmacion(e.target.value)}
              aria-invalid={noCoinciden || undefined}
              aria-describedby={noCoinciden ? 'clave-confirmacion-error' : undefined}
              required
            />
          </span>
          {noCoinciden && (
            <span id="clave-confirmacion-error" className="error">
              Las contraseñas no coinciden.
            </span>
          )}
        </div>
        {definir.isError && (
          <p className="aviso-error" role="alert">
            <Icono nombre="alerta" size={16} />{' '}
            {enlaceCaducado ? (
              <span>
                Este enlace dejó de servir mientras lo tenías abierto. <Link to="/recuperar">Pide uno nuevo</Link>.
              </span>
            ) : (
              mensajeError(definir.error, 'No pudimos guardar la contraseña. Intenta de nuevo.')
            )}
          </p>
        )}
        <button
          className="btn btn-primario btn-bloque btn-grande"
          type="submit"
          disabled={noCoinciden || definir.isPending}
        >
          {definir.isPending ? 'Guardando…' : activar ? 'Activar mi cuenta' : 'Guardar y entrar'}
        </button>
      </form>
    </>
  )
}
