import { useSearchParams } from 'react-router-dom'

import { Pestanas } from '@/components/Pestanas'
import { useAuth } from '@/features/auth'
import { puede } from '@/lib/permisos'

import { Remisiones } from './Remisiones'
import { Clinicas } from './Clinicas'
import { Liquidacion } from './Liquidacion'

export function AliadasPage() {
  const { usuario } = useAuth()
  // Cada perfil, su parte (Sección 12): Atención emite las remisiones, Operaciones lleva la red y
  // su liquidación, y Gerencia ve la liquidación como informe.
  const pestanas = [
    puede(usuario, 'remisiones') && { valor: 'remisiones', titulo: 'Remisiones', contenido: <Remisiones /> },
    puede(usuario, 'redAliadas') && { valor: 'clinicas', titulo: 'Clínicas y convenios', contenido: <Clinicas /> },
    puede(usuario, 'liquidacion') && { valor: 'liquidacion', titulo: 'Liquidación', contenido: <Liquidacion /> },
  ].filter((p) => p !== false)
  // La pestaña vive en la URL: la ficha de una clínica lleva a sus remisiones (`?pestana=remisiones`).
  const [params, setParams] = useSearchParams()
  const pestana = pestanas.find((p) => p.valor === params.get('pestana'))?.valor ?? pestanas[0]?.valor
  function cambiar(valor: string) {
    const siguiente = new URLSearchParams(params)
    siguiente.set('pestana', valor)
    setParams(siguiente, { replace: true })
  }
  return <Pestanas etiqueta="Secciones de aliadas" pestanas={pestanas} valor={pestana} onCambio={cambiar} />
}
