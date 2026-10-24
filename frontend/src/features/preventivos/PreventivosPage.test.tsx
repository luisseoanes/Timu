import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { PreventivosPage } from './PreventivosPage'
import { FAMILIA, USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { EventoRead } from '@/types'

const API = '*/api/v1'
const LUNA = FAMILIA.mascotas![0]!

const EVENTO: EventoRead = {
  id: 'e1',
  mascota_id: LUNA.id,
  esquema_codigo: 'rabia',
  tipo: 'vacuna',
  dosis_numero: 1,
  es_refuerzo: false,
  estado: 'programado',
  fecha_programada: '2099-01-10',
  fecha_aplicacion: null,
  proxima_fecha: null,
  producto: null,
  lote: null,
  requiere_autorizacion: true,
  autorizado: false,
  medio_autorizacion: null,
  autorizado_en: null,
  notificado_en: null,
  servicio_id: null,
}

const pagina = (items: unknown[]) => ({ items, total: items.length, limit: 25, offset: 0 })

describe('PreventivosPage', () => {
  it('lista el calendario con el nombre de la mascota', async () => {
    server.use(
      http.get(`${API}/preventivos`, () => HttpResponse.json(pagina([EVENTO]))),
      http.get(`${API}/mascotas/:id`, () => HttpResponse.json(LUNA)),
    )
    renderizar(<PreventivosPage />)
    const enlace = await screen.findByRole('link', { name: 'Luna' })
    const fila = enlace.closest('tr')!
    expect(within(fila).getByText('Vacuna · dosis 1')).toBeInTheDocument()
    expect(within(fila).getByText('Por autorizar')).toBeInTheDocument()
  })

  it('muestra el vacío y el error', async () => {
    server.use(http.get(`${API}/preventivos`, () => HttpResponse.json(pagina([]))))
    renderizar(<PreventivosPage />)
    expect(await screen.findByText(/no hay eventos preventivos/i)).toBeInTheDocument()
  })

  it('registra la autorización de la familia', async () => {
    let enviado: unknown = null
    server.use(
      http.get(`${API}/preventivos`, () => HttpResponse.json(pagina([EVENTO]))),
      http.get(`${API}/mascotas/:id`, () => HttpResponse.json(LUNA)),
      http.post(`${API}/preventivos/e1/autorizacion`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ ...EVENTO, autorizado: true })
      }),
    )
    const user = userEvent.setup()
    renderizar(<PreventivosPage />)
    await user.click(await screen.findByRole('button', { name: 'Gestionar' }))
    const modal = await screen.findByRole('dialog')
    // Sin autorización no se ofrece aplicar ni agendar.
    expect(within(modal).queryByRole('button', { name: 'Registrar aplicación' })).not.toBeInTheDocument()
    await user.click(within(modal).getByRole('button', { name: 'Registrar autorización' }))
    await user.selectOptions(within(modal).getByLabelText(/medio por el que respondió/i), 'telefono')
    await user.click(within(modal).getByRole('button', { name: 'La familia autorizó' }))
    await waitFor(() => expect(enviado).toEqual({ medio: 'telefono', aprobado: true }))
  })

  it('el médico registra la aplicación de un preventivo autorizado', async () => {
    let enviado: unknown = null
    server.use(
      http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'medico' })),
      http.get(`${API}/preventivos`, () => HttpResponse.json(pagina([{ ...EVENTO, autorizado: true }]))),
      http.get(`${API}/mascotas/:id`, () => HttpResponse.json(LUNA)),
      http.post(`${API}/preventivos/e1/aplicacion`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ ...EVENTO, estado: 'aplicado' })
      }),
    )
    const user = userEvent.setup()
    renderizar(<PreventivosPage />)
    await user.click(await screen.findByRole('button', { name: 'Gestionar' }))
    const modal = await screen.findByRole('dialog')
    await user.click(within(modal).getByRole('button', { name: 'Registrar aplicación' }))
    await user.type(within(modal).getByLabelText('Producto'), 'Nobivac Rabia')
    await user.type(within(modal).getByLabelText('Lote'), 'L-77')
    await user.click(within(modal).getAllByRole('button', { name: 'Registrar aplicación' }).at(-1)!)
    await waitFor(() => expect(enviado).toMatchObject({ producto: 'Nobivac Rabia', lote: 'L-77' }))
  })

  it('muestra el carnet de una mascota y emite el PDF', async () => {
    server.use(
      http.get(`${API}/preventivos/mascotas/:id/carnet`, () =>
        HttpResponse.json({
          mascota: { id: LUNA.id, nombre: 'Luna', especie: 'Canino', raza: null, fecha_nacimiento: null },
          aplicados: [
            { id: 'a1', tipo: 'vacuna', nombre: 'Rabia', dosis: 1, refuerzo: false, fecha_programada: '2026-09-01', fecha_aplicacion: '2026-09-01', producto: 'Nobivac', lote: 'L-1', proxima_fecha: null },
          ],
          vencidos: [],
          proximos: [],
        }),
      ),
      http.post(`${API}/preventivos/mascotas/:id/carnet/pdf`, () =>
        HttpResponse.json({ codigo: 'ABC234', url: 'https://s3/carnet.pdf', sha256: 'x' }),
      ),
    )
    const user = userEvent.setup()
    renderizar(<PreventivosPage />)
    await user.click(await screen.findByRole('tab', { name: 'Carnet por mascota' }))
    await user.type(screen.getByRole('searchbox'), 'Ana')
    await user.click(await screen.findByRole('button', { name: /ana ruiz/i }))
    expect(await screen.findByText('Rabia · dosis 1')).toBeInTheDocument()
    expect(screen.getByText('Nada vencido.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /emitir carnet pdf/i }))
    expect(await screen.findByRole('link', { name: 'Página de verificación' })).toHaveAttribute('href', '/verificar/ABC234')
  })
})
