import { useEffect, useState, type ReactNode } from 'react'
import { Link, Navigate, useSearchParams } from 'react-router-dom'

import { Icono } from '@/components/Icono'
import { MarcaTimu } from '@/components/MarcaTimu'
import { mensajeError } from '@/lib/errores'
import { hoyISO, moneda } from '@/lib/formato'
import type { RegistroRead } from '@/types'

import {
  ESPECIES_REGISTRO,
  esperandoPago,
  guardarToken,
  leerToken,
  olvidarToken,
  subirFotos,
  useCompletarRegistro,
  useConsultaRegistro,
  useReintentarRegistro,
  type FormularioRegistro,
} from './registro'

const MAX_CONTACTOS = 3
const nombreEspecie = (codigo: string) => ESPECIES_REGISTRO.find((e) => e.codigo === codigo)?.nombre ?? codigo

function Publica({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <div className="publica">
      <MarcaTimu />
      <section className="publica-tarjeta publica-ancha">
        <h1>{titulo}</h1>
        {children}
      </section>
    </div>
  )
}

function SinEnlace() {
  return (
    <p className="apagado">
      Si ya pagaste, te enviamos un enlace por correo y WhatsApp para completar los datos de tu familia.{' '}
      <Link to="/afiliacion">Empezar una afiliación</Link>
    </p>
  )
}

/** Reintenta en el mismo registro: lo elegido se conserva y vuelve a la pasarela. */
function PagoRechazado({ token }: { token: string }) {
  const reintentar = useReintentarRegistro()
  return (
    <>
      <p className="aviso-error" role="alert">
        La pasarela no aprobó el pago. No se hizo ningún cobro.
      </p>
      {reintentar.isError && (
        <p className="aviso-error" role="alert">
          {mensajeError(reintentar.error, 'No pudimos generar otro intento de pago.')}{' '}
          <Link to="/afiliacion" onClick={olvidarToken}>
            Empezar de nuevo
          </Link>
        </p>
      )}
      <button
        className="btn btn-primario"
        type="button"
        disabled={reintentar.isPending || reintentar.isSuccess}
        onClick={() => reintentar.mutate(token, { onSuccess: (r) => window.location.assign(r.enlace_pago) })}
      >
        <Icono nombre="pago" size={18} /> {reintentar.isPending ? 'Preparando el pago…' : 'Intentar de nuevo'}
      </button>
    </>
  )
}

function EnRevision() {
  return (
    <p className="aviso-ok" role="status">
      Recibimos tu pago. Nuestro equipo revisa tu afiliación y te escribe pronto por WhatsApp.
    </p>
  )
}

/**
 * Regreso desde la pasarela. Con el token que guardó esta pestaña se pregunta por el pago
 * hasta que la pasarela lo confirma; entonces sigue al formulario de la familia.
 */
export function RegistroResultadoPage() {
  const [token] = useState(leerToken)
  const consulta = useConsultaRegistro(token)
  const registro = consulta.data

  if (!token) {
    return (
      <Publica titulo="Gracias por afiliarte">
        <SinEnlace />
      </Publica>
    )
  }
  if (registro?.estado === 'pagada') return <Navigate to="/afiliacion/completar" replace />
  return (
    <Publica titulo="Estamos confirmando tu pago">
      {consulta.isPending && <p className="apagado">Consultando tu pago…</p>}
      {consulta.isError && (
        <>
          <p className="aviso-error" role="alert">
            {mensajeError(consulta.error, 'No encontramos tu afiliación.')}
          </p>
          <SinEnlace />
        </>
      )}
      {registro && <EstadoRegistro token={token} registro={registro} />}
    </Publica>
  )
}

function EstadoRegistro({ token, registro }: { token: string; registro: RegistroRead }) {
  if (esperandoPago(registro)) {
    return (
      <p className="apagado" role="status">
        La pasarela aún no confirma el pago de {moneda(registro.valor_inicial)}. Esta página se actualiza sola; si la
        cierras, te enviamos el enlace por correo y WhatsApp cuando se confirme.
      </p>
    )
  }
  if (registro.estado === 'pendiente_pago') return <PagoRechazado token={token} />
  if (registro.estado === 'cancelada') {
    return (
      <p className="apagado" role="status">
        Este registro se cerró porque no recibimos el pago.{' '}
        <Link to="/afiliacion" onClick={olvidarToken}>
          Empezar una afiliación
        </Link>
      </p>
    )
  }
  if (registro.estado === 'completada') {
    return (
      <>
        <p className="aviso-ok" role="status">
          <Icono nombre="check" size={16} /> Tu afiliación ya está activa.
        </p>
        <Link to="/login" className="btn btn-suave">
          Ir al ingreso
        </Link>
      </>
    )
  }
  return <EnRevision />
}

/**
 * Formulario posterior al pago (6.1): titular, contactos, contraseña y la ficha de cada
 * peludo. Se abre desde el resultado del pago o con el enlace enviado por correo y WhatsApp.
 */
export function CompletarRegistroPage() {
  const [params, setParams] = useSearchParams()
  const [token] = useState(() => {
    const delEnlace = params.get('token')
    if (delEnlace) guardarToken(delEnlace)
    return delEnlace ?? leerToken()
  })
  // El token no se queda en la barra de direcciones ni en el historial.
  useEffect(() => {
    if (params.has('token')) setParams({}, { replace: true })
  }, [params, setParams])
  const consulta = useConsultaRegistro(token)

  if (!token) {
    return (
      <Publica titulo="Completa tu afiliación">
        <SinEnlace />
      </Publica>
    )
  }
  if (consulta.isPending) {
    return (
      <Publica titulo="Completa tu afiliación">
        <p className="apagado">Cargando tu afiliación…</p>
      </Publica>
    )
  }
  if (consulta.isError) {
    return (
      <Publica titulo="Completa tu afiliación">
        <p className="aviso-error" role="alert">
          {mensajeError(consulta.error, 'El enlace no es válido.')}
        </p>
      </Publica>
    )
  }
  const registro = consulta.data
  if (registro.estado !== 'pagada') {
    return (
      <Publica titulo="Completa tu afiliación">
        <EstadoRegistro token={token} registro={registro} />
      </Publica>
    )
  }
  return <Formulario token={token} registro={registro} />
}

type Contacto = FormularioRegistro['contactos'][number]

function Formulario({ token, registro }: { token: string; registro: RegistroRead }) {
  const completar = useCompletarRegistro()
  const [contactos, setContactos] = useState<Contacto[]>([])
  const [claveDistinta, setClaveDistinta] = useState(false)
  const [fotos, setFotos] = useState<Map<number, File>>(new Map())
  const [final, setFinal] = useState<{ mensaje: string; fotosFallaron?: boolean } | null>(null)

  async function terminar(nombres: Map<number, string>) {
    olvidarToken()
    const porNombre = new Map<string, File>()
    fotos.forEach((foto, posicion) => porNombre.set((nombres.get(posicion) ?? '').toLowerCase(), foto))
    try {
      await subirFotos(porNombre)
    } catch {
      setFinal({ mensaje: 'Tu afiliación quedó activa.', fotosFallaron: true })
      return
    }
    window.location.assign('/portal')
  }

  function enviar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    const texto = (c: string) => String(d.get(c) ?? '').trim()
    if (texto('clave') !== texto('clave_repetida')) {
      setClaveDistinta(true)
      return
    }
    setClaveDistinta(false)
    const peludos = registro.peludos.map((p) => ({
      posicion: p.posicion,
      nombre: texto(`nombre_${p.posicion}`),
      raza: texto(`raza_${p.posicion}`) || undefined,
      sexo: (texto(`sexo_${p.posicion}`) || undefined) as 'macho' | 'hembra' | undefined,
      fecha_nacimiento: texto(`fecha_${p.posicion}`),
      peso_kg: Number(texto(`peso_${p.posicion}`)),
    }))
    completar.mutate(
      {
        token,
        titular: {
          titular_nombre: texto('titular_nombre'),
          tipo_documento: texto('tipo_documento'),
          documento: texto('documento'),
          telefono: texto('telefono'),
          email: texto('email'),
          barrio: texto('barrio'),
          direccion: texto('direccion'),
          complemento: texto('complemento') || undefined,
        },
        contactos: contactos.map((c) => ({ ...c, relacion: c.relacion?.trim() || undefined })),
        clave: texto('clave'),
        peludos,
      },
      {
        onSuccess: (r) => {
          if (r.estado === 'completada') {
            void terminar(new Map(peludos.map((p) => [p.posicion, p.nombre])))
          } else {
            olvidarToken()
            setFinal({ mensaje: r.mensaje })
          }
        },
      },
    )
  }

  if (final) {
    return (
      <Publica titulo={final.fotosFallaron ? 'Bienvenidos a TIMU' : 'Recibimos tus datos'}>
        <p className="aviso-ok" role="status">
          {final.mensaje}
        </p>
        {final.fotosFallaron && (
          <>
            <p className="apagado">No pudimos subir las fotos de tus peludos: puedes subirlas desde el portal.</p>
            <a href="/portal" className="btn btn-primario">
              Ir a mi portal
            </a>
          </>
        )}
      </Publica>
    )
  }

  const enviando = completar.isPending || completar.isSuccess
  return (
    <Publica titulo="Completa tu afiliación">
      <p className="apagado">Recibimos tu pago. Con estos datos activamos la afiliación y tu acceso al portal.</p>
      <form className="formulario" onSubmit={enviar}>
        <fieldset className="ancho formulario">
          <legend className="ancho">Titular</legend>
          <label className="campo ancho">
            <span>Nombre completo</span>
            <input
              className="input"
              name="titular_nombre"
              required
              minLength={2}
              maxLength={160}
              autoComplete="name"
              defaultValue={registro.contacto_nombre ?? ''}
            />
          </label>
          <label className="campo">
            <span>Tipo de documento</span>
            <select className="input" name="tipo_documento" defaultValue="CC">
              <option value="CC">Cédula de ciudadanía</option>
              <option value="CE">Cédula de extranjería</option>
              <option value="PA">Pasaporte</option>
              <option value="PPT">Permiso de protección temporal</option>
            </select>
          </label>
          <label className="campo">
            <span>Número de documento</span>
            <input className="input" name="documento" required inputMode="numeric" />
          </label>
          <label className="campo">
            <span>Celular (WhatsApp)</span>
            <input
              className="input"
              name="telefono"
              required
              inputMode="tel"
              autoComplete="tel"
              defaultValue={registro.contacto_telefono ?? ''}
            />
          </label>
          <label className="campo">
            <span>Correo</span>
            <input
              className="input"
              name="email"
              type="email"
              required
              autoComplete="email"
              defaultValue={registro.contacto_email ?? ''}
            />
          </label>
          <label className="campo">
            <span>Ciudad</span>
            <input className="input" value={registro.ciudad} readOnly aria-readonly="true" />
          </label>
          <label className="campo">
            <span>Barrio</span>
            <input className="input" name="barrio" required minLength={2} maxLength={120} />
          </label>
          <label className="campo">
            <span>Dirección</span>
            <input
              className="input"
              name="direccion"
              required
              minLength={3}
              maxLength={255}
              autoComplete="street-address"
            />
          </label>
          <label className="campo">
            <span>Complemento (opcional)</span>
            <input className="input" name="complemento" maxLength={255} placeholder="Torre, apartamento, indicaciones" />
          </label>
        </fieldset>

        <fieldset className="ancho formulario">
          <legend className="ancho">Otros contactos (opcional)</legend>
          <p className="apagado ancho">Personas a quienes podemos llamar si no te encontramos. No reciben mensajes.</p>
          {contactos.map((c, i) => (
            <div key={i} className="ancho formulario">
              <label className="campo">
                <span>Nombre del contacto {i + 1}</span>
                <input
                  className="input"
                  value={c.nombre}
                  required
                  minLength={2}
                  maxLength={160}
                  onChange={(e) => setContactos(contactos.map((x, j) => (j === i ? { ...x, nombre: e.target.value } : x)))}
                />
              </label>
              <label className="campo">
                <span>Celular del contacto {i + 1}</span>
                <input
                  className="input"
                  value={c.telefono}
                  required
                  inputMode="tel"
                  onChange={(e) =>
                    setContactos(contactos.map((x, j) => (j === i ? { ...x, telefono: e.target.value } : x)))
                  }
                />
              </label>
              <label className="campo">
                <span>Relación (opcional)</span>
                <input
                  className="input"
                  value={c.relacion ?? ''}
                  maxLength={60}
                  placeholder="Pareja, hijo, vecina…"
                  onChange={(e) =>
                    setContactos(contactos.map((x, j) => (j === i ? { ...x, relacion: e.target.value } : x)))
                  }
                />
              </label>
              <button
                className="btn btn-plano"
                type="button"
                onClick={() => setContactos(contactos.filter((_, j) => j !== i))}
              >
                Quitar contacto {i + 1}
              </button>
            </div>
          ))}
          {contactos.length < MAX_CONTACTOS && (
            <button
              className="btn btn-suave ancho"
              type="button"
              onClick={() => setContactos([...contactos, { nombre: '', telefono: '' }])}
            >
              <Icono nombre="mas" size={16} /> Agregar contacto
            </button>
          )}
        </fieldset>

        {registro.peludos.map((p) => (
          <fieldset key={p.posicion} className="ancho formulario">
            <legend className="ancho">
              {p.nombre} · {nombreEspecie(p.especie)}
            </legend>
            <label className="campo">
              <span>Nombre</span>
              <input
                className="input"
                name={`nombre_${p.posicion}`}
                required
                maxLength={120}
                defaultValue={p.nombre}
              />
            </label>
            <label className="campo">
              <span>Raza (opcional)</span>
              <input className="input" name={`raza_${p.posicion}`} maxLength={80} placeholder="Criollo, mestizo…" />
            </label>
            <label className="campo">
              <span>Sexo (opcional)</span>
              <select className="input" name={`sexo_${p.posicion}`} defaultValue="">
                <option value="">Sin dato</option>
                <option value="hembra">Hembra</option>
                <option value="macho">Macho</option>
              </select>
            </label>
            <label className="campo">
              <span>Fecha de nacimiento (aproximada)</span>
              <input className="input" name={`fecha_${p.posicion}`} type="date" required max={hoyISO()} />
            </label>
            <label className="campo">
              <span>Peso en kg</span>
              <input
                className="input"
                name={`peso_${p.posicion}`}
                type="number"
                required
                min={0.1}
                max={149}
                step={0.1}
                inputMode="decimal"
              />
            </label>
            <label className="campo">
              <span>Foto (opcional)</span>
              <input
                className="input"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={(e) => {
                  const foto = e.target.files?.[0]
                  setFotos((previas) => {
                    const nuevas = new Map(previas)
                    if (foto) nuevas.set(p.posicion, foto)
                    else nuevas.delete(p.posicion)
                    return nuevas
                  })
                }}
              />
            </label>
          </fieldset>
        ))}

        <fieldset className="ancho formulario">
          <legend className="ancho">Tu acceso al portal</legend>
          <label className="campo">
            <span>Contraseña</span>
            <input className="input" name="clave" type="password" required minLength={8} maxLength={128} autoComplete="new-password" />
          </label>
          <label className="campo">
            <span>Repite la contraseña</span>
            <input
              className="input"
              name="clave_repetida"
              type="password"
              required
              minLength={8}
              maxLength={128}
              autoComplete="new-password"
            />
          </label>
          {claveDistinta && (
            <p className="aviso-error ancho" role="alert">
              Las contraseñas no coinciden.
            </p>
          )}
        </fieldset>

        {completar.isError && (
          <p className="aviso-error ancho" role="alert">
            {mensajeError(completar.error, 'No pudimos completar la afiliación.')}
          </p>
        )}
        <button className="btn btn-primario btn-grande ancho" type="submit" disabled={enviando}>
          {enviando ? 'Activando tu afiliación…' : 'Activar mi afiliación'}
        </button>
      </form>
    </Publica>
  )
}
