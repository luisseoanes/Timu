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

const SATISFACCION = { tipo: 'satisfaccion', atencion: 'Consulta domiciliaria', fecha: '2026-10-26', mascota: 'Luna', respondida: false }
const SEGUIMIENTO = { ...SATISFACCION, tipo: 'seguimiento', atencion: 'Control post atención' }

describe('Encuesta pública', () => {
  function abrir() {
    return renderizar(
      <Routes>
        <Route path="/encuesta/:token" element={<EncuestaPage />} />
      </Routes>,
      { ruta: '/encuesta/tk1' },
    )
  }

  function conEncuesta(contexto: object, respuesta = { detail: 'Gracias por tu respuesta', te_contactamos: false }) {
    const enviado: unknown[] = []
    server.use(
      sinSesion,
      http.get(`${API}/encuestas/respuesta/tk1`, () => HttpResponse.json(contexto)),
      http.post(`${API}/encuestas/respuesta/tk1`, async ({ request }) => {
        enviado.push(await request.json())
        return HttpResponse.json(respuesta)
      }),
    )
    return enviado
  }

  it('pregunta por la atención y envía la calificación', async () => {
    const enviado = conEncuesta(SATISFACCION)
    const user = userEvent.setup()
    abrir()
    expect(await screen.findByRole('heading', { level: 1, name: '¿Cómo te fue en la atención de Luna?' })).toBeInTheDocument()
    expect(screen.getByText('Consulta domiciliaria del lunes, 26 de octubre.')).toBeInTheDocument()
    // La frase del panel le habla a quien llega, sin repetir la pregunta.
    expect(screen.getByText('Tu opinión nos ayuda a cuidar mejor a Luna.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Enviar respuesta' })).toBeDisabled()
    await user.click(screen.getByRole('radio', { name: /excelente/i }))
    await user.type(screen.getByLabelText(/algo que quieras contarnos/i), 'Muy amables')
    await user.click(screen.getByRole('button', { name: 'Enviar respuesta' }))
    expect(await screen.findByRole('heading', { name: '¡Gracias!' })).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Tu respuesta nos ayuda a cuidar mejor a Luna.')
    expect(enviado).toEqual([{ puntaje: 5, comentario: 'Muy amables' }])
  })

  it('con una calificación que deja tarea, dice que el equipo contacta a la familia', async () => {
    conEncuesta(SATISFACCION, { detail: 'Gracias por tu respuesta', te_contactamos: true })
    const user = userEvent.setup()
    abrir()
    await user.click(await screen.findByRole('radio', { name: /Mala$/ }))
    await user.click(screen.getByRole('button', { name: 'Enviar respuesta' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Alguien del equipo TIMU te va a contactar')
  })

  it('el seguimiento pregunta cómo sigue la mascota y una novedad recuerda qué hacer si es urgente', async () => {
    const enviado = conEncuesta(SEGUIMIENTO, { detail: 'Gracias por tu respuesta', te_contactamos: true })
    const user = userEvent.setup()
    abrir()
    expect(
      await screen.findByRole('heading', { level: 1, name: '¿Cómo sigue Luna después de la atención?' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Control post atención del lunes, 26 de octubre.')).toBeInTheDocument()
    expect(screen.queryByRole('radio', { name: /excelente/i })).not.toBeInTheDocument()
    expect(screen.queryByText(/si es una urgencia/i)).not.toBeInTheDocument()

    await user.click(screen.getByRole('radio', { name: 'Algo no va bien' }))
    expect(screen.getByText(/si es una urgencia, no esperes/i)).toBeInTheDocument()
    await user.type(screen.getByLabelText('¿Qué notaste? (opcional)'), 'No quiere comer')
    await user.click(screen.getByRole('button', { name: 'Enviar respuesta' }))
    expect(await screen.findByRole('status')).toHaveTextContent('te va a contactar')
    expect(enviado).toEqual([{ como_sigue: 'novedad', comentario: 'No quiere comer' }])
  })

  it('la duda cambia lo que se pide contar', async () => {
    conEncuesta(SEGUIMIENTO)
    const user = userEvent.setup()
    abrir()
    await user.click(await screen.findByRole('radio', { name: 'Tenemos una duda' }))
    expect(screen.getByLabelText('¿Cuál es tu duda? (opcional)')).toBeInTheDocument()
  })

  it('dice que ya se respondió si se abre otra vez', async () => {
    conEncuesta({ ...SATISFACCION, respondida: true })
    abrir()
    expect(await screen.findByRole('heading', { name: 'Ya nos respondiste' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Enviar respuesta' })).not.toBeInTheDocument()
  })

  it('si otra pestaña la respondió antes, lo dice y no deja enviar otra vez', async () => {
    server.use(
      sinSesion,
      http.get(`${API}/encuestas/respuesta/tk1`, () => HttpResponse.json(SATISFACCION)),
      http.post(`${API}/encuestas/respuesta/tk1`, () =>
        HttpResponse.json({ detail: 'La encuesta ya fue respondida' }, { status: 422 }),
      ),
    )
    const user = userEvent.setup()
    abrir()
    await user.click(await screen.findByRole('radio', { name: /buena/i }))
    await user.click(screen.getByRole('button', { name: 'Enviar respuesta' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Esta encuesta ya tenía una respuesta.')
    expect(screen.getByRole('button', { name: 'Enviar respuesta' })).toBeDisabled()
  })

  it('un enlace que no existe lo dice en el título, sin el texto del servidor', async () => {
    server.use(
      sinSesion,
      http.get(`${API}/encuestas/respuesta/tk1`, () => HttpResponse.json({ detail: 'Encuesta no encontrada' }, { status: 404 })),
    )
    abrir()
    expect(await screen.findByRole('heading', { name: 'Esta encuesta no está disponible' })).toBeInTheDocument()
    expect(screen.queryByText(/encuesta no encontrada/i)).not.toBeInTheDocument()
  })

  it('si el servidor no responde, ofrece reintentar', async () => {
    let intentos = 0
    server.use(
      sinSesion,
      http.get(`${API}/encuestas/respuesta/tk1`, () => {
        intentos += 1
        return intentos === 1 ? new HttpResponse(null, { status: 503 }) : HttpResponse.json(SATISFACCION)
      }),
    )
    const user = userEvent.setup()
    abrir()
    expect(await screen.findByRole('heading', { name: 'No pudimos abrir la encuesta' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(await screen.findByRole('heading', { level: 1, name: /cómo te fue/i })).toBeInTheDocument()
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
