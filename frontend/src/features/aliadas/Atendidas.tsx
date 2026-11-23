import { useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { fechaCorta, hoyISO, moneda } from '@/lib/formato'

import { useAtendidas } from './api'

const MES = new Intl.DateTimeFormat('es-CO', { month: 'long', year: 'numeric' })
const MESES_ATRAS = 12

interface Mes {
  /** `2026-11` */
  valor: string
  /** «noviembre de 2026» */
  nombre: string
  desde: string
  hasta: string
}

/** El mes en curso y los doce anteriores, del más reciente al más antiguo. */
function meses(hoy = hoyISO()): Mes[] {
  const [anio, mes] = hoy.split('-').map(Number)
  return Array.from({ length: MESES_ATRAS + 1 }, (_, n) => {
    const inicio = new Date(anio, mes - 1 - n, 1)
    const valor = `${inicio.getFullYear()}-${String(inicio.getMonth() + 1).padStart(2, '0')}`
    const ultimo = new Date(inicio.getFullYear(), inicio.getMonth() + 1, 0).getDate()
    return { valor, nombre: MES.format(inicio), desde: `${valor}-01`, hasta: `${valor}-${String(ultimo).padStart(2, '0')}` }
  })
}

/** Lo que la clínica ya atendió en el mes y lo que cubrió TIMU: para cuadrar con la liquidación. */
export function Atendidas() {
  const [params, setParams] = useSearchParams()
  const opciones = meses()
  const elegido = opciones.find((m) => m.valor === params.get('mes')) ?? opciones[0]
  const atendidas = useAtendidas(elegido.desde, elegido.hasta)
  const enCurso = elegido === opciones[0]

  return (
    <section className="aliada-panel aliada-atendidas" aria-labelledby="aliada-atendidas-titulo">
      <div className="aliada-atendidas-cabeza">
        <h2 id="aliada-atendidas-titulo">Atendidas</h2>
        <label className="campo">
          <span className="sr-only">Mes</span>
          <select
            className="input"
            value={elegido.valor}
            onChange={(e) => {
              const siguiente = new URLSearchParams(params)
              if (e.target.value === opciones[0].valor) siguiente.delete('mes')
              else siguiente.set('mes', e.target.value)
              setParams(siguiente, { replace: true })
            }}
          >
            {opciones.map((m) => (
              <option key={m.valor} value={m.valor}>
                {m.nombre}
              </option>
            ))}
          </select>
        </label>
      </div>
      <Consulta consulta={atendidas} cargando="Cargando lo atendido…" error="No pudimos cargar lo atendido.">
        {(a) => (
          <>
            {/* Sin atenciones, la frase basta: cuatro ceros no dicen nada más. */}
            {a.atenciones > 0 && (
            <dl className="cifras">
              <div>
                <dt>Atenciones</dt>
                <dd className="numero">{a.atenciones}</dd>
              </div>
              <div>
                <dt>Facturado</dt>
                <dd className="numero">{moneda(a.valor_atenciones)}</dd>
              </div>
              <div>
                <dt>TIMU cubrió</dt>
                <dd className="numero">{moneda(a.valor_cubierto)}</dd>
              </div>
              <div>
                <dt>Pagaron las familias</dt>
                <dd className="numero">{moneda(a.valor_familias)}</dd>
              </div>
            </dl>
            )}
            {a.items.length === 0 ? (
              <p className="aliada-nota">
                {enCurso
                  ? 'Todavía no hay atenciones reportadas este mes. Al reportar una, aparece aquí con lo que cubre TIMU.'
                  : `No se reportaron atenciones en ${elegido.nombre}.`}
              </p>
            ) : (
              <ul className="aliada-atendidas-lista">
                {a.items.map((i) => (
                  <li key={i.codigo}>
                    <strong>
                      {i.titular} · {i.mascota}
                    </strong>
                    <span>
                      <span className="numero">{fechaCorta(i.fecha_atencion)}</span> · {i.motivo}
                    </span>
                    <span className="numero">
                      {moneda(i.valor_atencion)} · TIMU cubrió {moneda(i.valor_cubierto)} · {i.codigo}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </Consulta>
    </section>
  )
}
