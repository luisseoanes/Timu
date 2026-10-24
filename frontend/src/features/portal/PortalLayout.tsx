import { NavLink, Outlet } from 'react-router-dom'

import { Icono, type NombreIcono } from '@/components/Icono'
import { MarcaTimu } from '@/features/auth/AccesoLayout'
import { useAuth } from '@/features/auth/AuthContext'

const NAV: { to: string; label: string; icono: NombreIcono; end?: boolean }[] = [
  { to: '/portal', label: 'Inicio', icono: 'portal', end: true },
  { to: '/portal/mascotas', label: 'Mascotas', icono: 'huella' },
  { to: '/portal/citas', label: 'Citas', icono: 'calendario' },
  { to: '/portal/pagos', label: 'Pagos', icono: 'pago' },
  { to: '/portal/datos', label: 'Mis datos', icono: 'usuario' },
]

/**
 * Portal de las familias afiliadas (F3-POR). Pensado primero para el celular: cabecera
 * corta y navegación fija abajo; en pantallas grandes, la navegación sube a la cabecera.
 */
export function PortalLayout() {
  const { usuario, logout } = useAuth()
  return (
    <div className="portal">
      <header className="portal-cabeza">
        <MarcaTimu />
        <nav className="portal-nav" aria-label="Portal">
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.end}>
              <Icono nombre={n.icono} size={20} />
              <span>{n.label}</span>
            </NavLink>
          ))}
        </nav>
        <button className="btn btn-plano" type="button" onClick={logout} aria-label={`Salir (${usuario?.nombre ?? ''})`}>
          <Icono nombre="salir" size={18} />
        </button>
      </header>
      <main className="portal-contenido">
        <Outlet />
      </main>
    </div>
  )
}
