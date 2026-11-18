import { Navigate, useLocation } from 'react-router-dom'

/** Un enlace guardado a una dirección antigua del panel (`/familias/f1?q=…`) lleva a la nueva. */
export function AlPanel() {
  const { pathname, search } = useLocation()
  return <Navigate to={`/panel${pathname}${search}`} replace />
}
