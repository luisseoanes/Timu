import { moneda } from '@/lib/formato'
import type { PlanPublico } from '@/types'

import { tarifaCon } from './registro'

/**
 * Los planes lado a lado (R3-PUB-02): el precio, cada servicio, los adicionales y sus condiciones,
 * con cada plan en su color. Lo que es igual en todos se dice una vez. Lo usan el registro y la
 * portada (R3-PUB-04).
 */
export function Comparador({
  id,
  planes,
  titulo,
  totalPeludos,
}: {
  id?: string
  planes: PlanPublico[]
  /** Lo que dice la tabla a un lector de pantalla. */
  titulo: string
  totalPeludos: number
}) {
  // Las filas: el precio, cada servicio que trae alguno de los planes y sus condiciones.
  const servicios = new Map<string, string>()
  for (const p of planes) for (const b of p.beneficios) if (!servicios.has(b.tipo_servicio_codigo)) servicios.set(b.tipo_servicio_codigo, b.nombre)
  const filas: [string, string, (p: PlanPublico) => string][] = [
    ['valor', 'Al mes', (p) => moneda(tarifaCon(p, totalPeludos))],
    ...[...servicios].map(
      ([codigo, servicio]): [string, string, (p: PlanPublico) => string] => [
        codigo,
        servicio,
        (p) => p.beneficios.find((b) => b.tipo_servicio_codigo === codigo)?.texto ?? 'No incluye',
      ],
    ),
  ]
  // Lo que dan sin ser un servicio que se agenda (R3-PUB-04): el servicio fúnebre, lo de terceros.
  const adicionales = [...new Set(planes.flatMap((p) => p.adicionales.map((a) => a.nombre)))]
  for (const nombre of adicionales)
    filas.push([`adicional:${nombre}`, nombre, (p) => p.adicionales.find((a) => a.nombre === nombre)?.cubre ?? 'No incluye'])
  if (planes.some((p) => p.carencia)) filas.push(['carencia', 'Carencia', (p) => p.carencia ?? '—'])
  if (planes.some((p) => p.exclusiones)) filas.push(['exclusiones', 'No cubre', (p) => p.exclusiones ?? '—'])
  return (
    <div id={id} className="registro-comparador">
      <table className="tabla">
        <caption className="sr-only">{titulo}</caption>
        <thead>
          <tr>
            <th>Servicio</th>
            {planes.map((p) => (
              <th key={p.id} data-color={p.color}>
                {p.nombre}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filas.map(([clave, servicio, valor]) => {
            const valores = planes.map(valor)
            // Lo que es igual en todos se dice una vez: la diferencia salta a la vista.
            const igual = valores.every((v) => v === valores[0])
            return (
              <tr key={clave}>
                <td className="principal" data-etiqueta="Servicio">
                  {servicio}
                </td>
                {igual ? (
                  <td colSpan={planes.length} className="registro-comparador-igual">
                    <span>
                      {valores[0]} <span className="registro-comparador-nota">· igual en los {planes.length}</span>
                    </span>
                  </td>
                ) : (
                  planes.map((p, i) => (
                    <td key={p.id} className="registro-comparador-valor">
                      {/* Apilado (en el celular), cada valor dice de qué plan es, con su color. */}
                      <span className="registro-comparador-plan" aria-hidden="true">
                        <span className="marcador-plan" data-color={p.color} />
                        {p.nombre}
                      </span>
                      <span>{valores[i]}</span>
                    </td>
                  ))
                )}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
