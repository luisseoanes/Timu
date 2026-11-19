import { Pestanas } from '@/components/Pestanas'

import { Campanas } from './Campanas'
import { Segmentos } from './Segmentos'

/** Campañas de Comercial (6.16, 6.18). Las encuestas y los mensajes tienen su módulo y las plantillas
 * de WhatsApp las registra Administración (docs/perfiles-y-permisos.md). */
export function CampanasPage() {
  const pestanas = [
    { valor: 'campanas', titulo: 'Campañas', contenido: <Campanas /> },
    { valor: 'segmentos', titulo: 'Segmentos', contenido: <Segmentos /> },
  ]
  return <Pestanas etiqueta="Secciones de campañas" pestanas={pestanas} />
}
