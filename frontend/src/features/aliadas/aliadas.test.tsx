import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { AliadasPage } from './AliadasPage'
import { MiClinicaPage } from './MiClinicaPage'
import { USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { ClinicaRead, RemisionRead } from '@/types'

const API = '*/api/v1'

const CLINICA: ClinicaRead = { id: 'cl1', nombre: 'Clínica Norte', ciudad: 'Bogota', activa: true, nit: '900123', telefono: '6011234' }

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
}

describe('AliadasPage', () => {
  it('lista las remisiones con su clínica y cobertura y permite anular', async () => {
    let motivo: unknown = null
    server.use(
      http.get(`${API}/aliadas`, () => HttpResponse.json([CLINICA])),
      http.get(`${API}/aliadas/remisiones`, () => HttpResponse.json([REMISION])),
      http.post(`${API}/aliadas/remisiones/r1/anulacion`, async ({ request }) => {
        motivo = await request.json()
        return HttpResponse.json({ ...REMISION, estado: 'anulada' })
      }),
    )
    const user = userEvent.setup()
    renderizar(<AliadasPage />)
    const fila = (await screen.findByRole('link', { name: 'REM7K2Q' })).closest('tr')!
    expect(within(fila).getByText(/80% hasta/)).toBeInTheDocument()
    expect(await within(fila).findByText('Clínica Norte')).toBeInTheDocument()
    await user.click(within(fila).getByRole('button', { name: 'Anular' }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Motivo'), 'Se atenderá a domicilio')
    await user.click(within(modal).getByRole('button', { name: 'Anular' }))
    await waitFor(() => expect(motivo).toEqual({ motivo: 'Se atenderá a domicilio' }))
  })

  it('muestra los convenios de la clínica elegida', async () => {
    server.use(
      http.get(`${API}/aliadas`, () => HttpResponse.json([CLINICA])),
      http.get(`${API}/aliadas/remisiones`, () => HttpResponse.json([])),
      http.get(`${API}/aliadas/cl1/convenios`, () =>
        HttpResponse.json([{ id: 'cv1', clinica_id: 'cl1', beneficio: 'Hospitalización', cobertura_pct: 70, tarifa: '150000.00', vigente_desde: '2026-01-01', activo: true }]),
      ),
    )
    const user = userEvent.setup()
    renderizar(<AliadasPage />)
    await user.click(await screen.findByRole('tab', { name: 'Clínicas y convenios' }))
    await user.click(await screen.findByRole('button', { name: /clínica norte/i }))
    expect(await screen.findByText('Hospitalización')).toBeInTheDocument()
  })

  it('la liquidación sólo la ve administración', async () => {
    server.use(
      http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'operaciones' })),
      http.get(`${API}/aliadas`, () => HttpResponse.json([])),
      http.get(`${API}/aliadas/remisiones`, () => HttpResponse.json([])),
    )
    renderizar(<AliadasPage />)
    await screen.findByRole('tab', { name: 'Remisiones' })
    await waitFor(() => expect(screen.queryByRole('tab', { name: 'Liquidación' })).not.toBeInTheDocument())
  })
})

describe('MiClinicaPage', () => {
  it('la clínica valida el código y reporta la atención', async () => {
    let reporte: unknown = null
    const vista = {
      codigo: 'REM7K2Q',
      estado: 'emitida',
      vigente: true,
      vence_en: '2026-11-10',
      titular: 'Ana Ruiz',
      documento_ultimos: '4050',
      mascota: { nombre: 'Luna', especie: 'canino', raza: null },
      motivo: 'Radiografía',
      beneficio: 'Radiografía',
      cobertura_pct: 80,
      tope_cubierto: null,
      valor_cubierto: null,
    }
    server.use(
      http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'aliada', nombre: 'Clínica Norte' })),
      http.get(`${API}/aliadas/mi-clinica/remisiones/REM7K2Q`, () => HttpResponse.json(vista)),
      http.post(`${API}/aliadas/mi-clinica/remisiones/REM7K2Q/atencion`, async ({ request }) => {
        reporte = await request.json()
        return HttpResponse.json({ ...vista, estado: 'utilizada', valor_cubierto: '96000.00' })
      }),
    )
    const user = userEvent.setup()
    renderizar(<MiClinicaPage />)
    await user.type(screen.getByLabelText('Código de la remisión'), 'rem7k2q')
    await user.click(screen.getByRole('button', { name: 'Validar' }))
    expect(await screen.findByText(/remisión vigente hasta/i)).toBeInTheDocument()
    expect(screen.getByText('…4050')).toBeInTheDocument()
    await user.type(screen.getByLabelText('Valor de la atención (COP)'), '120000')
    await user.type(screen.getByLabelText('Resumen clínico'), 'Rx de cadera sin hallazgos')
    await user.click(screen.getByRole('button', { name: 'Reportar atención' }))
    expect(await screen.findByText(/TIMU cubre/)).toBeInTheDocument()
    expect(reporte).toMatchObject({ valor_atencion: '120000', resumen: 'Rx de cadera sin hallazgos' })
  })

  it('avisa si el código no existe', async () => {
    server.use(
      http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'aliada' })),
      http.get(`${API}/aliadas/mi-clinica/remisiones/:codigo`, () => HttpResponse.json({ detail: 'Remision no encontrada' }, { status: 404 })),
    )
    const user = userEvent.setup()
    renderizar(<MiClinicaPage />)
    await user.type(screen.getByLabelText('Código de la remisión'), 'NOEXISTE')
    await user.click(screen.getByRole('button', { name: 'Validar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Remision no encontrada')
  })
})
