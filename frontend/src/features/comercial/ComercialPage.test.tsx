import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { ComercialPage } from './ComercialPage'
import { USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { InteresadoRead } from '@/types'

const API = '*/api/v1'

const INTERESADO: InteresadoRead = {
  id: 'i1',
  nombre: 'Paula Díaz',
  telefono: '573005551234',
  email: null,
  ciudad: 'Bogota',
  origen: 'whatsapp',
  etapa: 'contactado',
  responsable_id: null,
  familia_id: null,
  plan_sugerido: 'familiar',
  datos: {},
  motivo_perdida: null,
  ultimo_contacto: '2026-10-23T15:00:00Z',
  created_at: '2026-10-20T10:00:00Z',
}

const base = [
  http.get(`${API}/comercial/embudo`, () =>
    HttpResponse.json({
      total: 10,
      por_etapa: { nuevo: 3, contactado: 4, cotizado: 1, en_afiliacion: 1, afiliado: 1, perdido: 0 },
      por_origen: {},
      conversion: 0.1,
    }),
  ),
  http.get(`${API}/auth/equipo`, () => HttpResponse.json([{ id: 'c1', nombre: 'Valentina', rol: 'comercial' }])),
  http.get(`${API}/comercial/interesados`, () => HttpResponse.json({ items: [INTERESADO], total: 1, limit: 25, offset: 0 })),
]

describe('ComercialPage', () => {
  it('muestra el embudo y filtra el listado al elegir una etapa', async () => {
    const etapas: (string | null)[] = []
    // El handler propio va antes que los de base: MSW usa el primero que coincide.
    server.use(
      http.get(`${API}/comercial/interesados`, ({ request }) => {
        etapas.push(new URL(request.url).searchParams.get('etapa'))
        return HttpResponse.json({ items: [INTERESADO], total: 1, limit: 25, offset: 0 })
      }),
      ...base,
    )
    const user = userEvent.setup()
    renderizar(<ComercialPage />)
    expect(await screen.findByText('Conversión 10%')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /cotizado/i }))
    await waitFor(() => expect(etapas).toContain('cotizado'))
  })

  it('avanza la etapa y asigna responsable', async () => {
    const cambios: unknown[] = []
    server.use(
      ...base,
      http.patch(`${API}/comercial/interesados/i1`, async ({ request }) => {
        cambios.push(await request.json())
        return HttpResponse.json(INTERESADO)
      }),
    )
    const user = userEvent.setup()
    renderizar(<ComercialPage />)
    await user.selectOptions(await screen.findByLabelText('Etapa de Paula Díaz'), 'cotizado')
    await waitFor(() => expect(within(screen.getByLabelText('Responsable de Paula Díaz')).getByRole('option', { name: 'Valentina' })).toBeInTheDocument())
    await user.selectOptions(screen.getByLabelText('Responsable de Paula Díaz'), 'c1')
    await waitFor(() => expect(cambios).toEqual([{ etapa: 'cotizado' }, { responsable_id: 'c1' }]))
  })

  it('marca un interesado como perdido con motivo', async () => {
    let enviado: unknown = null
    server.use(
      ...base,
      http.post(`${API}/comercial/interesados/i1/perdida`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ ...INTERESADO, etapa: 'perdido' })
      }),
    )
    const user = userEvent.setup()
    renderizar(<ComercialPage />)
    await user.click(await screen.findByRole('button', { name: 'Perdido' }))
    const modal = await screen.findByRole('dialog')
    await user.selectOptions(within(modal).getByLabelText('Motivo'), 'No responde')
    await user.click(within(modal).getByRole('button', { name: 'Marcar perdido' }))
    await waitFor(() => expect(enviado).toEqual({ motivo: 'No responde' }))
  })

  it('el asesor responde una conversación que espera atención', async () => {
    let enviado: unknown = null
    server.use(
      ...base,
      http.get(`${API}/comercial/conversaciones`, () =>
        HttpResponse.json([
          { id: 'cv1', telefono: '573005551234', interesado_id: 'i1', nodo: 'asesor', datos: { ciudad: 'Bogota' }, estado: 'asesor', asesor_id: null, tarea_id: null, updated_at: '2026-10-24T14:00:00Z' },
        ]),
      ),
      http.post(`${API}/comercial/conversaciones/cv1/mensajes`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({})
      }),
    )
    const user = userEvent.setup()
    renderizar(<ComercialPage />)
    await user.click(await screen.findByRole('tab', { name: 'Conversaciones' }))
    await user.click(await screen.findByRole('button', { name: 'Responder' }))
    await user.type(screen.getByLabelText('Mensaje para 573005551234'), 'Hola Paula, te cuento del plan')
    await user.click(screen.getByRole('button', { name: /enviar/i }))
    await waitFor(() => expect(enviado).toEqual({ texto: 'Hola Paula, te cuento del plan' }))
  })

  it('sólo administración edita el guion del bot', async () => {
    server.use(...base, http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'comercial' })))
    renderizar(<ComercialPage />)
    await screen.findByRole('tab', { name: 'Conversaciones' })
    await waitFor(() => expect(screen.queryByRole('tab', { name: 'Guion del bot' })).not.toBeInTheDocument())
  })
})
