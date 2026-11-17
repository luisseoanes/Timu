import { useState, type ReactNode } from 'react'
import { Link, Navigate } from 'react-router-dom'

import { Icono } from '@/components/Icono'
import { esErrorPasajero, mensajeError } from '@/lib/errores'
import { hora, moneda } from '@/lib/formato'
import type { RegistroRead } from '@/types'

import { Contacto } from './Contacto'
import { ManadaPagada, MarcoRegistro } from './MarcoRegistro'
import { esperandoPago, leerToken, olvidarToken, tituloDe, useConsultaRegistro, useReintentarRegistro } from './registro'

/** Una página del registro después de la pasarela: título, lo que pasó y, si se sabe, la manada. */
export function PaginaRegistro({
  titulo,
  texto,
  registro,
  children,
}: {
  titulo: string
  texto?: ReactNode
  registro?: RegistroRead
  children?: ReactNode
}) {
  return (
    <MarcoRegistro aparte={registro && <ManadaPagada registro={registro} />}>
      <div className="registro-pago">
        <div className="registro-titulo">
          <h1>{titulo}</h1>
          {texto && <p>{texto}</p>}
        </div>
        {children}
      </div>
    </MarcoRegistro>
  )
}

export function SinEnlace() {
  return (
    <p className="registro-nota">
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
        <Icono nombre="alerta" size={16} /> La pasarela no aprobó el pago. No se hizo ningún cobro: puedes intentarlo otra
        vez con lo que ya elegiste.
      </p>
      {reintentar.isError && (
        <p className="aviso-error" role="alert">
          <Icono nombre="alerta" size={16} />
          <span>
            {mensajeError(reintentar.error, 'No pudimos generar otro intento de pago.')}{' '}
            <Link to="/afiliacion" onClick={olvidarToken}>
              Empezar de nuevo
            </Link>
          </span>
        </p>
      )}
      <button
        className="btn btn-primario btn-bloque btn-grande"
        type="button"
        disabled={reintentar.isPending || reintentar.isSuccess}
        onClick={() => reintentar.mutate(token, { onSuccess: (r) => window.location.assign(r.enlace_pago) })}
      >
        <Icono nombre="pago" size={18} /> {reintentar.isPending ? 'Preparando el pago…' : 'Intentar de nuevo'}
      </button>
      {/* Otra forma de pago u otra manada es otra afiliación: lo elegido aquí se descarta. */}
      <Link to="/afiliacion" className="btn btn-plano registro-volver" onClick={olvidarToken}>
        Empezar de nuevo con otra forma de pago
      </Link>
      <Contacto texto="Si el problema sigue, escríbenos por WhatsApp" />
    </>
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
      <PaginaRegistro titulo="Gracias por afiliarte">
        <SinEnlace />
      </PaginaRegistro>
    )
  }
  if (registro?.estado === 'pagada') return <Navigate to="/afiliacion/completar" replace />
  if (consulta.isPending) {
    return (
      <PaginaRegistro titulo="Consultando tu pago">
        <div className="esqueleto" role="status">
          <span className="sr-only">Consultando tu pago…</span>
          <span className="esqueleto-linea" aria-hidden="true" />
          <span className="esqueleto-linea" aria-hidden="true" />
        </div>
      </PaginaRegistro>
    )
  }
  if (consulta.isError) {
    return (
      <PaginaRegistro titulo="No encontramos tu afiliación">
        <p className="aviso-error" role="alert">
          <Icono nombre="alerta" size={16} />{' '}
          {esErrorPasajero(consulta.error)
            ? mensajeError(consulta.error, 'El servidor no respondió. Intenta de nuevo en un momento.')
            : 'El enlace no sirve o ya se usó.'}
        </p>
        <SinEnlace />
      </PaginaRegistro>
    )
  }
  return (
    <PaginaRegistro titulo={tituloDe(consulta.data)} registro={consulta.data}>
      <EstadoRegistro token={token} registro={consulta.data} consultadoEn={consulta.dataUpdatedAt} />
    </PaginaRegistro>
  )
}

export function EstadoRegistro({
  token,
  registro,
  consultadoEn,
}: {
  token: string
  registro: RegistroRead
  consultadoEn?: number
}) {
  if (esperandoPago(registro)) {
    return (
      <div className="registro-espera" role="status">
        <span className="registro-espera-pulso" aria-hidden="true" />
        <p>
          La pasarela aún no confirma el pago de {moneda(registro.valor_inicial)}. Volvemos a preguntar cada pocos
          segundos{consultadoEn ? ` (última vez a las ${hora(new Date(consultadoEn).toISOString())})` : ''}; si cierras
          la página, te enviamos el enlace por correo y WhatsApp cuando se confirme.
        </p>
      </div>
    )
  }
  if (registro.estado === 'pendiente_pago') return <PagoRechazado token={token} />
  if (registro.estado === 'cancelada') {
    return (
      <p className="registro-nota" role="status">
        Se cerró porque no recibimos el pago, y no se hizo ningún cobro.{' '}
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
          <Icono nombre="check" size={16} /> Ya puedes entrar a tu portal con tu correo o tu celular.
        </p>
        <Link to="/login" className="btn btn-primario btn-bloque btn-grande">
          Ir al ingreso
        </Link>
      </>
    )
  }
  return (
    <p className="aviso-ok" role="status">
      <Icono nombre="check" size={16} /> Recibimos tu pago. Nuestro equipo revisa tu afiliación y te escribe pronto por
      WhatsApp.
    </p>
  )
}
