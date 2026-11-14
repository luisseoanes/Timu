import { useState, type KeyboardEvent, type PointerEvent } from 'react'

import { dominio, formatear, formatearEje, mesCorto, mesLargo, type Escala, type Serie } from './cifras'
import type { MesEvolucion } from './api'
import { useAncho } from './useAncho'

const MARGEN = { arriba: 12, derecha: 20, abajo: 44, izquierda: 64 }
/** Los dos colores de un gráfico de dos series: la 1 y la 3 del manual. La 1 y la 2 (verde y
 * naranja) son casi iguales para quien no distingue el rojo del verde (ΔE 2,7, validado con la
 * skill dataviz), así que nunca van juntas. */
const COLORES = ['var(--serie-1)', 'var(--serie-3)'] as const

/**
 * La serie de 12 meses de una cifra: un eje, una o dos líneas, el mes en curso marcado y la cruz
 * que da el valor de cada mes con el cursor o con las flechas. La tabla de debajo da los mismos
 * datos sin el gráfico.
 */
export function GraficoSerie({
  titulo,
  meses,
  series,
  escala,
  compacto = false,
}: {
  titulo: string
  meses: MesEvolucion[]
  series: Serie[]
  escala: Escala
  /** Más bajo, para la columna del Inicio. */
  compacto?: boolean
}) {
  const [ref, ancho] = useAncho<HTMLDivElement>(720, 260)
  const ALTO = compacto ? 180 : 240
  const [activo, setActivo] = useState<number | null>(null)
  const [anuncio, setAnuncio] = useState('')

  const valores = series.map((s) => meses.map((m) => s.valor(m.indicadores) ?? null))
  const { min, max, marcas } = dominio(escala, valores.flat().filter((v): v is number => v !== null))
  const n = meses.length
  const plano = ancho - MARGEN.izquierda - MARGEN.derecha
  const x = (i: number) => MARGEN.izquierda + (n > 1 ? (i * plano) / (n - 1) : plano / 2)
  const y = (v: number) => MARGEN.arriba + (1 - (v - min) / (max - min)) * (ALTO - MARGEN.arriba - MARGEN.abajo)
  const cadaCuanto = plano / n >= 44 ? 1 : 2
  const rotulados = meses.map((_, i) => i).filter((i) => i % cadaCuanto === (n - 1) % cadaCuanto)
  const enCurso = meses[n - 1]?.parcial ? n - 1 : null

  const leer = (i: number) =>
    `${mesLargo(meses[i])}: ${series.map((s, j) => `${s.nombre} ${formatear(valores[j][i], escala)}`).join(', ')}`

  function mover(e: PointerEvent<SVGRectElement>) {
    const caja = e.currentTarget.getBoundingClientRect()
    const relativo = ((e.clientX - caja.left) / caja.width) * plano
    setActivo(Math.min(n - 1, Math.max(0, Math.round((relativo / plano) * (n - 1)))))
  }

  function teclado(e: KeyboardEvent<HTMLDivElement>) {
    const actual = activo ?? n - 1
    const siguiente =
      e.key === 'ArrowRight' ? Math.min(n - 1, actual + 1)
        : e.key === 'ArrowLeft' ? Math.max(0, actual - 1)
          : e.key === 'Home' ? 0
            : e.key === 'End' ? n - 1
              : null
    if (siguiente === null) return
    e.preventDefault()
    setActivo(siguiente)
    setAnuncio(leer(siguiente))
  }

  /** Tramos con dato seguido; el del mes en curso se dibuja aparte, punteado. */
  function trazos(serie: (number | null)[]) {
    const completos: string[] = []
    let actual: string[] = []
    serie.forEach((v, i) => {
      if (v === null || i === enCurso) {
        if (actual.length > 1) completos.push(actual.join(' '))
        actual = []
        return
      }
      actual.push(`${actual.length ? 'L' : 'M'}${x(i)},${y(v)}`)
    })
    if (actual.length > 1) completos.push(actual.join(' '))
    const previo = enCurso === null ? null : serie[enCurso - 1]
    const ultimo = enCurso === null ? null : serie[enCurso]
    const enCursoTrazo =
      enCurso !== null && previo != null && ultimo != null
        ? `M${x(enCurso - 1)},${y(previo)} L${x(enCurso)},${y(ultimo)}`
        : null
    return { completos, enCursoTrazo }
  }

  const izquierdaTooltip = activo === null ? 0 : Math.min(Math.max(x(activo), 110), ancho - 110)

  return (
    <div className="grafico">
      {series.length > 1 && (
        <ul className="grafico-leyenda" aria-label="Series">
          {series.map((s, j) => (
            <li key={s.nombre}>
              <span className="grafico-clave" style={{ background: COLORES[j] }} aria-hidden="true" />
              {s.nombre}
            </li>
          ))}
        </ul>
      )}
      <div
        ref={ref}
        className="grafico-lienzo"
        role="group"
        aria-label={`${titulo} mes a mes. Recorre los meses con las flechas.`}
        tabIndex={0}
        onKeyDown={teclado}
        onFocus={() => {
          const i = activo ?? n - 1
          setActivo(i)
          setAnuncio(leer(i))
        }}
        onBlur={() => setActivo(null)}
      >
        <svg width={ancho} height={ALTO} aria-hidden="true">
          {marcas.map((m) => (
            <g key={m}>
              <line className="grafico-rejilla" x1={MARGEN.izquierda} x2={ancho - MARGEN.derecha} y1={y(m)} y2={y(m)} />
              <text className="grafico-eje" x={MARGEN.izquierda - 8} y={y(m)} textAnchor="end" dominantBaseline="middle">
                {formatearEje(m, escala)}
              </text>
            </g>
          ))}
          {meses.map((m, i) => {
            const rotulado = rotulados.includes(i)
            // El año va bajo el primer mes rotulado y donde cambia: «dic» solo no dice de qué año es.
            const previo = rotulados[rotulados.indexOf(i) - 1]
            const anio =
              rotulado && (previo === undefined || meses[previo].periodo.desde.slice(0, 4) !== m.periodo.desde.slice(0, 4))
                ? m.periodo.desde.slice(0, 4)
                : null
            return (
              <g key={m.periodo.desde}>
                {rotulado && (
                  <text className="grafico-eje" x={x(i)} y={ALTO - MARGEN.abajo + 18} textAnchor="middle">
                    {mesCorto(m.periodo.desde)}
                  </text>
                )}
                {anio && (
                  <text className="grafico-eje grafico-eje-anio" x={x(i)} y={ALTO - MARGEN.abajo + 34} textAnchor="middle">
                    {anio}
                  </text>
                )}
              </g>
            )
          })}
          {activo !== null && <line className="grafico-cruz" x1={x(activo)} x2={x(activo)} y1={MARGEN.arriba} y2={ALTO - MARGEN.abajo} />}
          {valores.map((serie, j) => {
            const { completos, enCursoTrazo } = trazos(serie)
            const ultimo = serie.reduce<number | null>((u, v, i) => (v === null ? u : i), null)
            return (
              <g key={series[j].nombre} style={{ color: COLORES[j] }}>
                {completos.map((d) => (
                  <path key={d} className="grafico-linea" d={d} />
                ))}
                {enCursoTrazo && <path className="grafico-linea grafico-linea-en-curso" d={enCursoTrazo} />}
                {ultimo !== null && (
                  <circle
                    className={ultimo === enCurso ? 'grafico-punto grafico-punto-en-curso' : 'grafico-punto'}
                    cx={x(ultimo)}
                    cy={y(serie[ultimo]!)}
                    r={4}
                  />
                )}
                {activo !== null && serie[activo] !== null && <circle className="grafico-punto" cx={x(activo)} cy={y(serie[activo]!)} r={4} />}
              </g>
            )
          })}
          <rect
            className="grafico-zona"
            x={MARGEN.izquierda}
            y={0}
            width={plano}
            height={ALTO}
            onPointerMove={mover}
            onPointerLeave={() => setActivo(null)}
          />
        </svg>
        {activo !== null && (
          <div className="grafico-tooltip" style={{ left: izquierdaTooltip }} aria-hidden="true">
            <span className="grafico-tooltip-mes">{mesLargo(meses[activo])}</span>
            {series.map((s, j) => (
              <span key={s.nombre} className="grafico-tooltip-fila">
                <span className="grafico-clave" style={{ background: COLORES[j] }} />
                <strong className="numero">{formatear(valores[j][activo], escala)}</strong>
                {s.nombre}
              </span>
            ))}
          </div>
        )}
        <span className="sr-only" aria-live="polite">
          {anuncio}
        </span>
      </div>
      {enCurso !== null && (
        <p className="grafico-nota">
          <span className="grafico-clave grafico-clave-en-curso" aria-hidden="true" />
          {mesLargo(meses[enCurso])}: el mes está en curso.
        </p>
      )}
      <details className="grafico-datos">
        <summary>Ver los datos</summary>
        <div className="scroll-x">
          <table className="tabla tabla-apilable">
            <thead>
              <tr>
                <th scope="col">Mes</th>
                {series.map((s) => (
                  <th key={s.nombre} scope="col" className="numero">
                    {s.nombre}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {meses.map((m, i) => (
                <tr key={m.periodo.desde}>
                  <td data-etiqueta="Mes">{mesLargo(m)}</td>
                  {series.map((s, j) => (
                    <td key={s.nombre} data-etiqueta={s.nombre} className="numero">
                      {formatear(valores[j][i], escala)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  )
}
