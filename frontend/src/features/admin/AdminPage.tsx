import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { Pestanas } from '@/components/Pestanas'
import { ConfiguracionEncuestas, PlantillasWhatsApp } from '@/features/campanas'
import { GuionBot } from '@/features/comercial'

import { Catalogos } from './Catalogos'
import { DatosTimu } from './DatosTimu'
import { InteligenciaArtificial } from './InteligenciaArtificial'
import { Planes } from './Planes'
import { Reglas } from './Reglas'
import { Supresion } from './Supresion'
import { Usuarios } from './Usuarios'

/** Lo que la URL abre dentro de cada pestaña: la ficha de un plan o una regla. */
const PESTANA_DE: Record<string, string> = { plan: 'planes', regla: 'reglas' }

/** Administración de la plataforma: sólo el perfil admin llega aquí (App.tsx). Configura y nada más
 * (Sección 12, docs/perfiles-y-permisos.md): los reportes son de Gerencia y la pasarela de Cartera. */
export function AdminPage() {
  const [params, setParams] = useSearchParams()
  const pedida = Object.keys(PESTANA_DE).find((p) => params.has(p))
  // `?pestana=` abre una pestaña (el Inicio del administrador lleva a lo que falta configurar).
  const directa = params.get('pestana')
  const [pestana, setPestana] = useState(pedida ? PESTANA_DE[pedida]! : (directa ?? 'usuarios'))
  // Lo que aparece en la URL (al recargar o desde un enlace) lleva a su pestaña.
  const [vista, setVista] = useState(pedida)
  if (pedida !== vista) {
    setVista(pedida)
    if (pedida) setPestana(PESTANA_DE[pedida]!)
  }

  function cambiar(valor: string) {
    setPestana(valor)
    // La URL dice lo que se ve: lo de la pestaña que se deja no vuelve a abrirse al recargar.
    const siguiente = new URLSearchParams(params)
    for (const [parametro, deLaPestana] of Object.entries(PESTANA_DE)) {
      if (deLaPestana !== valor) siguiente.delete(parametro)
    }
    setParams(siguiente, { replace: true })
  }

  return (
    <Pestanas
      etiqueta="Secciones de administración"
      valor={pestana}
      onCambio={cambiar}
      pestanas={[
        { valor: 'usuarios', titulo: 'Usuarios', contenido: <Usuarios /> },
        { valor: 'planes', titulo: 'Planes', contenido: <Planes /> },
        { valor: 'reglas', titulo: 'Reglas', contenido: <Reglas /> },
        { valor: 'catalogos', titulo: 'Catálogos', contenido: <Catalogos /> },
        { valor: 'plantillas', titulo: 'Plantillas de WhatsApp', contenido: <PlantillasWhatsApp /> },
        { valor: 'guion', titulo: 'Guion del asistente', contenido: <GuionBot /> },
        { valor: 'encuestas', titulo: 'Encuestas', contenido: <ConfiguracionEncuestas /> },
        { valor: 'ia', titulo: 'Inteligencia artificial', contenido: <InteligenciaArtificial /> },
        { valor: 'timu', titulo: 'Datos de TIMU', contenido: <DatosTimu /> },
        { valor: 'supresion', titulo: 'Supresión de datos', contenido: <Supresion /> },
      ]}
    />
  )
}
