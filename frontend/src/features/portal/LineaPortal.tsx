import { useId, useState } from 'react'
import { Link } from 'react-router-dom'

import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { mensajeError } from '@/lib/errores'
import { fechaCorta, fechaCortaConDia, moneda } from '@/lib/formato'
import type { ColorPlan, EstacionRead, EstadoCuenta, ServicioPortalRead } from '@/types'

import { usePagarPortal } from './api'
import { accionPrincipal, meses, PROXIMO_COBRO, type Elemento } from './linea'

interface Props {
  elementos: Elemento[]
  hoy: string
  /** El color del plan (catálogo); sin plan, la línea va en gris. */
  color: ColorPlan | null
  cuenta: EstadoCuenta | null
  servicios: ServicioPortalRead[]
  /** Por qué no se puede agendar ahora, o null si se puede. */
  sinAgendar: string | null
  onAgendar: () => void
  etiqueta: string
  /** Qué dice la línea cuando no hay nada después de hoy. */
  fin: string
  /** En la ficha de un peludo su nombre sobra en cada estación. */
  dePeludo?: boolean
}

/**
 * La línea de la familia abierta en «hoy» (contrato de la superficie del portal): lo hecho
 * plegado arriba, lo vencido agrupado con su acción, la marca de hoy y lo que viene. Cada
 * estación dice en palabras qué es y qué hacer: la familia no tiene por qué leer un diagrama.
 */
export function LineaPortal({ elementos, hoy, color, cuenta, servicios, sinAgendar, onAgendar, etiqueta, fin, dePeludo = false }: Props) {
  const pagar = usePagarPortal()
  const [desplegado, setDesplegado] = useState(false)
  const idHechas = useId()
  const principal = accionPrincipal(elementos, sinAgendar === null)
  const estadoServicio = (id: string) => servicios.find((s) => s.id === id)?.estado
  const porPagar = (id: string): string | null => {
    if (id === PROXIMO_COBRO) return cuenta?.proximo_cobro?.valor ?? null
    const cuota = cuenta?.cuotas.find((c) => c.id === id)
    return cuota ? String(Number(cuota.valor) - Number(cuota.valor_pagado)) : null
  }
  // «Vacuna · Michi»: el peludo va con lo que le toca; la cuota es de la familia.
  const titulo = (e: EstacionRead) => (e.mascota && !dePeludo ? `${e.titulo} · ${e.mascota}` : e.titulo)

  function iniciarPago(cuotaId?: string) {
    pagar.mutate(cuotaId, { onSuccess: (r) => window.location.assign(r.enlace_pago) })
  }

  const boton = (esPrincipal: boolean) => `btn ${esPrincipal ? 'btn-primario' : 'btn-secundario'}`

  return (
    <>
    <ol className="linea-portal" data-color={color ?? 'ninguno'} aria-label={etiqueta}>
      {elementos.map((e, i) => {
        if (e.tipo === 'hoy') {
          return (
            <li key="hoy" className="linea-portal-hoy" aria-current="date">
              <span className="linea-portal-hoy-marca" aria-hidden="true" />
              <span>Hoy · {fechaCortaConDia(hoy)}</span>
            </li>
          )
        }

        if (e.tipo === 'fin') {
          return (
            <li key="fin" className="parada-portal" data-estado="futura">
              <Punto estado="futura" />
              <div className="parada-portal-cuerpo">
                <p className="parada-portal-fin">{fin}</p>
              </div>
            </li>
          )
        }

        if (e.tipo === 'hechas') {
          return (
            <li key="hechas" className="parada-portal" data-estado="hecha">
              <span className="parada-portal-punto" aria-hidden="true" />
              <div className="parada-portal-cuerpo">
                <button
                  className="linea-tramo-boton"
                  type="button"
                  aria-expanded={desplegado}
                  aria-controls={idHechas}
                  onClick={() => setDesplegado(!desplegado)}
                >
                  <Icono nombre="check" size={12} />
                  {e.estaciones.length} {e.estaciones.length === 1 ? 'hecha' : 'hechas'}
                  <span className="linea-tramo-flecha">
                    <Icono nombre="abajo" size={12} />
                  </span>
                </button>
                <ul id={idHechas} className="parada-portal-hechas" hidden={!desplegado}>
                  {e.estaciones.map((h) => (
                    <li key={h.referencia_id}>
                      <span className="numero">{fechaCorta(h.fecha)}</span> · {titulo(h)}
                    </li>
                  ))}
                </ul>
              </div>
            </li>
          )
        }

        if (e.tipo === 'cuotas-vencidas') {
          const n = e.estaciones.length
          const vencido = cuenta ? moneda(cuenta.saldo_vencido) : null
          return (
            <li key="cuotas" className="parada-portal" data-estado="vencida">
              <Punto estado="vencida" />
              <div className="parada-portal-cuerpo">
                <h3>
                  {n} {n === 1 ? 'cuota vencida' : 'cuotas vencidas'}
                  {vencido && <span className="numero"> · {vencido}</span>}
                </h3>
                <p>
                  {n === 1 ? 'La' : 'Las'} de {meses(e.estaciones)}.
                </p>
                {cuenta && Number(cuenta.saldo_pendiente) > Number(cuenta.saldo_vencido) && (
                  <p>El pago incluye lo que vence pronto.</p>
                )}
                <div className="parada-portal-acciones">
                  <button className={boton(principal === 'pagar-vencidas')} type="button" disabled={pagar.isPending} onClick={() => iniciarPago()}>
                    {cuenta ? `Pagar ${moneda(cuenta.saldo_pendiente)}` : 'Pagar'}
                  </button>
                </div>
              </div>
            </li>
          )
        }

        if (e.tipo === 'preventivos-vencidos') {
          const n = e.estaciones.length
          return (
            <li key="preventivos" className="parada-portal" data-estado="vencida">
              <Punto estado="vencida" />
              <div className="parada-portal-cuerpo">
                <h3>
                  {n} {n === 1 ? 'preventivo vencido' : 'preventivos vencidos'} desde el {fechaCorta(e.desde)}
                </h3>
                {e.porMascota.length > 1 && (
                <p>
                  {e.porMascota.map((m, j) => (
                    <span key={m.mascotaId ?? m.mascota}>
                      {j > 0 && ' · '}
                      {m.mascotaId ? <Link to={`/portal/mascotas/${m.mascotaId}`}>{m.mascota}</Link> : m.mascota} {m.cuantos}
                    </span>
                  ))}
                </p>
                )}
                {sinAgendar ? (
                  <p>{sinAgendar}</p>
                ) : (
                  <div className="parada-portal-acciones">
                    <button className={boton(principal === 'agendar-preventivos')} type="button" onClick={onAgendar}>
                      Agendar
                    </button>
                  </div>
                )}
              </div>
            </li>
          )
        }

        const { estacion } = e
        const valor = estacion.tipo === 'cuota' ? porPagar(estacion.referencia_id) : null
        const estado = estacion.tipo === 'servicio' ? estadoServicio(estacion.referencia_id) : undefined
        return (
          <li key={`${estacion.tipo}-${estacion.referencia_id}-${i}`} className="parada-portal" data-estado={estacion.estado}>
            <Punto estado={estacion.estado} />
            <div className="parada-portal-cuerpo">
              <h3>
                <span className="numero">{fechaCorta(estacion.fecha)}</span> · {titulo(estacion)}
              </h3>
              {valor && <p className="numero">{moneda(valor)}</p>}
              {estacion.tipo === 'preventivo' && estacion.estado !== 'hecha' && <p>{estacion.estado === 'vencida' ? 'Vencida' : 'Programada'}</p>}
              {estado && <Distintivo dominio="servicio" valor={estado} />}
              {estacion.tipo === 'servicio' && estacion.estado !== 'hecha' && (
                <p>
                  <Link to="/portal/citas">Ver tus citas</Link>
                </p>
              )}
              {estacion.estado === 'proxima' && estacion.tipo === 'cuota' && principal === 'pagar-proxima' && (
                <div className="parada-portal-acciones">
                  <button className="btn btn-primario" type="button" disabled={pagar.isPending} onClick={() => iniciarPago(estacion.referencia_id)}>
                    Pagar {valor ? moneda(valor) : 'la cuota'}
                  </button>
                </div>
              )}
            </div>
          </li>
        )
      })}
    </ol>
    {pagar.isError && (
      <p className="error" role="alert">
        {mensajeError(pagar.error, 'No pudimos iniciar el pago.')}
      </p>
    )}
    </>
  )
}

function Punto({ estado }: { estado: EstacionRead['estado'] }) {
  return (
    <span className="parada-portal-punto" aria-hidden="true">
      {estado === 'vencida' && <Icono nombre="alerta" size={12} />}
    </span>
  )
}
