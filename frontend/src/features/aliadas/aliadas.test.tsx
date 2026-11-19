import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'

import { AliadasPage } from './AliadasPage'
import { sesionDe } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { ClinicaRead, RemisionRead } from '@/types'

const API = '*/api/v1'

const CLINICA: ClinicaRead = { id: 'cl1', nombre: 'Clínica Norte', ciudad: 'Bogotá', activa: true, nit: '900123', telefono: '6011234' }

const REMISION: RemisionRead = {
  id: 'r1',
  codigo: 'REM7K2Q',
  clinica_id: 'cl1',
  familia_id: 'f1',
  mascota_id: 'm1',
  servicio_id: 's1',
  motivo: 'Radiografía de cadera',
  beneficio_aplicado: 'Radiografía',
  cobertura_pct: 80,
  tope_cubierto: '200000.00',
  vence_en: '2026-11-10',
  estado: 'emitida',
  fecha_atencion: null,
  valor_atencion: null,
  valor_cubierto: null,
  created_at: '2026-10-24T10:00:00Z',
  vencida: false,
  titular: 'Ana Ruiz',
  mascota: 'Luna',
  clinica: 'Clínica Norte',
}

beforeEach(() => {
  server.use(http.get(`${API}/aliadas/remisiones/recuentos`, () => HttpResponse.json({ emitida: 1, utilizada: 0, anulada: 0, todas: 1 })))
})

describe('AliadasPage', () => {
  it('lista las remisiones con su clínica y cobertura y permite anular', async () => {
    let motivo: unknown = null
    server.use(
      sesionDe('atencion_cliente'),
      http.get(`${API}/aliadas`, () => HttpResponse.json([CLINICA])),
      http.get(`${API}/aliadas/remisiones`, () => HttpResponse.json([REMISION])),
      http.post(`${API}/aliadas/remisiones/r1/anulacion`, async ({ request }) => {
        motivo = await request.json()
        return HttpResponse.json({ ...REMISION, estado: 'anulada' })
      }),
    )
    const user = userEvent.setup()
    renderizar(<AliadasPage />)
    const fila = (await screen.findByRole('link', { name: 'Ana Ruiz · Luna' })).closest('tr')!
    expect(within(fila).getByText(/^80 %\shasta/)).toBeInTheDocument()
    expect(within(fila).getByText('Clínica Norte')).toBeInTheDocument()
    await user.click(within(fila).getByRole('button', { name: 'Anular la remisión REM7K2Q' }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Motivo'), 'Se atenderá a domicilio')
    await user.click(within(modal).getByRole('button', { name: 'Anular remisión' }))
    await waitFor(() => expect(motivo).toEqual({ motivo: 'Se atenderá a domicilio' }))
  })

  it('muestra los convenios de la clínica elegida', async () => {
    server.use(
      sesionDe('operaciones'),
      http.get(`${API}/aliadas`, () => HttpResponse.json([CLINICA])),
      http.get(`${API}/aliadas/remisiones`, () => HttpResponse.json([])),
      http.get(`${API}/aliadas/cl1/convenios`, () =>
        HttpResponse.json([{ id: 'cv1', clinica_id: 'cl1', beneficio: 'Hospitalización', cobertura_pct: 70, tarifa: '150000.00', vigente_desde: '2026-01-01', activo: true }]),
      ),
    )
    const user = userEvent.setup()
    renderizar(<AliadasPage />)
    await user.click(await screen.findByRole('tab', { name: 'Clínicas y convenios' }))
    await user.click(await screen.findByRole('link', { name: 'Clínica Norte' }))
    expect(await screen.findByText('Hospitalización')).toBeInTheDocument()
  })

  it('la liquidación no la ve Atención: es de Operaciones y Gerencia', async () => {
    server.use(
      sesionDe('atencion_cliente'),
      http.get(`${API}/aliadas`, () => HttpResponse.json([])),
      http.get(`${API}/aliadas/remisiones`, () => HttpResponse.json([])),
    )
    renderizar(<AliadasPage />)
    await screen.findByRole('tab', { name: 'Remisiones' })
    await waitFor(() => expect(screen.queryByRole('tab', { name: 'Liquidación' })).not.toBeInTheDocument())
  })
})
