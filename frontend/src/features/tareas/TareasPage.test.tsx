import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { TareasPage } from './TareasPage'
import { USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { TareaRead } from '@/types'

const API = '*/api/v1'

const TAREA: TareaRead = {
  id: 't1',
  titulo: 'Llamar por cuota vencida',
  descripcion: null,
  area: 'cartera',
  prioridad: 'alta',
  estado: 'abierta',
  vence_el: '2026-10-20',
  asignada_a_id: null,
  familia_id: null,
  servicio_id: null,
  contrato_id: null,
  origen: null,
  cerrada_en: null,
  resolucion: null,
  created_at: '2026-10-18T10:00:00Z',
}

const pagina = (items: unknown[]) => ({ items, total: items.length, limit: 25, offset: 0 })

describe('TareasPage', () => {
  it('lista las tareas y se toma una sin asignar', async () => {
    let asignacion: unknown = null
    server.use(
      http.get(`${API}/tareas`, () => HttpResponse.json(pagina([TAREA]))),
      http.get(`${API}/auth/equipo`, () => HttpResponse.json([])),
      http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'operaciones' })),
      http.patch(`${API}/tareas/t1/asignacion`, async ({ request }) => {
        asignacion = await request.json()
        return HttpResponse.json({ ...TAREA, asignada_a_id: USUARIO_ADMIN.id })
      }),
    )
    const user = userEvent.setup()
    renderizar(<TareasPage />)
    const fila = (await screen.findByText('Llamar por cuota vencida')).closest('tr')!
    expect(within(fila).getByText('Alta')).toBeInTheDocument()
    await user.click(within(fila).getByRole('button', { name: 'Tomar' }))
    await waitFor(() => expect(asignacion).toEqual({ usuario_id: USUARIO_ADMIN.id }))
  })

  it('cambia de vista y consulta con el filtro correspondiente', async () => {
    const consultas: string[] = []
    server.use(
      http.get(`${API}/tareas`, ({ request }) => {
        consultas.push(new URL(request.url).search)
        return HttpResponse.json(pagina([]))
      }),
    )
    const user = userEvent.setup()
    renderizar(<TareasPage />)
    expect(await screen.findByText(/no hay tareas en esta vista/i)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Vencidas' }))
    await waitFor(() => expect(consultas.some((c) => c.includes('vencidas=true'))).toBe(true))
  })

  it('cierra una tarea con su resolución', async () => {
    let cierre: unknown = null
    server.use(
      http.get(`${API}/tareas`, () => HttpResponse.json(pagina([TAREA]))),
      http.post(`${API}/tareas/t1/cerrar`, async ({ request }) => {
        cierre = await request.json()
        return HttpResponse.json({ ...TAREA, estado: 'cerrada' })
      }),
    )
    const user = userEvent.setup()
    renderizar(<TareasPage />)
    await user.click(await screen.findByRole('button', { name: 'Cerrar' }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Cómo se resolvió'), 'Pagó por transferencia')
    await user.click(within(modal).getByRole('button', { name: 'Cerrar tarea' }))
    await waitFor(() => expect(cierre).toEqual({ resolucion: 'Pagó por transferencia' }))
  })

  it('crea una tarea', async () => {
    let creada: unknown = null
    server.use(
      http.post(`${API}/tareas`, async ({ request }) => {
        creada = await request.json()
        return HttpResponse.json(TAREA, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<TareasPage />)
    await user.click(await screen.findByRole('button', { name: /nueva tarea/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Qué hay que hacer'), 'Confirmar dirección')
    await user.selectOptions(within(modal).getByLabelText('Prioridad'), 'alta')
    await user.type(within(modal).getByLabelText('Vence en (días)'), '2')
    await user.click(within(modal).getByRole('button', { name: 'Crear tarea' }))
    await waitFor(() =>
      expect(creada).toEqual({ titulo: 'Confirmar dirección', area: 'operaciones', prioridad: 'alta', vence_en_dias: 2 }),
    )
  })

  it('muestra el error del servidor', async () => {
    server.use(http.get(`${API}/tareas`, () => HttpResponse.json({ detail: 'Sin conexión a la base' }, { status: 503 })))
    renderizar(<TareasPage />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Sin conexión a la base')
  })
})
