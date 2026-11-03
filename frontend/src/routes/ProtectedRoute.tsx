import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '@/features/auth/AuthContext'
import { inicioDeRol } from '@/lib/permisos'
import type { Rol } from '@/types'

export function ProtectedRoute({ roles }: { roles?: Rol[] }) {
  const { usuario, cargando, errorSesion, reintentarSesion } = useAuth()
  const location = useLocation()

  if (cargando) return <p className="centrado">Cargando sesión…</p>
  // No es que no haya sesión: el servidor no contestó. Mandar al ingreso obligaría a
  // entrar otra vez por un fallo pasajero.
  if (errorSesion) {
    return (
      <div className="centrado" role="alert">
        <div className="pila" style={{ textAlign: 'center' }}>
          <p>No pudimos comprobar tu sesión porque el servidor no respondió. Espera un momento.</p>
          <div>
            <button className="btn btn-primario" type="button" onClick={reintentarSesion}>
              Reintentar
            </button>
          </div>
        </div>
      </div>
    )
  }
  if (!usuario) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  // Sin permiso para esta zona: a la suya, no a «/», que también podría estarle vedada.
  if (roles && !roles.includes(usuario.rol)) return <Navigate to={inicioDeRol(usuario.rol)} replace />
  return <Outlet />
}
