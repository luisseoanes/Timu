import * as Menu from '@radix-ui/react-dropdown-menu'
import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'

import { Icono, type NombreIcono } from '@/components/Icono'
import { MarcaTimu } from '@/components/MarcaTimu'
import { MenuCuenta } from '@/components/MenuCuenta'
import { useAuth } from '@/features/auth'
import { NOMBRE_ROL, puede, type Accion } from '@/lib/permisos'
import type { Rol } from '@/types'

interface ItemNav {
  to: string
  label: string
  icono: NombreIcono
  titulo: string
  sub: string
  end?: boolean
  /** Sin permiso, el módulo no aparece en el menú (el backend respondería 403). */
  permiso?: Accion
  /** La pantalla escribe su propio h1 (el saludo del Inicio) y la cabecera no se repite. */
  cabeceraPropia?: boolean
}

// Un elemento por dominio de la plataforma (sección A de la propuesta). Cada perfil ve solo los
// suyos (Sección 12, docs/perfiles-y-permisos.md): el permiso es el mismo que aplica la API.
const NAV: ItemNav[] = [
  { to: '/panel', label: 'Inicio', icono: 'panel', end: true, titulo: 'Inicio', sub: 'Lo que toca hoy', cabeceraPropia: true },
  { to: '/panel/familias', label: 'Familias', icono: 'familias', titulo: 'Familias y mascotas', sub: 'Afiliaciones, titulares y mascotas', permiso: 'verFamilias' },
  { to: '/panel/cartera', label: 'Cartera', icono: 'cartera', titulo: 'Cartera', sub: 'Cuotas, mora y renovaciones', permiso: 'verCartera' },
  { to: '/panel/servicios', label: 'Servicios', icono: 'servicios', titulo: 'Servicios', sub: 'Agenda, autorizaciones y pendientes', permiso: 'servicios' },
  { to: '/panel/rutas', label: 'Rutas', icono: 'rutas', titulo: 'Rutas', sub: 'Visitas domiciliarias del día', permiso: 'campo' },
  { to: '/panel/clinica', label: 'Clínica', icono: 'clinica', titulo: 'Clínica', sub: 'Historia clínica y atención virtual', permiso: 'clinico' },
  { to: '/panel/preventivos', label: 'Preventivos', icono: 'preventivos', titulo: 'Preventivos', sub: 'Calendario, autorizaciones y carnet', permiso: 'preventivos' },
  { to: '/panel/tareas', label: 'Tareas', icono: 'tareas', titulo: 'Tareas', sub: 'Lo que tu área tiene por resolver', permiso: 'tareas' },
  { to: '/panel/comercial', label: 'Comercial', icono: 'comercial', titulo: 'Comercial', sub: 'Interesados y conversaciones', permiso: 'mercadeo' },
  { to: '/panel/campanas', label: 'Campañas', icono: 'campanas', titulo: 'Campañas', sub: 'Segmentos y envíos', permiso: 'mercadeo' },
  { to: '/panel/mensajes', label: 'Mensajes', icono: 'mensaje', titulo: 'Mensajes', sub: 'WhatsApp y bajas', permiso: 'mensajes' },
  { to: '/panel/encuestas', label: 'Encuestas', icono: 'campanas', titulo: 'Encuestas', sub: 'Satisfacción y seguimiento', permiso: 'encuestas' },
  { to: '/panel/aliadas', label: 'Aliadas', icono: 'aliadas', titulo: 'Clínicas aliadas', sub: 'Convenios, remisiones y liquidación', permiso: 'aliadas' },
  { to: '/panel/admin', label: 'Administración', icono: 'ajustes', titulo: 'Administración', sub: 'Usuarios, planes, reglas e IA', permiso: 'administrar' },
]

/** Los cuatro módulos que cada perfil usa más: van en la barra inferior del celular. */
const PRINCIPALES: Partial<Record<Rol, string[]>> = {
  admin: ['/panel', '/panel/admin'],
  gerencia: ['/panel', '/panel/encuestas', '/panel/aliadas'],
  comercial: ['/panel', '/panel/comercial', '/panel/familias', '/panel/campanas'],
  atencion_cliente: ['/panel', '/panel/familias', '/panel/cartera', '/panel/servicios'],
  operaciones: ['/panel', '/panel/servicios', '/panel/rutas', '/panel/preventivos'],
  medico: ['/panel', '/panel/rutas', '/panel/servicios', '/panel/clinica'],
}

// Cuántos módulos caben en la barra superior según el ancho. Con 0 la navegación pasa a la
// barra inferior. Sin matchMedia (pruebas en jsdom) se asume el escritorio ancho.
const CORTES: [string, number][] = [
  ['(min-width: 1360px)', 8],
  ['(min-width: 1180px)', 6],
  ['(min-width: 900px)', 3],
]

function capacidadActual(): number {
  if (typeof window.matchMedia !== 'function') return CORTES[0][1]
  return CORTES.find(([consulta]) => window.matchMedia(consulta).matches)?.[1] ?? 0
}

function useCapacidad(): number {
  const [capacidad, setCapacidad] = useState(capacidadActual)
  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return
    const consultas = CORTES.map(([consulta]) => window.matchMedia(consulta))
    const cambiar = () => setCapacidad(capacidadActual())
    consultas.forEach((c) => c.addEventListener('change', cambiar))
    return () => consultas.forEach((c) => c.removeEventListener('change', cambiar))
  }, [])
  return capacidad
}

const esActual = (item: ItemNav, pathname: string) => (item.end ? pathname === item.to : pathname.startsWith(item.to))

/** Menú «Más»: los módulos que no caben, como enlaces. */
function MenuMas({ items, activo, arriba }: { items: ItemNav[]; activo: boolean; arriba?: boolean }) {
  return (
    <Menu.Root>
      <Menu.Trigger className="mas" data-activo={activo}>
        {/* Ni «+», que se lee como «crear»: en la barra inferior, tres puntos; arriba, una flecha. */}
        {arriba && <Icono nombre="puntos" size={22} />}
        Más
        {!arriba && <Icono nombre="abajo" size={16} />}
      </Menu.Trigger>
      <Menu.Portal>
        <Menu.Content className="menu" side={arriba ? 'top' : 'bottom'} align="end" sideOffset={6}>
          {items.map((item) => (
            <Menu.Item key={item.to} asChild>
              <NavLink className="menu-item" to={item.to} end={item.end}>
                <Icono nombre={item.icono} size={18} />
                {item.label}
              </NavLink>
            </Menu.Item>
          ))}
        </Menu.Content>
      </Menu.Portal>
    </Menu.Root>
  )
}

export function AppLayout() {
  const { usuario, logout } = useAuth()
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const capacidad = useCapacidad()
  const [busqueda, setBusqueda] = useState('')
  const visibles = NAV.filter((n) => !n.permiso || puede(usuario, n.permiso))
  const actual = visibles.find((n) => esActual(n, pathname)) ?? NAV[0]
  const movil = capacidad === 0

  const enBarra = visibles.slice(0, capacidad)
  const enMas = visibles.slice(capacidad)
  const rutasPrincipales = (usuario && PRINCIPALES[usuario.rol]) ?? NAV.slice(0, 4).map((n) => n.to)
  const principales = visibles.filter((n) => rutasPrincipales.includes(n.to))
  const resto = visibles.filter((n) => !rutasPrincipales.includes(n.to))

  return (
    <div className="shell" data-movil={movil}>
      <header className="barra-marca">
        <MarcaTimu claro compacta />
        {!movil && (
          <nav className="modulos" aria-label="Módulos">
            {enBarra.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.end}>
                {item.label}
              </NavLink>
            ))}
            {enMas.length > 0 && <MenuMas items={enMas} activo={enMas.includes(actual)} />}
          </nav>
        )}
        {/* El buscador lleva a Familias: solo para quien la ve. */}
        {!movil && puede(usuario, 'verFamilias') && (
          <form
            role="search"
            onSubmit={(e) => {
              e.preventDefault()
              const q = busqueda.trim()
              if (q) navigate(`/panel/familias?q=${encodeURIComponent(q)}`)
            }}
          >
            <label className="buscador">
              <Icono nombre="buscar" size={18} />
              <input
                type="search"
                placeholder="Buscar familia"
                aria-label="Buscar familias"
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
              />
            </label>
          </form>
        )}
        <MenuCuenta nombre={usuario?.nombre} detalle={usuario ? NOMBRE_ROL[usuario.rol] : ''} alSalir={logout} />
      </header>

      <main className="contenido">
        {!actual.cabeceraPropia && (
          <header className="cabecera-pagina">
            <h1>{actual.titulo}</h1>
            <p>{actual.sub}</p>
          </header>
        )}
        <Outlet />
      </main>

      {movil && (
        <nav className="barra-inferior" aria-label="Módulos principales">
          {principales.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end}>
              <Icono nombre={item.icono} size={22} />
              {item.label}
            </NavLink>
          ))}
          {resto.length > 0 && <MenuMas items={resto} activo={resto.includes(actual)} arriba />}
        </nav>
      )}
    </div>
  )
}
