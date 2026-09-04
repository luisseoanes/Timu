import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '@/features/auth/AuthContext'
import type { Rol } from '@/types'

export function ProtectedRoute({ roles }: { roles?: Rol[] }) {
  const { usuario, cargando } = useAuth()
  const location = useLocation()

  if (cargando) return <p className="centrado">Cargando sesion...</p>
  if (!usuario) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (roles && !roles.includes(usuario.rol)) return <Navigate to="/" replace />
  return <Outlet />
}
