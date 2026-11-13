import { fireEvent, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { PortalAgregarPeludo } from './AgregarPeludo'
import { USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const API = '*/api/v1'

const plan = (id: string, nombre: string, especies: string[]) => ({
  id,
  codigo: id,
  nombre,
  descripcion: null,
  especies,
  tarifas: [{ peludos: 1, valor: '40000.00' }],
  tarifas_periodicidad: [],
  beneficios: [],
})
const COTIZACION = {
  periodicidad: 'mensual',
  valor_periodo_actual: '40000.00',
  valor_periodo_nuevo: '70000.00',
  valor_ajuste: '20000.00',
  hasta: '2026-12-01',
  cuotas_adelantadas: 0,
}
const alta = (estado: string, estado_pago: string | null) => ({
  id: 'a1',
  nombre: 'Kira',
  especie: 'canino',
  plan_id: 'p-perro',
  valor_ajuste: '20000.00',
  valor_periodo_nuevo: '70000.00',
  estado,
  estado_pago,
  created_at: '2026-11-10T15:00:00Z',
})

let asignar: ReturnType<typeof vi.fn>

beforeEach(() => {
  asignar = vi.fn()
  vi.stubGlobal('location', { ...window.location, pathname: '/portal/mascotas/nueva', assign: asignar })
})
afterEach(() => vi.unstubAllGlobals())

function portal(altas: unknown[] = []) {
  const cotizaciones: unknown[] = []
  server.use(
    http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'familia', nombre: 'Ana Ruiz' })),
    http.get(`${API}/portal/peludos/altas`, () => HttpResponse.json(altas)),
    http.get(`${API}/portal/peludos/planes`, () =>
      HttpResponse.json([plan('p-perro', 'Mi Amigo Fiel', ['canino']), plan('p-gato', 'Colita Feliz', ['felino'])]),
    ),
    http.post(`${API}/portal/peludos/cotizacion`, async ({ request }) => {
      cotizaciones.push(await request.json())
      return HttpResponse.json(COTIZACION)
    }),
  )
  return cotizaciones
}

async function llenar(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText('Nombre'), 'Kira')
  await user.type(screen.getByLabelText('Raza (opcional)'), 'Criolla')
  fireEvent.change(screen.getByLabelText('Fecha de nacimiento (aproximada)'), { target: { value: '2023-01-10' } })
  await user.type(screen.getByLabelText('Peso en kg'), '8.5')
  await screen.findByRole('option', { name: 'Mi Amigo Fiel' })
  await user.selectOptions(screen.getByLabelText('Plan'), 'p-perro')
}

describe('Agregar un peludo desde el portal', () => {
  it('muestra el valor nuevo, lo que se paga hoy y lleva a la pasarela', async () => {
    const cotizaciones = portal()
    let enviado: unknown = null
    server.use(
      http.post(`${API}/portal/peludos`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(
          { alta_id: 'a1', valor: '20000.00', enlace_pago: 'https://checkout.wompi.co/p/?reference=ALT-1' },
          { status: 201 },
        )
      }),
    )
    const user = userEvent.setup()
    renderizar(<PortalAgregarPeludo />)
    // Solo los planes de la especie elegida.
    await screen.findByRole('option', { name: 'Mi Amigo Fiel' })
    expect(screen.queryByRole('option', { name: 'Colita Feliz' })).not.toBeInTheDocument()
    await llenar(user)
    const valor = await screen.findByRole('status', { name: 'Valor del peludo nuevo' })
    expect(valor).toHaveTextContent(/pasa de \$\s?40\.000 a \$\s?70\.000 al mes/)
    expect(valor).toHaveTextContent(/Hoy pagas \$\s?20\.000/)
    expect(cotizaciones).toEqual([{ especie: 'canino', plan_id: 'p-perro' }])
    await user.click(screen.getByRole('button', { name: /^pagar/i }))

    await waitFor(() => expect(asignar).toHaveBeenCalledWith('https://checkout.wompi.co/p/?reference=ALT-1'))
    expect(enviado).toEqual({
      nombre: 'Kira',
      especie: 'canino',
      raza: 'Criolla',
      fecha_nacimiento: '2023-01-10',
      peso_kg: 8.5,
      plan_id: 'p-perro',
    })
  })

  it('si la próxima cuota ya se emitió, explica que el pago también la cubre', async () => {
    portal()
    server.use(
      http.post(`${API}/portal/peludos/cotizacion`, () =>
        HttpResponse.json({ ...COTIZACION, valor_ajuste: '50000.00', cuotas_adelantadas: 1 }),
      ),
    )
    const user = userEvent.setup()
    renderizar(<PortalAgregarPeludo />)
    await llenar(user)
    const valor = await screen.findByRole('status', { name: 'Valor del peludo nuevo' })
    expect(valor).toHaveTextContent(/Hoy pagas \$\s?50\.000/)
    expect(valor).toHaveTextContent('la diferencia de la próxima cuota')
  })

  it('cambiar de especie obliga a elegir de nuevo el plan', async () => {
    portal()
    const user = userEvent.setup()
    renderizar(<PortalAgregarPeludo />)
    await llenar(user)
    await screen.findByRole('status', { name: 'Valor del peludo nuevo' })
    await user.selectOptions(screen.getByLabelText('Especie'), 'felino')
    expect(screen.getByLabelText('Plan')).toHaveValue('')
    expect(screen.getByRole('option', { name: 'Colita Feliz' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^pagar/i })).toBeDisabled()
  })

  it('con la afiliación en mora explica por qué no se puede', async () => {
    portal()
    server.use(
      http.post(`${API}/portal/peludos/cotizacion`, () =>
        HttpResponse.json({ detail: 'Tu afiliacion tiene pagos pendientes: ponte al dia para agregar un peludo' }, { status: 422 }),
      ),
    )
    const user = userEvent.setup()
    renderizar(<PortalAgregarPeludo />)
    await llenar(user)
    expect(await screen.findByRole('alert')).toHaveTextContent('ponte al dia')
    expect(screen.getByRole('button', { name: /^pagar/i })).toBeDisabled()
  })

  it('mientras la pasarela confirma no ofrece pagar otra vez', async () => {
    portal([alta('pendiente_pago', 'pendiente')])
    renderizar(<PortalAgregarPeludo />)
    expect(await screen.findByRole('status')).toHaveTextContent('esperando la confirmación del pago para afiliar a Kira')
    expect(screen.queryByLabelText('Nombre')).not.toBeInTheDocument()
  })

  it('con el pago rechazado deja intentarlo de nuevo', async () => {
    portal([alta('pendiente_pago', 'rechazado')])
    renderizar(<PortalAgregarPeludo />)
    expect(await screen.findByRole('alert')).toHaveTextContent('no aprobó el pago para afiliar a Kira')
    expect(screen.getByLabelText('Nombre')).toBeInTheDocument()
  })

  it('confirma cuando el peludo ya quedó afiliado', async () => {
    portal([alta('completada', 'aprobado')])
    renderizar(<PortalAgregarPeludo />)
    expect(await screen.findByText(/Kira ya está afiliado/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Ver tus peludos' })).toHaveAttribute('href', '/portal/mascotas')
  })

  it('si el pago entró pero el equipo debe terminarlo, lo dice', async () => {
    portal([alta('error', 'aprobado')])
    renderizar(<PortalAgregarPeludo />)
    expect(await screen.findByText(/Un asesor termina su afiliación/)).toBeInTheDocument()
  })
})
