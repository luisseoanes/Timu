import { useParams, useSearchParams } from 'react-router-dom'

import { HistoriaClinica } from './HistoriaClinica'

/**
 * Historia clínica de una mascota. `?nueva=1` abre una consulta nueva; `?servicio=` abre la de esa
 * visita (desde Rutas): continúa su borrador, enseña la ya firmada o empieza una enlazada a él.
 */
export function HistoriaMascotaPage() {
  const { mascotaId = '' } = useParams()
  const [params] = useSearchParams()
  return (
    <HistoriaClinica
      key={`${mascotaId}-${params.toString()}`}
      mascotaId={mascotaId}
      nueva={params.get('nueva') === '1'}
      servicioId={params.get('servicio') ?? undefined}
    />
  )
}
