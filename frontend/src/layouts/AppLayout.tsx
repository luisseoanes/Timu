import { useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'

import { Icono, type NombreIcono } from '@/components/Icono'
import { MarcaTimu } from '@/features/auth/AccesoLayout'
import { useAuth } from '@/features/auth/AuthContext'
import { NOMBRE_ROL, puede, type Accion } from '@/lib/permisos'

interface ItemNav {
  to: string
  label: string
  icono: NombreIcono
  titulo: string
  sub: string
  end?: boolean
  /** Sin permiso, el módulo no aparece en el menú (el backend respondería 403). */
  permiso?: Accion
}

// Un elemento por dominio de la plataforma (sección A de la propuesta).
const NAV: ItemNav[] = [
  { to: '/', label: 'Panel', icono: 'panel', end: true, titulo: 'Panel', sub: 'Resumen de la operación' },
  { to: '/familias', label: 'Familias', icono: 'familias', titulo: 'Familias y mascotas', sub: 'Afiliaciones, titulares y mascotas' },
  { to: '/cartera', label: 'Cartera', icono: 'cartera', titulo: 'Cartera', sub: 'Cuotas, mora y renovaciones' },
  { to: '/servicios', label: 'Servicios', icono: 'servicios', titulo: 'Servicios', sub: 'Agenda, autorizaciones y pendientes' },
  { to: '/tareas', label: 'Tareas', icono: 'tareas', titulo: 'Tareas', sub: 'Lo que el equipo tiene por resolver' },
  { to: '/preventivos', label: 'Preventivos', icono: 'preventivos', titulo: 'Preventivos', sub: 'Calendario, autorizaciones y carnet' },
  { to: '/clinica', label: 'Clínica', icono: 'clinica', titulo: 'Clínica', sub: 'Historia clínica y atención virtual' },
  { to: '/rutas', label: 'Rutas', icono: 'rutas', titulo: 'Rutas', sub: 'Visitas domiciliarias del día' },
  { to: '/comercial', label: 'Comercial', icono: 'comercial', titulo: 'Comercial', sub: 'Interesados y conversaciones', permiso: 'mercadeo' },
  { to: '/campanas', label: 'Campañas', icono: 'campanas', titulo: 'Campañas y encuestas', sub: 'Segmentos, envíos y satisfacción' },
  { to: '/aliadas', label: 'Aliadas', icono: 'aliadas', titulo: 'Clínicas aliadas', sub: 'Convenios, remisiones y liquidación' },
  { to: '/admin', label: 'Administración', icono: 'ajustes', titulo: 'Administración', sub: 'Usuarios, planes, reglas e IA', permiso: 'administrar' },
]

export function AppLayout() {
  const { usuario, logout } = useAuth()
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const [busqueda, setBusqueda] = useState('')
  const visibles = NAV.filter((n) => !n.permiso || puede(usuario, n.permiso))
  const actual = visibles.find((n) => (n.end ? pathname === n.to : pathname.startsWith(n.to))) ?? NAV[0]
  const iniciales = (usuario?.nombre ?? '')
    .split(' ')
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase()

  return (
    <div className="shell">
      <aside className="sidebar">
        <MarcaTimu />

        <nav className="nav" aria-label="Módulos">
          {visibles.map((item) => (
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
              <span>{usuario ? NOMBRE_ROL[usuario.rol] : ''}</span>
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
          <form
            role="search"
            onSubmit={(e) => {
              e.preventDefault()
              const q = busqueda.trim()
              if (q) navigate(`/familias?q=${encodeURIComponent(q)}`)
            }}
          >
            <label className="buscador">
              <Icono nombre="buscar" size={18} />
              <input
                type="search"
                placeholder="Buscar familia por nombre, documento o celular"
                aria-label="Buscar familias"
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
              />
            </label>
          </form>
        </header>

        <main className="contenido">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
