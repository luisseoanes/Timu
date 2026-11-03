import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { ServiciosPage } from './ServiciosPage'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { FranjaRead, PendienteRead, ServicioRead } from '@/types'

const API = '*/api/v1'

const pagina = (items: unknown[]) => ({ items, total: items.length, limit: 25, offset: 0 })

const servicio = (cambios: Partial<ServicioRead>): ServicioRead => ({
  id: 's1',
  familia_id: 'f1',
  mascota_id: null,
  tipo_codigo: 'consulta_domiciliaria',
  tipo: 'domiciliario',
  estado: 'agendado',
  ciudad: 'Bogota',
  programado_para: '2026-10-26T14:30:00Z',
  termina_en: null,
  requiere_autorizacion: false,
  autorizado: false,
  autorizado_en: null,
  profesional_id: null,
  pendiente_origen_id: null,
  observaciones: null,
  motivo_estado: null,
  ...cambios,
})

const pendiente = (cambios: Partial<PendienteRead>): PendienteRead => ({
  id: 'p1',
  servicio_origen_id: 's1',
  descripcion: 'Ecografía abdominal',
  requiere_autorizacion: true,
  estado: 'pendiente_autorizacion',
  autorizado_por_id: null,
  autorizado_en: null,
  medio_autorizacion: null,
  resolucion: null,
  ...cambios,
})

const FRANJA: FranjaRead = {
  id: 'fr1',
  ciudad: 'Bogota',
  modalidad: 'domiciliario',
  dia_semana: 2,
  hora_inicio: '08:00:00',
  hora_fin: '12:00:00',
  capacidad: 2,
  activa: true,
}

describe('listado de servicios', () => {
  it('distingue los que no requieren autorización, los autorizados y los que esperan', async () => {
    server.use(
      http.get(`${API}/servicios`, () =>
        HttpResponse.json(
          pagina([
            servicio({ id: 'a' }),
            servicio({ id: 'b', requiere_autorizacion: true, autorizado: true }),
            servicio({ id: 'c', requiere_autorizacion: true, autorizado: false }),
          ]),
        ),
      ),
    )
    renderizar(<ServiciosPage />)
    expect(await screen.findByText('No requiere')).toBeInTheDocument()
    expect(screen.getByText('Autorizado')).toBeInTheDocument()
    expect(screen.getAllByText('Por autorizar').length).toBeGreaterThan(0)
    expect(screen.getByText('3 servicios')).toBeInTheDocument()
  })

  it('combina ciudad y rango de fechas en la consulta', async () => {
    const consultas: URLSearchParams[] = []
    server.use(
      http.get(`${API}/servicios`, ({ request }) => {
        consultas.push(new URL(request.url).searchParams)
        return HttpResponse.json(pagina([]))
      }),
    )
    const user = userEvent.setup()
    renderizar(<ServiciosPage />)
    await screen.findByText('No hay servicios con estos filtros.')
    await user.selectOptions(screen.getByLabelText('Ciudad'), 'Bogota')
    const hasta = screen.getByLabelText('Hasta')
    await user.clear(hasta)
    await user.type(hasta, '2026-12-31')
    await waitFor(() => {
      const ultima = consultas.at(-1)!
      expect(ultima.get('ciudad')).toBe('Bogota')
      expect(ultima.get('hasta')).toBe('2026-12-31')
      expect(ultima.get('orden')).toBe('programado_para')
    })
  })

  it('avisa si no puede cargar los servicios', async () => {
    server.use(http.get(`${API}/servicios`, () => HttpResponse.json({ detail: 'Base caída' }, { status: 500 })))
    renderizar(<ServiciosPage />)
    expect(await screen.findByRole('alert')).toHaveTextContent('No fue posible cargar los servicios. Base caída')
  })

  it('abre el formulario de agendar si la ruta lo pide', async () => {
    renderizar(<ServiciosPage />, { ruta: '/servicios?nuevo=1' })
    expect(await screen.findByRole('dialog')).toBeInTheDocument()
  })
})

describe('pendientes', () => {
  async function abrirPendientes(pendientes: PendienteRead[]) {
    server.use(http.get(`${API}/pendientes`, () => HttpResponse.json(pendientes)))
    const user = userEvent.setup()
    renderizar(<ServiciosPage />)
    await user.click(await screen.findByRole('tab', { name: 'Pendientes' }))
    return user
  }

  it('solo se gestionan los que siguen abiertos', async () => {
    await abrirPendientes([
      pendiente({ id: 'p1', descripcion: 'Ecografía' }),
      pendiente({ id: 'p2', descripcion: 'Radiografía', estado: 'resuelto' }),
      pendiente({ id: 'p3', descripcion: 'Cirugía', estado: 'rechazado' }),
    ])
    const filas = await screen.findAllByRole('row')
    const fila = (texto: string) => filas.find((f) => within(f).queryByText(texto))!
    expect(within(fila('Ecografía')).getByRole('button', { name: 'Gestionar' })).toBeInTheDocument()
    expect(within(fila('Radiografía')).queryByRole('button', { name: 'Gestionar' })).not.toBeInTheDocument()
    expect(within(fila('Cirugía')).queryByRole('button', { name: 'Gestionar' })).not.toBeInTheDocument()
    expect(within(fila('Ecografía')).getByRole('link', { name: 'Ver servicio' })).toHaveAttribute('href', '/servicios/s1')
  })

  it('filtra por estado y muestra el vacío', async () => {
    const estados: (string | null)[] = []
    server.use(
      http.get(`${API}/pendientes`, ({ request }) => {
        estados.push(new URL(request.url).searchParams.get('estado'))
        return HttpResponse.json([])
      }),
    )
    const user = userEvent.setup()
    renderizar(<ServiciosPage />)
    await user.click(await screen.findByRole('tab', { name: 'Pendientes' }))
    expect(await screen.findByText('No hay pendientes en este estado.')).toBeInTheDocument()
    await user.selectOptions(screen.getByLabelText('Estado del pendiente'), '')
    await waitFor(() => expect(estados).toEqual(['pendiente_autorizacion', null]))
  })

  it('registra la autorización de la familia con el medio elegido', async () => {
    let enviado: unknown = null
    server.use(
      http.post(`${API}/pendientes/p1/autorizacion`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(pendiente({ estado: 'autorizado' }))
      }),
    )
    const user = await abrirPendientes([pendiente({})])
    await user.click(await screen.findByRole('button', { name: 'Gestionar' }))
    const modal = await screen.findByRole('dialog')
    await user.selectOptions(within(modal).getByLabelText('Medio por el que la familia autorizó'), 'llamada')
    await user.click(within(modal).getByRole('button', { name: 'Autorizado por la familia' }))
    await waitFor(() => expect(enviado).toEqual({ aprobado: true, medio: 'llamada' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('registra que la familia no autorizó', async () => {
    let enviado: unknown = null
    server.use(
      http.post(`${API}/pendientes/p1/autorizacion`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(pendiente({ estado: 'rechazado' }))
      }),
    )
    const user = await abrirPendientes([pendiente({})])
    await user.click(await screen.findByRole('button', { name: 'Gestionar' }))
    await user.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'La familia no lo autorizó' }))
    await waitFor(() => expect(enviado).toEqual({ aprobado: false, medio: 'whatsapp' }))
  })

  it('un autorizado pasa a gestión y luego se resuelve con su resolución', async () => {
    const avances: unknown[] = []
    server.use(
      http.post(`${API}/pendientes/p1/avance`, async ({ request }) => {
        avances.push(await request.json())
        return HttpResponse.json(pendiente({ estado: 'en_gestion' }))
      }),
    )
    const user = await abrirPendientes([pendiente({ estado: 'autorizado' })])
    await user.click(await screen.findByRole('button', { name: 'Gestionar' }))
    let modal = await screen.findByRole('dialog')
    await user.click(within(modal).getByRole('button', { name: 'Pasar a gestión' }))
    await waitFor(() => expect(avances).toEqual([{ estado: 'en_gestion' }]))

    await user.click(await screen.findByRole('button', { name: 'Gestionar' }))
    modal = await screen.findByRole('dialog')
    const resolver = within(modal).getByRole('button', { name: 'Marcar resuelto' })
    expect(resolver).toBeDisabled()
    await user.type(within(modal).getByLabelText('Resolución'), '  Se agendó la ecografía  ')
    await user.click(resolver)
    await waitFor(() =>
      expect(avances.at(-1)).toEqual({ estado: 'resuelto', resolucion: 'Se agendó la ecografía' }),
    )
  })

  it('en gestión ya no ofrece pasar a gestión', async () => {
    const user = await abrirPendientes([pendiente({ estado: 'en_gestion' })])
    await user.click(await screen.findByRole('button', { name: 'Gestionar' }))
    const modal = await screen.findByRole('dialog')
    expect(within(modal).queryByRole('button', { name: 'Pasar a gestión' })).not.toBeInTheDocument()
    expect(within(modal).getByRole('button', { name: 'Marcar resuelto' })).toBeInTheDocument()
  })

  it('muestra el motivo si el backend rechaza la gestión', async () => {
    server.use(
      http.post(`${API}/pendientes/p1/autorizacion`, () =>
        HttpResponse.json({ detail: 'El pendiente ya fue gestionado' }, { status: 409 }),
      ),
    )
    const user = await abrirPendientes([pendiente({})])
    await user.click(await screen.findByRole('button', { name: 'Gestionar' }))
    const modal = await screen.findByRole('dialog')
    await user.click(within(modal).getByRole('button', { name: 'Autorizado por la familia' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('El pendiente ya fue gestionado')
  })
})

describe('franjas de agenda', () => {
  async function abrirFranjas(franjas: FranjaRead[] = [FRANJA]) {
    server.use(http.get(`${API}/agenda/franjas`, () => HttpResponse.json(franjas)))
    const user = userEvent.setup()
    renderizar(<ServiciosPage />)
    await user.click(await screen.findByRole('tab', { name: 'Franjas de agenda' }))
    return user
  }

  it('activa y desactiva una franja', async () => {
    const cambios: (string | null)[] = []
    server.use(
      http.patch(`${API}/agenda/franjas/fr1`, ({ request }) => {
        cambios.push(new URL(request.url).searchParams.get('activa'))
        return HttpResponse.json({ ...FRANJA, activa: false })
      }),
    )
    const user = await abrirFranjas([FRANJA, { ...FRANJA, id: 'fr2', dia_semana: 3, activa: false }])
    expect(await screen.findByRole('button', { name: 'Activar franja Jueves 08:00' })).toHaveTextContent('Inactiva')
    await user.click(screen.getByRole('button', { name: 'Desactivar franja Miércoles 08:00' }))
    await waitFor(() => expect(cambios).toEqual(['false']))
  })

  it('sin franjas avisa de que no se puede agendar', async () => {
    await abrirFranjas([])
    expect(await screen.findByText('No hay franjas configuradas. Sin franjas no se puede agendar.')).toBeInTheDocument()
  })

  it('filtra las franjas por ciudad', async () => {
    const ciudades: (string | null)[] = []
    server.use(
      http.get(`${API}/agenda/franjas`, ({ request }) => {
        ciudades.push(new URL(request.url).searchParams.get('ciudad'))
        return HttpResponse.json([FRANJA])
      }),
    )
    const user = userEvent.setup()
    renderizar(<ServiciosPage />)
    await user.click(await screen.findByRole('tab', { name: 'Franjas de agenda' }))
    await user.selectOptions(await screen.findByLabelText('Ciudad de las franjas'), 'Bogota')
    await waitFor(() => expect(ciudades).toContain('Bogota'))
  })

  it('crea una franja nueva con todos sus datos', async () => {
    let enviado: unknown = null
    server.use(
      http.post(`${API}/agenda/franjas`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(FRANJA, { status: 201 })
      }),
    )
    const user = await abrirFranjas()
    await user.click(screen.getByRole('button', { name: /nueva franja/i }))
    const modal = await screen.findByRole('dialog')
    await user.selectOptions(within(modal).getByLabelText('Ciudad'), 'Bogota')
    await user.selectOptions(within(modal).getByLabelText('Modalidad'), 'preventivo')
    await user.selectOptions(within(modal).getByLabelText('Día'), 'Viernes')
    const capacidad = within(modal).getByLabelText('Capacidad (servicios simultáneos)')
    await user.clear(capacidad)
    await user.type(capacidad, '3')
    await user.click(within(modal).getByRole('button', { name: 'Guardar franja' }))
    await waitFor(() =>
      expect(enviado).toEqual({
        ciudad: 'Bogota',
        modalidad: 'preventivo',
        dia_semana: 4,
        hora_inicio: '08:00',
        hora_fin: '12:00',
        capacidad: 3,
      }),
    )
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('explica por qué no se pudo crear la franja', async () => {
    server.use(
      http.post(`${API}/agenda/franjas`, () =>
        HttpResponse.json({ detail: 'La franja se cruza con otra existente' }, { status: 409 }),
      ),
    )
    const user = await abrirFranjas()
    await user.click(screen.getByRole('button', { name: /nueva franja/i }))
    const modal = await screen.findByRole('dialog')
    await user.selectOptions(within(modal).getByLabelText('Ciudad'), 'Bogota')
    await user.click(within(modal).getByRole('button', { name: 'Guardar franja' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('La franja se cruza con otra existente')
  })

  it('bloquea un día para todas las ciudades y modalidades', async () => {
    let enviado: unknown = null
    server.use(
      http.post(`${API}/agenda/bloqueos`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({}, { status: 201 })
      }),
    )
    const user = await abrirFranjas()
    await user.click(screen.getByRole('button', { name: 'Bloquear un día' }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Fecha'), '2099-12-25')
    await user.type(within(modal).getByLabelText('Motivo'), '  Navidad ')
    await user.click(within(modal).getByRole('button', { name: 'Bloquear' }))
    await waitFor(() => expect(enviado).toEqual({ fecha: '2099-12-25', motivo: 'Navidad' }))
  })

  it('explica por qué no se pudo bloquear el día', async () => {
    server.use(
      http.post(`${API}/agenda/bloqueos`, () => HttpResponse.json({ detail: 'Ya hay servicios agendados' }, { status: 409 })),
    )
    const user = await abrirFranjas()
    await user.click(screen.getByRole('button', { name: 'Bloquear un día' }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Fecha'), '2099-12-25')
    await user.selectOptions(within(modal).getByLabelText('Ciudad'), 'Bogota')
    await user.selectOptions(within(modal).getByLabelText('Modalidad'), 'virtual')
    await user.type(within(modal).getByLabelText('Motivo'), 'Capacitación')
    await user.click(within(modal).getByRole('button', { name: 'Bloquear' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('Ya hay servicios agendados')
  })
})
