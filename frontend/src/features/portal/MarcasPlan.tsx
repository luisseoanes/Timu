import type { PlanPortal } from './api'
import { planesDe } from './plan'

/** El plan de la familia con el cuadrado de su color, como en el carnet impreso: uno por plan y,
 * si los peludos tienen planes distintos, a quién cubre cada uno. Lo usan el inicio y Pagos. */
export function MarcasPlan({ plan }: { plan: PlanPortal }) {
  return planesDe(plan).map((pl, _, todos) => (
    <span key={pl.nombre} className="portal-plan-marca">
      <span className="marcador-plan" data-color={pl.color} aria-hidden="true" />
      {pl.nombre}
      {todos.length > 1 && <span className="apagado"> · {pl.mascotas.join(' y ')}</span>}
    </span>
  ))
}
