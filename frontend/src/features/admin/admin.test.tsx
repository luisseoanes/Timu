import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { AdminPage } from './AdminPage'
import { USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const API = '*/api/v1'

const OPERADOR = { id: 'u2', email: 'op@timu.co', telefono: null, nombre: 'Carlos Peña', rol: 'operaciones', activo: true }

describe('AdminPage', () => {
  it('cambia el perfil de un usuario y no deja desactivarse a sí mismo', async () => {
    let cambio: unknown = null
    server.use(
      http.get(`${API}/auth/usuarios`, () => HttpResponse.json({ items: [{ ...USUARIO_ADMIN, telefono: null }, OPERADOR], total: 2, limit: 200, offset: 0 })),
      http.patch(`${API}/auth/usuarios/u2`, async ({ request }) => {
        cambio = await request.json()
        return HttpResponse.json({ ...OPERADOR, rol: 'medico' })
      }),
    )
    const user = userEvent.setup()
    renderizar(<AdminPage />)
    await user.selectOptions(await screen.findByLabelText('Perfil de Carlos Peña'), 'medico')
    await waitFor(() => expect(cambio).toEqual({ rol: 'medico' }))
    expect(screen.getByLabelText('Admin activo')).toBeDisabled()
  })

  it('crea un usuario de clínica aliada con su clínica', async () => {
    let creado: unknown = null
    server.use(
      http.get(`${API}/auth/usuarios`, () => HttpResponse.json({ items: [], total: 0, limit: 200, offset: 0 })),
      http.get(`${API}/aliadas`, () => HttpResponse.json([{ id: 'cl1', nombre: 'Clínica Norte', ciudad: 'Bogota', activa: true }])),
      http.post(`${API}/auth/usuarios`, async ({ request }) => {
        creado = await request.json()
        return HttpResponse.json({}, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<AdminPage />)
    await user.click(await screen.findByRole('button', { name: /nuevo usuario/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nombre'), 'Recepción Norte')
    await user.type(within(modal).getByLabelText('Correo'), 'norte@aliada.co')
    await user.selectOptions(within(modal).getByLabelText('Perfil'), 'aliada')
    await user.type(within(modal).getByLabelText('Contraseña inicial'), 'segura1234')
    await waitFor(() => expect(within(modal).getByRole('option', { name: 'Clínica Norte' })).toBeInTheDocument())
    await user.selectOptions(within(modal).getByLabelText('Clínica aliada'), 'cl1')
    await user.click(within(modal).getByRole('button', { name: 'Crear usuario' }))
    await waitFor(() =>
      expect(creado).toEqual({ nombre: 'Recepción Norte', email: 'norte@aliada.co', rol: 'aliada', password: 'segura1234', clinica_aliada_id: 'cl1' }),
    )
  })

  it('muestra los planes con sus beneficios', async () => {
    server.use(
      http.get(`${API}/auth/usuarios`, () => HttpResponse.json({ items: [], total: 0, limit: 200, offset: 0 })),
      http.get(`${API}/planes`, () =>
        HttpResponse.json([
          {
            id: 'p1',
            codigo: 'familiar',
            nombre: 'Plan Familiar',
            descripcion: null,
            ciudad: null,
            valor_mensual: '75000.00',
            cupos_mascotas: 3,
            especies: [],
            activo: true,
            beneficios: [{ id: 'b1', tipo_servicio_codigo: 'consulta_domiciliaria', cupo: 6, periodo_cupo: 'anual', cobertura_pct: 100, copago: '0' }],
          },
        ]),
      ),
    )
    const user = userEvent.setup()
    renderizar(<AdminPage />)
    await user.click(await screen.findByRole('tab', { name: 'Planes' }))
    const plan = await screen.findByRole('article', { name: 'Plan Familiar' })
    expect(within(plan).getByText(/consulta domiciliaria · 6 al año/)).toBeInTheDocument()
  })

  it('una versión de prompt sólo se activa si pasa todos sus casos', async () => {
    server.use(
      http.get(`${API}/auth/usuarios`, () => HttpResponse.json({ items: [], total: 0, limit: 200, offset: 0 })),
      http.get(`${API}/ia/consumo`, () => HttpResponse.json({ mes: '2026-10', gasto_usd: 12.5, presupuesto_usd: 50, disponible_usd: 37.5, por_prompt: [] })),
      http.get(`${API}/ia/prompts`, () =>
        HttpResponse.json([{ id: 'pr1', codigo: 'comercial_guion', version: 2, sistema: 'Eres el asesor…', estado: 'borrador', nota: null, evaluado_en: null, evaluacion: {} }]),
      ),
      http.get(`${API}/ia/casos`, () => HttpResponse.json([])),
      http.get(`${API}/ia/consultas`, () => HttpResponse.json([])),
      http.post(`${API}/ia/prompts/pr1/evaluacion`, () =>
        HttpResponse.json({ total: 2, aprobados: 1, detalle: [{ caso: 'Precio', aprobado: false, motivo: 'alcance distinto' }], en: '' }),
      ),
    )
    const user = userEvent.setup()
    renderizar(<AdminPage />)
    await user.click(await screen.findByRole('tab', { name: 'Inteligencia artificial' }))
    expect(await screen.findByText('US$ 12.50')).toBeInTheDocument()
    const activar = await screen.findByRole('button', { name: 'Activar' })
    expect(activar).toBeDisabled()
    await user.click(screen.getByRole('button', { name: 'Correr casos' }))
    expect(await screen.findByText(/1 de 2 casos aprobados · Precio: alcance distinto/)).toBeInTheDocument()
    expect(activar).toBeDisabled()
  })
})
