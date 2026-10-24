import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { RutasPage } from './RutasPage'
import type { Ruta } from './api'
import { USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const API = '*/api/v1'
const MEDICA = { id: 'm1', nombre: 'Dra. Sara', rol: 'medico' }

const parada = (orden: number, estado: string) => ({
  id: `p${orden}`,
  servicio_id: `s${orden}`,
  orden,
  estado,
  latitud: 4.7,
  longitud: -74.05,
  llegada_estimada: '2026-10-24T14:00:00Z',
  llegada_en: null,
  salida_en: null,
  nota: null,
  motivo_omision: null,
})

const RUTA: Ruta = {
  id: 'r1',
  fecha: '2026-10-24',
  ciudad: 'Bogota',
  responsable_id: MEDICA.id,
  estado: 'en_curso',
  distancia_km: 13.8,
  duracion_min: 82,
  inicio_real: null,
  fin_real: null,
  paradas: [parada(1, 'completada'), parada(2, 'en_sitio')],
}

const base = [
  http.get(`${API}/auth/equipo`, () => HttpResponse.json([MEDICA])),
  http.get(`${API}/rutas/por-rutear`, () => HttpResponse.json([])),
]

describe('RutasPage', () => {
  it('muestra cada ruta con su responsable, paradas y el cumplimiento del día', async () => {
    server.use(...base, http.get(`${API}/rutas`, () => HttpResponse.json([RUTA])))
    renderizar(<RutasPage />)
    const ruta = await screen.findByRole('region', { name: 'Ruta de Dra. Sara' })
    expect(within(ruta).getByText(/2 paradas · 13.8 km · 82 min/)).toBeInTheDocument()
    expect(screen.getByText('1 de 2 paradas completadas')).toBeInTheDocument()
  })

  it('dice cuando no hay rutas', async () => {
    server.use(...base, http.get(`${API}/rutas`, () => HttpResponse.json([])))
    renderizar(<RutasPage />)
    expect(await screen.findByText(/no hay rutas para el/i)).toBeInTheDocument()
  })

  it('en campo se termina la visita con una nota', async () => {
    let enviado: FormData | null = null
    server.use(
      ...base,
      http.get(`${API}/rutas`, () => HttpResponse.json([RUTA])),
      http.post(`${API}/rutas/paradas/p2/salida`, async ({ request }) => {
        enviado = await request.formData()
        return HttpResponse.json(RUTA)
      }),
    )
    const user = userEvent.setup()
    renderizar(<RutasPage />)
    await user.click(await screen.findByRole('button', { name: 'Terminar visita' }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nota de la visita'), 'Todo en orden')
    await user.click(within(modal).getByRole('button', { name: 'Registrar salida' }))
    await waitFor(() => expect(enviado?.get('nota')).toBe('Todo en orden'))
  })

  it('planea rutas con quienes salen a campo y espera el resultado del optimizador', async () => {
    let pedido: unknown = null
    let consultas = 0
    server.use(
      ...base,
      http.get(`${API}/rutas`, () => HttpResponse.json([])),
      http.post(`${API}/rutas/planificaciones`, async ({ request }) => {
        pedido = await request.json()
        return HttpResponse.json({ id: 'pl1', estado: 'pendiente', resultado: {}, error: null })
      }),
      http.get(`${API}/rutas/planificaciones/pl1`, () => {
        consultas += 1
        return HttpResponse.json(
          consultas < 2
            ? { id: 'pl1', estado: 'pendiente', resultado: {}, error: null }
            : { id: 'pl1', estado: 'lista', resultado: { rutas: ['r1'], asignados: 3, sin_asignar: [{ servicio_id: 's9', motivo: 'sin_ubicacion' }] }, error: null },
        )
      }),
    )
    const user = userEvent.setup()
    renderizar(<RutasPage />)
    await user.click(await screen.findByRole('button', { name: /planear rutas/i }))
    const modal = await screen.findByRole('dialog')
    await user.click(await within(modal).findByRole('checkbox', { name: /dra. sara/i }))
    await user.click(within(modal).getByRole('button', { name: 'Planear' }))
    expect(await within(modal).findByText('1 rutas creadas con 3 servicios.', {}, { timeout: 5000 })).toBeInTheDocument()
    expect(within(modal).getByText(/la familia no tiene ubicación/)).toBeInTheDocument()
    expect(pedido).toMatchObject({ ciudad: 'Bogota', responsables: ['m1'] })
  })

  it('el comercial no planea ni cancela rutas', async () => {
    server.use(
      ...base,
      http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'comercial' })),
      http.get(`${API}/rutas`, () => HttpResponse.json([{ ...RUTA, estado: 'planificada' }])),
    )
    renderizar(<RutasPage />)
    await screen.findByRole('region', { name: 'Ruta de Dra. Sara' })
    expect(screen.queryByRole('button', { name: /planear rutas/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Cancelar ruta' })).not.toBeInTheDocument()
  })
})
