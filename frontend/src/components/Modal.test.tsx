import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it } from 'vitest'

import { Modal } from './Modal'
import { renderizar } from '@/test/utils'

function Anfitrion() {
  const [abierto, setAbierto] = useState(false)
  return (
    <>
      <button onClick={() => setAbierto(true)}>abrir</button>
      <Modal abierto={abierto} onCambio={setAbierto} titulo="Confirmar" descripcion="Detalle">
        <p>cuerpo del modal</p>
      </Modal>
    </>
  )
}

// Lo que se prueba aquí es el comportamiento accesible que aporta Radix: si algún
// día alguien lo sustituye por un div a mano, estas pruebas lo cazan.
describe('Modal', () => {
  it('no se muestra hasta que se abre', () => {
    renderizar(<Anfitrion />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('se abre con rol de diálogo y título accesible', async () => {
    renderizar(<Anfitrion />)
    await userEvent.click(screen.getByRole('button', { name: 'abrir' }))
    const dialogo = await screen.findByRole('dialog')
    expect(dialogo).toBeInTheDocument()
    expect(screen.getByText('Confirmar')).toBeInTheDocument()
    expect(screen.getByText('cuerpo del modal')).toBeInTheDocument()
  })

  it('se cierra con la tecla Escape', async () => {
    renderizar(<Anfitrion />)
    await userEvent.click(screen.getByRole('button', { name: 'abrir' }))
    await screen.findByRole('dialog')
    await userEvent.keyboard('{Escape}')
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('se cierra con el botón de cerrar, que tiene etiqueta accesible', async () => {
    renderizar(<Anfitrion />)
    await userEvent.click(screen.getByRole('button', { name: 'abrir' }))
    await screen.findByRole('dialog')
    await userEvent.click(screen.getByRole('button', { name: 'Cerrar' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })
})
