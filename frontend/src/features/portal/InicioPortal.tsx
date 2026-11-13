import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { useAuth } from '@/features/auth'
import { hoyISO } from '@/lib/formato'
import type { EstacionRead, MascotaRead } from '@/types'

import { AgendarModal, OrientacionModal } from './Agenda'
import { useMiCuenta, useMiFamilia, useMiLinea, useMiPlan, useMisServicios } from './api'
import { conProximoCobro, recorrido, vencidasDe } from './linea'
import { LineaPortal } from './LineaPortal'
import { estadoDelPlan, finDeLinea, frase, motivoSinAgendar, planesDe } from './plan'

/**
 * R3-POR-01 El inicio del portal: la línea de la familia abierta en «hoy» (contrato de la
 * superficie, «Hoy, estás aquí»). Arriba, el plan con su estado dicho en una frase y los
 * peludos; debajo, lo vencido con su acción, la marca de hoy y lo que viene.
 */
export function PortalInicio() {
  const { usuario } = useAuth()
  const plan = useMiPlan()
  const cuenta = useMiCuenta()
  const linea = useMiLinea()
  const familia = useMiFamilia()
  const servicios = useMisServicios()
  const [agendando, setAgendando] = useState(false)
  const [orientacion, setOrientacion] = useState(false)
  const hoy = hoyISO()
  const estaciones = linea.data?.estaciones ?? []
  const sinAgendar = motivoSinAgendar(plan.data)
  const orden = (familia.data?.mascotas ?? []).map((m) => m.id)

  return (
    <div className="portal-inicio">
      <h1 className="portal-inicio-hola">Hola, {usuario?.nombre?.split(' ')[0]}</h1>

      <section className="portal-plan" aria-labelledby="portal-plan-titulo">
        <h2 id="portal-plan-titulo" className="sr-only">
          Tu plan
        </h2>
        <Consulta consulta={plan} cargando="Cargando tu plan…" error="No pudimos cargar tu plan.">
          {(p) => (
            <>
              <div className="portal-plan-nombre">
                {p &&
                  planesDe(p).map((pl, _, todos) => (
                    <span key={pl.nombre} className="portal-plan-marca">
                      <span className="marcador-plan" data-color={pl.color} aria-hidden="true" />
                      {pl.nombre}
                      {todos.length > 1 && <span className="apagado"> · {pl.mascotas.join(' y ')}</span>}
                    </span>
                  ))}
                {p && <Insignia tono={estadoDelPlan(p.estado).tono}>{estadoDelPlan(p.estado).label}</Insignia>}
              </div>
              <p className="portal-plan-frase">{frase(p, linea.data ? vencidas(estaciones, 'cuota') : null)}</p>
            </>
          )}
        </Consulta>
        <div className="acciones">
          {sinAgendar === null && (
            <button className="btn btn-secundario" type="button" onClick={() => setAgendando(true)}>
              <Icono nombre="calendario" size={18} /> Agendar una visita
            </button>
          )}
          <button className="btn btn-secundario" type="button" onClick={() => setOrientacion(true)}>
            <Icono nombre="mensaje" size={18} /> Hablar con un veterinario
          </button>
        </div>
      </section>

      <section className="portal-peludos" aria-labelledby="portal-peludos-titulo">
        <h2 id="portal-peludos-titulo" className="sr-only">
          Tus peludos
        </h2>
        <Consulta consulta={familia} cargando="Cargando tus peludos…" error="No pudimos cargar tus peludos.">
          {(f) => (
            <ul className="portal-peludos-lista">
              {(f.mascotas ?? [])
                .filter((m) => m.activa)
                .map((m) => (
                  <li key={m.id}>
                    <AccesoPeludo mascota={m} vencidos={linea.data ? vencidasDe(estaciones, m.id) : null} />
                  </li>
                ))}
            </ul>
          )}
        </Consulta>
      </section>

      <section className="portal-linea" aria-labelledby="portal-linea-titulo">
        <h2 id="portal-linea-titulo" className="sr-only">
          Lo que toca
        </h2>
        <Consulta
          consulta={linea}
          cargando="Cargando tus cuotas, vacunas, desparasitaciones y visitas…"
          error="No pudimos cargar tus cuotas, vacunas, desparasitaciones y visitas."
          vacio="Nada pendiente. Cuando tengas una cuota, una vacuna o una visita, la verás aquí."
          estaVacio={(l) => l.estaciones.length === 0 && !cuenta.data?.proximo_cobro}
        >
          {(l) => (
            <LineaPortal
              elementos={recorrido(conProximoCobro(l.estaciones, cuenta.data?.proximo_cobro, hoy), hoy, orden)}
              hoy={hoy}
              color={l.planes[0]?.color ?? null}
              fin={finDeLinea(plan.data)}
              cuenta={cuenta.data ?? null}
              servicios={servicios.data ?? []}
              sinAgendar={sinAgendar}
              onAgendar={() => setAgendando(true)}
              etiqueta="Tu línea: lo vencido, hoy y lo que viene"
            />
          )}
        </Consulta>
      </section>

      <AgendarModal abierto={agendando} onCerrar={() => setAgendando(false)} />
      <OrientacionModal abierto={orientacion} onCerrar={() => setOrientacion(false)} />
    </div>
  )
}

/** Un peludo con su foto (o su huella) y lo que tiene vencido, que abre su ficha. */
export function AccesoPeludo({
  mascota,
  vencidos,
  detalle,
}: {
  mascota: MascotaRead
  /** null mientras no se sabe: sin la línea no se afirma que esté al día. */
  vencidos: number | null
  detalle?: string
}) {
  return (
    <Link className="acceso-peludo" to={`/portal/mascotas/${mascota.id}`}>
      <span className="acceso-peludo-foto" aria-hidden="true">
        {mascota.foto_url ? <img src={mascota.foto_url} alt="" /> : <Icono nombre="huella" size={20} />}
      </span>
      <span className="acceso-peludo-texto">
        <strong>{mascota.nombre}</strong>
        {detalle && <span>{detalle}</span>}
        {vencidos !== null &&
          (vencidos > 0 ? (
            <span className="acceso-peludo-vencidos">
              {vencidos} {vencidos === 1 ? 'vencido' : 'vencidos'}
            </span>
          ) : (
            <span>Al día</span>
          ))}
      </span>
    </Link>
  )
}

function vencidas(estaciones: EstacionRead[], tipo: EstacionRead['tipo']): number {
  return estaciones.filter((e) => e.tipo === tipo && e.estado === 'vencida').length
}
