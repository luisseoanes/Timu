import { Pestanas } from '@/components/Pestanas'
import { useAuth } from '@/features/auth'
import { puede } from '@/lib/permisos'

import { Remisiones } from './Remisiones'
import { Clinicas } from './Clinicas'
import { Liquidacion } from './Liquidacion'

export function AliadasPage() {
  const { usuario } = useAuth()
  const pestanas = [
    { valor: 'remisiones', titulo: 'Remisiones', contenido: <Remisiones /> },
    { valor: 'clinicas', titulo: 'Clínicas y convenios', contenido: <Clinicas /> },
  ]
  if (puede(usuario, 'administrar')) pestanas.push({ valor: 'liquidacion', titulo: 'Liquidación', contenido: <Liquidacion /> })
  return <Pestanas etiqueta="Secciones de aliadas" pestanas={pestanas} />
}
