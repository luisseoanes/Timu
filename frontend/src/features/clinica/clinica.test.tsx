import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { ClinicaPage } from './ClinicaPage'
import { EntradaPage } from './EntradaPage'
import { HistoriaMascotaPage } from './HistoriaMascotaPage'
import type { EntradaHistoria } from './api'
import { FAMILIA, USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const API = '*/api/v1'
const LUNA = FAMILIA.mascotas![0]!
const comoMedico = http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'medico' }))

const ENTRADA: EntradaHistoria = {
  id: 'h1',
  mascota_id: LUNA.id,
  profesional_id: USUARIO_ADMIN.id,
  tipo: 'domiciliaria',
  fecha: '2026-10-04',
  motivo: 'Rasca el oído',
  diagnostico: 'Otitis externa',
  tratamiento: 'Gotas cada 12 horas',
  estado: 'borrador',
}

describe('Historia clínica de una mascota', () => {
  function abrir() {
    return renderizar(
      <Routes>
        <Route path="/clinica/mascotas/:mascotaId" element={<HistoriaMascotaPage />} />
        <Route path="/clinica/historias/:id" element={<p>Consulta abierta</p>} />
      </Routes>,
      { ruta: `/clinica/mascotas/${LUNA.id}` },
    )
  }

  it('muestra la línea de tiempo con estado y diagnóstico', async () => {
    server.use(
      http.get(`${API}/mascotas/:id`, () => HttpResponse.json(LUNA)),
      http.get(`${API}/clinica/mascotas/:id/historia`, () => HttpResponse.json([{ ...ENTRADA, estado: 'firmada' }])),
    )
    abrir()
    expect(await screen.findByRole('heading', { name: 'Historia de Luna' })).toBeInTheDocument()
    expect(await screen.findByText('Diagnóstico: Otitis externa')).toBeInTheDocument()
    expect(screen.getByText('Firmada')).toBeInTheDocument()
  })

  it('el resto del equipo ve el resumen y no puede crear consultas', async () => {
    server.use(
      http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'operaciones' })),
      http.get(`${API}/mascotas/:id`, () => HttpResponse.json(LUNA)),
      http.get(`${API}/clinica/mascotas/:id/historia`, () => HttpResponse.json([])),
    )
    abrir()
    expect(await screen.findByText(/tu perfil ve el resumen/i)).toBeInTheDocument()
    expect(screen.getByText('Esta mascota todavía no tiene consultas registradas.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /nueva consulta/i })).not.toBeInTheDocument()
  })

  it('el médico registra una consulta con plantilla y la abre', async () => {
    let enviado: Record<string, unknown> | null = null
    server.use(
      comoMedico,
      http.get(`${API}/mascotas/:id`, () => HttpResponse.json(LUNA)),
      http.get(`${API}/clinica/mascotas/:id/historia`, () => HttpResponse.json([])),
      http.get(`${API}/clinica/plantillas`, () =>
        HttpResponse.json([{ codigo: 'otitis', nombre: 'Otitis', tipo_servicio_codigo: null, campos: { tratamiento: 'Limpieza ótica' }, activa: true }]),
      ),
      http.post(`${API}/clinica/historias`, async ({ request }) => {
        enviado = (await request.json()) as Record<string, unknown>
        return HttpResponse.json(ENTRADA, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    abrir()
    await user.click(await screen.findByRole('button', { name: /nueva consulta/i }))
    const modal = await screen.findByRole('dialog')
    await waitFor(() => expect(within(modal).getByRole('option', { name: 'Otitis' })).toBeInTheDocument())
    await user.selectOptions(within(modal).getByLabelText('Plantilla'), 'otitis')
    expect(within(modal).getByLabelText('Tratamiento')).toHaveValue('Limpieza ótica')
    await user.type(within(modal).getByLabelText('Motivo de consulta'), 'Rasca el oído')
    await user.click(within(modal).getByRole('button', { name: 'Guardar borrador' }))
    expect(await screen.findByText('Consulta abierta')).toBeInTheDocument()
    expect(enviado).toMatchObject({ mascota_id: LUNA.id, motivo: 'Rasca el oído', tratamiento: 'Limpieza ótica', plantilla_codigo: 'otitis' })
  })
})

describe('Consulta de la historia', () => {
  function abrir() {
    return renderizar(
      <Routes>
        <Route path="/clinica/historias/:id" element={<EntradaPage />} />
      </Routes>,
      { ruta: '/clinica/historias/h1' },
    )
  }

  it('el médico firma un borrador', async () => {
    let firmada = false
    server.use(
      comoMedico,
      http.get(`${API}/clinica/historias/h1`, () => HttpResponse.json(ENTRADA)),
      http.get(`${API}/clinica/historias/h1/adjuntos`, () => HttpResponse.json([])),
      http.post(`${API}/clinica/historias/h1/firma`, () => {
        firmada = true
        return HttpResponse.json({ ...ENTRADA, estado: 'firmada' })
      }),
    )
    const user = userEvent.setup()
    abrir()
    expect(await screen.findByText('Gotas cada 12 horas')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Firmar consulta' }))
    await waitFor(() => expect(firmada).toBe(true))
  })

  it('una consulta firmada se corrige, no se edita', async () => {
    server.use(
      comoMedico,
      http.get(`${API}/clinica/historias/h1`, () => HttpResponse.json({ ...ENTRADA, estado: 'firmada', firmada_en: '2026-10-04T15:00:00Z' })),
      http.get(`${API}/clinica/historias/h1/adjuntos`, () => HttpResponse.json([])),
    )
    abrir()
    expect(await screen.findByRole('button', { name: 'Corregir' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /editar/i })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Emitir fórmula' })).toBeInTheDocument()
  })

  it('emite una fórmula con sus medicamentos', async () => {
    let enviado: unknown = null
    server.use(
      comoMedico,
      http.get(`${API}/clinica/historias/h1`, () => HttpResponse.json({ ...ENTRADA, estado: 'firmada' })),
      http.get(`${API}/clinica/historias/h1/adjuntos`, () => HttpResponse.json([])),
      http.post(`${API}/clinica/historias/h1/formulas`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ id: 'f1', url: 'https://s3/formula.pdf' })
      }),
    )
    const user = userEvent.setup()
    abrir()
    await user.click(await screen.findByRole('button', { name: 'Emitir fórmula' }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Medicamento'), 'Otomax')
    await user.type(within(modal).getByLabelText('Dosis'), '4 gotas')
    await user.click(within(modal).getByRole('button', { name: 'Emitir fórmula' }))
    expect(await within(modal).findByRole('link', { name: 'Abrir PDF' })).toHaveAttribute('href', 'https://s3/formula.pdf')
    expect(enviado).toEqual({ items: [{ medicamento: 'Otomax', dosis: '4 gotas' }] })
  })
})

describe('Atención virtual', () => {
  it('el médico responde con una respuesta aprobada y sus variables', async () => {
    let enviado: unknown = null
    server.use(
      comoMedico,
      http.get(`${API}/mascotas/:id`, () => HttpResponse.json(LUNA)),
      http.get(`${API}/clinica/virtual/cola`, () =>
        HttpResponse.json([
          {
            id: 'v1',
            familia_id: FAMILIA.id,
            mascota_id: LUNA.id,
            canal: 'whatsapp',
            motivo: '¿Cómo cambio el concentrado?',
            estado: 'en_atencion',
            prioridad: 'baja',
            asignada_a_id: USUARIO_ADMIN.id,
            respuesta: null,
            historia_id: null,
            borrador_ia: { borrador: 'Cambio gradual en 7 días.', senales_alarma: [], recomendar_presencial: false },
            created_at: '2026-10-24T13:00:00Z',
          },
        ]),
      ),
      http.get(`${API}/clinica/respuestas-virtuales`, () =>
        HttpResponse.json([
          { codigo: 'alimento', titulo: 'Cambio de alimento', cuerpo: 'Para {{1}} haz el cambio en 7 días.', variables: ['mascota'], estado: 'aprobada' },
        ]),
      ),
      http.post(`${API}/clinica/virtual/v1/respuesta`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({})
      }),
    )
    const user = userEvent.setup()
    renderizar(<ClinicaPage />)
    await user.click(await screen.findByRole('tab', { name: 'Atención virtual' }))
    await user.click(await screen.findByRole('button', { name: 'Atender' }))
    const modal = await screen.findByRole('dialog')
    expect(within(modal).getByText('Cambio gradual en 7 días.')).toBeInTheDocument()
    await waitFor(() => expect(within(modal).getByRole('option', { name: 'Cambio de alimento' })).toBeInTheDocument())
    await user.selectOptions(within(modal).getByLabelText('Respuesta aprobada'), 'alimento')
    await user.type(within(modal).getByLabelText('mascota'), 'Luna')
    expect(within(modal).getByText('Para Luna haz el cambio en 7 días.')).toBeInTheDocument()
    await user.click(within(modal).getByRole('button', { name: 'Enviar respuesta' }))
    await waitFor(() => expect(enviado).toEqual({ respuesta_codigo: 'alimento', variables: ['Luna'] }))
  })

  it('sin permisos clínicos sólo aparece la búsqueda de historias', async () => {
    server.use(http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'comercial' })))
    renderizar(<ClinicaPage />)
    expect(await screen.findByRole('tab', { name: 'Historia clínica' })).toBeInTheDocument()
    await waitFor(() => expect(screen.queryByRole('tab', { name: 'Atención virtual' })).not.toBeInTheDocument())
  })
})
