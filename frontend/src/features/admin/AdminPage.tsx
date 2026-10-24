import { Pestanas } from '@/components/Pestanas'

import { Catalogos } from './Catalogos'
import { InteligenciaArtificial } from './InteligenciaArtificial'
import { Planes } from './Planes'
import { Reglas } from './Reglas'
import { Reportes } from './Reportes'
import { Usuarios } from './Usuarios'

/** Administración de la plataforma: sólo el perfil admin llega aquí (App.tsx). */
export function AdminPage() {
  return (
    <Pestanas
      etiqueta="Secciones de administración"
      pestanas={[
        { valor: 'usuarios', titulo: 'Usuarios', contenido: <Usuarios /> },
        { valor: 'planes', titulo: 'Planes', contenido: <Planes /> },
        { valor: 'reglas', titulo: 'Reglas', contenido: <Reglas /> },
        { valor: 'catalogos', titulo: 'Catálogos', contenido: <Catalogos /> },
        { valor: 'ia', titulo: 'Inteligencia artificial', contenido: <InteligenciaArtificial /> },
        { valor: 'reportes', titulo: 'Reportes y pasarela', contenido: <Reportes /> },
      ]}
    />
  )
}
