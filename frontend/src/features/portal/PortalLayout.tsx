import * as Menu from '@radix-ui/react-dropdown-menu'
import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'

import { Icono, type NombreIcono } from '@/components/Icono'
import { MarcaTimu } from '@/components/MarcaTimu'
import { useAuth } from '@/features/auth'

const NAV: { to: string; label: string; icono: NombreIcono; end?: boolean }[] = [
  { to: '/portal', label: 'Inicio', icono: 'portal', end: true },
  { to: '/portal/mascotas', label: 'Peludos', icono: 'huella' },
  { to: '/portal/citas', label: 'Citas', icono: 'calendario' },
  { to: '/portal/pagos', label: 'Pagos', icono: 'pago' },
  { to: '/portal/datos', label: 'Mis datos', icono: 'usuario' },
]

const MOVIL = '(max-width: 899px)'

function esMovil(): boolean {
  return typeof window.matchMedia === 'function' && window.matchMedia(MOVIL).matches
}

function useMovil(): boolean {
  const [movil, setMovil] = useState(esMovil)
  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return
    const consulta = window.matchMedia(MOVIL)
    const cambiar = () => setMovil(consulta.matches)
    consulta.addEventListener('change', cambiar)
    return () => consulta.removeEventListener('change', cambiar)
  }, [])
  return movil
}

/**
 * Portal de las familias afiliadas (R3-POR-01). La misma estructura que el panel: barra marina
 * con los destinos y la cuenta y, por debajo de 900 px, los destinos en una barra inferior al
 * alcance del pulgar. Los cinco caben siempre: no hay «Más».
 */
export function PortalLayout() {
  const { usuario, logout } = useAuth()
  const movil = useMovil()
  const iniciales = (usuario?.nombre ?? '')
    .split(' ')
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase()

  const destinos = NAV.map((n) => (
    <NavLink key={n.to} to={n.to} end={n.end}>
      {movil && <Icono nombre={n.icono} size={22} />}
      {n.label}
    </NavLink>
  ))

  return (
    <div className="shell portal" data-movil={movil}>
      <header className="barra-marca">
        <MarcaTimu claro compacta />
        {!movil && (
          <nav className="modulos" aria-label="Portal">
            {destinos}
          </nav>
        )}
        <Menu.Root>
          <Menu.Trigger className="cuenta" aria-label={`Cuenta de ${usuario?.nombre ?? 'tu familia'}`}>
            {iniciales || '—'}
          </Menu.Trigger>
          <Menu.Portal>
            <Menu.Content className="menu" align="end" sideOffset={8}>
              <Menu.Label className="menu-etiqueta">
                <strong>{usuario?.nombre}</strong>
                <span>Portal de familias</span>
              </Menu.Label>
              <Menu.Separator className="menu-separador" />
              <Menu.Item className="menu-item" onSelect={logout}>
                <Icono nombre="salir" size={18} />
                Cerrar sesión
              </Menu.Item>
            </Menu.Content>
          </Menu.Portal>
        </Menu.Root>
      </header>
      <main className="contenido portal-contenido">
        <Outlet />
      </main>
      {movil && (
        <nav className="barra-inferior" aria-label="Portal">
          {destinos}
        </nav>
      )}
    </div>
  )
}
