import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'

import { InteligenciaArtificial } from './InteligenciaArtificial'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { PromptRead } from '@/types'

const API = '*/api/v1'

const PROMPT: PromptRead = {
  id: 'pr1',
  codigo: 'comercial_guion',
  version: 2,
  sistema: 'Eres el asesor comercial de TIMU.',
  estado: 'borrador',
  nota: null,
  evaluado_en: null,
  evaluacion: {},
}

const consumo = (cambios = {}) =>
  http.get(`${API}/ia/consumo`, () =>
    HttpResponse.json({ mes: '2026-10', gasto_usd: 12.5, presupuesto_usd: 50, disponible_usd: 37.5, por_prompt: [], ...cambios }),
  )

beforeEach(() =>
  server.use(
    consumo(),
    http.get(`${API}/ia/prompts`, () => HttpResponse.json([PROMPT])),
    http.get(`${API}/ia/casos`, () => HttpResponse.json([])),
    http.get(`${API}/ia/consultas`, () => HttpResponse.json([])),
  ),
)

function abrir() {
  renderizar(<InteligenciaArtificial />)
  return userEvent.setup()
}

describe('gasto del mes', () => {
  it('mide el presupuesto usado', async () => {
    abrir()
    expect(await screen.findByText('US$ 37.50')).toBeInTheDocument()
    expect(screen.getByRole('meter', { name: 'Presupuesto de IA usado' })).toHaveAttribute('aria-valuenow', '25')
  })

  it('sin presupuesto no divide por cero', async () => {
    server.use(consumo({ gasto_usd: 0, presupuesto_usd: 0, disponible_usd: 0 }))
    abrir()
    expect(await screen.findByRole('meter', { name: 'Presupuesto de IA usado' })).toHaveAttribute('aria-valuenow', '0')
  })

  it('explica por qué no pudo consultar el gasto', async () => {
    server.use(http.get(`${API}/ia/consumo`, () => HttpResponse.json({ detail: 'Sin conexión' }, { status: 503 })))
    abrir()
    expect(await screen.findByRole('alert')).toHaveTextContent('No fue posible consultar el gasto. Sin conexión')
  })
})

describe('prompts', () => {
  it('sin prompts propone cargar las versiones iniciales', async () => {
    let sembrado = false
    server.use(
      http.get(`${API}/ia/prompts`, () => HttpResponse.json([])),
      http.post(`${API}/ia/prompts/sembrar`, () => {
        sembrado = true
        return HttpResponse.json({ creados: 2 })
      }),
    )
    const user = abrir()
    expect(await screen.findByText('No hay prompts. Carga las versiones iniciales.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Cargar versiones iniciales' }))
    await waitFor(() => expect(sembrado).toBe(true))
  })

  it('una versión activa no se evalúa ni se activa de nuevo', async () => {
    server.use(
      http.get(`${API}/ia/prompts`, () => HttpResponse.json([{ ...PROMPT, estado: 'activo', nota: 'Tono más cercano' }])),
    )
    abrir()
    expect(await screen.findByText('Tono más cercano')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Correr casos' })).not.toBeInTheDocument()
    expect(screen.getByText('Eres el asesor comercial de TIMU.')).toBeInTheDocument()
  })

  it('un borrador que pasó todos sus casos se puede activar', async () => {
    let activado = false
    server.use(
      http.get(`${API}/ia/prompts`, () =>
        HttpResponse.json([
          { ...PROMPT, evaluado_en: '2026-10-30T10:00:00Z', evaluacion: { total: 2, aprobados: 2, detalle: [], en: '' } },
        ]),
      ),
      http.post(`${API}/ia/prompts/pr1/activacion`, () => {
        activado = true
        return HttpResponse.json({ ...PROMPT, estado: 'activo' })
      }),
    )
    const user = abrir()
    expect(await screen.findByRole('status')).toHaveTextContent('2 de 2 casos aprobados')
    await user.click(screen.getByRole('button', { name: 'Activar' }))
    await waitFor(() => expect(activado).toBe(true))
  })

  it('una evaluación sin casos no habilita la activación', async () => {
    server.use(http.post(`${API}/ia/prompts/pr1/evaluacion`, () => HttpResponse.json({ total: 0, aprobados: 0, detalle: [], en: '' })))
    const user = abrir()
    await user.click(await screen.findByRole('button', { name: 'Correr casos' }))
    expect(await screen.findByRole('status')).toHaveTextContent('0 de 0 casos aprobados')
    expect(screen.getByRole('button', { name: 'Activar' })).toBeDisabled()
  })

  it('explica por qué no se pudo activar', async () => {
    server.use(
      http.get(`${API}/ia/prompts`, () =>
        HttpResponse.json([{ ...PROMPT, evaluado_en: '2026-10-30T10:00:00Z', evaluacion: { total: 1, aprobados: 1, detalle: [], en: '' } }]),
      ),
      http.post(`${API}/ia/prompts/pr1/activacion`, () =>
        HttpResponse.json({ detail: 'Los casos cambiaron desde la evaluación' }, { status: 409 }),
      ),
    )
    const user = abrir()
    await user.click(await screen.findByRole('button', { name: 'Activar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Los casos cambiaron desde la evaluación')
  })

  it('guarda una versión nueva como borrador', async () => {
    let enviado: unknown = null
    server.use(
      http.post(`${API}/ia/prompts`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ ...PROMPT, id: 'pr2', version: 3 }, { status: 201 })
      }),
    )
    const user = abrir()
    await user.click(await screen.findByRole('button', { name: /nueva versión/i }))
    const modal = await screen.findByRole('dialog')
    await user.selectOptions(within(modal).getByLabelText('Uso'), 'veterinario_borrador')
    await user.type(within(modal).getByLabelText('Instrucciones del sistema'), 'Eres veterinario.')
    await user.type(within(modal).getByLabelText('Qué cambia en esta versión'), '   ')
    await user.click(within(modal).getByRole('button', { name: 'Guardar borrador' }))
    await waitFor(() => expect(enviado).toEqual({ codigo: 'veterinario_borrador', sistema: 'Eres veterinario.' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('explica por qué no se pudo guardar la versión', async () => {
    server.use(http.post(`${API}/ia/prompts`, () => HttpResponse.json({ detail: 'Instrucciones vacías' }, { status: 422 })))
    const user = abrir()
    await user.click(await screen.findByRole('button', { name: /nueva versión/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Instrucciones del sistema'), 'x')
    await user.click(within(modal).getByRole('button', { name: 'Guardar borrador' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('Instrucciones vacías')
  })
})

describe('casos de prueba', () => {
  it('lista los casos con su uso y lo que se espera', async () => {
    server.use(
      http.get(`${API}/ia/casos`, () =>
        HttpResponse.json([{ id: 'k1', prompt_codigo: 'comercial_guion', nombre: 'Precio', entrada: '¿Cuánto vale?', esperado: { alcance: 'dentro' } }]),
      ),
    )
    abrir()
    expect(await screen.findByText('Precio')).toBeInTheDocument()
    expect(screen.getByText(/Atención comercial por WhatsApp · «¿Cuánto vale\?»/)).toBeInTheDocument()
    expect(screen.getByText('{"alcance":"dentro"}')).toBeInTheDocument()
  })

  it('sin casos avisa de que no se podrá activar ninguna versión', async () => {
    abrir()
    expect(await screen.findByText('Sin casos: no se podrá activar ninguna versión.')).toBeInTheDocument()
  })

  it('rechaza lo esperado si no es JSON, sin llamar a la API', async () => {
    let llamadas = 0
    server.use(
      http.post(`${API}/ia/casos`, () => {
        llamadas += 1
        return HttpResponse.json({}, { status: 201 })
      }),
    )
    const user = abrir()
    await user.click(await screen.findByRole('button', { name: /nuevo caso/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nombre'), 'Fuera de alcance')
    await user.type(within(modal).getByLabelText('Entrada'), '¿Venden comida?')
    const esperado = within(modal).getByLabelText('Esperado (JSON)')
    await user.clear(esperado)
    await user.type(esperado, 'no es json')
    await user.click(within(modal).getByRole('button', { name: 'Guardar caso' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('Lo esperado no es un JSON válido.')
    expect(llamadas).toBe(0)
  })

  it('guarda un caso con lo esperado como objeto', async () => {
    let enviado: unknown = null
    server.use(
      http.post(`${API}/ia/casos`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ id: 'k2' }, { status: 201 })
      }),
    )
    const user = abrir()
    await user.click(await screen.findByRole('button', { name: /nuevo caso/i }))
    const modal = await screen.findByRole('dialog')
    await user.selectOptions(within(modal).getByLabelText('Uso'), 'veterinario_borrador')
    await user.type(within(modal).getByLabelText('Nombre'), ' Vómito ')
    await user.type(within(modal).getByLabelText('Entrada'), ' Vomitó sangre ')
    await user.click(within(modal).getByRole('button', { name: 'Guardar caso' }))
    await waitFor(() =>
      expect(enviado).toEqual({
        prompt_codigo: 'veterinario_borrador',
        nombre: 'Vómito',
        entrada: 'Vomitó sangre',
        esperado: { alcance: 'fuera' },
      }),
    )
  })

  it('explica por qué no se pudo guardar el caso', async () => {
    server.use(http.post(`${API}/ia/casos`, () => HttpResponse.json({ detail: 'Nombre repetido' }, { status: 409 })))
    const user = abrir()
    await user.click(await screen.findByRole('button', { name: /nuevo caso/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nombre'), 'Precio')
    await user.type(within(modal).getByLabelText('Entrada'), '¿Cuánto vale?')
    await user.click(within(modal).getByRole('button', { name: 'Guardar caso' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('Nombre repetido')
  })
})

describe('últimas consultas', () => {
  it('muestra uso, versión, estado, tokens y costo de cada consulta', async () => {
    const consulta = (cambios: object) => ({
      id: 'q1',
      prompt_codigo: 'comercial_guion',
      prompt_version: 2,
      estado: 'ok',
      error: null,
      tokens_entrada: 1200,
      tokens_salida: 300,
      costo_usd: 0.0123,
      created_at: '2026-10-30T10:00:00Z',
      ...cambios,
    })
    server.use(
      http.get(`${API}/ia/consultas`, () =>
        HttpResponse.json([
          consulta({}),
          consulta({ id: 'q2', estado: 'error', error: 'Tiempo agotado', prompt_version: null }),
          consulta({ id: 'q3', estado: 'sin_presupuesto', prompt_codigo: 'otro_uso' }),
        ]),
      ),
    )
    abrir()
    expect(await screen.findByText('Tiempo agotado')).toBeInTheDocument()
    expect(screen.getAllByText('1200 / 300')).toHaveLength(3)
    expect(screen.getAllByText('US$ 0.0123')).toHaveLength(3)
    expect(screen.getByText('otro_uso')).toBeInTheDocument()
    expect(screen.getByText('sin_presupuesto')).toBeInTheDocument()
  })

  it('sin consultas lo dice', async () => {
    abrir()
    expect(await screen.findByText('Aún no se ha consultado la IA.')).toBeInTheDocument()
  })
})
