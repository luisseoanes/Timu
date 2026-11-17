import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { EncuestaPage } from './EncuestaPage'
import { VerificarCarnetPage } from './VerificarCarnetPage'
import { sinSesion } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const API = '*/api/v1'

describe('Encuesta pública', () => {
  function abrir() {
    return renderizar(
      <Routes>
        <Route path="/encuesta/:token" element={<EncuestaPage />} />
      </Routes>,
      { ruta: '/encuesta/tk1' },
    )
  }

  it('pregunta por la atención y envía la calificación', async () => {
    let enviado: unknown = null
    server.use(
      sinSesion,
      http.get(`${API}/encuestas/respuesta/tk1`, () =>
        HttpResponse.json({ tipo: 'satisfaccion', atencion: 'Consulta domiciliaria', fecha: '2026-10-20', mascota: 'Luna', respondida: false }),
      ),
      http.post(`${API}/encuestas/respuesta/tk1`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ detail: 'Gracias' })
      }),
    )
    const user = userEvent.setup()
    abrir()
    expect(await screen.findByText(/consulta domiciliaria de luna el 20\/10\/2026/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Enviar respuesta' })).toBeDisabled()
    await user.click(screen.getByRole('radio', { name: /excelente/i }))
    await user.type(screen.getByLabelText(/algo que quieras contarnos/i), 'Muy amables')
    await user.click(screen.getByRole('button', { name: 'Enviar respuesta' }))
    expect(await screen.findByRole('heading', { name: '¡Gracias!' })).toBeInTheDocument()
    expect(enviado).toEqual({ puntaje: 5, comentario: 'Muy amables' })
  })

  it('agradece directamente si ya fue respondida', async () => {
    server.use(
      sinSesion,
      http.get(`${API}/encuestas/respuesta/tk1`, () =>
        HttpResponse.json({ tipo: 'satisfaccion', atencion: null, fecha: null, mascota: null, respondida: true }),
      ),
    )
    abrir()
    expect(await screen.findByRole('heading', { name: '¡Gracias!' })).toBeInTheDocument()
  })

  it('dice que no existe si el enlace no es válido', async () => {
    server.use(
      sinSesion,
      http.get(`${API}/encuestas/respuesta/tk1`, () => HttpResponse.json({ detail: 'Encuesta no encontrada' }, { status: 404 })),
    )
    abrir()
    expect(await screen.findByRole('alert')).toHaveTextContent('No encontramos esta encuesta')
  })
})

const CARNET = {
  codigo: 'ABC2345678',
  emitido_en: '2026-10-01T15:00:00Z',
  sha256: 'f'.repeat(64),
  mascota: { nombre: 'Luna', especie: 'Canino', raza: 'Pug' },
  secciones: [
    {
      tipo: 'vacuna',
      titulo: 'Vacunación',
      aplicados: [
        { nombre: 'Antirrábica canina', dosis: 'Dosis 1', fecha_aplicacion: '2026-09-01', producto: 'Nobivac', lote: 'L-77', peso_kg: null, aplicado_por: 'Dra. Paula Gómez', proxima_fecha: '2027-09-01' },
      ],
    },
    {
      tipo: 'desparasitacion_interna',
      titulo: 'Desparasitación interna',
      aplicados: [
        { nombre: 'Desparasitación interna canina', dosis: null, fecha_aplicacion: '2026-09-15', producto: 'Drontal', lote: null, peso_kg: 8.4, aplicado_por: 'Dra. Paula Gómez', proxima_fecha: null },
      ],
    },
    { tipo: 'desparasitacion_externa', titulo: 'Desparasitación externa', aplicados: [] },
  ],
  pendientes: [
    { nombre: 'Desparasitación externa canina', dosis: null, fecha_programada: '2026-09-20', vencido: true },
    { nombre: 'Polivalente canina', dosis: 'Dosis 2, refuerzo', fecha_programada: '2026-11-10', vencido: false },
  ],
}

describe('Verificación de carnet', () => {
  function abrir(codigo = 'ABC2345678') {
    return renderizar(
      <Routes>
        <Route path="/verificar/:codigo" element={<VerificarCarnetPage />} />
      </Routes>,
      { ruta: `/verificar/${codigo}` },
    )
  }

  it('confirma la autenticidad y dice lo mismo que el carnet impreso, sección por sección', async () => {
    server.use(sinSesion, http.get(`${API}/verificacion/carnets/ABC2345678`, () => HttpResponse.json(CARNET)))
    abrir()
    // El veredicto es el título; debajo, de qué carnet se trata.
    expect(await screen.findByRole('heading', { level: 1, name: 'Carnet auténtico' })).toBeInTheDocument()
    expect(screen.getByText('Luna · Canino · Pug')).toBeInTheDocument()

    const vacunas = screen.getByRole('region', { name: 'Vacunación' })
    expect(vacunas).toHaveTextContent('Antirrábica canina')
    expect(vacunas).toHaveTextContent('Dosis 1')
    expect(vacunas).toHaveTextContent('01/09/2027')
    expect(screen.getByRole('region', { name: 'Desparasitación interna' })).toHaveTextContent('8,4 kg')
    expect(screen.getByRole('region', { name: 'Desparasitación externa' })).toHaveTextContent('Sin aplicaciones registradas.')

    const pendiente = screen.getByRole('region', { name: 'Pendiente al emitirse' })
    expect(pendiente).toHaveTextContent('Vencido')
    expect(pendiente).toHaveTextContent('Polivalente canina, dosis 2, refuerzo')
    // Lo próximo solo dice su fecha; el distintivo es para lo vencido.
    expect(pendiente).not.toHaveTextContent('Próximo')
    expect(screen.getByText(/certifica que TIMU emitió este carnet el 01\/10\/2026/i)).toBeInTheDocument()
    // La huella entera: cortada no se puede comparar con el PDF.
    expect(screen.getByText('f'.repeat(64))).toBeInTheDocument()
  })

  it('sin nada vencido, lo pendiente no lleva columna de estado', async () => {
    server.use(
      sinSesion,
      http.get(`${API}/verificacion/carnets/ABC2345678`, () =>
        HttpResponse.json({ ...CARNET, pendientes: CARNET.pendientes.filter((p) => !p.vencido) }),
      ),
    )
    abrir()
    const pendiente = await screen.findByRole('region', { name: 'Pendiente al emitirse' })
    expect(within(pendiente).getAllByRole('columnheader').map((c) => c.textContent)).toEqual(['Preventivo', 'Programado para'])
  })

  it('un carnet emitido antes no inventa lo pendiente', async () => {
    server.use(
      sinSesion,
      http.get(`${API}/verificacion/carnets/ABC2345678`, () => HttpResponse.json({ ...CARNET, pendientes: null })),
    )
    abrir()
    expect(await screen.findByText(/se emitió antes de que la verificación guardara lo pendiente/)).toBeInTheDocument()
  })

  it('un código que no existe se puede corregir ahí mismo', async () => {
    server.use(
      sinSesion,
      http.get(`${API}/verificacion/carnets/ABC234567B`, () => HttpResponse.json({ detail: 'Carnet no encontrado' }, { status: 404 })),
      http.get(`${API}/verificacion/carnets/ABC2345678`, () => HttpResponse.json(CARNET)),
    )
    const user = userEvent.setup()
    abrir('ABC234567B')
    expect(await screen.findByRole('heading', { name: 'No encontramos este carnet' })).toBeInTheDocument()
    expect(screen.queryByText(/carnet no encontrado/i)).not.toBeInTheDocument()
    const campo = screen.getByLabelText('Código del carnet')
    await user.clear(campo)
    await user.type(campo, ' abc2345678 ')
    await user.click(screen.getByRole('button', { name: 'Verificar' }))
    expect(await screen.findByRole('heading', { level: 1, name: 'Carnet auténtico' })).toBeInTheDocument()
  })

  it('si el servidor no responde, ofrece reintentar', async () => {
    server.use(
      sinSesion,
      http.get(`${API}/verificacion/carnets/ABC2345678`, () => new HttpResponse(null, { status: 503 })),
    )
    abrir()
    expect(await screen.findByRole('heading', { name: 'No pudimos verificar el carnet' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeInTheDocument()
  })
})
