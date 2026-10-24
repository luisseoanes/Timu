import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { CampanasPage } from './CampanasPage'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { CampanaRead } from '@/types'

const API = '*/api/v1'

const CAMPANA: CampanaRead = {
  id: 'c1',
  nombre: 'Renovación noviembre',
  canal: 'whatsapp',
  plantilla: 'recordatorio_renovacion',
  variables: ['titular_nombre'],
  segmento_id: null,
  segmento: {},
  estado: 'borrador',
  programada_para: null,
  recurrencia: 'ninguna',
  proxima_ejecucion: null,
}

const PLANTILLA = {
  id: 'p1',
  nombre: 'recordatorio_renovacion',
  idioma: 'es',
  version: 1,
  categoria: 'utility',
  cuerpo: 'Hola {{1}}, tu plan se renueva pronto.',
  variables: ['1'],
  estado_aprobacion: 'aprobada',
  activa: true,
}

const base = [
  http.get(`${API}/campanas`, () => HttpResponse.json([CAMPANA])),
  http.get(`${API}/segmentos`, () => HttpResponse.json([])),
  http.get(`${API}/comunicaciones/plantillas`, () => HttpResponse.json([PLANTILLA])),
  http.get(`${API}/planes`, () => HttpResponse.json([])),
]

describe('CampanasPage', () => {
  it('lista las campañas y muestra la audiencia con un ejemplo del mensaje', async () => {
    server.use(
      ...base,
      http.get(`${API}/campanas/c1/previsualizacion`, () =>
        HttpResponse.json({ audiencia: 40, excluidos_por_baja: 2, se_enviaran: 38, ejemplos: [{ titular: 'Ana Ruiz', mensaje: 'Hola Ana Ruiz, tu plan se renueva pronto.' }] }),
      ),
      http.get(`${API}/campanas/c1/resultados`, () => HttpResponse.json({ audiencia: 0 })),
      http.get(`${API}/campanas/c1/ejecuciones`, () => HttpResponse.json([])),
    )
    const user = userEvent.setup()
    renderizar(<CampanasPage />)
    const fila = (await screen.findByText('Renovación noviembre')).closest('tr')!
    await user.click(within(fila).getByRole('button', { name: 'Ver' }))
    const modal = await screen.findByRole('dialog')
    expect(await within(modal).findByText('38')).toBeInTheDocument()
    expect(within(modal).getByText('Hola Ana Ruiz, tu plan se renueva pronto.')).toBeInTheDocument()
  })

  it('envía ahora una campaña en borrador', async () => {
    let enviado: unknown = null
    server.use(
      ...base,
      http.get(`${API}/campanas/c1/previsualizacion`, () => HttpResponse.json({ audiencia: 1, excluidos_por_baja: 0, se_enviaran: 1, ejemplos: [] })),
      http.get(`${API}/campanas/c1/resultados`, () => HttpResponse.json({ audiencia: 0 })),
      http.get(`${API}/campanas/c1/ejecuciones`, () => HttpResponse.json([])),
      http.post(`${API}/campanas/c1/programacion`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ ...CAMPANA, estado: 'en_envio' })
      }),
    )
    const user = userEvent.setup()
    renderizar(<CampanasPage />)
    await user.click(await screen.findByRole('button', { name: 'Ver' }))
    await user.click(await within(await screen.findByRole('dialog')).findByRole('button', { name: 'Enviar ahora' }))
    await waitFor(() => expect(enviado).toEqual({ recurrencia: 'ninguna' }))
  })

  it('crea una campaña con plantilla aprobada, variable del titular y filtros', async () => {
    let enviado: Record<string, unknown> | null = null
    server.use(
      ...base,
      http.post(`${API}/segmentos/previsualizacion`, () => HttpResponse.json({ total: 12, muestra: [] })),
      http.post(`${API}/campanas`, async ({ request }) => {
        enviado = (await request.json()) as Record<string, unknown>
        return HttpResponse.json(CAMPANA, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<CampanasPage />)
    await user.click(await screen.findByRole('button', { name: /nueva campaña/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nombre'), 'Renovación')
    await waitFor(() => expect(within(modal).getByRole('option', { name: 'recordatorio_renovacion' })).toBeInTheDocument())
    await user.selectOptions(within(modal).getByLabelText('Plantilla'), 'recordatorio_renovacion')
    await user.click(within(modal).getByRole('button', { name: 'En mora' }))
    await user.click(within(modal).getByRole('button', { name: 'Contar audiencia' }))
    expect(await within(modal).findByText('12')).toBeInTheDocument()
    await user.click(within(modal).getByRole('button', { name: 'Crear campaña' }))
    await waitFor(() =>
      expect(enviado).toEqual({
        nombre: 'Renovación',
        plantilla: 'recordatorio_renovacion',
        variables: ['titular_nombre'],
        segmento: { estados: ['en_mora'] },
      }),
    )
  })

  it('muestra la satisfacción del mes', async () => {
    server.use(
      ...base,
      http.get(`${API}/encuestas/resumen`, () =>
        HttpResponse.json({ enviadas: 20, respondidas: 15, tasa_respuesta: 0.75, promedio: 4.7, por_responsable: [], por_tipo_servicio: [] }),
      ),
      http.get(`${API}/encuestas`, () =>
        HttpResponse.json({
          items: [{ id: 'e1', servicio_id: 's1', familia_id: 'f1', responsable_id: null, tipo: 'satisfaccion', estado: 'respondida', programada_para: '', enviada_en: null, respondida_en: '2026-10-22T15:00:00Z', canal_respuesta: 'enlace', puntaje: 2, comentario: 'Llegaron tarde', tarea_id: 't1' }],
          total: 1,
          limit: 20,
          offset: 0,
        }),
      ),
      http.get(`${API}/encuestas/configuracion`, () => HttpResponse.json([])),
    )
    const user = userEvent.setup()
    renderizar(<CampanasPage />)
    await user.click(await screen.findByRole('tab', { name: 'Encuestas' }))
    expect(await screen.findByText('4.7 / 5')).toBeInTheDocument()
    expect(screen.getByText('Llegaron tarde')).toBeInTheDocument()
    expect(screen.getByText('Con tarea de seguimiento')).toBeInTheDocument()
  })
})
