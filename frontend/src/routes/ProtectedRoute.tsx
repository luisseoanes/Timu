import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '@/features/auth/AuthContext'
import { inicioDeRol } from '@/lib/permisos'
import type { Rol } from '@/types'

export function ProtectedRoute({ roles }: { roles?: Rol[] }) {
  const { usuario, cargando } = useAuth()
  const location = useLocation()

  if (cargando) return <p className="centrado">Cargando sesión…</p>
  if (!usuario) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  // Sin permiso para esta zona: a la suya, no a «/», que también podría estarle vedada.
  if (roles && !roles.includes(usuario.rol)) return <Navigate to={inicioDeRol(usuario.rol)} replace />
  return <Outlet />
}
