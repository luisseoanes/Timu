import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { PortalInicio } from './InicioPortal'
import { PortalMascota, PortalMascotas } from './PeludosPortal'
import { PortalCitas, PortalDatos, PortalPagos } from './PortalPages'
import { FAMILIA, USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { FamiliaRead, ServicioPortalRead } from '@/types'

const API = '*/api/v1'
const LUNA = FAMILIA.mascotas![0]!
const FAMILIA_CON_BAJA: FamiliaRead = {
  ...FAMILIA,
  mascotas: [LUNA, { ...LUNA, id: 'm2', nombre: 'Tom', raza: null, especie: 'gato', activa: false }],
}

const cita = (cambios: Partial<ServicioPortalRead>): ServicioPortalRead => ({
  id: 's1',
  mascota_id: LUNA.id,
  tipo_codigo: 'consulta_domiciliaria',
  estado: 'agendado',
  programado_para: '2099-01-10T14:00:00Z',
  termina_en: null,
  ...cambios,
})

const PLAN = {
  estado: 'activa',
  periodicidad: 'trimestral',
  valor_periodo: '103800.00',
  valor_mensual: '35500.00',
  fecha_inicio: '2026-01-01',
  fecha_renovacion: '2027-01-01',
  mascotas: [
    {
      mascota_id: LUNA.id,
      mascota: 'Luna',
      plan: 'Colita Feliz',
      color: 'naranja',
      valor_mensual: '35500.00',
      beneficios: [
        { tipo_servicio: 'orientacion_virtual', cupo: null, periodo: 'anual', usados: 3, disponibles: null, cobertura_pct: 100 },
        { tipo_servicio: 'vacunacion', cupo: 2, periodo: 'mensual', usados: 1, disponibles: 1, cobertura_pct: 100 },
        { tipo_servicio: 'consulta_domiciliaria', cupo: 6, periodo: 'anual', usados: 0, disponibles: 6, cobertura_pct: 70 },
      ],
    },
  ],
}

const CUENTA = {
  saldo_pendiente: '75000.00',
  saldo_vencido: '0.00',
  proximo_cobro: { valor: '75000.00', fecha: '2026-12-05' },
  cuotas: [
    { id: 'q1', periodo: '2026-11', tipo: 'cuota', meses: 1, fecha_vencimiento: '2026-11-05', valor: '75000.00', valor_pagado: '0.00', estado: 'pendiente', dias_mora: 0, descripcion: null },
    { id: 'q0', periodo: '2026-10', tipo: 'cuota', meses: 1, fecha_vencimiento: '2026-10-05', valor: '75000.00', valor_pagado: '75000.00', estado: 'pagada', dias_mora: 0, descripcion: 'Octubre' },
  ],
  pagos: [],
}

beforeEach(() =>
  server.use(
    http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'familia', nombre: 'Ana Ruiz' })),
    http.get(`${API}/portal/mi-familia`, () => HttpResponse.json(FAMILIA_CON_BAJA)),
    http.get(`${API}/portal/servicios`, () => HttpResponse.json([])),
    http.get(`${API}/portal/plan`, () => HttpResponse.json({ detail: 'Sin plan' }, { status: 404 })),
    http.get(`${API}/portal/estado-cuenta`, () => HttpResponse.json(CUENTA)),
    http.get(`${API}/portal/pagos`, () => HttpResponse.json([])),
    http.get(`${API}/portal/disponibilidad`, () =>
      HttpResponse.json([
        { inicio: '2099-01-10T13:00:00Z', fin: '2099-01-10T13:45:00Z', disponibles: 0 },
        { inicio: '2099-01-10T15:00:00Z', fin: '2099-01-10T15:45:00Z', disponibles: 1 },
      ]),
    ),
  ),
)

afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe('inicio del portal', () => {
  it('al día no avisa nada vencido ni pinta acción verde sin nada que pagar', async () => {
    server.use(
      http.get(`${API}/portal/plan`, () => HttpResponse.json(PLAN)),
      http.get(`${API}/portal/estado-cuenta`, () => HttpResponse.json({ ...CUENTA, proximo_cobro: null })),
    )
    renderizar(<PortalInicio />)
    expect(await screen.findByText('Tu plan está al día. Se renueva el 1 de enero de 2027.')).toBeInTheDocument()
    expect(await screen.findByText(/Nada pendiente/)).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(document.querySelectorAll('.btn-primario')).toHaveLength(0)
    // Solo los peludos activos, cada uno al día.
    expect(screen.getByRole('link', { name: /luna/i })).toHaveTextContent('Al día')
    expect(screen.queryByRole('link', { name: /tom/i })).not.toBeInTheDocument()
  })

  it('pide orientación virtual solo sobre las mascotas activas', async () => {
    let enviado: unknown = null
    server.use(
      http.post(`${API}/portal/orientacion-virtual`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ id: 'v1', estado: 'en_espera' }, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<PortalInicio />)
    await user.click(await screen.findByRole('button', { name: /hablar con un veterinario/i }))
    const modal = await screen.findByRole('dialog')
    await waitFor(() => expect(within(modal).getByRole('option', { name: 'Luna' })).toBeInTheDocument())
    expect(within(modal).queryByRole('option', { name: 'Tom' })).not.toBeInTheDocument()
    await user.type(within(modal).getByLabelText('Cuéntanos qué pasa'), ' No quiere comer ')
    await user.click(within(modal).getByRole('button', { name: 'Enviar consulta' }))
    expect(await within(modal).findByRole('status')).toHaveTextContent('Recibimos tu consulta')
    expect(enviado).toEqual({ mascota_id: LUNA.id, motivo: 'No quiere comer' })
    expect(within(modal).queryByRole('button', { name: 'Enviar consulta' })).not.toBeInTheDocument()
  })

  it('explica por qué no se pudo enviar la consulta', async () => {
    server.use(
      http.post(`${API}/portal/orientacion-virtual`, () =>
        HttpResponse.json({ detail: 'Tu plan no incluye orientación virtual' }, { status: 422 }),
      ),
    )
    const user = userEvent.setup()
    renderizar(<PortalInicio />)
    await user.click(await screen.findByRole('button', { name: /hablar con un veterinario/i }))
    const modal = await screen.findByRole('dialog')
    await waitFor(() => expect(within(modal).getByRole('option', { name: 'Luna' })).toBeInTheDocument())
    await user.type(within(modal).getByLabelText('Cuéntanos qué pasa'), 'No quiere comer')
    await user.click(within(modal).getByRole('button', { name: 'Enviar consulta' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('no incluye orientación virtual')
  })

  it('explica por qué no cargó el plan', async () => {
    server.use(http.get(`${API}/portal/plan`, () => HttpResponse.json({ detail: 'Sin conexión' }, { status: 503 })))
    renderizar(<PortalInicio />)
    expect(await screen.findByText(/No pudimos cargar tu plan/)).toBeInTheDocument()
  })
})

describe('mascotas', () => {
  function abrirMascota() {
    renderizar(
      <Routes>
        <Route path="/portal/mascotas/:mascotaId" element={<PortalMascota />} />
      </Routes>,
      { ruta: `/portal/mascotas/${LUNA.id}` },
    )
    return userEvent.setup()
  }

  const carnet = (cambios = {}) =>
    http.get(`${API}/portal/mascotas/:id/carnet`, () =>
      HttpResponse.json({ mascota: { id: LUNA.id, nombre: 'Luna' }, aplicados: [], vencidos: [], proximos: [], ...cambios }),
    )

  it('la familia sube y quita la foto de su mascota', async () => {
    const pedidos: string[] = []
    let conFoto = false
    server.use(
      carnet(),
      http.get(`${API}/portal/mi-familia`, () =>
        HttpResponse.json({ ...FAMILIA_CON_BAJA, mascotas: [{ ...LUNA, foto_url: conFoto ? 'https://s3/luna.png' : null }] }),
      ),
      http.put(`${API}/portal/mascotas/:id/foto`, async ({ request, params }) => {
        pedidos.push(`PUT ${String(params.id)} ${(await request.text()).includes('name="foto"')}`)
        conFoto = true
        return HttpResponse.json({ ...LUNA, foto_url: 'https://s3/luna.png' })
      }),
      http.delete(`${API}/portal/mascotas/:id/foto`, ({ params }) => {
        pedidos.push(`DELETE ${String(params.id)}`)
        conFoto = false
        return HttpResponse.json({ ...LUNA, foto_url: null })
      }),
    )
    const user = abrirMascota()
    await user.upload(await screen.findByLabelText('Subir foto'), new File(['png'], 'luna.png', { type: 'image/png' }))
    expect(await screen.findByRole('img', { name: 'Foto de Luna' })).toHaveAttribute('src', 'https://s3/luna.png')
    await user.click(screen.getByRole('button', { name: 'Quitar foto' }))
    await waitFor(() => expect(screen.queryByRole('img', { name: 'Foto de Luna' })).not.toBeInTheDocument())
    expect(pedidos).toEqual([`PUT ${LUNA.id} true`, `DELETE ${LUNA.id}`])
  })

  it('explica por qué no pudo guardar la foto', async () => {
    server.use(
      carnet(),
      http.put(`${API}/portal/mascotas/:id/foto`, () =>
        HttpResponse.json({ detail: 'Tipo de archivo no permitido' }, { status: 422 }),
      ),
    )
    const user = abrirMascota()
    await user.upload(await screen.findByLabelText('Subir foto'), new File(['x'], 'x.png', { type: 'image/png' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Tipo de archivo no permitido')
  })

  it('solo lista las mascotas activas, con su raza o su especie', async () => {
    renderizar(<PortalMascotas />)
    expect(await screen.findByRole('link', { name: /luna/i })).toHaveTextContent('Criolla')
    expect(screen.queryByRole('link', { name: /tom/i })).not.toBeInTheDocument()
  })

  it('el carnet distingue lo aplicado de lo programado', async () => {
    server.use(
      carnet({
        aplicados: [
          { id: 'a1', nombre: 'Rabia', dosis: 1, fecha_aplicacion: '2026-09-01' },
          { id: 'a2', nombre: 'Desparasitación interna', dosis: 1, fecha_aplicacion: '2026-09-05', peso_kg: 8.4, aplicado_por: 'Dra. Paula Gómez' },
        ],
        proximos: [{ id: 'p1', nombre: 'Polivalente', dosis: 2, fecha_programada: '2026-12-01' }],
      }),
    )
    abrirMascota()
    expect(await screen.findByRole('heading', { name: 'Luna' })).toBeInTheDocument()
    expect((await screen.findAllByText('Aplicada')).length).toBe(2)
    expect(screen.getByText(/por Dra\. Paula Gómez · pesaba 8,4 kg/)).toBeInTheDocument()
    expect(screen.getByText('Polivalente').closest('li')).toHaveTextContent('el 01/12/2026')
    expect(screen.queryByText(/no tiene vacunas/)).not.toBeInTheDocument()
  })

  it('sin preventivos lo dice y explica si el PDF falla', async () => {
    server.use(
      carnet(),
      http.post(`${API}/portal/mascotas/:id/carnet/pdf`, () => HttpResponse.json({ detail: 'Generador caído' }, { status: 503 })),
    )
    const user = abrirMascota()
    expect(await screen.findByText('Aún no tiene vacunas ni desparasitaciones en su calendario.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /descargar pdf/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Generador caído')
  })

  it('la historia muestra diagnóstico y tratamiento, o dice que está vacía', async () => {
    server.use(
      carnet(),
      http.get(`${API}/portal/mascotas/:id/historia`, () =>
        HttpResponse.json([
          { id: 'h1', fecha: '2026-10-04', tipo: 'domiciliaria', motivo: 'Rasca el oído', diagnostico: null, tratamiento: 'Gotas', examen_fisico: null, estado: 'firmada' },
        ]),
      ),
    )
    const user = abrirMascota()
    await user.click(await screen.findByRole('tab', { name: 'Historia clínica' }))
    expect(await screen.findByText('Tratamiento: Gotas')).toBeInTheDocument()
    expect(screen.queryByText(/Diagnóstico:/)).not.toBeInTheDocument()
  })

  it('su plan dice el cupo de frente, sin «ilimitado», y lo que no cubre entero', async () => {
    server.use(carnet(), http.get(`${API}/portal/plan`, () => HttpResponse.json(PLAN)))
    const user = abrirMascota()
    await user.click(await screen.findByRole('tab', { name: 'Su plan' }))
    expect(await screen.findByText(/sin tope de usos este año/)).toBeInTheDocument()
    expect(screen.getByText(/le queda 1 de 2 este mes/)).toBeInTheDocument()
    expect(screen.getByText(/le quedan 6 de 6 este año · cubre el 70 %/)).toBeInTheDocument()
    expect(screen.queryByText(/ilimitado/)).not.toBeInTheDocument()
  })

  it('su línea solo trae lo suyo y deja agendar lo vencido con el plan al día', async () => {
    server.use(
      carnet(),
      http.get(`${API}/portal/plan`, () => HttpResponse.json(PLAN)),
      http.get(`${API}/portal/linea`, () =>
        HttpResponse.json({
          familia_id: FAMILIA.id,
          planes: [{ plan_id: 'p1', nombre: 'Colita Feliz', color: 'naranja', mascotas: ['Luna'] }],
          estaciones: [
            { tipo: 'cuota', referencia_id: 'q1', fecha: '2026-01-05', estado: 'vencida', titulo: 'Cuota de enero', mascota: null, mascota_id: null },
            { tipo: 'preventivo', referencia_id: 'v1', fecha: '2026-01-04', estado: 'vencida', titulo: 'Vacuna', mascota: 'Luna', mascota_id: LUNA.id },
            { tipo: 'preventivo', referencia_id: 'v2', fecha: '2026-01-04', estado: 'vencida', titulo: 'Vacuna', mascota: 'Tom', mascota_id: 'm2' },
          ],
        }),
      ),
    )
    const user = abrirMascota()
    const lista = await screen.findByRole('list', { name: 'La línea de Luna' })
    expect(lista).toHaveAttribute('data-color', 'naranja')
    expect(within(lista).getByRole('heading', { name: /1 preventivo vencido desde el/ })).toBeInTheDocument()
    expect(within(lista).queryByText(/cuota/i)).not.toBeInTheDocument()
    expect(screen.getByText('Colita Feliz')).toBeInTheDocument()
    await user.click(within(lista).getByRole('button', { name: 'Agendar' }))
    const modal = await screen.findByRole('dialog', { name: 'Agendar una visita' })
    await waitFor(() => expect(within(modal).getByLabelText('Mascota')).toHaveValue(LUNA.id))
  })

  it('una mascota sin consultas lo dice', async () => {
    server.use(carnet(), http.get(`${API}/portal/mascotas/:id/historia`, () => HttpResponse.json([])))
    const user = abrirMascota()
    await user.click(await screen.findByRole('tab', { name: 'Historia clínica' }))
    expect(await screen.findByText('Aún no tiene consultas registradas.')).toBeInTheDocument()
  })
})

describe('citas', () => {
  it('las abiertas se cambian o cancelan; las pasadas se ven a pedido', async () => {
    const pedidas: (string | null)[] = []
    server.use(
      http.get(`${API}/portal/servicios`, ({ request }) => {
        pedidas.push(new URL(request.url).searchParams.get('incluir_pasados'))
        return HttpResponse.json([cita({ id: 'a' }), cita({ id: 'b', estado: 'completado', mascota_id: null })])
      }),
    )
    const user = userEvent.setup()
    renderizar(<PortalCitas />)
    expect(await screen.findByText('Consulta domiciliaria · Luna')).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Cambiar fecha' })).toHaveLength(1)
    await user.click(screen.getByLabelText('Ver también las pasadas'))
    await waitFor(() => expect(pedidas).toEqual([null, 'true']))
  })

  it('cambia la fecha a un horario con cupo y explica un rechazo', async () => {
    let enviado: unknown = null
    server.use(
      http.get(`${API}/portal/servicios`, () => HttpResponse.json([cita({})])),
      http.post(`${API}/portal/servicios/s1/reprogramacion`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ detail: 'Ese horario ya se ocupó' }, { status: 409 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<PortalCitas />)
    await user.click(await screen.findByRole('button', { name: 'Cambiar fecha' }))
    const modal = await screen.findByRole('dialog')
    const horarios = await within(modal).findByRole('group', { name: 'Horarios disponibles' })
    expect(within(horarios).getAllByRole('button')).toHaveLength(1)
    await user.click(within(horarios).getByRole('button'))
    await user.type(within(modal).getByLabelText('Motivo'), ' Viaje ')
    await user.click(within(modal).getByRole('button', { name: 'Cambiar fecha' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('Ese horario ya se ocupó')
    expect(enviado).toEqual({ inicio: '2099-01-10T15:00:00Z', motivo: 'Viaje' })
  })

  it('cancela una cita con su motivo y explica un rechazo', async () => {
    const motivos: unknown[] = []
    server.use(
      http.get(`${API}/portal/servicios`, () => HttpResponse.json([cita({})])),
      http.post(`${API}/portal/servicios/s1/cancelacion`, async ({ request }) => {
        motivos.push(await request.json())
        return motivos.length === 1
          ? HttpResponse.json({ detail: 'Faltan menos de 12 horas' }, { status: 422 })
          : HttpResponse.json(cita({ estado: 'cancelado' }))
      }),
    )
    const user = userEvent.setup()
    renderizar(<PortalCitas />)
    await user.click(await screen.findByRole('button', { name: 'Cancelar' }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Motivo'), 'Viaje')
    await user.click(within(modal).getByRole('button', { name: 'Cancelar cita' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('Faltan menos de 12 horas')
    await user.click(within(modal).getByRole('button', { name: 'Cancelar cita' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(motivos).toEqual([{ motivo: 'Viaje' }, { motivo: 'Viaje' }])
  })

  it('el selector de horario guía hasta elegir tipo y avisa días sin cupo o sin agenda', async () => {
    server.use(http.get(`${API}/portal/disponibilidad`, () => HttpResponse.json([{ inicio: '2099-01-10T13:00:00Z', fin: '', disponibles: 0 }])))
    const user = userEvent.setup()
    renderizar(<PortalCitas />)
    await user.click(await screen.findByRole('button', { name: /agendar/i }))
    const modal = await screen.findByRole('dialog')
    expect(within(modal).getByText('Elige el tipo de visita para ver los horarios.')).toBeInTheDocument()
    await waitFor(() => expect(within(modal).getByRole('option', { name: 'Vacunación' })).toBeInTheDocument())
    await user.selectOptions(within(modal).getByLabelText('Tipo de visita'), 'vacunacion')
    expect(await within(modal).findByText('No hay horarios ese día. Prueba otra fecha.')).toBeInTheDocument()
    expect(within(modal).getByRole('button', { name: 'Agendar' })).toBeDisabled()

    server.use(http.get(`${API}/portal/disponibilidad`, () => HttpResponse.json({ detail: 'Agenda en mantenimiento' }, { status: 503 })))
    const dia = within(modal).getByLabelText('Día')
    await user.clear(dia)
    await user.type(dia, '2099-02-01')
    expect(await within(modal).findByRole('alert')).toHaveTextContent('Agenda en mantenimiento')
  })

  it('explica por qué no se pudo agendar', async () => {
    server.use(
      http.post(`${API}/portal/servicios`, () => HttpResponse.json({ detail: 'Tu plan no cubre este servicio' }, { status: 422 })),
    )
    const user = userEvent.setup()
    renderizar(<PortalCitas />)
    await user.click(await screen.findByRole('button', { name: /agendar/i }))
    const modal = await screen.findByRole('dialog')
    await waitFor(() => expect(within(modal).getByRole('option', { name: 'Consulta domiciliaria' })).toBeInTheDocument())
    await user.selectOptions(within(modal).getByLabelText('Tipo de visita'), 'consulta_domiciliaria')
    await user.click(await within(modal).findByRole('button', { pressed: false }))
    await user.type(within(modal).getByLabelText('¿Algo que debamos saber? (opcional)'), 'Perro nervioso')
    await user.click(within(modal).getByRole('button', { name: 'Agendar' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('Tu plan no cubre este servicio')
  })
})

describe('pagos', () => {
  it('sin contrato no ofrece pagar', async () => {
    server.use(http.get(`${API}/portal/estado-cuenta`, () => HttpResponse.json({ detail: 'Sin contrato' }, { status: 404 })))
    renderizar(<PortalPagos />)
    expect(await screen.findByText('Aún no tienes un contrato activo.')).toBeInTheDocument()
    expect(await screen.findByText('Aún no tienes pagos.')).toBeInTheDocument()
  })

  it('solo cobra lo pendiente y lleva a la pasarela', async () => {
    const asignar = vi.fn()
    vi.stubGlobal('location', { ...window.location, assign: asignar })
    server.use(
      http.post(`${API}/portal/pagos`, () =>
        HttpResponse.json({ pago: { id: 'p1' }, enlace_pago: 'https://checkout.wompi.co/p/?reference=X' }, { status: 201 }),
      ),
    )
    const user = userEvent.setup()
    renderizar(<PortalPagos />)
    expect(await screen.findByText(/el 05/)).toBeInTheDocument()
    const pagar = screen.getAllByRole('button', { name: 'Pagar' })
    expect(pagar).toHaveLength(1)
    await user.click(pagar[0]!)
    await waitFor(() => expect(asignar).toHaveBeenCalledWith('https://checkout.wompi.co/p/?reference=X'))
  })

  it('una cuota pendiente con mora se ve vencida', async () => {
    const vencida = { ...CUENTA.cuotas[0]!, dias_mora: 6 }
    server.use(http.get(`${API}/portal/estado-cuenta`, () => HttpResponse.json({ ...CUENTA, cuotas: [vencida] })))
    renderizar(<PortalPagos />)
    expect(await screen.findByText('Vencida')).toBeInTheDocument()
    expect(screen.queryByText('Pendiente')).not.toBeInTheDocument()
  })

  it('el comprobante solo existe para pagos aprobados y explica si falla', async () => {
    server.use(
      http.get(`${API}/portal/pagos`, () =>
        HttpResponse.json([
          { id: 'p1', referencia_externa: 'R1', valor: '75000.00', estado: 'aprobado', fecha_pago: '2026-10-05T15:00:00Z', created_at: '2026-10-05T14:00:00Z' },
          { id: 'p2', referencia_externa: 'R2', valor: '75000.00', estado: 'pendiente', fecha_pago: null, created_at: '2026-11-01T14:00:00Z' },
        ]),
      ),
      http.get(`${API}/portal/pagos/p1/comprobante`, () => HttpResponse.json({ detail: 'No disponible' }, { status: 503 })),
    )
    const user = userEvent.setup()
    renderizar(<PortalPagos />)
    const comprobantes = await screen.findAllByRole('button', { name: /comprobante/i })
    expect(comprobantes).toHaveLength(1)
    await user.click(comprobantes[0]!)
    expect(await screen.findByRole('alert')).toHaveTextContent('No pudimos descargar el comprobante.')
  })
})

describe('mis datos', () => {
  it('lista sus documentos con el tipo y la mascota, o dice que no tiene', async () => {
    server.use(
      http.get(`${API}/portal/documentos`, () =>
        HttpResponse.json([
          {
            archivo_id: 'a1',
            documento_id: 'd1',
            origen: 'subido',
            categoria: 'examen_externo',
            descripcion: 'Ecografía de Luna',
            mascota_id: FAMILIA.mascotas?.[0]?.id,
            nombre: 'eco.pdf',
            content_type: 'application/pdf',
            tamano_bytes: 1000,
            visible_familia: true,
            creado_en: '2026-11-02T15:00:00Z',
            url: 'https://s3/eco.pdf',
          },
          {
            archivo_id: 'a2',
            origen: 'contrato',
            descripcion: 'Contrato TM-0001',
            nombre: 'contrato.pdf',
            content_type: 'application/pdf',
            tamano_bytes: 1000,
            visible_familia: true,
            creado_en: '2026-10-01T15:00:00Z',
            url: 'https://s3/contrato.pdf',
          },
        ]),
      ),
    )
    renderizar(<PortalDatos />)
    const lista = await screen.findByRole('list', { name: 'Mis documentos' })
    expect(within(lista).getByRole('link', { name: 'Ecografía de Luna' })).toHaveAttribute('href', 'https://s3/eco.pdf')
    expect(within(lista).getByText(/Documento · Luna · 02\/11\/2026/)).toBeInTheDocument()
    expect(within(lista).getByRole('link', { name: 'Contrato TM-0001' })).toBeInTheDocument()
  })

  it('dice que todavía no tiene documentos', async () => {
    renderizar(<PortalDatos />)
    expect(await screen.findByText('Todavía no tienes documentos.')).toBeInTheDocument()
  })

  it('explica si no pudo cargar sus documentos', async () => {
    server.use(http.get(`${API}/portal/documentos`, () => HttpResponse.json({ detail: 'Fallo' }, { status: 500 })))
    renderizar(<PortalDatos />)
    expect(await screen.findByText(/No fue posible cargar tus documentos/)).toBeInTheDocument()
  })

  it('abre el contrato en otra pestaña', async () => {
    const abrir = vi.spyOn(window, 'open').mockReturnValue(null)
    server.use(http.get(`${API}/portal/contrato`, () => HttpResponse.json({ url: 'https://s3/contrato.pdf' })))
    const user = userEvent.setup()
    renderizar(<PortalDatos />)
    await user.click(await screen.findByRole('button', { name: /mi contrato/i }))
    await waitFor(() => expect(abrir).toHaveBeenCalledWith('https://s3/contrato.pdf', '_blank', 'noopener'))
  })

  it('explica por qué no se pudo abrir el contrato', async () => {
    server.use(http.get(`${API}/portal/contrato`, () => HttpResponse.json({ detail: 'Contrato no generado' }, { status: 404 })))
    const user = userEvent.setup()
    renderizar(<PortalDatos />)
    await user.click(await screen.findByRole('button', { name: /mi contrato/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Contrato no generado')
  })

  it('confirma lo guardado y explica un rechazo', async () => {
    let llamadas = 0
    server.use(
      http.patch(`${API}/portal/mi-familia`, () => {
        llamadas += 1
        return llamadas === 1
          ? HttpResponse.json(FAMILIA)
          : HttpResponse.json({ detail: 'Celular inválido' }, { status: 422 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<PortalDatos />)
    const correo = await screen.findByLabelText('Correo')
    await user.type(correo, 'ana@correo.co')
    await user.click(screen.getByRole('button', { name: 'Guardar' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Datos guardados.')
    await user.clear(screen.getByLabelText('Celular (WhatsApp)'))
    await user.type(screen.getByLabelText('Celular (WhatsApp)'), '123')
    await user.click(screen.getByRole('button', { name: 'Guardar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Celular inválido')
  })
})
