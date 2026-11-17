import type { ReactNode } from 'react'

import { MarcaTimu } from '@/components/MarcaTimu'
import { moneda } from '@/lib/formato'
import type { RegistroRead } from '@/types'

import { ESPECIES_REGISTRO } from './registro'

/**
 * El marco del registro en línea (R3-PUB-02): la franja marina con el logo y, debajo, el contenido
 * con la manada a la derecha (fija en escritorio). Lo comparten el registro, el resultado del pago
 * y el formulario de la familia: es el mismo viaje de la misma familia.
 */
export function MarcoRegistro({ children, aparte }: { children: ReactNode; aparte?: ReactNode }) {
  return (
    <div className="registro">
      <header className="registro-franja">
        <MarcaTimu claro compacta />
      </header>
      <main className="registro-cuerpo">
        {children}
        {aparte}
      </main>
    </div>
  )
}

const nombreEspecie = (codigo: string) => ESPECIES_REGISTRO.find((e) => e.codigo === codigo)?.nombre ?? codigo

/** La manada que eligió la familia, con cada plan en su color y lo que paga o pagó. */
export function ManadaPagada({ registro }: { registro: RegistroRead }) {
  const pagada = registro.estado === 'pagada' || registro.estado === 'completada'
  return (
    <aside className="registro-resumen registro-resumen-quieto" aria-label="Tu afiliación">
      <h2 className="registro-resumen-titulo">Tu manada en {registro.ciudad}</h2>
      <ul className="registro-resumen-lista">
        {registro.peludos.map((p) => (
          <li key={p.posicion}>
            <span className="registro-resumen-quien">
              {p.nombre} <span className="apagado">· {nombreEspecie(p.especie)}</span>
            </span>
            <span className="registro-resumen-plan">
              {p.plan_color && <span className="marcador-plan" data-color={p.plan_color} aria-hidden="true" />}
              {p.plan_nombre ? `${p.plan_nombre} · ` : ''}
              <span className="numero">{moneda(p.valor_mensual)} al mes</span>
            </span>
          </li>
        ))}
      </ul>
      <p className="registro-total">
        <span>{pagada ? 'Pagaste' : 'Por pagar'}</span>
        <strong className="numero">{moneda(registro.valor_inicial)}</strong>
      </p>
    </aside>
  )
}
