import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { PortalInicio } from './InicioPortal'
import { PortalCitas, PortalDatos, PortalPagos } from './PortalPages'
import { FAMILIA, USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { EstacionRead, LineaFamiliaRead } from '@/types'

const API = '*/api/v1'

const LUNA_ID = FAMILIA.mascotas![0]!.id

/** Fecha ISO a `dias` de hoy: la línea sitúa «hoy» con el reloj del navegador. */
function dentroDe(dias: number): string {
  const d = new Date()
  d.setDate(d.getDate() + dias)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

let n = 0
function estacion(dias: number, estado: EstacionRead['estado'], titulo: string, extra: Partial<EstacionRead> = {}): EstacionRead {
  n += 1
  return { tipo: 'cuota', referencia_id: `e${n}`, fecha: dentroDe(dias), estado, titulo, mascota: null, mascota_id: null, ...extra }
}

const linea = (estaciones: EstacionRead[]): LineaFamiliaRead => ({
  familia_id: FAMILIA.id,
  planes: [{ plan_id: 'p1', nombre: 'Plan Familiar', color: 'verde', mascotas: ['Luna', 'Max'] }],
  estaciones,
})

const plan = (estado: string) => ({
  estado,
  periodicidad: 'mensual',
  valor_periodo: '75000.00',
  valor_mensual: '75000.00',
  fecha_inicio: '2026-01-01',
  fecha_renovacion: '2027-01-01',
  mascotas: [
    { mascota_id: LUNA_ID, mascota: 'Luna', plan: 'Plan Familiar', color: 'verde', valor_mensual: '37500.00', beneficios: [] },
    { mascota_id: 'max', mascota: 'Max', plan: 'Plan Familiar', color: 'verde', valor_mensual: '37500.00', beneficios: [] },
  ],
})

const comoFamilia = [
  http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'familia', nombre: 'Ana Ruiz' })),
  http.get(`${API}/portal/mi-familia`, () => HttpResponse.json(FAMILIA)),
]

describe('Portal de la familia', () => {
  it('con el plan congelado explica por qué, agrupa lo vencido y solo deja pagar', async () => {
    let pagado: unknown = null
    server.use(
      ...comoFamilia,
      http.get(`${API}/portal/plan`, () => HttpResponse.json(plan('congelada'))),
      http.get(`${API}/portal/estado-cuenta`, () =>
        HttpResponse.json({ saldo_pendiente: '225000.00', saldo_vencido: '225000.00', cuotas: [], pagos: [] }),
      ),
      http.get(`${API}/portal/servicios`, () => HttpResponse.json([])),
      http.get(`${API}/portal/linea`, () =>
        HttpResponse.json(
          linea([
            estacion(-83, 'vencida', 'Cuota de agosto'),
            estacion(-52, 'vencida', 'Cuota de septiembre'),
            estacion(-22, 'vencida', 'Cuota de octubre'),
            estacion(-8, 'vencida', 'Vacuna', { tipo: 'preventivo', mascota: 'Luna', mascota_id: LUNA_ID }),
            estacion(-8, 'vencida', 'Vacuna', { tipo: 'preventivo', mascota: 'Max', mascota_id: 'max' }),
          ]),
        ),
      ),
      http.post(`${API}/portal/pagos`, async ({ request }) => {
        pagado = await request.json()
        return HttpResponse.json({ detail: 'Pasarela no disponible' }, { status: 503 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<PortalInicio />)
    expect(await screen.findByRole('heading', { name: 'Hola, Ana' })).toBeInTheDocument()
    expect(await screen.findByText(/Tus 3 cuotas vencidas pausaron el plan\. Al pagar, Luna y Max recuperan/)).toBeInTheDocument()
    const lista = await screen.findByRole('list', { name: /tu línea/i })
    await within(lista).findByRole('button', { name: /^Pagar \$\s225\.000$/ })
    expect(within(lista).getAllByRole('heading')[0]).toHaveTextContent(/^3 cuotas vencidas · \$\s225\.000$/)
    expect(within(lista).getByText('Las de agosto, septiembre y octubre.')).toBeInTheDocument()
    expect(within(lista).getByRole('heading', { name: /2 preventivos vencidos desde el/ })).toBeInTheDocument()
    // Con el plan congelado no se agenda: lo dice en vez de ofrecer algo que el backend rechaza.
    expect(within(lista).getByText('Se agendan al ponerte al día.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /agendar/i })).not.toBeInTheDocument()
    // Una sola acción verde: pagar todo lo pendiente.
    const pagar = within(lista).getByRole('button', { name: /^Pagar \$\s225\.000$/ })
    expect(document.querySelectorAll('.btn-primario')).toHaveLength(1)
    expect(pagar).toHaveClass('btn-primario')
    expect(within(lista).getByText(/^Hoy · /)).toBeInTheDocument()
    await user.click(pagar)
    expect(await screen.findByRole('alert')).toHaveTextContent('Pasarela no disponible')
    expect(pagado).toEqual({})
  })

  it('al día con preventivos vencidos, agendarlos es la acción verde', async () => {
    server.use(
      ...comoFamilia,
      http.get(`${API}/portal/plan`, () => HttpResponse.json(plan('activa'))),
      http.get(`${API}/portal/estado-cuenta`, () => HttpResponse.json({ saldo_pendiente: '0.00', saldo_vencido: '0.00', cuotas: [], pagos: [] })),
      http.get(`${API}/portal/servicios`, () => HttpResponse.json([])),
      http.get(`${API}/portal/linea`, () =>
        HttpResponse.json(linea([estacion(-8, 'vencida', 'Vacuna', { tipo: 'preventivo', mascota: 'Luna', mascota_id: LUNA_ID })])),
      ),
      http.get(`${API}/portal/disponibilidad`, () => HttpResponse.json([])),
    )
    const user = userEvent.setup()
    renderizar(<PortalInicio />)
    expect(await screen.findByText('Tu plan está al día. Se renueva el 1 de enero de 2027.')).toBeInTheDocument()
    const agendar = await screen.findByRole('button', { name: 'Agendar' })
    expect(agendar).toHaveClass('btn-primario')
    expect(screen.getByRole('button', { name: /agendar una visita/i })).toHaveClass('btn-secundario')
    await user.click(agendar)
    expect(await screen.findByRole('dialog', { name: 'Agendar una visita' })).toBeInTheDocument()
  })

  it('pinta lo hecho plegado, lo que viene con su estado y paga la próxima cuota', async () => {
    server.use(
      ...comoFamilia,
      http.get(`${API}/portal/plan`, () => HttpResponse.json(plan('activa'))),
      http.get(`${API}/portal/estado-cuenta`, () =>
        HttpResponse.json({
          saldo_pendiente: '75000.00',
          saldo_vencido: '0.00',
          cuotas: [{ id: 'q-dic', valor: '75000.00', valor_pagado: '0.00' }],
          pagos: [],
        }),
      ),
      http.get(`${API}/portal/servicios`, () =>
        HttpResponse.json([{ id: 's-1', mascota_id: LUNA_ID, tipo_codigo: 'consulta_domiciliaria', estado: 'en_ruta', programado_para: '2099-01-01T14:00:00Z', termina_en: null }]),
      ),
      http.get(`${API}/portal/linea`, () =>
        HttpResponse.json(
          linea([
            estacion(-40, 'hecha', 'Cuota de octubre'),
            estacion(0, 'futura', 'Consulta domiciliaria', { tipo: 'servicio', referencia_id: 's-1', mascota: 'Luna', mascota_id: LUNA_ID }),
            estacion(9, 'proxima', 'Cuota de diciembre', { referencia_id: 'q-dic' }),
          ]),
        ),
      ),
    )
    const user = userEvent.setup()
    renderizar(<PortalInicio />)
    const lista = await screen.findByRole('list', { name: /tu línea/i })
    const hechas = within(lista).getByRole('button', { name: /1 hecha/ })
    expect(within(lista).queryByText(/Cuota de octubre/)).not.toBeVisible()
    await user.click(hechas)
    expect(hechas).toHaveAttribute('aria-expanded', 'true')
    expect(within(lista).getByText(/Cuota de octubre/)).toBeVisible()
    expect(within(lista).getByText('En ruta')).toBeInTheDocument()
    expect(within(lista).getByRole('button', { name: /^Pagar \$\s75\.000$/ })).toHaveClass('btn-primario')
  })

  it('si la línea no carga, no afirma que los peludos estén al día ni cuenta cuotas', async () => {
    server.use(
      ...comoFamilia,
      http.get(`${API}/portal/plan`, () => HttpResponse.json(plan('congelada'))),
      http.get(`${API}/portal/linea`, () => HttpResponse.json({ detail: 'Servicio no disponible' }, { status: 503 })),
    )
    renderizar(<PortalInicio />)
    expect(await screen.findByText(/No pudimos cargar tus cuotas, vacunas, desparasitaciones y visitas/)).toBeInTheDocument()
    expect(await screen.findByText(/^Tus cuotas vencidas pausaron el plan/)).toBeInTheDocument()
    expect(await screen.findByRole('link', { name: /luna/i })).not.toHaveTextContent('Al día')
    expect(screen.queryByText(/escríbenos por WhatsApp para reactivarlo/i)).not.toBeInTheDocument()
    expect(screen.getByText('Plan Familiar')).toBeInTheDocument()
  })

  it('con el plan en pausa no muere en hoy: pone el próximo cobro, sin pagarlo, y dice qué viene', async () => {
    server.use(
      ...comoFamilia,
      http.get(`${API}/portal/plan`, () => HttpResponse.json(plan('congelada'))),
      http.get(`${API}/portal/estado-cuenta`, () =>
        HttpResponse.json({ saldo_pendiente: '75000.00', saldo_vencido: '75000.00', proximo_cobro: { valor: '75000.00', fecha: dentroDe(9) }, cuotas: [], pagos: [] }),
      ),
      http.get(`${API}/portal/linea`, () => HttpResponse.json(linea([estacion(-22, 'vencida', 'Cuota de octubre')]))),
    )
    renderizar(<PortalInicio />)
    const lista = await screen.findByRole('list', { name: /tu línea/i })
    expect(await within(lista).findByText(/Próximo cobro/)).toBeInTheDocument()
    // Esa cuota aún no existe: se paga lo vencido, no ella.
    expect(within(lista).getAllByRole('button', { name: /^Pagar/ })).toHaveLength(1)
    expect(screen.getByText('En pausa')).toBeInTheDocument()
    expect(screen.queryByText('Congelada')).not.toBeInTheDocument()
  })

  it('sin nada después de hoy, la línea cierra diciendo qué viene', async () => {
    server.use(
      ...comoFamilia,
      http.get(`${API}/portal/plan`, () => HttpResponse.json(plan('congelada'))),
      http.get(`${API}/portal/linea`, () => HttpResponse.json(linea([estacion(-22, 'vencida', 'Cuota de octubre')]))),
    )
    renderizar(<PortalInicio />)
    const lista = await screen.findByRole('list', { name: /tu línea/i })
    expect(await within(lista).findByText(/^Al ponerte al día, aquí aparecen tus próximas cuotas/)).toBeInTheDocument()
  })

  it('sin contrato invita a afiliarse en lugar de fallar', async () => {
    server.use(
      ...comoFamilia,
      http.get(`${API}/portal/plan`, () => HttpResponse.json({ detail: 'Sin plan' }, { status: 404 })),
      http.get(`${API}/portal/estado-cuenta`, () => HttpResponse.json({ detail: 'Sin contrato' }, { status: 404 })),
      http.get(`${API}/portal/servicios`, () => HttpResponse.json([])),
    )
    renderizar(<PortalInicio />)
    expect(await screen.findByText(/aún no tienes un plan activo/i)).toBeInTheDocument()
    expect(await screen.findByText(/Nada pendiente/)).toBeInTheDocument()
  })

  it('agenda una visita eligiendo mascota, tipo y horario', async () => {
    let enviado: unknown = null
    server.use(
      ...comoFamilia,
      http.get(`${API}/portal/servicios`, () => HttpResponse.json([])),
      http.get(`${API}/portal/disponibilidad`, () =>
        HttpResponse.json([{ inicio: '2099-01-10T14:00:00Z', fin: '2099-01-10T14:45:00Z', disponibles: 1 }]),
      ),
      http.post(`${API}/portal/servicios`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ id: 's1', mascota_id: 'm', tipo_codigo: 'consulta_domiciliaria', estado: 'agendado', programado_para: '2099-01-10T14:00:00Z', termina_en: null }, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<PortalCitas />)
    expect(await screen.findByText('No tienes citas.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /agendar/i }))
    const modal = await screen.findByRole('dialog')
    await waitFor(() => expect(within(modal).getByRole('option', { name: 'Consulta domiciliaria' })).toBeInTheDocument())
    await user.selectOptions(within(modal).getByLabelText('Tipo de visita'), 'consulta_domiciliaria')
    await user.click(await within(modal).findByRole('button', { pressed: false }))
    await user.click(within(modal).getByRole('button', { name: 'Agendar' }))
    expect(await within(modal).findByText(/tu visita quedó/i)).toBeInTheDocument()
    expect(enviado).toMatchObject({ mascota_id: FAMILIA.mascotas?.[0]?.id, tipo_codigo: 'consulta_domiciliaria', inicio: '2099-01-10T14:00:00Z' })
  })

  it('paga una cuota y lleva a la pasarela', async () => {
    let pagada: unknown = null
    server.use(
      ...comoFamilia,
      http.get(`${API}/portal/estado-cuenta`, () =>
        HttpResponse.json({
          saldo_pendiente: '75000.00',
          saldo_vencido: '0.00',
          proximo_cobro: null,
          cuotas: [{ id: 'q1', periodo: '2026-11', tipo: 'cuota', meses: 1, fecha_vencimiento: '2026-11-05', valor: '75000.00', valor_pagado: '0.00', estado: 'pendiente', dias_mora: 0, descripcion: 'Cuota noviembre' }],
          pagos: [],
        }),
      ),
      http.get(`${API}/portal/pagos`, () => HttpResponse.json([])),
      http.post(`${API}/portal/pagos`, async ({ request }) => {
        pagada = await request.json()
        return HttpResponse.json({ detail: 'Pasarela no disponible' }, { status: 503 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<PortalPagos />)
    await user.click(await screen.findByRole('button', { name: 'Pagar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Pasarela no disponible')
    expect(pagada).toEqual({ cuota_id: 'q1' })
  })

  it('actualiza sólo los datos que cambiaron', async () => {
    let cambios: unknown = null
    server.use(
      ...comoFamilia,
      http.patch(`${API}/portal/mi-familia`, async ({ request }) => {
        cambios = await request.json()
        return HttpResponse.json(FAMILIA)
      }),
    )
    const user = userEvent.setup()
    renderizar(<PortalDatos />)
    await user.type(await screen.findByLabelText('Dirección de las visitas'), 'Calle 80 # 15-20')
    await user.click(screen.getByRole('button', { name: 'Guardar' }))
    await waitFor(() => expect(cambios).toEqual({ direccion: 'Calle 80 # 15-20' }))
  })
})
