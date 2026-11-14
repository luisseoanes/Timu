import { Pestanas } from '@/components/Pestanas'
import { useAuth } from '@/features/auth'
import { puede } from '@/lib/permisos'

import { Campanas } from './Campanas'
import { Encuestas } from './Encuestas'
import { Mensajes } from './Mensajes'
import { PlantillasWhatsApp } from './PlantillasWhatsApp'
import { Segmentos } from './Segmentos'

export function CampanasPage() {
  const { usuario } = useAuth()
  const pestanas = [
    { valor: 'campanas', titulo: 'Campañas', contenido: <Campanas /> },
    { valor: 'segmentos', titulo: 'Segmentos', contenido: <Segmentos /> },
    { valor: 'encuestas', titulo: 'Encuestas', contenido: <Encuestas /> },
    { valor: 'mensajes', titulo: 'Mensajes', contenido: <Mensajes /> },
  ]
  if (puede(usuario, 'mercadeo')) pestanas.push({ valor: 'plantillas', titulo: 'Plantillas de WhatsApp', contenido: <PlantillasWhatsApp /> })
  return <Pestanas etiqueta="Secciones de campañas" pestanas={pestanas} />
}
