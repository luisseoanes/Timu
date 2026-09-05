import * as Dialog from '@radix-ui/react-dialog'
import type { ReactNode } from 'react'

import { Icono } from './Icono'

/**
 * Modal accesible sobre Radix Dialog.
 *
 * Radix aporta sólo el comportamiento —foco atrapado, cierre con Escape, roles
 * ARIA, bloqueo del scroll—; el aspecto sigue saliendo íntegro de tokens.css, así
 * que el sistema visual no cambia. Ver docs/frontend/components.md.
 */
export function Modal({
  abierto,
  onCambio,
  titulo,
  descripcion,
  children,
  pie,
}: {
  abierto: boolean
  onCambio: (abierto: boolean) => void
  titulo: string
  descripcion?: string
  children: ReactNode
  pie?: ReactNode
}) {
  return (
    <Dialog.Root open={abierto} onOpenChange={onCambio}>
      <Dialog.Portal>
        <Dialog.Overlay className="velo" />
        <Dialog.Content className="modal" aria-describedby={descripcion ? undefined : ''}>
          <div className="modal-cabecera">
            <Dialog.Title className="modal-titulo">{titulo}</Dialog.Title>
            <Dialog.Close className="boton-icono" aria-label="Cerrar">
              <Icono nombre="cerrar" />
            </Dialog.Close>
          </div>
          {descripcion && <Dialog.Description className="modal-descripcion">{descripcion}</Dialog.Description>}
          <div className="modal-cuerpo">{children}</div>
          {pie && <div className="modal-pie">{pie}</div>}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
