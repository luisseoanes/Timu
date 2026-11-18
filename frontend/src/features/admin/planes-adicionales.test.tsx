import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { AdminPage } from './AdminPage'
import { PLAN as PLAN_TIMU } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const API = '*/api/v1'

const base = [
  http.get(`${API}/auth/usuarios/recuentos`, () => HttpResponse.json({ equipo: 0, aliadas: 0, familias: 0, inactivos: 0 })),
  http.get(`${API}/auth/usuarios`, () => HttpResponse.json({ items: [], total: 0, limit: 25, offset: 0 })),
]

const PLAN = {
  ...PLAN_TIMU,
  adicionales: [
    { id: 'a1', nombre: 'Servicio fúnebre', cubre: '100 %', detalle: 'Traslado las 24 horas.', carencia_dias: 30, tercero: false },
    { id: 'a2', nombre: 'Baño y peluquería', cubre: '30 %', detalle: null, carencia_dias: null, tercero: true },
  ],
}

async function abrirPlan() {
  const user = userEvent.setup()
  renderizar(<AdminPage />, { ruta: '/panel/admin?plan=p1' })
  await user.click(await screen.findByRole('tab', { name: 'Planes' }))
  const titulo = await screen.findByRole('heading', { level: 2, name: 'Colita Feliz' })
  return { user, ficha: titulo.closest('section')! }
}

describe('Administración: beneficios adicionales de un plan', () => {
  it('los dice en la ficha como los leerá la familia', async () => {
    server.use(...base, http.get(`${API}/planes`, () => HttpResponse.json([PLAN])))
    const { ficha } = await abrirPlan()
    const lista = within(ficha).getByRole('list', { name: 'Beneficios adicionales de Colita Feliz' })
    const [funebre, peluqueria] = within(lista).getAllByRole('listitem')
    expect(funebre).toHaveTextContent('Servicio fúnebre · 100 %')
    expect(funebre).toHaveTextContent('Desde los 30 días')
    expect(funebre).toHaveTextContent('Traslado las 24 horas.')
    expect(peluqueria).toHaveTextContent('Lo presta un tercero')
  })

  it('sin adicionales lo dice y deja crearlos', async () => {
    server.use(...base, http.get(`${API}/planes`, () => HttpResponse.json([{ ...PLAN, adicionales: [] }])))
    const { ficha } = await abrirPlan()
    expect(within(ficha).getByText(/^Sin adicionales: la portada y el registro/)).toBeInTheDocument()
  })

  it('añade, ordena y quita, y guarda en el orden en que se dirán', async () => {
    const guardados: unknown[] = []
    server.use(
      ...base,
      http.get(`${API}/planes`, () => HttpResponse.json([PLAN])),
      http.put(`${API}/planes/p1/adicionales`, async ({ request }) => {
        guardados.push(await request.json())
        return HttpResponse.json(PLAN)
      }),
    )
    const { user, ficha } = await abrirPlan()
    await user.click(within(ficha).getByRole('button', { name: 'Editar adicionales' }))
    const modal = await screen.findByRole('dialog', { name: 'Beneficios adicionales de Colita Feliz' })
    expect(within(modal).getByRole('button', { name: 'Subir Servicio fúnebre' })).toBeDisabled()
    await user.click(within(modal).getByRole('button', { name: 'Bajar Servicio fúnebre' }))
    await user.click(within(modal).getByRole('button', { name: 'Otro beneficio adicional' }))
    const nombres = within(modal).getAllByLabelText('Beneficio')
    await user.type(nombres[2]!, 'Certificados de salud')
    await user.type(within(modal).getAllByLabelText('Lo que cubre')[2]!, '20 % de descuento')
    await user.click(within(modal).getAllByRole('button', { name: 'Quitar' })[0]!)
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    await waitFor(() => expect(guardados).toHaveLength(1))
    expect(guardados[0]).toEqual([
      { nombre: 'Servicio fúnebre', cubre: '100 %', detalle: 'Traslado las 24 horas.', carencia_dias: 30, tercero: false },
      { nombre: 'Certificados de salud', cubre: '20 % de descuento', detalle: null, carencia_dias: null, tercero: false },
    ])
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('dice el error de la API sin cerrar la ventana', async () => {
    server.use(
      ...base,
      http.get(`${API}/planes`, () => HttpResponse.json([PLAN])),
      http.put(`${API}/planes/p1/adicionales`, () => HttpResponse.json({ detail: 'El plan no existe' }, { status: 404 })),
    )
    const { user, ficha } = await abrirPlan()
    await user.click(within(ficha).getByRole('button', { name: 'Editar adicionales' }))
    const modal = await screen.findByRole('dialog')
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('El plan no existe')
  })
})
