import { NavLink, Outlet, useLocation } from 'react-router-dom'

import { Icono, type NombreIcono } from '@/components/Icono'
import { useAuth } from '@/features/auth/AuthContext'

// Un elemento por dominio de la plataforma (sección A de la propuesta).
const NAV: { to: string; label: string; icono: NombreIcono; end?: boolean; titulo: string; sub: string }[] = [
  { to: '/', label: 'Panel', icono: 'panel', end: true, titulo: 'Panel', sub: 'Resumen de la operación de hoy' },
  { to: '/familias', label: 'Familias', icono: 'familias', titulo: 'Familias y mascotas', sub: 'Afiliaciones, titulares y mascotas' },
  { to: '/cartera', label: 'Cartera', icono: 'cartera', titulo: 'Cartera', sub: 'Cuotas, mora y renovaciones' },
  { to: '/servicios', label: 'Servicios', icono: 'servicios', titulo: 'Servicios', sub: 'Programación, pendientes y estados' },
  { to: '/preventivos', label: 'Preventivos', icono: 'preventivos', titulo: 'Preventivos', sub: 'Calendario, autorizaciones y carnet' },
  { to: '/clinica', label: 'Clínica', icono: 'clinica', titulo: 'Clínica', sub: 'Historia clínica y atención virtual' },
  { to: '/rutas', label: 'Rutas', icono: 'rutas', titulo: 'Rutas', sub: 'Planeación domiciliaria del día' },
  { to: '/campanas', label: 'Campañas', icono: 'campanas', titulo: 'Campañas', sub: 'Segmentación, envíos y encuestas' },
]

export function AppLayout() {
  const { usuario, logout } = useAuth()
  const { pathname } = useLocation()
  const actual = NAV.find((n) => (n.end ? pathname === n.to : pathname.startsWith(n.to))) ?? NAV[0]
  const iniciales = (usuario?.nombre ?? '')
    .split(' ')
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase()

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="marca">
          <span className="marca-icono"><Icono nombre="preventivos" size={18} /></span>
          TIMU
        </div>

        <nav className="nav">
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end}>
              <Icono nombre={item.icono} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="usuario">
          <div className="usuario-datos">
            <span className="avatar">{iniciales || '—'}</span>
            <div>
              <strong>{usuario?.nombre}</strong>
              <span>{usuario?.rol}</span>
            </div>
          </div>
          <button className="btn btn-suave" type="button" onClick={logout}>
            <Icono nombre="salir" size={16} />
            Cerrar sesión
          </button>
        </div>
      </aside>

      <div className="principal">
        <header className="topbar">
          <div className="topbar-titulo">
            <h2>{actual.titulo}</h2>
            <p>{actual.sub}</p>
          </div>
          <label className="buscador">
            <Icono nombre="buscar" size={18} />
            <input type="search" placeholder="Buscar familia, mascota o servicio" aria-label="Buscar" />
          </label>
          <button className="btn-icono" type="button" aria-label="Notificaciones">
            <Icono nombre="campana" size={18} />
          </button>
          <button className="btn-icono" type="button" aria-label="Ayuda">
            <Icono nombre="ayuda" size={18} />
          </button>
        </header>

        <main className="contenido">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
