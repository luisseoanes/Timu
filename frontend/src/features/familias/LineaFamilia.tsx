import { useLayoutEffect, useRef, useState } from 'react'

import { Icono } from '@/components/Icono'
import { fechaCorta, hoyISO } from '@/lib/formato'
import type { ColorPlan, EstacionRead } from '@/types'

import { esHoy, esTramo, orientacion, recorrido, resumen, type Parada } from './linea'

const ESTADO: Record<Parada['estado'], string> = {
  hecha: 'hecha',
  vencida: 'vencida',
  proxima: 'próxima',
  futura: 'programada',
}

function nombre(parada: Parada): string {
  const quees = parada.estaciones
    .map((e) => (e.mascota ? `${e.titulo} de ${e.mascota}` : e.titulo))
    .join(' y ')
  return `${quees}, ${ESTADO[parada.estado]}, ${fechaCorta(parada.fecha)}`
}

/** Lo que se lee bajo la parada: si un día junta varias cosas, la primera y cuántas más. El
 * nombre accesible del botón las dice todas. */
function rotulo(parada: Parada): string {
  const [primera, ...resto] = parada.estaciones
  return resto.length === 0 ? primera.titulo : `${primera.titulo} y ${resto.length} más`
}

/** Color de la línea: el del plan o gris si la familia no tiene. */
type ColorLinea = ColorPlan | 'ninguno'

/** Orientación según el ancho real de la línea y cuántos elementos lleva. Sin ResizeObserver
 * (pruebas en jsdom) se queda horizontal. */
function useOrientacion(elementos: number) {
  const ref = useRef<HTMLOListElement>(null)
  const [valor, setValor] = useState<'horizontal' | 'vertical'>('horizontal')
  useLayoutEffect(() => {
    const lista = ref.current
    if (!lista || typeof ResizeObserver === 'undefined') return
    // En el celular siempre vertical: sin cursor, los rótulos que aparecen al pasar por encima
    // no se verían nunca.
    const estrecha = window.matchMedia?.('(max-width: 600px)')
    const medir = () =>
      setValor(
        estrecha?.matches ? 'vertical' : orientacion(lista.parentElement?.clientWidth ?? lista.clientWidth, elementos),
      )
    medir()
    const observador = new ResizeObserver(medir)
    observador.observe(lista.parentElement ?? lista)
    return () => observador.disconnect()
  }, [elementos])
  return [ref, valor] as const
}

/**
 * La línea completa de la familia, como un plano de metro: el año entero en una línea, «hoy»
 * marcado, lo próximo y lo vencido siempre rotulado. Activar una parada la entrega a
 * `onActivar`, que abre la sección donde se atiende.
 */
export function LineaFamilia({
  estaciones,
  color = 'ninguno',
  onActivar,
}: {
  estaciones: EstacionRead[]
  color?: ColorLinea
  onActivar?: (parada: Parada) => void
}) {
  const [desplegado, setDesplegado] = useState(false)
  const elementos = recorrido(estaciones, hoyISO(), desplegado)
  const [ref, forma] = useOrientacion(elementos.length)
  if (estaciones.length === 0) {
    return (
      <p className="linea-vacia">
        Sin cuotas, preventivos ni servicios en el último medio año ni en el próximo.
      </p>
    )
  }
  return (
    <ol ref={ref} className="linea" data-color={color} data-orientacion={forma} aria-label="Línea de la familia">
      {elementos.map((el, i) => {
        if (esHoy(el)) {
          return (
            <li key="hoy" className="linea-hoy" aria-current="date">
              <span className="linea-hoy-marca" aria-hidden="true" />
              <span className="linea-hoy-texto">Hoy</span>
            </li>
          )
        }
        if (esTramo(el)) {
          return (
            <li key="tramo" className="linea-tramo">
              <button className="linea-tramo-boton" type="button" onClick={() => setDesplegado(true)}>
                {el.paradas.length} hechas
              </button>
            </li>
          )
        }
        const siempre = el.estado === 'vencida' || el.estado === 'proxima'
        return (
          <li key={`${el.fecha}-${i}`} className="parada" data-estado={el.estado} data-rotulada={siempre}>
            <button className="parada-punto" type="button" aria-label={nombre(el)} onClick={() => onActivar?.(el)}>
              {el.estado === 'vencida' && <Icono nombre="alerta" size={12} />}
            </button>
            <span className="parada-etiqueta" aria-hidden="true">
              <strong>{rotulo(el)}</strong>
              <span>{fechaCorta(el.fecha)}</span>
            </span>
          </li>
        )
      })}
    </ol>
  )
}

/** La línea en miniatura de una fila del listado: dibujo para quien ve, resumen para quien no. */
export function LineaMini({ estaciones, color = 'ninguno' }: { estaciones: EstacionRead[]; color?: ColorLinea }) {
  const elementos = recorrido(estaciones, hoyISO())
  return (
    <span className="linea-mini" data-color={color} role="img" aria-label={resumen(estaciones, fechaCorta)}>
      {elementos.map((el, i) =>
        esHoy(el) ? (
          <span key="hoy" className="linea-mini-hoy" />
        ) : esTramo(el) ? (
          <span key="tramo" className="linea-mini-punto" data-estado="hecha" />
        ) : (
          <span key={`${el.fecha}-${i}`} className="linea-mini-punto" data-estado={el.estado} />
        ),
      )}
    </span>
  )
}
