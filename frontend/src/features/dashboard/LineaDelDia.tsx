import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { Icono } from '@/components/Icono'
import { fechaCortaConDia } from '@/lib/formato'

export interface Estacion {
  clave: string
  /** Vencida: roja con alerta. Próxima: lo siguiente, con halo. Futura: lo que viene. */
  estado: 'vencida' | 'proxima' | 'futura'
  titulo: string
  /** Hora de lo que viene («11:00 a. m.»), delante del título y en cifras tabulares. */
  hora?: string
  detalle?: ReactNode
  /** `secundaria`: nunca lleva el verde, aunque sea la primera acción de la línea. */
  accion?: { texto: string; to: string; secundaria?: boolean }
}

const ESTADO_LEIDO: Record<Estacion['estado'], string> = {
  vencida: 'Vencido: ',
  proxima: 'Lo siguiente: ',
  futura: '',
}

function Parada({ e, principal, repetida }: { e: Estacion; principal: boolean; repetida: boolean }) {
  return (
    <li className="inicio-parada" data-estado={e.estado}>
      <span className="inicio-parada-punto" aria-hidden="true">
        {e.estado === 'vencida' && <Icono nombre="alerta" size={12} />}
      </span>
      <div className="inicio-parada-cuerpo">
        <div>
          <h3>
            <span className="sr-only">{ESTADO_LEIDO[e.estado]}</span>
            {e.hora && <span className="inicio-parada-hora numero">{e.hora}</span>}
            {e.titulo}
          </h3>
          {e.detalle && <p>{e.detalle}</p>}
        </div>
        {e.accion && (
          <Link className={principal ? 'btn btn-primario' : 'btn btn-secundario'} to={e.accion.to}>
            {e.accion.texto}
            {/* Cuatro «Ver» y seis «Ver la agenda» se leían iguales (DEU-79): una acción que se
                repite en la línea dice de qué estación es, después de su texto visible. */}
            {repetida && <span className="sr-only">: {e.hora ? `${e.hora} · ` : ''}{e.titulo}</span>}
          </Link>
        )}
      </div>
    </li>
  )
}

/**
 * El día como una línea de metro, de arriba abajo: lo vencido agrupado, la marca de Hoy y lo que
 * viene. La primera estación con acción lleva el único verde de la vista; sin nada después de
 * hoy, la línea cierra con una frase que dice qué aparecerá ahí.
 */
export function LineaDelDia({
  etiqueta,
  hoy,
  antes,
  despues,
  cierre,
}: {
  etiqueta: string
  hoy: string
  antes: Estacion[]
  despues: Estacion[]
  cierre: string
}) {
  const todas = [...antes, ...despues]
  const principal = todas.find((e) => e.accion && !e.accion.secundaria)?.clave
  const repetida = (e: Estacion) => todas.filter((o) => o.accion?.texto === e.accion?.texto).length > 1
  return (
    <ol className="inicio-linea" aria-label={etiqueta}>
      {antes.map((e) => (
        <Parada key={e.clave} e={e} principal={e.clave === principal} repetida={repetida(e)} />
      ))}
      <li className="inicio-linea-hoy">
        <span className="inicio-linea-hoy-marca" aria-hidden="true" />
        <span>Hoy · {fechaCortaConDia(hoy)}</span>
      </li>
      {despues.map((e) => (
        <Parada key={e.clave} e={e} principal={e.clave === principal} repetida={repetida(e)} />
      ))}
      {despues.length === 0 && (
        <li className="inicio-parada" data-estado="futura">
          <span className="inicio-parada-punto" aria-hidden="true" />
          <div className="inicio-parada-cuerpo">
            <p>{cierre}</p>
          </div>
        </li>
      )}
    </ol>
  )
}
