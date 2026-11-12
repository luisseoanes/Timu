import { useParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'

import { useEntrada } from './api'
import { HistoriaClinica } from './HistoriaClinica'

/** Una consulta de la historia clínica, abierta junto a la historia de su mascota. */
export function EntradaPage() {
  const { id = '' } = useParams()
  const entrada = useEntrada(id)
  return (
    <Consulta consulta={entrada} cargando="Cargando la consulta…" error="No fue posible cargar la consulta.">
      {(e) => <HistoriaClinica key={e.id} mascotaId={e.mascota_id} entrada={e} />}
    </Consulta>
  )
}
