import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'

import { PreventivosPage } from './PreventivosPage'
import { FAMILIA, USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { EventoBandeja, FamiliaBandeja } from '@/types'

const API = '*/api/v1'
const LUNA = FAMILIA.mascotas![0]!

const EVENTO: EventoBandeja = {
  id: 'e1',
  mascota_id: LUNA.id,
  esquema_codigo: 'rabia',
  tipo: 'vacuna',
  dosis_numero: 1,
  es_refuerzo: false,
  estado: 'programado',
  fecha_programada: '2020-01-10',
  fecha_aplicacion: null,
  proxima_fecha: null,
  producto: null,
  lote: null,
  peso_kg: null,
  aplicado_por_nombre: null,
  requiere_autorizacion: true,
  autorizado: false,
  medio_autorizacion: null,
  autorizado_en: null,
  notificado_en: null,
  servicio_id: null,
  nombre: 'Rabia',
  mascota_nombre: 'Luna',
  especie: 'canino',
  siguiente: 'autorizar',
  visita: null,
}
const OTRO: EventoBandeja = { ...EVENTO, id: 'e2', nombre: 'Polivalente', fecha_programada: '2099-01-20', es_refuerzo: true }

const grupo = (eventos: EventoBandeja[]): FamiliaBandeja => ({
  familia_id: FAMILIA.id,
  titular_nombre: FAMILIA.titular_nombre,
  ciudad: 'Bogota',
  telefono: '+573001112233',
  eventos,
})
const pagina = (items: unknown[]) => ({ items, total: items.length, limit: 20, offset: 0 })
const RECUENTOS = { por_autorizar: 2, por_agendar: 1, agendados: 0, todos: 3 }

describe('PreventivosPage', () => {
  beforeEach(() => {
    server.use(
      http.get(`${API}/preventivos/bandeja/recuentos`, () => HttpResponse.json(RECUENTOS)),
      http.get(`${API}/preventivos/bandeja`, () => HttpResponse.json(pagina([grupo([EVENTO, OTRO])]))),
    )
  })

  it('agrupa por familia lo que falta autorizar, sin repetir el estado en cada fila', async () => {
    const consultas: string[] = []
    server.use(
      http.get(`${API}/preventivos/bandeja`, ({ request }) => {
        consultas.push(new URL(request.url).search)
        return HttpResponse.json(pagina([grupo([EVENTO, OTRO])]))
      }),
    )
    renderizar(<PreventivosPage />)
    const titular = await screen.findByRole('link', { name: FAMILIA.titular_nombre })
    expect(titular).toHaveAttribute('href', `/familias/${FAMILIA.id}`)
    expect(consultas[0]).toContain('vista=por_autorizar')
    expect(screen.getByRole('button', { name: 'Registrar autorización (2)' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /escribir/i })).toHaveAttribute('href', 'https://wa.me/573001112233')
    expect(screen.getByText('Luna · Rabia')).toBeInTheDocument()
    // Un refuerzo se dice «refuerzo»: «dosis 1, refuerzo» se leía como dos cosas.
    expect(screen.getByText('refuerzo')).toBeInTheDocument()
    expect(screen.getByText('dosis 1')).toBeInTheDocument()
    // Lo vencido con icono y palabra; lo que aún no llega, solo su fecha.
    expect(screen.getByText('vencido')).toBeInTheDocument()
    expect(screen.getByText('20 ene 2099')).toBeInTheDocument()
    expect(screen.queryByRole('columnheader', { name: 'Estado' })).not.toBeInTheDocument()
    expect(await screen.findByRole('button', { name: 'Por autorizar 2' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('registra de una vez lo que la familia autorizó', async () => {
    let enviado: unknown = null
    server.use(
      http.post(`${API}/preventivos/autorizaciones`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json([])
      }),
    )
    const user = userEvent.setup()
    renderizar(<PreventivosPage />)
    await user.click(await screen.findByRole('button', { name: 'Registrar autorización (2)' }))
    const ventana = await screen.findByRole('dialog', { name: `Autorización de ${FAMILIA.titular_nombre}` })
    // Llega todo marcado: se desmarca lo que la familia no autorizó.
    await user.click(within(ventana).getByRole('checkbox', { name: /Polivalente/ }))
    await user.selectOptions(within(ventana).getByLabelText('Por dónde respondió'), 'telefono')
    await user.click(within(ventana).getByRole('button', { name: 'La familia autorizó' }))
    await waitFor(() => expect(enviado).toEqual({ eventos: ['e1'], medio: 'telefono', aprobado: true }))
  })

  it('agenda la visita de lo autorizado contra las franjas de su ciudad', async () => {
    let agendado: unknown = null
    const autorizado = { ...EVENTO, autorizado: true, siguiente: 'agendar' as const, fecha_programada: '2099-01-10' }
    server.use(
      http.get(`${API}/preventivos/bandeja`, () => HttpResponse.json(pagina([grupo([autorizado])]))),
      http.get(`${API}/agenda/disponibilidad`, ({ request }) => {
        expect(new URL(request.url).searchParams.get('ciudad')).toBe('Bogota')
        return HttpResponse.json([{ inicio: '2099-01-10T14:00:00Z', fin: '2099-01-10T15:00:00Z', disponibles: 1 }])
      }),
      http.post(`${API}/preventivos/:id/agendar`, async ({ request }) => {
        agendado = await request.json()
        return HttpResponse.json(autorizado)
      }),
    )
    const user = userEvent.setup()
    renderizar(<PreventivosPage />, { ruta: '/preventivos?vista=por_agendar' })
    await user.click(await screen.findByRole('button', { name: 'Agendar Rabia de Luna' }))
    const ventana = await screen.findByRole('dialog', { name: 'Agendar Rabia de Luna' })
    await user.click(await within(ventana).findByRole('button', { name: '9:00 a. m.' }))
    await user.click(within(ventana).getByRole('button', { name: 'Agendar a las 9:00 a. m.' }))
    await waitFor(() => expect(agendado).toEqual({ inicio: '2099-01-10T14:00:00Z' }))
  })

  it('en «Todos» dice el estado y lleva a la visita agendada', async () => {
    const agendado = {
      ...EVENTO,
      autorizado: true,
      servicio_id: 's1',
      siguiente: 'visita' as const,
      visita: { id: 's1', programado_para: '2099-01-10T14:00:00Z', estado: 'agendado' },
    }
    server.use(http.get(`${API}/preventivos/bandeja`, () => HttpResponse.json(pagina([grupo([agendado, OTRO])]))))
    renderizar(<PreventivosPage />, { ruta: '/preventivos?vista=todos' })
    expect(await screen.findByRole('link', { name: /sáb 10 ene · 9:00 a\. m\./ })).toHaveAttribute('href', '/servicios/s1')
    expect(screen.getByRole('columnheader', { name: 'Estado' })).toBeInTheDocument()
    // El otro preventivo sigue por autorizar: la vista y su fila lo dicen.
    expect(within(screen.getByText('Luna · Polivalente').closest('tr')!).getByText('Por autorizar')).toBeInTheDocument()
  })

  it('el médico registra lo aplicado sin visita desde el menú del preventivo', async () => {
    let enviado: unknown = null
    const autorizado = { ...EVENTO, autorizado: true, siguiente: 'agendar' as const }
    server.use(
      http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'medico' })),
      http.get(`${API}/preventivos/bandeja`, () => HttpResponse.json(pagina([grupo([autorizado])]))),
      http.post(`${API}/preventivos/:id/aplicacion`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(autorizado)
      }),
    )
    const user = userEvent.setup()
    renderizar(<PreventivosPage />)
    await user.click(await screen.findByRole('button', { name: 'Más acciones de Rabia de Luna' }))
    await user.click(await screen.findByRole('menuitem', { name: 'Registrar aplicación sin visita' }))
    const ventana = await screen.findByRole('dialog', { name: 'Registrar aplicación de Rabia de Luna' })
    await user.type(within(ventana).getByLabelText('Producto'), 'Nobivac Rabia')
    await user.type(within(ventana).getByLabelText('Lote'), 'L-77')
    await user.type(within(ventana).getByLabelText(/peso/i), '8.4')
    await user.click(within(ventana).getByRole('button', { name: 'Registrar aplicación' }))
    await waitFor(() => expect(enviado).toMatchObject({ producto: 'Nobivac Rabia', lote: 'L-77', peso_kg: 8.4 }))
  })

  it('operaciones cancela un preventivo con su motivo, pero no registra aplicaciones', async () => {
    let enviado: unknown = null
    server.use(
      http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'operaciones' })),
      http.post(`${API}/preventivos/:id/cancelacion`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(EVENTO)
      }),
    )
    const user = userEvent.setup()
    renderizar(<PreventivosPage />)
    await user.click(await screen.findByRole('button', { name: 'Más acciones de Rabia de Luna' }))
    expect(screen.queryByRole('menuitem', { name: /registrar aplicación/i })).not.toBeInTheDocument()
    await user.click(await screen.findByRole('menuitem', { name: 'Cancelar preventivo' }))
    const ventana = await screen.findByRole('dialog', { name: 'Cancelar Rabia de Luna' })
    await user.type(within(ventana).getByLabelText('Motivo'), 'Se la aplicaron en otra clínica')
    await user.click(within(ventana).getByRole('button', { name: 'Cancelar preventivo' }))
    await waitFor(() => expect(enviado).toEqual({ motivo: 'Se la aplicaron en otra clínica' }))
  })

  it('dice por qué la vista está vacía y muestra el error del servidor', async () => {
    server.use(http.get(`${API}/preventivos/bandeja`, () => HttpResponse.json(pagina([]))))
    const { unmount } = renderizar(<PreventivosPage />, { ruta: '/preventivos?vista=agendados' })
    expect(await screen.findByText('Ningún preventivo tiene visita agendada.')).toBeInTheDocument()
    unmount()
    server.use(http.get(`${API}/preventivos/bandeja`, () => HttpResponse.json({ detail: 'Servicio no disponible' }, { status: 503 })))
    renderizar(<PreventivosPage />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Servicio no disponible')
  })

  it('muestra el carnet de una mascota y emite el PDF', async () => {
    server.use(
      http.get(`${API}/preventivos/mascotas/:id/carnet`, () =>
        HttpResponse.json({
          mascota: { id: LUNA.id, nombre: 'Luna', especie: 'Canino', raza: null, fecha_nacimiento: null },
          aplicados: [
            { id: 'a1', tipo: 'vacuna', nombre: 'Rabia', dosis: 1, refuerzo: false, fecha_programada: '2026-09-01', fecha_aplicacion: '2026-09-01', producto: 'Nobivac', lote: 'L-1', peso_kg: null, proxima_fecha: null },
            { id: 'a2', tipo: 'desparasitacion_interna', nombre: 'Desparasitación interna', dosis: 1, refuerzo: false, fecha_programada: '2026-09-05', fecha_aplicacion: '2026-09-05', producto: 'Drontal', lote: null, peso_kg: 8.4, aplicado_por: 'Dra. Paula Gómez', proxima_fecha: null },
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
    // La desparasitación lleva el peso que se anotó al aplicarla.
    expect(screen.getByText(/Drontal · 8,4 kg · aplicó Dra. Paula Gómez/)).toBeInTheDocument()
    expect(screen.getByText('Nada vencido.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /emitir carnet pdf/i }))
    expect(await screen.findByRole('link', { name: 'Página de verificación' })).toHaveAttribute('href', '/verificar/ABC234')
  })

  it('desde la ficha de una mascota abre directo su carnet', async () => {
    let pedido = ''
    server.use(
      http.get(`${API}/mascotas/:id`, () => HttpResponse.json(LUNA)),
      http.get(`${API}/preventivos/mascotas/:id/carnet`, ({ params }) => {
        pedido = String(params.id)
        return HttpResponse.json({
          mascota: { id: LUNA.id, nombre: 'Luna', especie: 'Canino', raza: null, fecha_nacimiento: null },
          aplicados: [],
          vencidos: [],
          proximos: [],
        })
      }),
    )
    renderizar(<PreventivosPage />, { ruta: `/preventivos?mascota=${LUNA.id}` })
    expect(await screen.findByRole('tab', { name: 'Carnet por mascota', selected: true })).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Carnet de Luna' })).toBeInTheDocument()
    expect(pedido).toBe(LUNA.id)
    // Con la familia de la mascota ya elegida, se puede pasar a otra de sus mascotas.
    expect(await screen.findByLabelText('Mascota')).toHaveValue(LUNA.id)
  })
})
