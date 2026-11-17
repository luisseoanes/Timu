import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'

import { Icono, type NombreIcono } from '@/components/Icono'
import { MarcaTimu } from '@/components/MarcaTimu'
import { MenuCuenta } from '@/components/MenuCuenta'
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
        <MenuCuenta nombre={usuario?.nombre} detalle="Portal de familias" alSalir={logout} />
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
