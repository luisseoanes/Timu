import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { EntradaPage } from './EntradaPage'
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

const ADJUNTO = {
  id: 'a1',
  historia_id: 'h1',
  nombre_archivo: 'citologia.pdf',
  tipo_mime: 'application/pdf',
  descripcion: 'Citología del oído',
  created_at: '2026-10-04T15:00:00Z',
}

function abrir(entrada: Partial<EntradaHistoria> = {}, { adjuntos = [] as unknown[], medico = true } = {}) {
  server.use(
    http.get(`${API}/clinica/historias/h1`, () => HttpResponse.json({ ...ENTRADA, ...entrada })),
    http.get(`${API}/clinica/historias/h1/adjuntos`, () => HttpResponse.json(adjuntos)),
  )
  if (medico) server.use(comoMedico)
  renderizar(
    <Routes>
      <Route path="/clinica/historias/:id" element={<EntradaPage />} />
    </Routes>,
    { ruta: '/clinica/historias/h1' },
  )
  return userEvent.setup()
}

afterEach(() => vi.restoreAllMocks())

describe('consulta en borrador', () => {
  it('el médico la edita y guarda solo los campos clínicos, sin espacios sobrantes', async () => {
    let enviado: unknown = null
    server.use(
      http.patch(`${API}/clinica/historias/h1`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ ...ENTRADA, diagnostico: 'Otitis bilateral' })
      }),
    )
    const user = abrir()
    await user.click(await screen.findByRole('button', { name: /editar/i }))
    const diagnostico = screen.getByLabelText('Diagnóstico')
    await user.clear(diagnostico)
    await user.type(diagnostico, '  Otitis bilateral ')
    await user.click(screen.getByRole('button', { name: 'Guardar cambios' }))
    await waitFor(() =>
      expect(enviado).toEqual({
        motivo: 'Rasca el oído',
        anamnesis: '',
        examen_fisico: '',
        diagnostico: 'Otitis bilateral',
        tratamiento: 'Gotas cada 12 horas',
        notas_internas: '',
      }),
    )
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Guardar cambios' })).not.toBeInTheDocument())
  })

  it('cancelar la edición vuelve a la lectura sin guardar', async () => {
    const user = abrir()
    await user.click(await screen.findByRole('button', { name: /editar/i }))
    await user.click(screen.getByRole('button', { name: 'Cancelar' }))
    expect(screen.getByText('Gotas cada 12 horas')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Firmar consulta' })).toBeInTheDocument()
  })

  it('explica por qué no se pudo guardar', async () => {
    server.use(http.patch(`${API}/clinica/historias/h1`, () => HttpResponse.json({ detail: 'Solo edita quien la abrió' }, { status: 403 })))
    const user = abrir()
    await user.click(await screen.findByRole('button', { name: /editar/i }))
    await user.click(screen.getByRole('button', { name: 'Guardar cambios' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Solo edita quien la abrió')
  })

  it('explica por qué no se pudo firmar', async () => {
    server.use(http.post(`${API}/clinica/historias/h1/firma`, () => HttpResponse.json({ detail: 'Falta el diagnóstico' }, { status: 422 })))
    const user = abrir()
    await user.click(await screen.findByRole('button', { name: 'Firmar consulta' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Falta el diagnóstico')
  })

  it('el resto del equipo la lee pero no la edita, firma ni adjunta', async () => {
    abrir({}, { medico: false })
    expect(await screen.findByText('Otitis externa')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /editar/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Firmar consulta' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /adjuntar/i })).not.toBeInTheDocument()
  })

  it('avisa si la consulta no existe', async () => {
    server.use(http.get(`${API}/clinica/historias/h1`, () => HttpResponse.json({ detail: 'No encontrada' }, { status: 404 })))
    renderizar(
      <Routes>
        <Route path="/clinica/historias/:id" element={<EntradaPage />} />
      </Routes>,
      { ruta: '/clinica/historias/h1' },
    )
    expect(await screen.findByRole('alert')).toHaveTextContent('No fue posible cargar la consulta. No encontrada')
  })
})

describe('consulta firmada', () => {
  const FIRMADA = { estado: 'firmada', firmada_en: '2026-10-04T16:00:00Z', version: 2 }

  it('muestra la versión y la fecha de firma', async () => {
    abrir(FIRMADA)
    expect(await screen.findByText('Versión 2')).toBeInTheDocument()
    expect(screen.getByText(/Ya no se edita: los cambios van como corrección/)).toBeInTheDocument()
  })

  it('la corrección crea una versión nueva y lleva a ella', async () => {
    let enviado: unknown = null
    server.use(
      http.post(`${API}/clinica/historias/h1/correccion`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ ...ENTRADA, id: 'h2', version: 3 }, { status: 201 })
      }),
      http.get(`${API}/clinica/historias/h2`, () => HttpResponse.json({ ...ENTRADA, id: 'h2', motivo: 'Versión corregida' })),
      http.get(`${API}/clinica/historias/h2/adjuntos`, () => HttpResponse.json([])),
    )
    const user = abrir(FIRMADA)
    await user.click(await screen.findByRole('button', { name: 'Corregir' }))
    const modal = await screen.findByRole('dialog')
    const tratamiento = within(modal).getByLabelText('Tratamiento')
    await user.clear(tratamiento)
    await user.type(tratamiento, 'Gotas cada 8 horas')
    await user.click(within(modal).getByRole('button', { name: 'Guardar corrección' }))
    await waitFor(() => expect(enviado).toMatchObject({ tratamiento: 'Gotas cada 8 horas', motivo: 'Rasca el oído' }))
    expect(await screen.findByText('Versión corregida')).toBeInTheDocument()
  })

  it('explica por qué no se pudo corregir', async () => {
    server.use(
      http.post(`${API}/clinica/historias/h1/correccion`, () => HttpResponse.json({ detail: 'Ya fue corregida' }, { status: 409 })),
    )
    const user = abrir(FIRMADA)
    await user.click(await screen.findByRole('button', { name: 'Corregir' }))
    const modal = await screen.findByRole('dialog')
    await user.click(within(modal).getByRole('button', { name: 'Guardar corrección' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('Ya fue corregida')
  })
})

describe('adjuntos', () => {
  it('abre un adjunto con su URL firmada en otra pestaña', async () => {
    const abrirVentana = vi.spyOn(window, 'open').mockReturnValue(null)
    server.use(http.get(`${API}/clinica/adjuntos/a1/url`, () => HttpResponse.json({ url: 'https://s3/citologia.pdf?firma=1' })))
    const user = abrir({}, { adjuntos: [ADJUNTO, { ...ADJUNTO, id: 'a2', nombre_archivo: 'foto.png', descripcion: null }] })
    expect(await screen.findByText('Citología del oído')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /citologia\.pdf/ }))
    await waitFor(() => expect(abrirVentana).toHaveBeenCalledWith('https://s3/citologia.pdf?firma=1', '_blank', 'noopener'))
  })

  it('explica por qué no se pudo abrir un adjunto', async () => {
    server.use(http.get(`${API}/clinica/adjuntos/a1/url`, () => HttpResponse.json({ detail: 'Adjunto no disponible' }, { status: 404 })))
    const user = abrir({}, { adjuntos: [ADJUNTO] })
    await user.click(await screen.findByRole('button', { name: /citologia\.pdf/ }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Adjunto no disponible')
  })

  it('sin adjuntos lo dice', async () => {
    abrir()
    expect(await screen.findByText('Sin exámenes ni imágenes adjuntas.')).toBeInTheDocument()
  })

  it('sube un archivo con su descripción y deja el formulario limpio', async () => {
    // jsdom y el parser multipart de undici no se entienden con los File, y jsdom serializa el
    // fichero como un Blob anónimo (filename="blob", sin contenido). Se mira el cuerpo crudo:
    // que viaja la parte `archivo` con su tipo y la descripción ya recortada.
    let cuerpo = ''
    server.use(
      http.post(`${API}/clinica/historias/h1/adjuntos`, async ({ request }) => {
        expect(request.headers.get('content-type')).toMatch(/^multipart\/form-data; boundary=/)
        cuerpo = await request.text()
        return HttpResponse.json(ADJUNTO, { status: 201 })
      }),
    )
    const user = abrir()
    const adjuntar = await screen.findByRole('button', { name: /adjuntar/i })
    expect(adjuntar).toBeDisabled()
    await user.upload(screen.getByLabelText('Archivo (JPG, PNG, WEBP o PDF)'), new File(['%PDF'], 'citologia.pdf', { type: 'application/pdf' }))
    await user.type(screen.getByLabelText('Descripción'), ' Citología ')
    await user.click(adjuntar)
    await waitFor(() => expect(cuerpo).toMatch(/name="archivo"; filename="[^"]+"\r\nContent-Type: application\/pdf/))
    expect(cuerpo).toMatch(/name="descripcion"\r\n\r\nCitología\r\n/)
    await waitFor(() => expect(screen.getByLabelText('Descripción')).toHaveValue(''))
    expect(screen.getByRole('button', { name: /adjuntar/i })).toBeDisabled()
  })

  it('explica por qué no se pudo subir', async () => {
    server.use(
      http.post(`${API}/clinica/historias/h1/adjuntos`, () => HttpResponse.json({ detail: 'Tipo de archivo no permitido' }, { status: 415 })),
    )
    const user = abrir()
    await user.upload(
      await screen.findByLabelText('Archivo (JPG, PNG, WEBP o PDF)'),
      new File(['x'], 'foto.png', { type: 'image/png' }),
    )
    await user.click(screen.getByRole('button', { name: /adjuntar/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Tipo de archivo no permitido')
  })
})

describe('fórmula médica', () => {
  it('omite los medicamentos vacíos y envía las indicaciones', async () => {
    let enviado: unknown = null
    server.use(
      http.post(`${API}/clinica/historias/h1/formulas`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ id: 'f1', url: 'https://s3/formula.pdf' })
      }),
    )
    const user = abrir({ estado: 'firmada' })
    await user.click(await screen.findByRole('button', { name: 'Emitir fórmula' }))
    const modal = await screen.findByRole('dialog')
    await user.click(within(modal).getByRole('button', { name: /otro medicamento/i }))
    await user.click(within(modal).getByRole('button', { name: /otro medicamento/i }))
    const medicamentos = within(modal).getAllByLabelText('Medicamento')
    expect(medicamentos).toHaveLength(3)
    await user.type(medicamentos[0]!, 'Otomax')
    await user.type(medicamentos[2]!, 'Meloxicam')
    await user.type(within(modal).getAllByLabelText('Frecuencia')[2]!, 'cada 24 horas')
    await user.type(within(modal).getByLabelText('Indicaciones generales'), ' Control en 8 días ')
    await user.click(within(modal).getByRole('button', { name: 'Emitir fórmula' }))
    await waitFor(() =>
      expect(enviado).toEqual({
        items: [{ medicamento: 'Otomax' }, { medicamento: 'Meloxicam', frecuencia: 'cada 24 horas' }],
        indicaciones: 'Control en 8 días',
      }),
    )
  })

  it('explica por qué no se pudo emitir', async () => {
    server.use(
      http.post(`${API}/clinica/historias/h1/formulas`, () => HttpResponse.json({ detail: 'La consulta no está firmada' }, { status: 409 })),
    )
    const user = abrir({ estado: 'firmada' })
    await user.click(await screen.findByRole('button', { name: 'Emitir fórmula' }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Medicamento'), 'Otomax')
    await user.click(within(modal).getByRole('button', { name: 'Emitir fórmula' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('La consulta no está firmada')
  })
})
