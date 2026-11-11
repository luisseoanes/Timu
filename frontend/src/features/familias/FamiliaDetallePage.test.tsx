import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { FamiliaDetallePage } from './FamiliaDetallePage'
import { FAMILIA, PLAN, USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { DocumentoRead, EstadoCuenta, MascotaRead } from '@/types'

const API = '*/api/v1'

function abrirFicha() {
  return renderizar(
    <Routes>
      <Route path="/familias/:id" element={<FamiliaDetallePage />} />
    </Routes>,
    { ruta: `/familias/${FAMILIA.id}` },
  )
}

const CUENTA: EstadoCuenta = {
  contrato: {
    id: 'c1',
    numero: 'TM-0001',
    familia_id: FAMILIA.id,
    fecha_inicio: '2026-01-01',
    fecha_renovacion: '2027-01-01',
    fecha_fin: null,
    dia_corte: 5,
    periodicidad: 'mensual',
    valor_mensual: '89000.00',
    valor_periodo: '89000.00',
    saldo_a_favor: '0.00',
    estado: 'activa',
    aceptado_en: null,
    medio_aceptacion: null,
  },
  mascotas: [
    {
      mascota_id: FAMILIA.mascotas![0]!.id,
      nombre: 'Luna',
      especie: 'perro',
      plan_id: 'p1',
      plan_nombre: 'Plan Esencial',
      valor_mensual: '89000.00',
    },
  ],
  estado: 'en_mora',
  saldo_pendiente: '89000.00',
  saldo_vencido: '89000.00',
  saldo_a_favor: '0.00',
  dias_mora: 12,
  proximo_cobro: null,
  cuotas: [
    {
      id: 'q1',
      periodo: '2026-09',
      tipo: 'cuota',
      meses: 1,
      fecha_vencimiento: '2026-09-05',
      valor: '89000.00',
      valor_pagado: '0.00',
      // La API no envía «vencida»: la cuota está pendiente y la mora la hace vencida.
      estado: 'pendiente',
      dias_mora: 12,
      descripcion: 'Cuota septiembre',
    },
  ],
  pagos: [],
}

describe('FamiliaDetallePage', () => {
  it('muestra el estado de carga', () => {
    abrirFicha()
    expect(screen.getByText(/cargando la familia/i)).toBeInTheDocument()
  })

  it('muestra el error con la causa del servidor', async () => {
    server.use(
      http.get(`${API}/familias/:id`, () =>
        HttpResponse.json({ detail: 'Familia no encontrada' }, { status: 404 }),
      ),
    )
    abrirFicha()
    expect(await screen.findByRole('alert')).toHaveTextContent('Familia no encontrada')
  })

  it('presenta la familia con sus pestañas y las acciones de gestión', async () => {
    abrirFicha()
    expect(await screen.findByRole('heading', { name: FAMILIA.titular_nombre })).toBeInTheDocument()
    const pestanas = screen.getByRole('tablist', { name: 'Secciones de la familia' })
    for (const nombre of ['Datos', 'Mascotas', 'Cartera', 'Servicios', 'Historial']) {
      expect(within(pestanas).getByRole('tab', { name: nombre })).toBeInTheDocument()
    }
    expect(screen.getByRole('button', { name: 'Gestionar afiliación' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Habilitar portal' })).toBeInTheDocument()
  })

  it('oculta las acciones de afiliación a quien no puede ejecutarlas', async () => {
    server.use(http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'operaciones' })))
    abrirFicha()
    await screen.findByRole('heading', { name: FAMILIA.titular_nombre })
    expect(screen.queryByRole('button', { name: 'Gestionar afiliación' })).not.toBeInTheDocument()
  })

  it('lista las mascotas con el nombre de la especie del catálogo', async () => {
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Mascotas' }))
    // Luna también sale en el resumen bajo la línea: se busca dentro de la pestaña.
    const pestana = screen.getByRole('tabpanel')
    expect(await within(pestana).findByText('Luna')).toBeInTheDocument()
    expect(await within(pestana).findByText('Perro')).toBeInTheDocument()
  })

  it('explica que no hay cartera cuando la familia no tiene contrato', async () => {
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Cartera' }))
    expect(await screen.findByText(/aún no tiene contrato/i)).toBeInTheDocument()
  })

  it('afilia con un plan por peludo, la forma de pago y el precio del backend', async () => {
    const pedidos: unknown[] = []
    const cotizacion = (periodicidad: string, meses: number, valor: string, descuento: boolean, ahorro = '0.00') => ({
      periodicidad,
      meses,
      tarifa_de: 1,
      peludos: [{ especie: 'perro', plan_id: 'p1', plan_nombre: 'Colita Feliz', valor_mensual: '35500.00' }],
      valor_mensual: '35500.00',
      valor_periodo: valor,
      descuento,
      ahorro,
    })
    server.use(
      http.get(`${API}/planes`, () => HttpResponse.json([PLAN])),
      http.post(`${API}/planes/cotizacion`, async ({ request }) => {
        pedidos.push(['cotizacion', await request.json()])
        return HttpResponse.json([
          cotizacion('mensual', 1, '35500.00', false),
          cotizacion('trimestral', 3, '106500.00', false),
          cotizacion('semestral', 6, '202350.00', true, '10650.00'),
          cotizacion('anual', 12, '378000.00', true, '48000.00'),
        ])
      }),
      http.post(`${API}/afiliaciones/asistida`, async ({ request }) => {
        pedidos.push(['asistida', await request.json()])
        return HttpResponse.json({ solicitud_id: 'sol1', valor: '202350.00', enlace_pago: 'https://pago/abc' }, { status: 201 })
      }),
      http.post(`${API}/afiliaciones/sol1/pago-manual`, async ({ request }) => {
        pedidos.push(['pago', await request.json()])
        return HttpResponse.json({})
      }),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Cartera' }))
    await user.click(await screen.findByRole('button', { name: 'Afiliar a un plan' }))
    const modal = await screen.findByRole('dialog')
    expect(within(modal).getByText('Elige el plan de cada peludo para ver el precio.')).toBeInTheDocument()
    expect(within(modal).getByRole('button', { name: 'Iniciar afiliación' })).toBeDisabled()
    const plan = within(modal).getByLabelText('Luna · Perro')
    await waitFor(() => expect(within(plan).getByRole('option', { name: /colita feliz/i })).toBeInTheDocument())
    await user.selectOptions(plan, 'p1')
    await user.selectOptions(within(modal).getByLabelText('Forma de pago'), 'semestral')
    const precio = await within(modal).findByRole('status', { name: 'Precio de la afiliación' })
    expect(precio).toHaveTextContent(/202\.350 cada 6 meses/)
    expect(precio).toHaveTextContent(/ahorra .*10\.650/)
    await user.click(within(modal).getByRole('button', { name: 'Iniciar afiliación' }))
    expect(await within(modal).findByLabelText('Enlace de pago')).toHaveValue('https://pago/abc')
    await user.type(within(modal).getByLabelText('Comprobante'), 'TRF-99')
    await user.click(within(modal).getByRole('button', { name: 'Registrar pago recibido' }))
    expect(await within(modal).findByText(/la afiliación quedó activa/i)).toBeInTheDocument()
    expect(pedidos).toEqual([
      ['cotizacion', { ciudad: FAMILIA.ciudad, peludos: [{ especie: 'perro', plan_id: 'p1' }] }],
      [
        'asistida',
        {
          familia_id: FAMILIA.id,
          peludos: [{ mascota_id: FAMILIA.mascotas![0]!.id, plan_id: 'p1' }],
          periodicidad: 'semestral',
          medio_aceptacion: 'whatsapp',
        },
      ],
      ['pago', { medio: 'transferencia', comprobante: 'TRF-99' }],
    ])
  })

  it('registra un pago manual sobre la cuota elegida', async () => {
    let enviado: unknown = null
    server.use(
      http.get(`${API}/cartera/familias/:id/estado-cuenta`, () => HttpResponse.json(CUENTA)),
      http.post(`${API}/cartera/pagos`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ id: 'pg1' }, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Cartera' }))
    expect(await screen.findByText('Cuota septiembre')).toBeInTheDocument()
    expect(screen.getByText('Vencida')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Registrar pago' }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Valor (COP)'), '89000')
    await user.type(within(modal).getByLabelText('Referencia o comprobante'), 'TRF-123')
    await user.selectOptions(within(modal).getByLabelText('Cuota'), 'q1')
    await user.click(within(modal).getByRole('button', { name: 'Registrar pago' }))

    await waitFor(() =>
      expect(enviado).toEqual({
        familia_id: FAMILIA.id,
        valor: '89000',
        medio: 'transferencia',
        referencia: 'TRF-123',
        cuota_id: 'q1',
      }),
    )
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('una cuota pendiente de la línea se paga desde su estación, con la cuota y el saldo puestos', async () => {
    const cuota = { tipo: 'cuota' as const, referencia_id: 'q1', fecha: '2099-01-05', estado: 'proxima' as const, titulo: 'Cuota septiembre', mascota: null }
    server.use(
      http.get(`${API}/cartera/familias/:id/estado-cuenta`, () => HttpResponse.json(CUENTA)),
      http.get(`${API}/familias/:id/linea`, () => HttpResponse.json({ familia_id: FAMILIA.id, planes: [], estaciones: [cuota] })),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('button', { name: 'Registrar pago de cuota septiembre' }))
    const modal = await screen.findByRole('dialog', { name: 'Registrar pago' })
    expect(within(modal).getByLabelText('Cuota')).toHaveValue('q1')
    expect(within(modal).getByLabelText('Valor (COP)')).toHaveValue(89000)
  })

  it('sin permiso para cobrar, la cuota de la línea solo lleva a la cartera', async () => {
    const cuota = { tipo: 'cuota' as const, referencia_id: 'q1', fecha: '2099-01-05', estado: 'proxima' as const, titulo: 'Cuota septiembre', mascota: null }
    server.use(
      http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'operaciones' })),
      http.get(`${API}/cartera/familias/:id/estado-cuenta`, () => HttpResponse.json(CUENTA)),
      http.get(`${API}/familias/:id/linea`, () => HttpResponse.json({ familia_id: FAMILIA.id, planes: [], estaciones: [cuota] })),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('button', { name: 'Ver cuota septiembre' }))
    expect(screen.getByRole('tab', { name: 'Cartera' })).toHaveAttribute('aria-selected', 'true')
  })

  it('muestra el historial vacío sin dejar la pestaña en blanco', async () => {
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Historial' }))
    expect(await screen.findByText('Sin cambios registrados.')).toBeInTheDocument()
  })

  it('pide el motivo y da de baja a la familia', async () => {
    let motivo: unknown = null
    server.use(
      http.post(`${API}/familias/:id/baja`, async ({ request }) => {
        motivo = ((await request.json()) as { motivo: string }).motivo
        return HttpResponse.json({ ...FAMILIA, estado: 'cancelada' })
      }),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('button', { name: 'Gestionar afiliación' }))
    await user.click(await screen.findByRole('menuitem', { name: 'Dar de baja' }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Motivo de la baja'), 'Se muda del país')
    await user.click(within(modal).getByRole('button', { name: 'Confirmar baja' }))
    await waitFor(() => expect(motivo).toBe('Se muda del país'))
  })

  it('edita los datos y envía sólo los campos que cambiaron', async () => {
    let enviado: unknown = null
    server.use(
      http.patch(`${API}/familias/:id`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ ...FAMILIA, direccion: 'Calle 1 # 2-3' })
      }),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('button', { name: 'Editar' }))
    await user.type(screen.getByLabelText('Dirección'), 'Calle 1 # 2-3')
    await user.click(screen.getByRole('button', { name: 'Guardar cambios' }))
    await waitFor(() => expect(enviado).toEqual({ direccion: 'Calle 1 # 2-3' }))
    expect(await screen.findByText('Cambios guardados.')).toBeInTheDocument()
  })

  it('muestra el barrio y corrige barrio y complemento por separado de las notas', async () => {
    let enviado: unknown = null
    server.use(
      http.patch(`${API}/familias/:id`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ ...FAMILIA, barrio: 'Rosales', complemento: 'Torre 2 apto 301' })
      }),
    )
    const user = userEvent.setup()
    abrirFicha()
    expect(await screen.findByText('Chapinero')).toBeInTheDocument()
    await user.click(await screen.findByRole('button', { name: 'Editar' }))
    const barrio = screen.getByLabelText('Barrio')
    await user.clear(barrio)
    await user.type(barrio, 'Rosales')
    await user.type(screen.getByLabelText('Complemento'), 'Torre 2 apto 301')
    await user.click(screen.getByRole('button', { name: 'Guardar cambios' }))
    await waitFor(() => expect(enviado).toEqual({ barrio: 'Rosales', complemento: 'Torre 2 apto 301' }))
  })

  it('muestra el error del servidor al editar', async () => {
    server.use(
      http.patch(`${API}/familias/:id`, () =>
        HttpResponse.json({ detail: 'Teléfono inválido' }, { status: 422 }),
      ),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('button', { name: 'Editar' }))
    await user.type(screen.getByLabelText('Dirección'), 'x')
    await user.click(screen.getByRole('button', { name: 'Guardar cambios' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Teléfono inválido')
    await user.click(screen.getByRole('button', { name: 'Cancelar' }))
    expect(screen.getByRole('button', { name: 'Editar' })).toBeInTheDocument()
  })

  it('cuenta en el historial qué cambió, campo por campo', async () => {
    server.use(
      http.get(`${API}/familias/:id/historial`, () =>
        HttpResponse.json([
          { fecha: '2026-10-01T15:00:00Z', accion: 'cambio_estado', usuario_id: null, cambios: { estado: ['activa', 'congelada'] } },
          { fecha: '2026-09-01T15:00:00Z', accion: 'editar', usuario_id: null, cambios: { direccion: [null, 'Calle 1'] } },
          { fecha: '2026-08-01T15:00:00Z', accion: 'crear', usuario_id: null, cambios: {} },
        ]),
      ),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Historial' }))
    expect(await screen.findByText('estado: activa → congelada')).toBeInTheDocument()
    expect(screen.getByText('direccion: vacío → Calle 1')).toBeInTheDocument()
    expect(screen.getByText('Registro creado')).toBeInTheDocument()
  })

  const SERVICIO = {
    id: 's1',
    familia_id: FAMILIA.id,
    mascota_id: FAMILIA.mascotas?.[0]?.id,
    tipo_codigo: 'consulta_domiciliaria',
    tipo: 'domiciliario',
    estado: 'agendado',
    ciudad: 'Bogota',
    programado_para: '2026-11-02T15:00:00Z',
  }

  function resumen(datos: Record<string, unknown> = {}) {
    return {
      desde: '2026-11-01',
      hasta: '2026-11-30',
      utilizados: [],
      pendientes: [],
      cancelados: [],
      pendientes_atencion: [],
      cupos: [],
      ...datos,
    }
  }

  it('separa los servicios pendientes de los utilizados, con el cupo del plan', async () => {
    let consultado: URLSearchParams | null = null
    server.use(
      http.get(`${API}/servicios/resumen`, ({ request }) => {
        consultado = new URL(request.url).searchParams
        return HttpResponse.json(
          resumen({
            pendientes: [SERVICIO],
            utilizados: [{ ...SERVICIO, id: 's2', estado: 'completado' }],
            pendientes_atencion: [
              {
                id: 'p1',
                servicio_origen_id: 's2',
                descripcion: 'Ecografía abdominal',
                requiere_autorizacion: true,
                estado: 'pendiente_autorizacion',
              },
            ],
            cupos: [{ tipo_codigo: 'consulta_domiciliaria', cupo: 4, usados: 1, periodo: 'anual', mascota_id: FAMILIA.mascotas![0]!.id }],
          }),
        )
      }),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Servicios' }))
    const pendientes = await screen.findByRole('table', { name: 'Pendientes' })
    expect(within(pendientes).getByText('Agendado')).toBeInTheDocument()
    expect(within(pendientes).getByText('Luna')).toBeInTheDocument()
    expect(within(screen.getByRole('table', { name: 'Utilizados' })).getByText('Completado')).toBeInTheDocument()
    expect(screen.getByText('Ecografía abdominal')).toBeInTheDocument()
    expect(screen.getByText('1 de 4')).toBeInTheDocument()
    expect(screen.getByText('Este año')).toBeInTheDocument()
    // Por defecto, el mes en curso.
    const params = consultado as URLSearchParams | null
    expect(params?.get('familia_id')).toBe(FAMILIA.id)
    expect(params?.get('desde')).toMatch(/^\d{4}-\d{2}-01$/)
  })

  it('separa el cupo de cada mascota aunque compartan beneficio', async () => {
    const luna = FAMILIA.mascotas![0]!
    const kira = { ...luna, id: 'm2', nombre: 'Kira' }
    const cupo = (mascota_id: string, usados: number) => ({ tipo_codigo: 'consulta_domiciliaria', cupo: 4, usados, periodo: 'anual', mascota_id })
    server.use(
      http.get(`${API}/familias/:id`, () => HttpResponse.json({ ...FAMILIA, mascotas: [luna, kira] })),
      http.get(`${API}/servicios/resumen`, () =>
        HttpResponse.json({
          desde: '2026-11-01',
          hasta: '2026-11-30',
          utilizados: [],
          pendientes: [],
          pendientes_atencion: [],
          cupos: [cupo(luna.id, 1), cupo('m2', 3)],
        }),
      ),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Servicios' }))
    expect(within(await screen.findByRole('table', { name: 'Cupo de Luna' })).getByText('1 de 4')).toBeInTheDocument()
    expect(within(screen.getByRole('table', { name: 'Cupo de Kira' })).getByText('3 de 4')).toBeInTheDocument()
  })

  it('filtra por mascota, por rango y muestra los cancelados si se piden', async () => {
    const consultas: URLSearchParams[] = []
    server.use(
      http.get(`${API}/servicios/resumen`, ({ request }) => {
        consultas.push(new URL(request.url).searchParams)
        return HttpResponse.json(resumen())
      }),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Servicios' }))
    expect(await screen.findByText('No hay servicios pendientes en este rango.')).toBeInTheDocument()

    await user.selectOptions(screen.getByLabelText('Mascota'), 'Luna')
    await waitFor(() => expect(consultas.at(-1)?.get('mascota_id')).toBe(FAMILIA.mascotas?.[0]?.id))

    const desde = screen.getByLabelText('Desde')
    await user.clear(desde)
    await user.type(desde, '2026-01-01')
    await waitFor(() => expect(consultas.at(-1)?.get('desde')).toBe('2026-01-01'))

    await user.click(screen.getByLabelText('Ver cancelados'))
    await waitFor(() => expect(consultas.at(-1)?.get('incluir_cancelados')).toBe('true'))
    expect(await screen.findByText('No hay servicios cancelados en este rango.')).toBeInTheDocument()
  })

  it('no consulta con un rango incompleto o invertido y lo explica', async () => {
    const consultas: URLSearchParams[] = []
    server.use(
      http.get(`${API}/servicios/resumen`, ({ request }) => {
        consultas.push(new URL(request.url).searchParams)
        return HttpResponse.json(resumen())
      }),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Servicios' }))
    await screen.findByText('No hay servicios pendientes en este rango.')
    const hasta = screen.getByLabelText('Hasta')
    await user.clear(hasta)
    expect(await screen.findByText('Elige la fecha inicial y la final del rango.')).toBeInTheDocument()
    await user.type(hasta, '2000-01-01')
    expect(await screen.findByText('La fecha final es anterior a la inicial.')).toBeInTheDocument()
    expect(consultas.every((c) => c.get('hasta') !== '' && c.get('hasta') !== '2000-01-01')).toBe(true)
  })

  it('avisa que la familia está dada de baja y no ofrece acciones', async () => {
    server.use(
      http.get(`${API}/familias/:id`, () =>
        HttpResponse.json({
          ...FAMILIA,
          estado: 'cancelada',
          dada_de_baja_en: '2026-10-01T10:00:00Z',
          motivo_baja: 'Se mudó',
          usuario_portal_id: 'u1',
        }),
      ),
    )
    abrirFicha()
    expect(await screen.findByText(/dada de baja el 01\/10\/2026: se mudó/i)).toBeInTheDocument()
    expect(screen.getByText('Con portal')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Gestionar afiliación' })).not.toBeInTheDocument()
  })

  it('cambia el estado con su motivo', async () => {
    let enviado: unknown = null
    server.use(
      http.post(`${API}/familias/:id/estado`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ ...FAMILIA, estado: 'congelada' })
      }),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('button', { name: 'Gestionar afiliación' }))
    await user.click(await screen.findByRole('menuitem', { name: 'Cambiar estado' }))
    const modal = await screen.findByRole('dialog')
    await user.selectOptions(within(modal).getByLabelText('Nuevo estado'), 'congelada')
    await user.type(within(modal).getByLabelText('Motivo'), 'Viaje largo')
    await user.click(within(modal).getByRole('button', { name: 'Cambiar estado' }))
    await waitFor(() => expect(enviado).toEqual({ estado: 'congelada', motivo: 'Viaje largo' }))
  })

  it('habilita el portal y dice el resultado', async () => {
    server.use(
      http.post(`${API}/familias/:id/acceso-portal`, () =>
        HttpResponse.json({ ...FAMILIA, usuario_portal_id: 'u1' }),
      ),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('button', { name: 'Habilitar portal' }))
    expect(await screen.findByText(/portal habilitado/i)).toBeInTheDocument()
  })

  it('informa si no se pudo habilitar el portal', async () => {
    server.use(
      http.post(`${API}/familias/:id/acceso-portal`, () =>
        HttpResponse.json({ detail: 'La familia no tiene un celular válido' }, { status: 409 }),
      ),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('button', { name: 'Habilitar portal' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('no tiene un celular válido')
  })

  it('agrega una mascota y da de baja otra', async () => {
    let nueva: unknown = null
    let baja: unknown = null
    server.use(
      http.post(`${API}/familias/:id/mascotas`, async ({ request }) => {
        nueva = await request.json()
        return HttpResponse.json({}, { status: 201 })
      }),
      http.post(`${API}/mascotas/:id/baja`, async ({ request }) => {
        baja = await request.json()
        return HttpResponse.json({})
      }),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Mascotas' }))

    await user.click(await screen.findByRole('button', { name: 'Agregar mascota' }))
    let modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nombre'), 'Michi')
    await user.selectOptions(within(modal).getByLabelText('Especie'), 'gato')
    expect(within(modal).getByLabelText('Fecha de nacimiento')).toHaveAccessibleDescription(/aproximada/)
    await user.type(within(modal).getByLabelText('Fecha de nacimiento'), '2024-06-01')
    await user.type(within(modal).getByLabelText('Peso (kg)'), '3.4')
    await user.selectOptions(within(modal).getByLabelText('Esterilizada (opcional)'), 'Sí')
    await user.click(within(modal).getByRole('button', { name: 'Agregar' }))
    await waitFor(() =>
      expect(nueva).toEqual({
        nombre: 'Michi',
        especie: 'gato',
        fecha_nacimiento: '2024-06-01',
        peso_kg: 3.4,
        esterilizada: true,
      }),
    )
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())

    const tabla = screen.getByRole('table')
    await user.click(within(tabla).getByRole('button', { name: 'Dar de baja' }))
    modal = await screen.findByRole('dialog', { name: 'Dar de baja a Luna' })
    await user.type(within(modal).getByLabelText('Motivo'), 'Falleció')
    await user.click(within(modal).getByRole('button', { name: 'Confirmar baja' }))
    await waitFor(() => expect(baja).toEqual({ motivo: 'Falleció' }))
  })

  const CONTACTO = { id: 'k1', posicion: 1, nombre: 'Rocío Ruiz', telefono: '+573009998877', relacion: 'hermana', email: null }

  it('lista los contactos adicionales y no deja pasar de tres', async () => {
    server.use(
      http.get(`${API}/familias/:id`, () =>
        HttpResponse.json({
          ...FAMILIA,
          contactos: [
            CONTACTO,
            { ...CONTACTO, id: 'k2', posicion: 2, nombre: 'Pedro Ruiz', relacion: null },
            { ...CONTACTO, id: 'k3', posicion: 3, nombre: 'Marta Gil', relacion: null },
          ],
        }),
      ),
    )
    abrirFicha()
    expect(await screen.findByText('Rocío Ruiz')).toBeInTheDocument()
    expect(screen.getByText('hermana')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Añadir contacto' })).toBeDisabled()
  })

  it('añade un contacto con solo los campos que se llenaron', async () => {
    let enviado: unknown = null
    server.use(
      http.post(`${API}/familias/:id/contactos`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(CONTACTO, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    abrirFicha()
    expect(await screen.findByText('Esta familia no tiene contactos adicionales.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Añadir contacto' }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nombre'), 'Rocío Ruiz')
    await user.type(within(modal).getByLabelText('Celular'), '3009998877')
    await user.type(within(modal).getByLabelText('Relación (opcional)'), 'hermana')
    await user.click(within(modal).getByRole('button', { name: 'Guardar contacto' }))
    await waitFor(() => expect(enviado).toEqual({ nombre: 'Rocío Ruiz', telefono: '3009998877', relacion: 'hermana' }))
  })

  it('quita un contacto tras confirmarlo en la página', async () => {
    let quitado = ''
    server.use(
      http.get(`${API}/familias/:id`, () => HttpResponse.json({ ...FAMILIA, contactos: [CONTACTO] })),
      http.post(`${API}/familias/:id/contactos/:contacto/baja`, ({ params }) => {
        quitado = String(params.contacto)
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('button', { name: 'Quitar' }))
    const modal = await screen.findByRole('dialog')
    expect(within(modal).getByText('Quitar a Rocío Ruiz')).toBeInTheDocument()
    await user.click(within(modal).getByRole('button', { name: 'Quitar contacto' }))
    await waitFor(() => expect(quitado).toBe('k1'))
  })

  const MENSAJE = {
    id: 'm1',
    familia_id: FAMILIA.id,
    canal: 'whatsapp',
    direccion: 'saliente',
    destino: '+573001112233',
    plantilla: 'cuota_vencida',
    contenido: null,
    estado: 'leido',
    intentos: 1,
    error: null,
    masivo: false,
    enviado_en: '2026-11-02T15:00:00Z',
    entregado_en: null,
    leido_en: null,
    created_at: '2026-11-02T14:59:00Z',
  }

  it('muestra el historial de comunicaciones de la familia, enviado y recibido', async () => {
    let consultado: URLSearchParams | null = null
    server.use(
      http.get(`${API}/comunicaciones/mensajes`, ({ request }) => {
        consultado = new URL(request.url).searchParams
        return HttpResponse.json({
          items: [
            MENSAJE,
            { ...MENSAJE, id: 'm2', direccion: 'entrante', plantilla: null, contenido: '¿A qué hora llegan?', estado: 'recibido' },
            { ...MENSAJE, id: 'm3', canal: 'email', estado: 'fallido', error: 'Buzón inexistente', masivo: true },
          ],
          total: 3,
          limit: 20,
          offset: 0,
        })
      }),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Comunicaciones' }))
    const tabla = await screen.findByRole('table', { name: 'Comunicaciones' })
    expect(within(tabla).getAllByText('Plantilla «cuota_vencida»')).toHaveLength(2)
    expect(within(tabla).getByText('¿A qué hora llegan?')).toBeInTheDocument()
    expect(within(tabla).getByText('Recibido', { selector: 'td' })).toBeInTheDocument()
    expect(within(tabla).getByText('Correo')).toBeInTheDocument()
    expect(within(tabla).getByText('Buzón inexistente')).toBeInTheDocument()
    expect(within(tabla).getByText('Fallido')).toBeInTheDocument()
    const params = consultado as URLSearchParams | null
    expect(params?.get('familia_id')).toBe(FAMILIA.id)
    expect(params?.get('orden')).toBe('-created_at')
  })

  it('pagina el historial de comunicaciones', async () => {
    const offsets: string[] = []
    server.use(
      http.get(`${API}/comunicaciones/mensajes`, ({ request }) => {
        const offset = new URL(request.url).searchParams.get('offset') ?? '0'
        offsets.push(offset)
        return HttpResponse.json({ items: [MENSAJE], total: 25, limit: 20, offset: Number(offset) })
      }),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Comunicaciones' }))
    await screen.findByRole('table', { name: 'Comunicaciones' })
    await user.click(screen.getByRole('button', { name: /siguiente/i }))
    await waitFor(() => expect(offsets).toContain('20'))
  })

  it('avisa que la familia no tiene comunicaciones', async () => {
    server.use(
      http.get(`${API}/comunicaciones/mensajes`, () =>
        HttpResponse.json({ items: [], total: 0, limit: 20, offset: 0 }),
      ),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Comunicaciones' }))
    expect(await screen.findByText('Esta familia todavía no tiene comunicaciones.')).toBeInTheDocument()
  })

  it('dice cuándo no pudo cargar los servicios o las comunicaciones', async () => {
    server.use(
      http.get(`${API}/servicios/resumen`, () => HttpResponse.json({ detail: 'Fallo' }, { status: 500 })),
      http.get(`${API}/comunicaciones/mensajes`, () => HttpResponse.json({ detail: 'Fallo' }, { status: 500 })),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Servicios' }))
    expect(await screen.findByText(/No fue posible cargar los servicios/)).toBeInTheDocument()
    await user.click(screen.getByRole('tab', { name: 'Comunicaciones' }))
    expect(await screen.findByText(/No fue posible cargar las comunicaciones/)).toBeInTheDocument()
  })

  const LUNA: MascotaRead = { ...FAMILIA.mascotas![0]!, peso_kg: 12.5, esterilizada: true, foto_url: null }

  async function abrirFichaDeLuna(familia = { ...FAMILIA, mascotas: [LUNA] }) {
    server.use(http.get(`${API}/familias/:id`, () => HttpResponse.json(familia)))
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Mascotas' }))
    await user.click(await screen.findByRole('button', { name: 'Ficha' }))
    return { user, modal: await screen.findByRole('dialog') }
  }

  it('abre la ficha de la mascota con su plan, sus servicios del mes y sus enlaces', async () => {
    let consultado: URLSearchParams | null = null
    server.use(
      http.get(`${API}/cartera/familias/:id/estado-cuenta`, () => HttpResponse.json(CUENTA)),
      http.get(`${API}/servicios/resumen`, ({ request }) => {
        consultado = new URL(request.url).searchParams
        return HttpResponse.json(resumen({ pendientes: [SERVICIO] }))
      }),
    )
    const { modal } = await abrirFichaDeLuna()
    expect(within(modal).getByRole('heading', { name: 'Luna' })).toBeInTheDocument()
    // El nombre del plan ya dice «Plan»: no se antepone otra vez.
    expect(await within(modal).findByText(/^Plan Esencial: paga .*89\.000 al mes\.$/)).toBeInTheDocument()
    expect(await within(modal).findByText(/Este mes: 1 pendientes y 0 utilizados/)).toBeInTheDocument()
    expect((consultado as URLSearchParams | null)?.get('mascota_id')).toBe(LUNA.id)
    expect(within(modal).getByRole('link', { name: 'Historia clínica' })).toHaveAttribute('href', `/clinica/mascotas/${LUNA.id}`)
    expect(within(modal).getByRole('link', { name: 'Carnet preventivo' })).toHaveAttribute('href', `/preventivos?mascota=${LUNA.id}`)
    expect(within(modal).getByLabelText('Peso (kg)')).toHaveValue(12.5)
    expect(within(modal).getByLabelText('Esterilizada (opcional)')).toHaveValue('si')
    expect(within(modal).getByText('Sin foto')).toBeInTheDocument()
  })

  it('dice si la familia no tiene plan y corrige los datos de la mascota', async () => {
    let enviado: unknown = null
    server.use(
      http.patch(`${API}/mascotas/:id`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(LUNA)
      }),
    )
    const { user, modal } = await abrirFichaDeLuna()
    expect(await within(modal).findByText('La familia no tiene un plan vigente.')).toBeInTheDocument()
    const peso = within(modal).getByLabelText('Peso (kg)')
    await user.clear(peso)
    await user.type(peso, '13.1')
    await user.clear(within(modal).getByLabelText('Raza (opcional)'))
    await user.click(within(modal).getByRole('button', { name: 'Guardar cambios' }))
    await waitFor(() =>
      expect(enviado).toEqual({
        nombre: 'Luna',
        raza: null,
        sexo: 'hembra',
        fecha_nacimiento: '2021-03-10',
        peso_kg: 13.1,
        esterilizada: true,
      }),
    )
    expect(await within(modal).findByText('Cambios guardados.')).toBeInTheDocument()
  })

  it('sube la foto de la mascota y rechaza una de más de 5 MB sin enviarla', async () => {
    const subidas: string[] = []
    server.use(
      http.put(`${API}/mascotas/:id/foto`, async ({ request }) => {
        subidas.push(await request.text())
        return HttpResponse.json({ ...LUNA, foto_url: 'https://s3.local/luna.jpg' })
      }),
    )
    const { user, modal } = await abrirFichaDeLuna()
    const grande = new File([new Uint8Array(5 * 1024 * 1024 + 1)], 'grande.jpg', { type: 'image/jpeg' })
    await user.upload(within(modal).getByLabelText('Subir foto'), grande)
    expect(await within(modal).findByText(/pesa más de 5 MB/)).toBeInTheDocument()
    expect(subidas).toHaveLength(0)

    await user.upload(within(modal).getByLabelText('Subir foto'), new File(['jpg'], 'luna.jpg', { type: 'image/jpeg' }))
    await waitFor(() => expect(subidas).toHaveLength(1))
    expect(subidas[0]).toContain('name="foto"')
    expect(within(modal).queryByText(/pesa más de 5 MB/)).not.toBeInTheDocument()
  })

  it('quita la foto de la mascota', async () => {
    let quitada = ''
    server.use(
      http.delete(`${API}/mascotas/:id/foto`, ({ params }) => {
        quitada = String(params.id)
        return HttpResponse.json({ ...LUNA, foto_url: null })
      }),
    )
    const { user, modal } = await abrirFichaDeLuna({ ...FAMILIA, mascotas: [{ ...LUNA, foto_url: 'https://s3.local/luna.jpg' }] })
    expect(within(modal).getByText('Cambiar foto')).toBeInTheDocument()
    await user.click(within(modal).getByRole('button', { name: 'Quitar foto' }))
    await waitFor(() => expect(quitada).toBe(LUNA.id))
  })

  it('muestra la foto y no deja editar una mascota de baja', async () => {
    const { modal } = await abrirFichaDeLuna({
      ...FAMILIA,
      mascotas: [{ ...LUNA, activa: false, motivo_baja: 'Falleció', foto_url: 'https://s3.local/luna.jpg' }],
    })
    expect(within(modal).getByRole('img', { name: 'Foto de Luna' })).toHaveAttribute('src', 'https://s3.local/luna.jpg')
    expect(within(modal).queryByRole('button', { name: 'Guardar cambios' })).not.toBeInTheDocument()
    expect(within(modal).queryByLabelText(/foto/i, { selector: 'input' })).not.toBeInTheDocument()
    expect(within(modal).getByLabelText('Nombre')).toBeDisabled()
  })

  const SUBIDO: DocumentoRead = {
    archivo_id: 'a1',
    documento_id: 'd1',
    origen: 'subido',
    categoria: 'identificacion',
    descripcion: 'Cédula del titular',
    mascota_id: null,
    nombre: 'cedula.pdf',
    content_type: 'application/pdf',
    tamano_bytes: 2048,
    visible_familia: false,
    creado_en: '2026-11-02T15:00:00Z',
    url: 'https://s3.local/cedula.pdf',
  }
  const CONTRATO_PDF: DocumentoRead = {
    ...SUBIDO,
    archivo_id: 'a2',
    documento_id: null,
    origen: 'contrato',
    categoria: null,
    descripcion: 'Contrato TM-0001',
    visible_familia: true,
    url: 'https://s3.local/contrato.pdf',
  }

  async function abrirDocumentos(documentos: DocumentoRead[] = [SUBIDO, CONTRATO_PDF]) {
    const consultas: URLSearchParams[] = []
    server.use(
      http.get(`${API}/familias/:id/documentos`, ({ request }) => {
        consultas.push(new URL(request.url).searchParams)
        return HttpResponse.json(documentos)
      }),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Documentos' }))
    return { user, consultas }
  }

  it('lista los documentos subidos y los generados, y filtra por mascota', async () => {
    const { user, consultas } = await abrirDocumentos()
    const tabla = await screen.findByRole('table', { name: 'Documentos' })
    expect(within(tabla).getByRole('link', { name: 'Cédula del titular' })).toHaveAttribute('href', SUBIDO.url)
    expect(within(tabla).getByText('Identificación')).toBeInTheDocument()
    expect(within(tabla).getByText('Contrato')).toBeInTheDocument()
    expect(within(tabla).getAllByText('Familia')).toHaveLength(2)
    // Solo los subidos se editan o se quitan; los generados se gestionan donde nacen.
    expect(within(tabla).getAllByRole('button', { name: 'Editar' })).toHaveLength(1)
    await user.selectOptions(screen.getByLabelText('Mascota'), 'Luna')
    await waitFor(() => expect(consultas.at(-1)?.get('mascota_id')).toBe(FAMILIA.mascotas?.[0]?.id))
  })

  it('sube un documento y no envía uno de más de 10 MB', async () => {
    const cuerpos: string[] = []
    server.use(
      http.post(`${API}/familias/:id/documentos`, async ({ request }) => {
        cuerpos.push(await request.text())
        return HttpResponse.json(SUBIDO, { status: 201 })
      }),
    )
    const { user } = await abrirDocumentos([])
    expect(await screen.findByText('No hay documentos.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Subir documento' }))
    const modal = await screen.findByRole('dialog')
    const grande = new File([new Uint8Array(10 * 1024 * 1024 + 1)], 'grande.pdf', { type: 'application/pdf' })
    await user.selectOptions(within(modal).getByLabelText('Categoría'), 'Examen externo')
    await user.click(within(modal).getByRole('button', { name: 'Subir' }))
    expect(await within(modal).findByText('Elige el fichero que vas a subir.')).toBeInTheDocument()
    await user.upload(within(modal).getByLabelText('Fichero'), grande)
    expect(await within(modal).findByText(/pesa más de 10 MB/)).toBeInTheDocument()
    await user.click(within(modal).getByRole('button', { name: 'Subir' }))
    expect(cuerpos).toHaveLength(0)

    await user.upload(within(modal).getByLabelText('Fichero'), new File(['%PDF'], 'eco.pdf', { type: 'application/pdf' }))
    await user.selectOptions(within(modal).getByLabelText('De'), 'Luna')
    await user.type(within(modal).getByLabelText('Descripción (opcional)'), 'Ecografía')
    await user.click(within(modal).getByLabelText('La familia lo ve en su portal'))
    await user.click(within(modal).getByRole('button', { name: 'Subir' }))
    await waitFor(() => expect(cuerpos).toHaveLength(1))
    for (const [campo, valor] of [
      ['categoria', 'examen_externo'],
      ['visible_familia', 'true'],
      ['descripcion', 'Ecografía'],
      ['mascota_id', FAMILIA.mascotas?.[0]?.id ?? ''],
    ]) {
      expect(cuerpos[0]).toMatch(new RegExp(`name="${campo}"\\r\\n\\r\\n${valor}`))
    }
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('edita y quita un documento subido', async () => {
    let cambios: unknown = null
    let quitado = ''
    server.use(
      http.patch(`${API}/documentos/:id`, async ({ request }) => {
        cambios = await request.json()
        return HttpResponse.json(SUBIDO)
      }),
      http.post(`${API}/documentos/:id/baja`, ({ params }) => {
        quitado = String(params.id)
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const { user } = await abrirDocumentos()
    await user.click(await screen.findByRole('button', { name: 'Editar' }))
    let modal = await screen.findByRole('dialog')
    await user.clear(within(modal).getByLabelText('Descripción (opcional)'))
    await user.click(within(modal).getByLabelText('La familia lo ve en su portal'))
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    await waitFor(() =>
      expect(cambios).toEqual({ categoria: 'identificacion', descripcion: null, visible_familia: true }),
    )
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: 'Quitar' }))
    modal = await screen.findByRole('dialog')
    await user.click(within(modal).getByRole('button', { name: 'Quitar documento' }))
    await waitFor(() => expect(quitado).toBe('d1'))
  })

  it('dice cuándo no pudo cargar los documentos', async () => {
    server.use(http.get(`${API}/familias/:id/documentos`, () => HttpResponse.json({ detail: 'Fallo' }, { status: 500 })))
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Documentos' }))
    expect(await screen.findByText(/No fue posible cargar los documentos/)).toBeInTheDocument()
  })

  it('con afiliación vigente, el alta de una mascota pide su plan y lo envía', async () => {
    let enviado: Record<string, unknown> | null = null
    server.use(
      http.get(`${API}/cartera/familias/:id/estado-cuenta`, () => HttpResponse.json(CUENTA)),
      http.get(`${API}/planes`, () => HttpResponse.json([PLAN])),
      http.post(`${API}/familias/:id/mascotas`, async ({ request }) => {
        enviado = (await request.json()) as Record<string, unknown>
        return HttpResponse.json({ ...FAMILIA.mascotas![0]!, id: 'm9', nombre: 'Coco' }, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Mascotas' }))
    await user.click(await screen.findByRole('button', { name: 'Agregar mascota' }))
    const modal = await screen.findByRole('dialog')
    expect(await within(modal).findByText(/todos pagan la tarifa del nuevo número de peludos/)).toBeInTheDocument()
    await user.type(within(modal).getByLabelText('Nombre'), 'Coco')
    await user.selectOptions(within(modal).getByLabelText('Especie'), 'gato')
    const plan = await within(modal).findByLabelText('Plan')
    await waitFor(() => expect(within(plan).getByRole('option', { name: /colita feliz/i })).toBeInTheDocument())
    await user.selectOptions(plan, 'p1')
    await user.type(within(modal).getByLabelText('Fecha de nacimiento'), '2024-06-01')
    await user.type(within(modal).getByLabelText('Peso (kg)'), '3')
    await user.click(within(modal).getByRole('button', { name: 'Agregar' }))
    await waitFor(() => expect(enviado).toMatchObject({ nombre: 'Coco', especie: 'gato', plan_id: 'p1' }))
  })

  it('cambia el plan de un peludo desde su ficha', async () => {
    let cambio: unknown = null
    const FIEL = { ...PLAN, id: 'p2', codigo: 'mi_amigo_fiel', nombre: 'Mi Amigo Fiel' }
    server.use(
      http.get(`${API}/cartera/familias/:id/estado-cuenta`, () =>
        HttpResponse.json({ ...CUENTA, mascotas: [{ ...CUENTA.mascotas[0]!, mascota_id: LUNA.id }] }),
      ),
      http.get(`${API}/planes`, () => HttpResponse.json([PLAN, FIEL])),
      http.post(`${API}/planes/contratos/:id/cambio`, async ({ request, params }) => {
        cambio = { contrato: params.id, ...((await request.json()) as object) }
        return HttpResponse.json({})
      }),
    )
    const { user, modal } = await abrirFichaDeLuna()
    const nuevo = await within(modal).findByLabelText('Cambiar de plan')
    expect(within(modal).getByRole('button', { name: 'Cambiar plan' })).toBeDisabled()
    await waitFor(() => expect(within(nuevo).getByRole('option', { name: /mi amigo fiel/i })).toBeInTheDocument())
    await user.selectOptions(nuevo, 'p2')
    await user.click(within(modal).getByRole('button', { name: 'Cambiar plan' }))
    await waitFor(() => expect(cambio).toEqual({ contrato: 'c1', mascota_id: LUNA.id, plan_id: 'p2' }))
    expect(await within(modal).findByText('Plan cambiado.')).toBeInTheDocument()
  })
})
