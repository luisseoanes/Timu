import type { UseQueryResult } from '@tanstack/react-query'
import { useEffect, useRef, type KeyboardEvent } from 'react'

import { Consulta } from '@/components/Consulta'
import { Icono } from '@/components/Icono'

import type { Evolucion, MesEvolucion, ValoresIndicadores } from './api'
import { useDefiniciones } from './api'
import { CIFRAS, contraQue, formatear, variacion, type CodigoCifra, type DefCifra, type Serie, type Variacion } from './cifras'
import { GraficoSerie } from './GraficoSerie'
import { useAncho } from './useAncho'

const SERIE_ID = 'inicio-serie'

/** La serie en miniatura de una cifra: solo dibujo, en píxeles para no deformar el punto. Como
 * la serie en grande, corta en los meses sin dato y dibuja punteado el mes en curso. */
function Tendencia({ meses, serie }: { meses: MesEvolucion[]; serie: Serie }) {
  const [ref, ancho] = useAncho<HTMLSpanElement>(160)
  const valores = meses.map((m) => serie.valor(m.indicadores) ?? null)
  const conDato = valores.filter((v): v is number => v !== null)
  if (conDato.length < 2) return <span ref={ref} className="inicio-tendencia" aria-hidden="true" />
  const [bajo, alto] = [Math.min(...conDato), Math.max(...conDato)]
  const n = valores.length - 1
  const x = (i: number) => 4 + (i / n) * (ancho - 8)
  const y = (v: number) => 30 - ((v - bajo) / (alto - bajo || 1)) * 24
  const enCurso = meses[n]?.parcial ? n : null
  const tramos: string[] = []
  let actual: string[] = []
  valores.forEach((v, i) => {
    if (v === null || i === enCurso) {
      if (actual.length > 1) tramos.push(actual.join(' '))
      actual = []
      return
    }
    actual.push(`${actual.length ? 'L' : 'M'}${x(i)},${y(v)}`)
  })
  if (actual.length > 1) tramos.push(actual.join(' '))
  const [previo, ultimo] = enCurso === null ? [null, null] : [valores[enCurso - 1], valores[enCurso]]
  return (
    <span ref={ref} className="inicio-tendencia" aria-hidden="true">
      <svg width={ancho} height={36}>
        {tramos.map((d) => (
          <path key={d} d={d} />
        ))}
        {enCurso !== null && previo !== null && ultimo !== null && (
          <path className="inicio-tendencia-en-curso" d={`M${x(enCurso - 1)},${y(previo)} L${x(enCurso)},${y(ultimo)}`} />
        )}
        {enCurso !== null && ultimo !== null && <circle cx={x(enCurso)} cy={y(ultimo)} r={3} />}
      </svg>
    </span>
  )
}

function TextoVariacion({ v }: { v: Variacion }) {
  if (v.direccion === 'igual') return <span className="inicio-variacion" data-tono="neutra">Sin cambio</span>
  return (
    <span className="inicio-variacion" data-tono={v.tono}>
      <Icono nombre={v.direccion === 'sube' ? 'arriba' : 'abajo'} size={14} />
      <span className="sr-only">{v.direccion === 'sube' ? 'Sube' : 'Baja'}</span>
      {v.texto}
    </span>
  )
}

function valorDe(def: DefCifra, v: Partial<ValoresIndicadores> | undefined) {
  return v ? def.series[0].valor(v) : undefined
}

/**
 * Las cifras del período en una franja, cada una con su variación y su serie en miniatura. Cada
 * cifra es un botón: abre debajo su serie de 12 meses en grande (el gesto del «Cuadro»).
 */
export function FranjaCifras({
  orden,
  indicadores,
  evolucion,
  abierta,
  onAbrir,
}: {
  orden: CodigoCifra[]
  indicadores: ValoresIndicadores
  evolucion: UseQueryResult<Evolucion>
  abierta: CodigoCifra | null
  onAbrir: (codigo: CodigoCifra | null) => void
}) {
  const botones = useRef(new Map<CodigoCifra, HTMLButtonElement>())
  const definiciones = useDefiniciones(abierta !== null)
  const datos = evolucion.data
  const contra = contraQue(datos)

  // En el celular la serie se abre debajo de la franja, fuera de la vista: se trae a ella.
  useEffect(() => {
    if (abierta) document.getElementById(SERIE_ID)?.scrollIntoView?.({ block: 'nearest' })
  }, [abierta])

  function cerrar() {
    if (!abierta) return
    botones.current.get(abierta)?.focus()
    onAbrir(null)
  }

  function teclado(e: KeyboardEvent<HTMLDivElement>) {
    if (e.key === 'Escape' && abierta) {
      e.preventDefault()
      cerrar()
    }
  }

  const def = abierta ? CIFRAS[abierta] : null
  const formula = def && definiciones.data?.find((d) => d.codigo === def.indicador)?.formula
  const vAbierta = def && variacion(def, valorDe(def, indicadores), valorDe(def, datos?.anterior.indicadores))

  return (
    <div className="inicio-cifras" onKeyDown={teclado}>
      <ul className="inicio-franja" aria-label="Cifras del período">
        {orden.map((codigo) => {
          const c = CIFRAS[codigo]
          const actual = valorDe(c, indicadores)
          const v = variacion(c, actual, valorDe(c, datos?.anterior.indicadores))
          return (
            <li key={codigo}>
              <button
                ref={(b) => {
                  if (b) botones.current.set(codigo, b)
                }}
                type="button"
                className="inicio-cifra"
                aria-expanded={abierta === codigo}
                aria-controls={SERIE_ID}
                onClick={() => onAbrir(abierta === codigo ? null : codigo)}
              >
                <span className="inicio-cifra-titulo">{c.titulo}</span>
                <span className="inicio-cifra-valor">{formatear(actual, c.escala)}</span>
                {v ? (
                  <TextoVariacion v={v} />
                ) : (
                  actual != null &&
                  datos && (
                    <span className="inicio-variacion" data-tono="neutra">
                      Sin dato para comparar
                    </span>
                  )
                )}
                <span className="inicio-cifra-detalle">{c.detalle(indicadores)}</span>
                <Tendencia meses={datos?.meses ?? []} serie={c.series[0]} />
              </button>
            </li>
          )
        })}
      </ul>
      {def && (
        <section id={SERIE_ID} className="inicio-panel inicio-serie" aria-labelledby="inicio-serie-titulo">
          <div className="inicio-serie-cabeza">
            <div>
              <h2 id="inicio-serie-titulo">{def.titulo} en los últimos 12 meses</h2>
              <p className="inicio-serie-resumen">
                <strong className="numero">{formatear(valorDe(def, indicadores), def.escala)}</strong> en el período
                {vAbierta && (
                  <>
                    {' · '}
                    <TextoVariacion v={vAbierta} /> {contra}
                  </>
                )}
              </p>
              {formula && <p className="inicio-serie-formula">{formula}</p>}
            </div>
            <button className="btn btn-plano btn-icono" type="button" aria-label="Cerrar la serie" onClick={cerrar}>
              <Icono nombre="cerrar" size={18} />
            </button>
          </div>
          <Consulta consulta={evolucion} cargando="Calculando la serie…" error="No fue posible calcular la serie.">
            {(d) => <GraficoSerie titulo={def.titulo} meses={d.meses} series={def.series} escala={def.escala} />}
          </Consulta>
        </section>
      )}
    </div>
  )
}
