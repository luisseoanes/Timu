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
})
