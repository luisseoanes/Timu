import * as Menu from '@radix-ui/react-dropdown-menu'

import { Icono } from './Icono'

/**
 * El menú de la cuenta en la barra marina de los tres espacios (panel, portal y clínica aliada):
 * las iniciales en un círculo y, al abrirlo, quién es, un detalle (su perfil, su familia o su
 * clínica) y cerrar sesión.
 */
export function MenuCuenta({ nombre, detalle, alSalir }: { nombre: string | undefined; detalle: string; alSalir: () => void }) {
  const iniciales = (nombre ?? '')
    .split(' ')
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase()

  return (
    <Menu.Root>
      {/* Bajo ProtectedRoute el usuario ya llegó; sin nombre solo queda la palabra. */}
      <Menu.Trigger className="cuenta" aria-label={nombre ? `Cuenta de ${nombre}` : 'Cuenta'}>
        {iniciales || '—'}
      </Menu.Trigger>
      <Menu.Portal>
        <Menu.Content className="menu" align="end" sideOffset={8}>
          <Menu.Label className="menu-etiqueta">
            <strong>{nombre}</strong>
            <span>{detalle}</span>
          </Menu.Label>
          <Menu.Separator className="menu-separador" />
          <Menu.Item className="menu-item" onSelect={alSalir}>
            <Icono nombre="salir" size={18} />
            Cerrar sesión
          </Menu.Item>
        </Menu.Content>
      </Menu.Portal>
    </Menu.Root>
  )
}
