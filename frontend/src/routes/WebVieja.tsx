import { Navigate, useLocation } from 'react-router-dom'

const SECCIONES: Record<string, string> = { planes: 'planes', aliados: 'aliadas', nosotros: 'nosotros', contactanos: 'contacto' }

/**
 * Un enlace guardado (o indexado por un buscador) a la web vieja lleva a su sitio nuevo: cada página
 * a su sección de la portada y cada plan (`/service/plan-colita-feliz/`) a su página.
 */
export function DeLaWebVieja() {
  const { pathname } = useLocation()
  const partes = pathname.split('/').filter(Boolean)
  if (partes[0] === 'service' && partes[1]?.startsWith('plan-')) return <Navigate to={`/planes/${partes[1].slice('plan-'.length)}`} replace />
  const ancla = SECCIONES[partes[0] ?? '']
  return <Navigate to={ancla ? { pathname: '/', hash: ancla } : '/'} replace />
}
