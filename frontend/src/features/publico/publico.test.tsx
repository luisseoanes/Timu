import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { AfiliacionPage } from './AfiliacionPage'
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

describe('Verificación de carnet', () => {
  function abrir() {
    return renderizar(
      <Routes>
        <Route path="/verificar/:codigo" element={<VerificarCarnetPage />} />
      </Routes>,
      { ruta: '/verificar/ABC123' },
    )
  }

  it('confirma la autenticidad y lista lo aplicado', async () => {
    server.use(
      sinSesion,
      http.get(`${API}/verificacion/carnets/ABC123`, () =>
        HttpResponse.json({
          codigo: 'ABC123',
          emitido_en: '2026-10-01T15:00:00Z',
          sha256: 'f'.repeat(64),
          mascota: { nombre: 'Luna', especie: 'canino', raza: null },
          aplicados: [{ nombre: 'Rabia', dosis: 'Única', fecha_aplicacion: '2026-09-01', producto: 'Nobivac', lote: 'L-77' }],
        }),
      ),
    )
    abrir()
    expect(await screen.findByRole('status')).toHaveTextContent('Carnet auténtico')
    expect(screen.getByText('Rabia · Única')).toBeInTheDocument()
    expect(screen.getByText('L-77')).toBeInTheDocument()
  })

  it('avisa cuando el código no existe', async () => {
    server.use(
      sinSesion,
      http.get(`${API}/verificacion/carnets/ABC123`, () => HttpResponse.json({ detail: 'Carnet no encontrado' }, { status: 404 })),
    )
    abrir()
    expect(await screen.findByRole('alert')).toHaveTextContent('No encontramos un carnet')
  })
})

describe('Afiliación en línea', () => {
  it('envía la solicitud con la aceptación expresa y el plan del enlace', async () => {
    let enviado: Record<string, unknown> | null = null
    server.use(
      sinSesion,
      http.post(`${API}/afiliaciones`, async ({ request }) => {
        enviado = (await request.json()) as Record<string, unknown>
        return HttpResponse.json({ detail: 'Ya tienes una afiliacion vigente' }, { status: 409 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<AfiliacionPage />, { ruta: '/afiliacion?plan=familiar' })
    await user.type(screen.getByLabelText('Nombre completo del titular'), 'Ana Ruiz')
    await user.type(screen.getByLabelText('Número de documento'), '1020304050')
    await user.type(screen.getByLabelText('Celular (WhatsApp)'), '3001112233')
    await user.type(screen.getByLabelText('Ciudad'), 'Bogota')
    await user.type(screen.getByLabelText('Nombre'), 'Luna')
    await user.click(screen.getByLabelText(/acepto las condiciones/i))
    await user.click(screen.getByLabelText(/autorizo el tratamiento/i))
    await user.click(screen.getByRole('button', { name: /continuar al pago/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Ya tienes una afiliacion vigente')
    expect(enviado).toMatchObject({
      titular_nombre: 'Ana Ruiz',
      plan_codigo: 'familiar',
      acepta_condiciones: true,
      acepta_tratamiento_datos: true,
      mascotas: [{ nombre: 'Luna', especie: 'canino' }],
    })
  })
})
