import { useState, type ReactNode } from 'react'
import { Link, Navigate } from 'react-router-dom'

import { Icono } from '@/components/Icono'
import { MarcaTimu } from '@/components/MarcaTimu'
import { mensajeError } from '@/lib/errores'
import { moneda } from '@/lib/formato'
import type { RegistroRead } from '@/types'

import { esperandoPago, leerToken, olvidarToken, useConsultaRegistro, useReintentarRegistro } from './registro'

export function Publica({ titulo, children }: { titulo: string; children: ReactNode }) {
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

export function SinEnlace() {
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

export function EstadoRegistro({ token, registro }: { token: string; registro: RegistroRead }) {
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
