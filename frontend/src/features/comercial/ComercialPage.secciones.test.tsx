import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'

import { ComercialPage } from './ComercialPage'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { ConversacionRead, InteresadoRead } from '@/types'

const API = '*/api/v1'
const pagina = (items: unknown[]) => ({ items, total: items.length, limit: 25, offset: 0 })

const interesado = (cambios: Partial<InteresadoRead>): InteresadoRead => ({
  id: 'i1',
  nombre: 'Paula Díaz',
  telefono: '573005551234',
  email: null,
  ciudad: 'Bogota',
  origen: 'whatsapp',
  etapa: 'contactado',
  responsable_id: null,
  familia_id: null,
  plan_sugerido: null,
  datos: {},
  motivo_perdida: null,
  ultimo_contacto: null,
  created_at: '2026-10-20T10:00:00Z',
  ...cambios,
})

const conversacion = (cambios: Partial<ConversacionRead>): ConversacionRead => ({
  id: 'cv1',
  telefono: '573005551234',
  interesado_id: 'i1',
  nodo: 'asesor',
  datos: {},
  estado: 'con_asesor',
  asesor_id: null,
  tarea_id: null,
  updated_at: '2026-10-24T14:00:00Z',
  ...cambios,
})

beforeEach(() =>
  server.use(
    http.get(`${API}/comercial/embudo`, () =>
      HttpResponse.json({ total: 0, por_etapa: {}, por_origen: {}, conversion: 0 }),
    ),
    http.get(`${API}/auth/equipo`, () => HttpResponse.json([{ id: 'c1', nombre: 'Valentina', rol: 'comercial' }])),
    http.get(`${API}/comercial/interesados`, () => HttpResponse.json(pagina([interesado({})]))),
    http.get(`${API}/comercial/conversaciones`, () => HttpResponse.json([])),
    http.get(`${API}/comercial/arbol`, () => HttpResponse.json({ inicio: { mensaje: 'Hola', opciones: {} } })),
  ),
)

async function abrirPestana(nombre: string) {
  const user = userEvent.setup()
  renderizar(<ComercialPage />)
  await user.click(await screen.findByRole('tab', { name: nombre }))
  return user
}

describe('embudo e interesados', () => {
  it('busca por nombre u origen y quita el filtro de etapa', async () => {
    const consultas: URLSearchParams[] = []
    server.use(
      http.get(`${API}/comercial/interesados`, ({ request }) => {
        consultas.push(new URL(request.url).searchParams)
        return HttpResponse.json(pagina([]))
      }),
    )
    const user = userEvent.setup()
    renderizar(<ComercialPage />)
    expect(await screen.findByText('No hay interesados con estos filtros.')).toBeInTheDocument()
    await user.type(screen.getByLabelText('Buscar interesados'), 'paula')
    await user.selectOptions(screen.getByLabelText('Origen'), 'referido')
    await waitFor(() => {
      const ultima = consultas.at(-1)!
      expect([ultima.get('q'), ultima.get('origen')]).toEqual(['paula', 'referido'])
    })
    await user.click(screen.getByRole('button', { name: /^cotizado/i }))
    await waitFor(() => expect(consultas.at(-1)!.get('etapa')).toBe('cotizado'))
    await user.click(screen.getByRole('button', { name: 'Quitar filtro de etapa' }))
    await waitFor(() => expect(consultas.at(-1)!.get('etapa')).toBeNull())
  })

  it('muestra cada etapa con su acción: perdido se reactiva, afiliado enlaza la familia', async () => {
    let reactivado = ''
    server.use(
      http.get(`${API}/comercial/interesados`, () =>
        HttpResponse.json(
          pagina([
            interesado({ id: 'p', nombre: 'Perdida', etapa: 'perdido' }),
            interesado({ id: 'a', nombre: 'Afiliada', etapa: 'afiliado', familia_id: 'f9', telefono: null, email: 'a@b.co', ciudad: null }),
            interesado({ id: 's', nombre: null, telefono: null, email: null, ultimo_contacto: '2026-10-23T15:00:00Z' }),
          ]),
        ),
      ),
      http.post(`${API}/comercial/interesados/:id/reactivacion`, ({ params }) => {
        reactivado = String(params.id)
        return HttpResponse.json(interesado({ id: 'p' }))
      }),
    )
    const user = userEvent.setup()
    renderizar(<ComercialPage />)
    const fila = (texto: string) => screen.getByText(texto).closest('tr')!
    await user.click(within(await waitFor(() => fila('Perdida'))).getByRole('button', { name: 'Reactivar' }))
    await waitFor(() => expect(reactivado).toBe('p'))
    expect(screen.getByRole('link', { name: 'Afiliada' })).toHaveAttribute('href', '/familias/f9')
    expect(within(fila('Afiliada')).getByText('a@b.co')).toBeInTheDocument()
    expect(within(fila('Afiliada')).queryByRole('combobox', { name: /etapa/i })).not.toBeInTheDocument()
    expect(screen.getByText('Sin nombre')).toBeInTheDocument()
  })

  it('asigna y desasigna responsable', async () => {
    const cambios: unknown[] = []
    server.use(
      http.get(`${API}/comercial/interesados`, () => HttpResponse.json(pagina([interesado({ responsable_id: 'c1' })]))),
      http.patch(`${API}/comercial/interesados/i1`, async ({ request }) => {
        cambios.push(await request.json())
        return HttpResponse.json(interesado({}))
      }),
    )
    const user = userEvent.setup()
    renderizar(<ComercialPage />)
    const responsable = await screen.findByLabelText('Responsable de Paula Díaz')
    await waitFor(() => expect(responsable).toHaveValue('c1'))
    await user.selectOptions(responsable, '')
    await waitFor(() => expect(cambios).toEqual([{ responsable_id: null }]))
  })

  it('explica por qué no se pudo cambiar la etapa', async () => {
    server.use(
      http.patch(`${API}/comercial/interesados/i1`, () => HttpResponse.json({ detail: 'Interesado bloqueado' }, { status: 409 })),
    )
    const user = userEvent.setup()
    renderizar(<ComercialPage />)
    await user.selectOptions(await screen.findByLabelText('Etapa de Paula Díaz'), 'cotizado')
    expect(await screen.findByRole('alert')).toHaveTextContent('Interesado bloqueado')
  })

  it('registra un interesado sin enviar los campos vacíos', async () => {
    let enviado: unknown = null
    server.use(
      http.post(`${API}/comercial/interesados`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(interesado({}), { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<ComercialPage />)
    await user.click(await screen.findByRole('button', { name: /nuevo interesado/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Celular'), ' 3005551234 ')
    await user.selectOptions(within(modal).getByLabelText('Origen'), 'evento')
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    await waitFor(() => expect(enviado).toEqual({ telefono: '3005551234', origen: 'evento' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('explica por qué no se pudo registrar el interesado o marcarlo perdido', async () => {
    server.use(
      http.post(`${API}/comercial/interesados`, () => HttpResponse.json({ detail: 'Celular inválido' }, { status: 422 })),
      http.post(`${API}/comercial/interesados/i1/perdida`, () =>
        HttpResponse.json({ detail: 'Un interesado afiliado no se marca como perdido' }, { status: 422 }),
      ),
    )
    const user = userEvent.setup()
    renderizar(<ComercialPage />)
    await user.click(await screen.findByRole('button', { name: /nuevo interesado/i }))
    let modal = await screen.findByRole('dialog')
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('Celular inválido')
    await user.keyboard('{Escape}')
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: 'Perdido' }))
    modal = await screen.findByRole('dialog')
    await user.selectOptions(within(modal).getByLabelText('Motivo'), 'No responde')
    await user.click(within(modal).getByRole('button', { name: 'Marcar perdido' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('no se marca como perdido')
  })

  it('explica por qué no se pudo calcular el embudo', async () => {
    server.use(http.get(`${API}/comercial/embudo`, () => HttpResponse.json({ detail: 'Sin conexión' }, { status: 503 })))
    renderizar(<ComercialPage />)
    expect(await screen.findByText(/No fue posible calcular el embudo/)).toBeInTheDocument()
  })
})

describe('conversaciones', () => {
  it('por defecto pide las que esperan asesor, con el valor que entiende el backend', async () => {
    const estados: (string | null)[] = []
    server.use(
      http.get(`${API}/comercial/conversaciones`, ({ request }) => {
        estados.push(new URL(request.url).searchParams.get('estado'))
        return HttpResponse.json([])
      }),
    )
    const user = await abrirPestana('Conversaciones')
    expect(await screen.findByText('No hay conversaciones en este estado.')).toBeInTheDocument()
    await user.selectOptions(screen.getByLabelText('Estado de la conversación'), 'automatica')
    await user.selectOptions(screen.getByLabelText('Estado de la conversación'), '')
    // Regresión: el panel pedía `asesor` y la API respondía 422 en la vista por defecto.
    await waitFor(() => expect(estados).toEqual(['con_asesor', 'automatica', null]))
  })

  it('muestra los datos recogidos por el bot y devuelve la conversación al bot', async () => {
    let liberada = ''
    server.use(
      http.get(`${API}/comercial/conversaciones`, () =>
        HttpResponse.json([
          conversacion({ datos: { ciudad: 'Cali', mascotas: 2 } }),
          conversacion({ id: 'cv2', telefono: '573001112233', estado: 'automatica', nodo: 'inicio' }),
        ]),
      ),
      http.post(`${API}/comercial/conversaciones/:id/liberacion`, ({ params }) => {
        liberada = String(params.id)
        return HttpResponse.json(conversacion({ estado: 'automatica' }))
      }),
    )
    const user = await abrirPestana('Conversaciones')
    expect(await screen.findByText('ciudad: Cali · mascotas: 2')).toBeInTheDocument()
    expect(screen.getByText('Espera asesor')).toBeInTheDocument()
    expect(screen.getByText('Bot')).toBeInTheDocument()
    const botones = screen.getAllByRole('button', { name: 'Devolver al bot' })
    expect(botones).toHaveLength(1)
    await user.click(botones[0]!)
    await waitFor(() => expect(liberada).toBe('cv1'))
  })

  it('explica por qué no se pudo responder', async () => {
    server.use(
      http.get(`${API}/comercial/conversaciones`, () => HttpResponse.json([conversacion({})])),
      http.post(`${API}/comercial/conversaciones/cv1/mensajes`, () =>
        HttpResponse.json({ detail: 'Pasaron más de 24 horas desde su último mensaje' }, { status: 422 }),
      ),
    )
    const user = await abrirPestana('Conversaciones')
    await user.click(await screen.findByRole('button', { name: 'Responder' }))
    await user.type(screen.getByLabelText('Mensaje para 573005551234'), 'Hola')
    await user.click(screen.getByRole('button', { name: /enviar/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Pasaron más de 24 horas')
  })
})

describe('guion del bot', () => {
  it('rechaza un JSON inválido sin llamar a la API', async () => {
    let llamadas = 0
    server.use(
      http.put(`${API}/comercial/arbol`, () => {
        llamadas += 1
        return HttpResponse.json({ version: 2 })
      }),
    )
    const user = await abrirPestana('Guion del bot')
    const nodos = await screen.findByLabelText('Nodos (JSON)')
    await user.clear(nodos)
    await user.type(nodos, 'no es json')
    await user.click(screen.getByRole('button', { name: 'Publicar versión' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('El guion no es un JSON válido.')
    expect(llamadas).toBe(0)
  })

  it('publica el guion vigente con su nota', async () => {
    let enviado: unknown = null
    server.use(
      http.put(`${API}/comercial/arbol`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ version: 2 })
      }),
    )
    const user = await abrirPestana('Guion del bot')
    await screen.findByLabelText('Nodos (JSON)')
    await user.type(screen.getByLabelText('Nota de la versión'), ' Menú más corto ')
    await user.click(screen.getByRole('button', { name: 'Publicar versión' }))
    await waitFor(() =>
      expect(enviado).toEqual({ nodos: { inicio: { mensaje: 'Hola', opciones: {} } }, nota: 'Menú más corto' }),
    )
    expect(await screen.findByRole('status')).toHaveTextContent('Versión publicada.')
  })

  it('muestra por qué el backend rechazó el guion', async () => {
    server.use(
      http.put(`${API}/comercial/arbol`, () => HttpResponse.json({ detail: 'El nodo inicio no existe' }, { status: 422 })),
    )
    const user = await abrirPestana('Guion del bot')
    await screen.findByLabelText('Nodos (JSON)')
    await user.click(screen.getByRole('button', { name: 'Publicar versión' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('El nodo inicio no existe')
  })
})
