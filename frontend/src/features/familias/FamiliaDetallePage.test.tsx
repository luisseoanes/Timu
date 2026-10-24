import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { FamiliaDetallePage } from './FamiliaDetallePage'
import { FAMILIA, USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { EstadoCuenta } from '@/types'

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
    plan_id: 'p1',
    fecha_inicio: '2026-01-01',
    fecha_renovacion: '2027-01-01',
    fecha_fin: null,
    dia_corte: 5,
    valor_plan: '89000.00',
    mascotas_adicionales: 0,
    valor_adicional_mascota: '0.00',
    valor_mensual: '89000.00',
    saldo_a_favor: '0.00',
    estado: 'activo',
  } as EstadoCuenta['contrato'],
  plan: { id: 'p1', codigo: 'esencial', nombre: 'Plan Esencial' },
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
      tipo: 'mensual',
      fecha_vencimiento: '2026-09-05',
      valor: '89000.00',
      valor_pagado: '0.00',
      estado: 'vencida',
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
    expect(screen.getByRole('button', { name: 'Cambiar estado' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Habilitar portal' })).toBeInTheDocument()
  })

  it('oculta las acciones de afiliación a quien no puede ejecutarlas', async () => {
    server.use(http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'operaciones' })))
    abrirFicha()
    await screen.findByRole('heading', { name: FAMILIA.titular_nombre })
    expect(screen.queryByRole('button', { name: 'Cambiar estado' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Dar de baja' })).not.toBeInTheDocument()
  })

  it('lista las mascotas con el nombre de la especie del catálogo', async () => {
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Mascotas' }))
    expect(await screen.findByText('Luna')).toBeInTheDocument()
    expect(await screen.findByText('Perro')).toBeInTheDocument()
  })

  it('explica que no hay cartera cuando la familia no tiene contrato', async () => {
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Cartera' }))
    expect(await screen.findByText(/aún no tiene contrato/i)).toBeInTheDocument()
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
    await user.click(await screen.findByRole('button', { name: 'Dar de baja' }))
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

  it('lista los servicios de la familia con su mascota', async () => {
    server.use(
      http.get(`${API}/servicios`, () =>
        HttpResponse.json({
          items: [
            {
              id: 's1',
              familia_id: FAMILIA.id,
              mascota_id: FAMILIA.mascotas?.[0]?.id,
              tipo_codigo: 'consulta_domiciliaria',
              tipo: 'Consulta domiciliaria',
              estado: 'agendado',
              ciudad: 'Bogota',
              programado_para: '2026-11-02T15:00:00Z',
            },
          ],
          total: 1,
          limit: 50,
          offset: 0,
        }),
      ),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('tab', { name: 'Servicios' }))
    expect(await screen.findByText('Consulta domiciliaria')).toBeInTheDocument()
    expect(screen.getByText('Luna')).toBeInTheDocument()
    expect(screen.getByText('Agendado')).toBeInTheDocument()
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
    expect(screen.queryByRole('button', { name: 'Cambiar estado' })).not.toBeInTheDocument()
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
    await user.click(await screen.findByRole('button', { name: 'Cambiar estado' }))
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
    await user.click(within(modal).getByRole('button', { name: 'Agregar' }))
    await waitFor(() => expect(nueva).toEqual({ nombre: 'Michi', especie: 'gato' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())

    const tabla = screen.getByRole('table')
    await user.click(within(tabla).getByRole('button', { name: 'Dar de baja' }))
    modal = await screen.findByRole('dialog', { name: 'Dar de baja a Luna' })
    await user.type(within(modal).getByLabelText('Motivo'), 'Falleció')
    await user.click(within(modal).getByRole('button', { name: 'Confirmar baja' }))
    await waitFor(() => expect(baja).toEqual({ motivo: 'Falleció' }))
  })
})
