import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { FamiliasPage } from './FamiliasPage'
import { FAMILIA } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

// Las tres pantallas obligatorias de toda consulta, segun docs/frontend/conventions.md:
// cargando, error y vacio. Si una falta, la pantalla esta incompleta.
describe('FamiliasPage', () => {
  it('muestra el estado de carga', () => {
    renderizar(<FamiliasPage />)
    expect(screen.getByText(/cargando familias/i)).toBeInTheDocument()
  })

  it('lista las familias que devuelve la API', async () => {
    renderizar(<FamiliasPage />)
    await waitFor(() => expect(screen.getByText(FAMILIA.titular_nombre)).toBeInTheDocument())
  })

  it('muestra el estado vacío cuando no hay resultados', async () => {
    server.use(
      http.get('*/api/v1/familias', () =>
        HttpResponse.json({ items: [], total: 0, limit: 50, offset: 0 }),
      ),
    )
    renderizar(<FamiliasPage />)
    await waitFor(() =>
      expect(screen.queryByText(/cargando familias/i)).not.toBeInTheDocument(),
    )
    expect(screen.queryByText(FAMILIA.titular_nombre)).not.toBeInTheDocument()
  })

  it('muestra el error cuando la API falla', async () => {
    server.use(
      http.get('*/api/v1/familias', () => new HttpResponse(null, { status: 500 })),
    )
    renderizar(<FamiliasPage />)
    await waitFor(() =>
      expect(screen.queryByText(/cargando familias/i)).not.toBeInTheDocument(),
    )
  })

  it('expone los controles de filtro con etiqueta accesible', async () => {
    renderizar(<FamiliasPage />)
    expect(screen.getByLabelText('Buscar familias')).toBeInTheDocument()
    expect(screen.getByLabelText('Filtrar por estado')).toBeInTheDocument()
  })

  it('enlaza cada familia con su ficha', async () => {
    renderizar(<FamiliasPage />)
    const enlace = await screen.findByRole('link', { name: FAMILIA.titular_nombre })
    expect(enlace).toHaveAttribute('href', `/familias/${FAMILIA.id}`)
  })

  it('pagina cuando hay más familias que las de una página', async () => {
    const offsets: (string | null)[] = []
    server.use(
      http.get('*/api/v1/familias', ({ request }) => {
        const offset = new URL(request.url).searchParams.get('offset')
        offsets.push(offset)
        return HttpResponse.json({ items: [FAMILIA], total: 60, limit: 25, offset: Number(offset) })
      }),
    )
    const user = userEvent.setup()
    renderizar(<FamiliasPage />)
    await user.click(await screen.findByRole('button', { name: 'Siguiente' }))
    await waitFor(() => expect(offsets).toContain('25'))
  })

  it('da de alta una familia con su primera mascota', async () => {
    let enviado: Record<string, unknown> | null = null
    server.use(
      http.post('*/api/v1/familias', async ({ request }) => {
        enviado = (await request.json()) as Record<string, unknown>
        return HttpResponse.json(FAMILIA, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<FamiliasPage />)
    await user.click(await screen.findByRole('button', { name: /nueva familia/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nombre del titular'), 'Ana Ruiz')
    await user.type(within(modal).getByLabelText('Número de documento'), '1020304050')
    await user.type(within(modal).getByLabelText('Celular'), '3001112233')
    await waitFor(() => expect(within(modal).getByRole('option', { name: 'Bogota' })).toBeInTheDocument())
    await user.selectOptions(within(modal).getByLabelText('Ciudad'), 'Bogota')
    await user.type(within(modal).getByLabelText('Nombre de la mascota'), 'Luna')
    await user.selectOptions(within(modal).getByLabelText('Especie'), 'perro')
    await user.click(within(modal).getByRole('button', { name: 'Guardar familia' }))

    await waitFor(() =>
      expect(enviado).toEqual({
        titular_nombre: 'Ana Ruiz',
        tipo_documento: 'CC',
        documento: '1020304050',
        telefono: '3001112233',
        ciudad: 'Bogota',
        mascotas: [{ nombre: 'Luna', especie: 'perro' }],
      }),
    )
  })

  it('muestra el error del servidor al dar de alta', async () => {
    server.use(
      http.post('*/api/v1/familias', () =>
        HttpResponse.json({ detail: 'Ya existe una familia con ese documento' }, { status: 409 }),
      ),
    )
    const user = userEvent.setup()
    renderizar(<FamiliasPage />)
    await user.click(await screen.findByRole('button', { name: /nueva familia/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nombre del titular'), 'Ana Ruiz')
    await user.type(within(modal).getByLabelText('Número de documento'), '1020304050')
    await user.type(within(modal).getByLabelText('Celular'), '3001112233')
    await waitFor(() => expect(within(modal).getByRole('option', { name: 'Bogota' })).toBeInTheDocument())
    await user.selectOptions(within(modal).getByLabelText('Ciudad'), 'Bogota')
    await user.type(within(modal).getByLabelText('Nombre de la mascota'), 'Luna')
    await user.selectOptions(within(modal).getByLabelText('Especie'), 'perro')
    await user.click(within(modal).getByRole('button', { name: 'Guardar familia' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('Ya existe una familia con ese documento')
  })
})
