import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { ServicioDetallePage } from './ServicioDetallePage'
import { ServiciosPage } from './ServiciosPage'
import { FAMILIA, USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { ServicioRead } from '@/types'

const API = '*/api/v1'

const SERVICIO: ServicioRead = {
  id: 's1',
  familia_id: FAMILIA.id,
  mascota_id: FAMILIA.mascotas?.[0]?.id ?? null,
  tipo_codigo: 'consulta_domiciliaria',
  tipo: 'domiciliario',
  estado: 'agendado',
  ciudad: 'Bogota',
  programado_para: '2026-10-26T14:30:00Z',
  termina_en: '2026-10-26T15:15:00Z',
  requiere_autorizacion: false,
  autorizado: false,
  autorizado_en: null,
  profesional_id: null,
  pendiente_origen_id: null,
  observaciones: 'Revisar oído',
  motivo_estado: null,
}

const pagina = (items: unknown[]) => ({ items, total: items.length, limit: 25, offset: 0 })

describe('ServiciosPage', () => {
  it('lista los servicios con el nombre del tipo y su estado', async () => {
    server.use(http.get(`${API}/servicios`, () => HttpResponse.json(pagina([SERVICIO]))))
    renderizar(<ServiciosPage />)
    const enlace = await screen.findByRole('link', { name: 'Consulta domiciliaria' })
    expect(enlace).toHaveAttribute('href', '/servicios/s1')
    expect(within(enlace.closest('tr')!).getByText('Agendado')).toBeInTheDocument()
  })

  it('filtra por estado', async () => {
    const estados: (string | null)[] = []
    server.use(
      http.get(`${API}/servicios`, ({ request }) => {
        estados.push(new URL(request.url).searchParams.get('estado'))
        return HttpResponse.json(pagina([]))
      }),
    )
    const user = userEvent.setup()
    renderizar(<ServiciosPage />)
    expect(await screen.findByText('No hay servicios con estos filtros.')).toBeInTheDocument()
    await user.selectOptions(screen.getByLabelText('Estado'), 'completado')
    await waitFor(() => expect(estados).toContain('completado'))
  })

  it('agenda un servicio eligiendo familia, tipo y una franja con cupo', async () => {
    let enviado: unknown = null
    server.use(
      http.get(`${API}/servicios/elegibilidad`, () => HttpResponse.json({ elegible: true, motivos: [] })),
      http.get(`${API}/agenda/disponibilidad`, () =>
        HttpResponse.json([
          { inicio: '2026-10-26T13:00:00Z', fin: '2026-10-26T13:45:00Z', disponibles: 0 },
          { inicio: '2026-10-26T14:00:00Z', fin: '2026-10-26T14:45:00Z', disponibles: 2 },
        ]),
      ),
      http.post(`${API}/servicios`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(SERVICIO, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<ServiciosPage />)
    await user.click(await screen.findByRole('button', { name: /agendar servicio/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByRole('searchbox'), 'Ana')
    await user.click(await within(modal).findByRole('button', { name: /ana ruiz/i }))
    await user.selectOptions(within(modal).getByLabelText('Mascota'), 'Luna')
    await waitFor(() => expect(within(modal).getByRole('option', { name: /consulta domiciliaria/i })).toBeInTheDocument())
    await user.selectOptions(within(modal).getByLabelText('Tipo de servicio'), 'consulta_domiciliaria')
    expect(await within(modal).findByText('El plan de la familia cubre este servicio.')).toBeInTheDocument()
    const franjas = await within(modal).findAllByRole('button', { pressed: false })
    expect(franjas[0]).toBeDisabled()
    await user.click(franjas[1]!)
    await user.click(within(modal).getByRole('button', { name: 'Agendar' }))
    await waitFor(() =>
      expect(enviado).toEqual({
        familia_id: FAMILIA.id,
        mascota_id: FAMILIA.mascotas?.[0]?.id,
        tipo_codigo: 'consulta_domiciliaria',
        inicio: '2026-10-26T14:00:00Z',
      }),
    )
  })

  it('los de operaciones administran las franjas de agenda', async () => {
    server.use(
      http.get(`${API}/agenda/franjas`, () =>
        HttpResponse.json([
          { id: 'f1', ciudad: 'Bogota', modalidad: 'domiciliario', dia_semana: 0, hora_inicio: '08:00:00', hora_fin: '12:00:00', capacidad: 2, activa: true },
        ]),
      ),
    )
    const user = userEvent.setup()
    renderizar(<ServiciosPage />)
    await user.click(await screen.findByRole('tab', { name: 'Franjas de agenda' }))
    expect(await screen.findByText('Lunes')).toBeInTheDocument()
    expect(screen.getByText('08:00 – 12:00')).toBeInTheDocument()
  })

  it('un médico no ve la pestaña de franjas', async () => {
    server.use(http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'medico' })))
    renderizar(<ServiciosPage />)
    await screen.findByRole('tab', { name: 'Pendientes' })
    await waitFor(() => expect(screen.queryByRole('tab', { name: 'Franjas de agenda' })).not.toBeInTheDocument())
  })
})

describe('ServicioDetallePage', () => {
  function abrir() {
    return renderizar(
      <Routes>
        <Route path="/servicios/:id" element={<ServicioDetallePage />} />
      </Routes>,
      { ruta: '/servicios/s1' },
    )
  }

  it('ofrece sólo las transiciones permitidas desde el estado actual', async () => {
    server.use(http.get(`${API}/servicios/s1`, () => HttpResponse.json(SERVICIO)))
    abrir()
    expect(await screen.findByRole('heading', { name: 'Consulta domiciliaria' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Salir en ruta' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Iniciar atención' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Completar servicio' })).not.toBeInTheDocument()
  })

  it('inicia la atención', async () => {
    let enviado: unknown = null
    server.use(
      http.get(`${API}/servicios/s1`, () => HttpResponse.json(SERVICIO)),
      http.post(`${API}/servicios/s1/estado`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ ...SERVICIO, estado: 'en_atencion' })
      }),
    )
    const user = userEvent.setup()
    abrir()
    await user.click(await screen.findByRole('button', { name: 'Iniciar atención' }))
    await waitFor(() => expect(enviado).toEqual({ estado: 'en_atencion' }))
  })

  it('durante la atención registra los pasos con sus campos', async () => {
    let enviado: unknown = null
    server.use(
      http.get(`${API}/servicios/s1`, () => HttpResponse.json({ ...SERVICIO, estado: 'en_atencion' })),
      http.put(`${API}/servicios/s1/pasos/valoracion`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ paso_codigo: 'valoracion', datos: {}, completado_por_id: null, created_at: '' })
      }),
    )
    const user = userEvent.setup()
    abrir()
    const pasos = await screen.findByRole('heading', { name: 'Pasos de la atención' })
    const tarjeta = pasos.closest('section')!
    await user.click((await within(tarjeta).findAllByRole('button', { name: 'Registrar' }))[0]!)
    await user.type(within(tarjeta).getByLabelText('Hallazgos'), 'Otitis leve')
    await user.click(within(tarjeta).getByRole('button', { name: 'Guardar paso' }))
    await waitFor(() => expect(enviado).toEqual({ datos: { hallazgos: 'Otitis leve' } }))
  })

  it('cancela con motivo', async () => {
    let enviado: unknown = null
    server.use(
      http.get(`${API}/servicios/s1`, () => HttpResponse.json(SERVICIO)),
      http.post(`${API}/servicios/s1/estado`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ ...SERVICIO, estado: 'cancelado' })
      }),
    )
    const user = userEvent.setup()
    abrir()
    await user.click(await screen.findByRole('button', { name: 'Cancelar servicio' }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Motivo de la cancelación'), 'La familia viaja')
    await user.click(within(modal).getByRole('button', { name: 'Confirmar cancelación' }))
    await waitFor(() => expect(enviado).toEqual({ estado: 'cancelado', motivo: 'La familia viaja' }))
  })

  it('muestra el error del servidor al cambiar de estado', async () => {
    server.use(
      http.get(`${API}/servicios/s1`, () => HttpResponse.json(SERVICIO)),
      http.post(`${API}/servicios/s1/estado`, () =>
        HttpResponse.json({ detail: 'Faltan pasos obligatorios' }, { status: 422 }),
      ),
    )
    const user = userEvent.setup()
    abrir()
    await user.click(await screen.findByRole('button', { name: 'Salir en ruta' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Faltan pasos obligatorios')
  })

  it('agrega un pendiente que requiere autorización', async () => {
    let enviado: unknown = null
    server.use(
      http.get(`${API}/servicios/s1`, () => HttpResponse.json(SERVICIO)),
      http.post(`${API}/servicios/s1/pendientes`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({}, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    abrir()
    await user.type(await screen.findByLabelText('Nuevo pendiente'), 'Examen de sangre')
    await user.click(screen.getByRole('button', { name: 'Agregar pendiente' }))
    await waitFor(() => expect(enviado).toEqual({ descripcion: 'Examen de sangre', requiere_autorizacion: true }))
  })
})
