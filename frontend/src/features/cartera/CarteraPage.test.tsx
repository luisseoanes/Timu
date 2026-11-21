import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'

import { CarteraPage } from './CarteraPage'
import { FAMILIA, sesionDe, USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { ContratoListado, EstadoCuenta } from '@/types'

// Sección 12: esta pantalla se prueba con el perfil que la usa (docs/perfiles-y-permisos.md).
beforeEach(() => server.use(sesionDe('atencion_cliente')))

const CONTRATO: ContratoListado = {
  id: 'c1',
  numero: 'TM-0001',
  familia_id: FAMILIA.id,
  titular: FAMILIA.titular_nombre,
  ciudad: 'Bogotá',
  plan: 'Plan Esencial',
  planes: [{ nombre: 'Plan Esencial', color: 'naranja' }],
  estado: 'en_mora',
  periodicidad: 'mensual',
  valor_mensual: '89000.00',
  valor_periodo: '89000.00',
  saldo_vencido: '178000.00',
  dias_mora: 40,
  fecha_renovacion: '2027-01-01',
  renovable: false,
}

const POR_RENOVAR: ContratoListado = {
  ...CONTRATO,
  id: 'c2',
  numero: 'TM-0002',
  estado: 'activa',
  saldo_vencido: '0.00',
  dias_mora: 0,
  fecha_renovacion: '2026-12-10',
  renovable: true,
}

const CUENTA = {
  contrato: { id: 'c1' },
  cuotas: [
    { id: 'q2', periodo: '2026-10', descripcion: 'Cuota de octubre', estado: 'pendiente', valor: '89000.00', valor_pagado: '0.00', fecha_vencimiento: '2026-10-05' },
    { id: 'q1', periodo: '2026-09', descripcion: 'Cuota de septiembre', estado: 'parcial', valor: '89000.00', valor_pagado: '9000.00', fecha_vencimiento: '2026-09-05' },
    { id: 'q0', periodo: '2026-08', descripcion: 'Cuota de agosto', estado: 'pagada', valor: '89000.00', valor_pagado: '89000.00', fecha_vencimiento: '2026-08-05' },
  ],
} as unknown as EstadoCuenta

const RUTA = '*/api/v1/cartera/contratos'
const pagina = (items: ContratoListado[]) => HttpResponse.json({ items, total: items.length, limit: 25, offset: 0 })

describe('CarteraPage', () => {
  beforeEach(() => {
    server.use(
      http.get(`${RUTA}/recuentos`, () => HttpResponse.json({ en_mora: 1, por_renovar: 1, todos: 4 })),
      http.get('*/api/v1/cartera/familias/:id/estado-cuenta', () => HttpResponse.json(CUENTA)),
    )
  })

  it('muestra el estado de carga', () => {
    server.use(http.get(RUTA, () => pagina([CONTRATO])))
    renderizar(<CarteraPage />)
    expect(screen.getByText(/cargando la cartera/i)).toBeInTheDocument()
  })

  it('abre en «Vencidas»: lo que debe cada familia, desde cuándo y su plan', async () => {
    const consultas: string[] = []
    server.use(
      http.get(RUTA, ({ request }) => {
        consultas.push(new URL(request.url).search)
        return pagina([CONTRATO])
      }),
    )
    renderizar(<CarteraPage />)
    const enlace = await screen.findByRole('link', { name: FAMILIA.titular_nombre })
    expect(enlace).toHaveAttribute('href', `/panel/familias/${FAMILIA.id}`)
    expect(consultas[0]).toContain('solo_mora=true')
    expect(screen.getByRole('button', { name: /^vencidas/i })).toHaveAttribute('aria-pressed', 'true')
    const fila = within(enlace.closest('tr')!)
    // Lo vencido con su importe y la palabra, no solo en rojo.
    expect(fila.getByText(/178\.000/)).toBeInTheDocument()
    expect(fila.getByText('hace 40 días')).toBeInTheDocument()
    expect(fila.getByText('Plan Esencial')).toBeInTheDocument()
    expect(fila.getByText('En mora')).toBeInTheDocument()
    expect(fila.getByText('al mes')).toBeInTheDocument()
    // Cada vista dice cuántos contratos tiene.
    expect(await screen.findByRole('button', { name: 'Todos 4' })).toBeInTheDocument()
  })

  it('registra un pago desde la fila con las cuotas abiertas de la familia', async () => {
    let pago: unknown
    server.use(
      http.get(RUTA, () => pagina([CONTRATO])),
      http.post('*/api/v1/cartera/pagos', async ({ request }) => {
        pago = await request.json()
        return HttpResponse.json({ id: 'p1' }, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<CarteraPage />)
    await user.click(await screen.findByRole('button', { name: `Registrar pago de ${FAMILIA.titular_nombre}` }))
    const ventana = await screen.findByRole('dialog', { name: `Registrar pago de ${FAMILIA.titular_nombre}` })
    // Solo las cuotas abiertas: la pagada no se ofrece.
    expect(within(ventana).getByRole('option', { name: /septiembre/ })).toBeInTheDocument()
    expect(within(ventana).queryByRole('option', { name: /agosto/ })).not.toBeInTheDocument()
    // Abre con la más antigua y lo que le falta, que es a la que se aplicaría.
    expect(within(ventana).getByLabelText('Cuota')).toHaveValue('q1')
    expect(within(ventana).getByLabelText('Valor (COP)')).toHaveValue(80000)
    await user.clear(within(ventana).getByLabelText('Valor (COP)'))
    await user.type(within(ventana).getByLabelText('Valor (COP)'), '89000')
    await user.type(within(ventana).getByLabelText('Referencia o comprobante'), 'TRF-881')
    await user.click(within(ventana).getByRole('button', { name: 'Registrar pago' }))
    await waitFor(() => expect(pago).toMatchObject({ familia_id: FAMILIA.id, valor: '89000', referencia: 'TRF-881', cuota_id: 'q1' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('en «Por renovar» Comercial renueva un año tras confirmarlo', async () => {
    const consultas: string[] = []
    let renovado = ''
    server.use(
      sesionDe('comercial'),
      http.get(RUTA, ({ request }) => {
        consultas.push(new URL(request.url).search)
        return pagina([POR_RENOVAR])
      }),
      http.post('*/api/v1/cartera/contratos/:id/renovar', ({ params }) => {
        renovado = String(params.id)
        return HttpResponse.json({ id: params.id })
      }),
    )
    const user = userEvent.setup()
    renderizar(<CarteraPage />)
    await user.click(await screen.findByRole('button', { name: /por renovar/i }))
    await waitFor(() => expect(consultas.some((c) => c.includes('por_renovar=true'))).toBe(true))
    const fila = within((await screen.findByText('· ya se puede renovar')).closest('tr')!)
    expect(fila.getByText('Al día')).toBeInTheDocument()
    // Sin deuda, no hay pago que registrar.
    expect(fila.queryByRole('button', { name: /registrar pago/i })).not.toBeInTheDocument()
    await user.click(fila.getByRole('button', { name: `Renovar el contrato de ${FAMILIA.titular_nombre}` }))
    const ventana = await screen.findByRole('dialog', { name: `Renovar el contrato de ${FAMILIA.titular_nombre}` })
    expect(ventana).toHaveTextContent('su vigencia se extiende un año')
    await user.click(within(ventana).getByRole('button', { name: 'Renovar un año' }))
    await waitFor(() => expect(renovado).toBe('c2'))
  })

  it('dice por qué la vista está vacía', async () => {
    server.use(http.get(RUTA, () => pagina([])))
    renderizar(<CarteraPage />, { ruta: '/panel/cartera?vista=por_renovar' })
    expect(await screen.findByText('Ningún contrato vence en los próximos 90 días.')).toBeInTheDocument()
  })

  it('busca en la vista elegida', async () => {
    const consultas: string[] = []
    server.use(
      http.get(RUTA, ({ request }) => {
        consultas.push(new URL(request.url).search)
        return pagina([])
      }),
    )
    const user = userEvent.setup()
    renderizar(<CarteraPage />, { ruta: '/panel/cartera?vista=todos' })
    // Con la sesión de Atención llegan las pestañas (contratos y pasarela): se busca después.
    await screen.findByRole('tab', { name: 'Contratos' })
    await user.type(await screen.findByRole('searchbox', { name: 'Buscar contratos' }), 'TM')
    await waitFor(() => expect(consultas.some((c) => c.includes('q=TM') && !c.includes('solo_mora'))).toBe(true))
    expect(await screen.findByText('Ningún contrato de esta vista coincide con la búsqueda.')).toBeInTheDocument()
  })

  it('muestra el error del servidor', async () => {
    server.use(http.get(RUTA, () => HttpResponse.json({ detail: 'Servicio no disponible' }, { status: 503 })))
    renderizar(<CarteraPage />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Servicio no disponible')
  })

  it('a quien no gestiona la cartera no le ofrece pagar ni renovar', async () => {
    server.use(
      http.get('*/api/v1/auth/me', () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'operaciones' })),
      http.get(RUTA, () => pagina([CONTRATO, POR_RENOVAR])),
    )
    renderizar(<CarteraPage />)
    expect(await screen.findAllByRole('link', { name: FAMILIA.titular_nombre })).toHaveLength(2)
    expect(screen.queryByRole('button', { name: /registrar pago|renovar el contrato/i })).not.toBeInTheDocument()
  })
})
