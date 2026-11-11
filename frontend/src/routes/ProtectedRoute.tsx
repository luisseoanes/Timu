import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { Icono } from '@/components/Icono'
import { MarcaTimu } from '@/components/MarcaTimu'
import { useAuth } from '@/features/auth'
import { inicioDeRol } from '@/lib/permisos'
import type { Rol } from '@/types'

/**
 * Lo que se ve mientras se comprueba la sesión, antes de saber a qué espacio va el usuario:
 * la marca sobre el lienzo, sin la barra de ningún espacio, y debajo el estado.
 */
function EsperaSesion({ children }: { children: React.ReactNode }) {
  return (
    <main className="espera-sesion">
      <MarcaTimu />
      {children}
    </main>
  )
}

export function ProtectedRoute({ roles }: { roles?: Rol[] }) {
  const { usuario, cargando, errorSesion, reintentarSesion } = useAuth()
  const location = useLocation()

  if (cargando) {
    return (
      <EsperaSesion>
        <div className="esqueleto espera-sesion-esqueleto" role="status">
          <span className="sr-only">Comprobando tu sesión…</span>
          <span className="esqueleto-linea" aria-hidden="true" />
          <span className="esqueleto-linea" aria-hidden="true" />
        </div>
      </EsperaSesion>
    )
  }
  // No es que no haya sesión: el servidor no contestó. Mandar al ingreso obligaría a
  // entrar otra vez por un fallo pasajero.
  if (errorSesion) {
    return (
      <EsperaSesion>
        <section className="espera-sesion-aviso" role="alert">
          <Icono nombre="alerta" size={22} />
          <h1>No pudimos comprobar tu sesión</h1>
          <p>El servidor no respondió. Tu sesión sigue abierta: espera un momento y vuelve a intentarlo.</p>
          <button className="btn btn-primario" type="button" onClick={reintentarSesion}>
            Reintentar
          </button>
        </section>
      </EsperaSesion>
    )
  }
  if (!usuario) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  // Sin permiso para esta zona: a la suya, no a «/», que también podría estarle vedada.
  if (roles && !roles.includes(usuario.rol)) return <Navigate to={inicioDeRol(usuario.rol)} replace />
  return <Outlet />
}
