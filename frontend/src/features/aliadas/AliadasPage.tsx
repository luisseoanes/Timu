import { useSearchParams } from 'react-router-dom'

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
  // La pestaña vive en la URL: la ficha de una clínica lleva a sus remisiones (`?pestana=remisiones`).
  const [params, setParams] = useSearchParams()
  const pestana = pestanas.find((p) => p.valor === params.get('pestana'))?.valor ?? 'remisiones'
  function cambiar(valor: string) {
    const siguiente = new URLSearchParams(params)
    siguiente.set('pestana', valor)
    setParams(siguiente, { replace: true })
  }
  return <Pestanas etiqueta="Secciones de aliadas" pestanas={pestanas} valor={pestana} onCambio={cambiar} />
}
