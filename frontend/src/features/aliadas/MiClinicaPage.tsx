import * as Menu from '@radix-ui/react-dropdown-menu'

import { Icono } from '@/components/Icono'
import { MarcaTimu } from '@/components/MarcaTimu'
import { useAuth } from '@/features/auth'

import { useMiClinica } from './api'
import { Atendidas } from './Atendidas'
import { ValidarRemision } from './ValidarRemision'

/**
 * Espacio de la clínica aliada (F2-ALI-03, R3-ALI-01): un mostrador. A la izquierda se valida
 * el código que trae la familia y se reporta la atención; a la derecha, lo que la clínica ya
 * atendió en el mes y lo que cubrió TIMU. Solo ve de la familia lo necesario para atender:
 * titular, últimos dígitos del documento y la mascota. Las remisiones por usar no se listan:
 * el código es la prueba de que la familia se presentó.
 */
export function MiClinicaPage() {
  const { usuario, logout } = useAuth()
  const clinica = useMiClinica()
  const iniciales = (usuario?.nombre ?? '')
    .split(' ')
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase()

  return (
    <div className="shell aliada">
      <header className="barra-marca">
        <MarcaTimu claro compacta />
        {/* En un computador compartido de recepción, en qué clínica se está. */}
        <p className="aliada-barra-clinica">{clinica.data?.nombre}</p>
        <Menu.Root>
          <Menu.Trigger className="cuenta" aria-label={`Cuenta de ${usuario?.nombre ?? 'la clínica'}`}>
            {iniciales || '—'}
          </Menu.Trigger>
          <Menu.Portal>
            <Menu.Content className="menu" align="end" sideOffset={8}>
              <Menu.Label className="menu-etiqueta">
                <strong>{usuario?.nombre}</strong>
                <span>{clinica.data ? `${clinica.data.nombre} · ${clinica.data.ciudad}` : 'Clínica aliada'}</span>
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
      <main className="contenido aliada-contenido">
        <div className="aliada-mostrador">
          <ValidarRemision />
          <Atendidas />
        </div>
      </main>
    </div>
  )
}
