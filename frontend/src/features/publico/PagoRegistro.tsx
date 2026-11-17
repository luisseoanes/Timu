import { useState } from 'react'

import { Icono } from '@/components/Icono'
import { mensajeError } from '@/lib/errores'
import { moneda } from '@/lib/formato'
import type { CotizacionRead, Periodicidad, PlanPublico } from '@/types'

import { abrirModeloContrato, guardarToken, useIniciarRegistro, type PeludoRegistro } from './registro'

const PERIODOS: Record<Periodicidad, string> = {
  mensual: 'Mensual',
  trimestral: 'Trimestral',
  semestral: 'Semestral',
  anual: 'Anual',
}

/**
 * Cómo paga la familia y a quién se envía el comprobante (6.12). Los datos de la familia se
 * piden después del pago; todo precio sale del backend, con cada periodicidad.
 */
export function PagoRegistro({
  ciudad,
  peludos,
  planes,
  opciones,
  cargando,
  error,
  periodicidad,
  onPeriodicidad,
  onVolver,
}: {
  ciudad: string
  peludos: PeludoRegistro[]
  planes: PlanPublico[]
  opciones: CotizacionRead[]
  cargando: boolean
  error: Error | null
  periodicidad: Periodicidad
  onPeriodicidad: (periodicidad: Periodicidad) => void
  onVolver: () => void
}) {
  const iniciar = useIniciarRegistro()
  const [modelo, setModelo] = useState<'listo' | 'abriendo' | 'error'>('listo')
  const elegida = opciones.find((o) => o.periodicidad === periodicidad)
  // Solo se promete ahorro si algún periodo lo da (con dos o más peludos no hay descuento por periodo).
  const conAhorro = opciones.some((o) => o.descuento)

  async function verModelo() {
    setModelo('abriendo')
    try {
      await abrirModeloContrato({ ciudad, peludos: peludos.map((p) => ({ ...p, nombre: p.nombre.trim() })), periodicidad })
      setModelo('listo')
    } catch {
      setModelo('error')
    }
  }
  const conTerminos = planes.filter((p) => p.terminos_url && peludos.some((x) => x.plan_id === p.id))

  function enviar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    const texto = (c: string) => String(d.get(c) ?? '').trim()
    iniciar.mutate(
      {
        ciudad,
        peludos: peludos.map((p) => ({ ...p, nombre: p.nombre.trim() })),
        periodicidad,
        contacto: { nombre: texto('contacto_nombre'), telefono: texto('contacto_telefono'), email: texto('contacto_email') },
        acepta_condiciones: d.get('acepta_condiciones') === 'on',
        acepta_tratamiento_datos: d.get('acepta_datos') === 'on',
        sitio_web: texto('sitio_web') || undefined,
      },
      {
        onSuccess: (r) => {
          guardarToken(r.token)
          window.location.assign(r.enlace_pago)
        },
      },
    )
  }

  return (
    <form className="registro-pago" onSubmit={enviar}>
      <button className="btn btn-plano registro-volver" type="button" onClick={onVolver}>
        <Icono nombre="volver" size={16} /> Volver a la manada
      </button>
      <div className="registro-titulo">
        <h1>¿Cómo quieres pagar?</h1>
        <p>
          {conAhorro ? 'Pagando por varios meses ahorras.' : 'Puedes pagar varios meses de una vez.'} Después del pago te
          pedimos los datos de la familia.
        </p>
      </div>

      {error && (
        <p className="aviso-error" role="alert">
          <Icono nombre="alerta" size={16} /> {mensajeError(error, 'No pudimos calcular el precio.')}
        </p>
      )}
      {!error && opciones.length === 0 && (
        <div className="esqueleto" role="status">
          <span className="sr-only">{cargando ? 'Calculando el precio…' : 'Elige el plan de cada peludo.'}</span>
          <span className="esqueleto-linea" aria-hidden="true" />
          <span className="esqueleto-linea" aria-hidden="true" />
        </div>
      )}
      {opciones.length > 0 && (
        <fieldset className="registro-periodos">
          <legend>Cada cuánto</legend>
          {opciones.map((o) => (
            <label key={o.periodicidad} className="registro-periodo">
              <input
                type="radio"
                name="periodicidad"
                value={o.periodicidad}
                checked={periodicidad === o.periodicidad}
                onChange={() => onPeriodicidad(o.periodicidad)}
              />
              <span className="registro-periodo-nombre">{PERIODOS[o.periodicidad]}</span>
              <span className="registro-periodo-valor numero">
                {moneda(o.valor_periodo)} {o.meses === 1 ? 'al mes' : `cada ${o.meses} meses`}
              </span>
              {o.descuento && <span className="registro-periodo-ahorro numero">Ahorras {moneda(o.ahorro)}</span>}
            </label>
          ))}
        </fieldset>
      )}

      <fieldset className="registro-contacto">
        <legend>¿A quién le enviamos el comprobante?</legend>
        <div className="campo">
          <label htmlFor="contacto-nombre">Tu nombre</label>
          <input id="contacto-nombre" className="input" name="contacto_nombre" required minLength={2} maxLength={160} autoComplete="name" />
        </div>
        <div className="campo">
          <label htmlFor="contacto-telefono">Celular (WhatsApp)</label>
          <input id="contacto-telefono" className="input" name="contacto_telefono" required inputMode="tel" autoComplete="tel" />
        </div>
        <div className="campo">
          <label htmlFor="contacto-email">Correo</label>
          <input id="contacto-email" className="input" name="contacto_email" type="email" required autoComplete="email" />
        </div>
        <p className="registro-nota">Si cierras el navegador después de pagar, te enviamos el enlace por correo y WhatsApp.</p>
      </fieldset>
      {/* Trampa para bots: invisible y fuera del orden de tabulación. */}
      <input name="sitio_web" tabIndex={-1} autoComplete="off" className="sr-only" aria-hidden="true" />

      <div className="registro-aceptar">
        <label className="registro-casilla">
          <input type="checkbox" name="acepta_condiciones" required />
          <span>
            Acepto las condiciones de los planes que elegí, con su carencia y lo que no cubren, y el contrato de afiliación.
          </span>
        </label>
        <button className="btn btn-plano registro-modelo" type="button" onClick={verModelo} disabled={modelo === 'abriendo'}>
          <Icono nombre="descargar" size={16} /> {modelo === 'abriendo' ? 'Preparando el contrato…' : 'Leer el contrato con lo que elegiste (PDF)'}
        </button>
        {modelo === 'error' && (
          <p className="aviso-error" role="alert">
            <Icono nombre="alerta" size={16} /> No pudimos abrir el contrato. Intenta de nuevo en un momento.
          </p>
        )}
        {conTerminos.length > 0 && (
          <p className="registro-nota">
            {conTerminos.map((p, i) => (
              <span key={p.id}>
                {i > 0 && ' · '}
                <a href={p.terminos_url!} target="_blank" rel="noreferrer">
                  Términos de {p.nombre}
                </a>
              </span>
            ))}
          </p>
        )}
        <label className="registro-casilla">
          <input type="checkbox" name="acepta_datos" required />
          <span>Autorizo el tratamiento de mis datos personales según la Ley 1581 de 2012.</span>
        </label>
      </div>

      {iniciar.isError && (
        <p className="aviso-error" role="alert">
          <Icono nombre="alerta" size={16} /> {mensajeError(iniciar.error, 'No pudimos iniciar la afiliación.')}
        </p>
      )}
      {iniciar.isSuccess && (
        <p className="aviso-ok" role="status">
          <Icono nombre="pago" size={16} /> Te llevamos a la pasarela para pagar {moneda(iniciar.data.valor)}…
        </p>
      )}
      <button
        className="btn btn-primario btn-bloque btn-grande"
        type="submit"
        disabled={!elegida || iniciar.isPending || iniciar.isSuccess}
      >
        <Icono nombre="pago" size={18} />
        {iniciar.isPending ? 'Registrando…' : elegida ? `Pagar ${moneda(elegida.valor_periodo)}` : 'Pagar'}
      </button>
    </form>
  )
}
