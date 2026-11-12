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

/** La historia de Luna y sus rutas: la de la mascota, la de una consulta y la placa de llegada. */
function abrir(ruta: string, historia: EntradaHistoria[] = []) {
  server.use(
    http.get(`${API}/mascotas/:id`, () => HttpResponse.json(LUNA)),
    http.get(`${API}/clinica/mascotas/:id/historia`, () => HttpResponse.json(historia)),
  )
  renderizar(
    <Routes>
      <Route path="/clinica/mascotas/:mascotaId" element={<HistoriaMascotaPage />} />
      <Route path="/clinica/historias/:id" element={<EntradaPage />} />
    </Routes>,
    { ruta },
  )
  return userEvent.setup()
}

describe('Historia clínica de una mascota', () => {
  it('muestra la mascota y sus consultas con estado y diagnóstico', async () => {
    abrir(`/clinica/mascotas/${LUNA.id}`, [{ ...ENTRADA, estado: 'firmada' }])
    expect(await screen.findByRole('heading', { name: 'Luna' })).toBeInTheDocument()
    expect(await screen.findByText('Diagnóstico: Otitis externa')).toBeInTheDocument()
    expect(screen.getByText('Firmada')).toBeInTheDocument()
    expect(screen.getByText(/Elige una consulta para leerla/)).toBeInTheDocument()
  })

  it('el resto del equipo ve el resumen y no puede crear consultas', async () => {
    server.use(http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'operaciones' })))
    abrir(`/clinica/mascotas/${LUNA.id}`)
    expect(await screen.findByText(/tu perfil ve el resumen/i)).toBeInTheDocument()
    expect(screen.getByText('Esta mascota todavía no tiene consultas registradas.')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /nueva consulta/i })).not.toBeInTheDocument()
  })

  it('una consulta nueva empieza con la plantilla y nace al dejar el motivo', async () => {
    let enviado: Record<string, unknown> | null = null
    server.use(
      comoMedico,
      http.get(`${API}/clinica/plantillas`, () =>
        HttpResponse.json([{ codigo: 'otitis', nombre: 'Otitis', tipo_servicio_codigo: null, campos: { tratamiento: 'Limpieza ótica' }, activa: true }]),
      ),
      http.post(`${API}/clinica/historias`, async ({ request }) => {
        enviado = (await request.json()) as Record<string, unknown>
        return HttpResponse.json({ ...ENTRADA, diagnostico: null, tratamiento: 'Limpieza ótica' }, { status: 201 })
      }),
      http.get(`${API}/clinica/historias/h1`, () => HttpResponse.json({ ...ENTRADA, diagnostico: null, tratamiento: 'Limpieza ótica' })),
      http.get(`${API}/clinica/historias/h1/adjuntos`, () => HttpResponse.json([])),
    )
    const user = abrir(`/clinica/mascotas/${LUNA.id}?nueva=1`)
    const consulta = await screen.findByRole('region', { name: 'Consulta de Luna' })
    await user.selectOptions(await within(consulta).findByLabelText('Plantilla'), 'otitis')
    // Sin motivo no se sigue: la historia lo exige para guardar.
    await user.click(within(consulta).getByRole('button', { name: 'Siguiente: anamnesis' }))
    expect(await within(consulta).findByRole('alert')).toHaveTextContent('Escribe el motivo para seguir')
    expect(enviado).toBeNull()
    await user.type(within(consulta).getByRole('textbox', { name: 'Motivo de consulta' }), 'Rasca el oído')
    await user.click(within(consulta).getByRole('button', { name: 'Siguiente: anamnesis' }))
    await waitFor(() =>
      expect(enviado).toMatchObject({ mascota_id: LUNA.id, motivo: 'Rasca el oído', tratamiento: 'Limpieza ótica', plantilla_codigo: 'otitis', tipo: 'presencial' }),
    )
    // Nacida la consulta, pasa a su dirección y sigue en el apartado al que se iba.
    expect(await screen.findByRole('heading', { name: 'Anamnesis' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Anamnesis, sin escribir' })).toHaveAttribute('aria-current', 'step')
  })
})

describe('La consulta de una visita', () => {
  const VISITA = `/clinica/mascotas/${LUNA.id}?servicio=s1`

  it('sin consulta todavía, empieza una domiciliaria enlazada al servicio', async () => {
    let enviado: Record<string, unknown> | null = null
    server.use(
      comoMedico,
      http.post(`${API}/clinica/historias`, async ({ request }) => {
        enviado = (await request.json()) as Record<string, unknown>
        return HttpResponse.json({ ...ENTRADA, servicio_id: 's1', diagnostico: null, tratamiento: null }, { status: 201 })
      }),
      http.get(`${API}/clinica/historias/h1/adjuntos`, () => HttpResponse.json([])),
    )
    const user = abrir(VISITA)
    expect(await screen.findByText('De la visita de hoy')).toBeInTheDocument()
    // En el celular la historia no está al lado: la consulta dice a quién se atiende.
    const consulta = screen.getByRole('region', { name: 'Consulta de Luna' })
    expect(await within(consulta).findByText('Luna · Ana Ruiz')).toBeInTheDocument()
    expect(within(consulta).getByText('perro')).toBeInTheDocument()
    await user.type(screen.getByRole('textbox', { name: 'Motivo de consulta' }), 'Vómito desde ayer')
    await user.click(screen.getByRole('button', { name: 'Siguiente: anamnesis' }))
    await waitFor(() => expect(enviado).toMatchObject({ servicio_id: 's1', tipo: 'domiciliaria', motivo: 'Vómito desde ayer' }))
    expect(await screen.findByRole('heading', { name: 'Anamnesis' })).toBeInTheDocument()
  })

  it('continúa el borrador de la visita y, para firmarla, pide el tratamiento', async () => {
    let firmada = false
    server.use(
      comoMedico,
      http.get(`${API}/clinica/historias/h1/adjuntos`, () => HttpResponse.json([])),
      http.post(`${API}/clinica/historias/h1/firma`, () => {
        firmada = true
        return HttpResponse.json({ ...ENTRADA, estado: 'firmada' })
      }),
    )
    const user = abrir(VISITA, [{ ...ENTRADA, servicio_id: 's1', tratamiento: null, anamnesis: 'Rasca hace una semana', examen_fisico: 'Eritema' }])
    // Abre en el primer apartado vacío: el tratamiento.
    expect(await screen.findByRole('heading', { name: 'Tratamiento' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Firmar consulta' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Para firmar falta: Tratamiento. Sin tratamiento, la visita no se puede terminar.')
    expect(firmada).toBe(false)
  })

  it('al firmarla, ofrece volver a la ruta para terminar la visita', async () => {
    let cambios: unknown = null
    let firmada = false
    const borrador = { ...ENTRADA, servicio_id: 's1', tratamiento: null, anamnesis: 'Rasca', examen_fisico: 'Eritema' }
    server.use(
      comoMedico,
      http.get(`${API}/clinica/historias/h1/adjuntos`, () => HttpResponse.json([])),
      http.patch(`${API}/clinica/historias/h1`, async ({ request }) => {
        cambios = await request.json()
        return HttpResponse.json({ ...borrador, tratamiento: 'Gotas' })
      }),
      http.post(`${API}/clinica/historias/h1/firma`, () => {
        firmada = true
        return HttpResponse.json({ ...borrador, tratamiento: 'Gotas', estado: 'firmada' })
      }),
      http.get(`${API}/clinica/historias/h1`, () =>
        HttpResponse.json(firmada ? { ...borrador, tratamiento: 'Gotas', estado: 'firmada', firmada_en: '2026-10-04T16:00:00Z' } : borrador),
      ),
    )
    const user = abrir(VISITA, [borrador])
    await user.type(await screen.findByRole('textbox', { name: 'Tratamiento' }), ' Gotas ')
    await user.click(screen.getByRole('button', { name: 'Firmar consulta' }))
    await waitFor(() => expect(firmada).toBe(true))
    expect(cambios).toEqual({ tratamiento: 'Gotas' })
    expect(await screen.findByText(/Los pasos del servicio quedaron registrados/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Volver a la ruta' })).toHaveAttribute('href', '/rutas')
  })

  it('si ya está firmada, la enseña en lugar de empezar otra', async () => {
    server.use(comoMedico, http.get(`${API}/clinica/historias/h1/adjuntos`, () => HttpResponse.json([])))
    abrir(VISITA, [{ ...ENTRADA, servicio_id: 's1', estado: 'firmada', firmada_en: '2026-10-04T16:00:00Z' }])
    expect(await screen.findByRole('heading', { name: 'Consulta del 04/10/2026' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Corregir' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Firmar consulta' })).not.toBeInTheDocument()
  })
})

describe('Consulta de la historia', () => {
  function conConsulta(entrada: Partial<EntradaHistoria>) {
    server.use(
      comoMedico,
      http.get(`${API}/clinica/historias/h1`, () => HttpResponse.json({ ...ENTRADA, ...entrada })),
      http.get(`${API}/clinica/historias/h1/adjuntos`, () => HttpResponse.json([])),
    )
    return abrir('/clinica/historias/h1', [{ ...ENTRADA, ...entrada }])
  }

  it('el médico firma su borrador desde el último apartado', async () => {
    let firmada = false
    server.use(
      http.post(`${API}/clinica/historias/h1/firma`, () => {
        firmada = true
        return HttpResponse.json({ ...ENTRADA, estado: 'firmada' })
      }),
    )
    const user = conConsulta({})
    await user.click(await screen.findByRole('button', { name: 'Tratamiento, escrito' }))
    expect(screen.getByRole('textbox', { name: 'Tratamiento' })).toHaveValue('Gotas cada 12 horas')
    await user.click(screen.getByRole('button', { name: 'Firmar consulta' }))
    await waitFor(() => expect(firmada).toBe(true))
  })

  it('una consulta firmada se corrige, no se edita', async () => {
    conConsulta({ estado: 'firmada', firmada_en: '2026-10-04T15:00:00Z' })
    expect(await screen.findByRole('button', { name: 'Corregir' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Firmar consulta' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Emitir fórmula' })).toBeInTheDocument()
    expect(screen.getByText('Gotas cada 12 horas')).toBeInTheDocument()
  })

  it('el borrador de otro profesional se lee, no se escribe', async () => {
    conConsulta({ profesional_id: 'otro' })
    expect(await screen.findByText(/Borrador de otro profesional/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Firmar consulta' })).not.toBeInTheDocument()
  })

  it('emite una fórmula con sus medicamentos', async () => {
    let enviado: unknown = null
    server.use(
      http.post(`${API}/clinica/historias/h1/formulas`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ id: 'f1', url: 'https://s3/formula.pdf' })
      }),
    )
    const user = conConsulta({ estado: 'firmada' })
    await user.click(await screen.findByRole('button', { name: 'Emitir fórmula' }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Medicamento'), 'Otomax')
    await user.type(within(modal).getByLabelText('Dosis'), '4 gotas')
    await user.click(within(modal).getByRole('button', { name: 'Emitir fórmula' }))
    expect(await within(modal).findByRole('link', { name: 'Abrir PDF' })).toHaveAttribute('href', 'https://s3/formula.pdf')
    expect(enviado).toEqual({ items: [{ medicamento: 'Otomax', dosis: '4 gotas' }] })
  })
})

describe('El trabajo pendiente del médico', () => {
  const PARADA = {
    id: 'p1',
    servicio_id: 's1',
    orden: 1,
    estado: 'en_sitio',
    latitud: null,
    longitud: null,
    llegada_estimada: '2026-10-24T15:20:00Z',
    llegada_en: null,
    salida_en: null,
    nota: null,
    motivo_omision: null,
    tipo_codigo: 'consulta_domiciliaria',
    observaciones: null,
    ventana_desde: null,
    ventana_hasta: null,
    familia: { id: FAMILIA.id, titular_nombre: 'Ana Ruiz', telefono: '+573001112233', direccion: null, complemento: null, barrio: null },
    mascota: { id: LUNA.id, nombre: 'Luna', especie: 'perro', fecha_nacimiento: null, peso_kg: null },
  }

  it('abre en las mascotas de su ruta de hoy y sus consultas sin firmar', async () => {
    server.use(
      comoMedico,
      http.get(`${API}/mascotas/:id`, () => HttpResponse.json(LUNA)),
      http.get(`${API}/rutas`, () =>
        HttpResponse.json([
          { id: 'r1', fecha: '2026-10-24', ciudad: 'Bogota', responsable_id: USUARIO_ADMIN.id, estado: 'en_curso', distancia_km: null, duracion_min: null, inicio_real: null, fin_real: null, paradas: [PARADA, { ...PARADA, id: 'p2', servicio_id: 's2', mascota: null }] },
        ]),
      ),
      http.get(`${API}/clinica/borradores`, () => HttpResponse.json([ENTRADA])),
    )
    renderizar(<ClinicaPage />)
    const visitas = await screen.findByRole('region', { name: 'En tu ruta' })
    // Solo las visitas con mascota abren una consulta.
    const enlaces = await within(visitas).findAllByRole('link')
    expect(enlaces).toHaveLength(1)
    expect(enlaces[0]).toHaveTextContent('Luna · Ana Ruiz')
    expect(enlaces[0]).toHaveAttribute('href', `/clinica/mascotas/${LUNA.id}?servicio=s1`)
    const borradores = screen.getByRole('region', { name: 'Consultas sin firmar' })
    expect(await within(borradores).findByRole('link', { name: 'Luna · 04/10/2026' })).toHaveAttribute('href', '/clinica/historias/h1')
    expect(within(borradores).getByText('Rasca el oído')).toBeInTheDocument()
  })

  it('sin ruta ni borradores lo dice, y el buscador sigue debajo', async () => {
    server.use(comoMedico)
    renderizar(<ClinicaPage />)
    expect(await screen.findByText('No tienes visitas en la ruta de hoy.')).toBeInTheDocument()
    expect(await screen.findByText('No tienes consultas sin firmar.')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Abrir una historia clínica' })).toBeInTheDocument()
  })

  it('administración no ve el trabajo pendiente: abre con el buscador', async () => {
    renderizar(<ClinicaPage />)
    expect(await screen.findByRole('heading', { name: 'Abrir una historia clínica' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Tu trabajo de hoy' })).not.toBeInTheDocument()
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
    const atender = await screen.findByRole('button', { name: 'Atender' })
    // Una por fila: ninguna es la acción verde de la vista.
    expect(atender).toHaveClass('btn-suave')
    await user.click(atender)
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
