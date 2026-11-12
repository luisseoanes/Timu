import { Insignia } from '@/components/Distintivo'
import { useEspecies } from '@/features/catalogos'
import { edad, fecha, moneda } from '@/lib/formato'
import type { FamiliaRead, PlanDeFamiliaRead } from '@/types'

import { useEstadoCuenta } from './api'

/** Los peludos de la familia con su plan, siempre a la vista bajo la línea (contrato del panel). */
export function ResumenMascotas({ familia, planes }: { familia: FamiliaRead; planes: PlanDeFamiliaRead[] }) {
  const activas = familia.mascotas?.filter((m) => m.activa) ?? []
  const especies = useEspecies()
  const nombreEspecie = (codigo: string) => especies.data?.find((e) => e.codigo === codigo)?.nombre ?? codigo
  return (
    <section className="resumen" aria-labelledby="resumen-mascotas">
      <h3 id="resumen-mascotas">Mascotas</h3>
      {activas.length === 0 ? (
        <p className="apagado">Sin mascotas activas. Agrégalas desde la pestaña Mascotas.</p>
      ) : (
        <ul className="resumen-filas">
          {activas.map((m) => {
            const plan = planes.find((p) => p.mascotas.includes(m.nombre))
            const datos = [nombreEspecie(m.especie), edad(m.fecha_nacimiento), m.peso_kg ? `${m.peso_kg} kg` : null].filter(Boolean)
            return (
              <li key={m.id}>
                <strong>{m.nombre}</strong>
                <span className="apagado">{datos.join(' · ')}</span>
                {plan ? (
                  <span className="familia-fila-marcador">
                    <span className="marcador-plan" data-color={plan.color} aria-hidden="true" />
                    {plan.nombre}
                  </span>
                ) : (
                  <span className="apagado">Sin plan</span>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}

/** La cartera en tres datos: cuota, próximo cobro y lo vencido. El detalle va en su pestaña. */
export function ResumenCartera({ familiaId }: { familiaId: string }) {
  const cuenta = useEstadoCuenta(familiaId)
  return (
    <section className="resumen" aria-labelledby="resumen-cartera">
      <h3 id="resumen-cartera">Cartera</h3>
      {cuenta.isPending ? (
        <div className="esqueleto" role="status">
          <span className="sr-only">Cargando la cartera…</span>
          <span className="esqueleto-linea" aria-hidden="true" />
        </div>
      ) : cuenta.isError ? (
        <p className="error">No fue posible cargar la cartera.</p>
      ) : cuenta.data === null ? (
        <p className="apagado">Sin contrato: no hay cuotas ni pagos.</p>
      ) : (
        <dl className="resumen-datos">
          <div>
            <dt>Cuota {cuenta.data.contrato.periodicidad}</dt>
            <dd className="numero">{moneda(cuenta.data.contrato.valor_periodo)}</dd>
          </div>
          <div>
            <dt>Próximo cobro</dt>
            <dd className="numero">
              {cuenta.data.proximo_cobro
                ? `${fecha(cuenta.data.proximo_cobro.fecha)} · ${moneda(cuenta.data.proximo_cobro.valor)}`
                : '—'}
            </dd>
          </div>
          <div>
            <dt>Vencido</dt>
            <dd>
              {Number(cuenta.data.saldo_vencido) > 0 ? (
                <Insignia tono="peligro">{moneda(cuenta.data.saldo_vencido)}</Insignia>
              ) : (
                <Insignia tono="ok">Al día</Insignia>
              )}
            </dd>
          </div>
        </dl>
      )}
    </section>
  )
}
