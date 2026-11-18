import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { delay, http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'

import { ComercialPage } from './ComercialPage'
import { USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { ConversacionDelInteresado, ConversacionRead, InteresadoRead, MensajeRead } from '@/types'

const API = '*/api/v1'
const pagina = (items: unknown[]) => ({ items, total: items.length, limit: 30, offset: 0 })

const interesado = (cambios: Partial<InteresadoRead>): InteresadoRead => ({
  id: 'i1',
  nombre: 'Paula Díaz',
  telefono: '+573005551234',
  email: null,
  ciudad: 'Bogotá',
  origen: 'whatsapp',
  etapa: 'contactado',
  responsable_id: null,
  familia_id: null,
  plan_sugerido: null,
  datos: {},
  motivo_perdida: null,
  ultimo_contacto: null,
  created_at: '2026-10-20T10:00:00Z',
  siguiente_etapa: 'cotizado',
  ...cambios,
})

const conversacion = (cambios: Partial<ConversacionRead>): ConversacionRead => ({
  id: 'cv1',
  telefono: '+573005551234',
  interesado_id: 'i1',
  nodo: 'asesor',
  datos: {},
  estado: 'con_asesor',
  asesor_id: null,
  tarea_id: null,
  updated_at: '2026-10-24T14:00:00Z',
  ...cambios,
})

const mensaje = (id: string, direccion: string, contenido: string): MensajeRead =>
  ({ id, familia_id: null, canal: 'whatsapp', direccion, destino: '+573005551234', plantilla: null, contenido, estado: 'enviado', created_at: '2026-10-24T14:00:00Z' }) as MensajeRead

const RECUENTOS = { nuevo: 1, contactado: 1, cotizado: 0, en_afiliacion: 0, afiliado: 2, perdido: 1, abiertos: 2 }

function conConversacion(datos: ConversacionDelInteresado) {
  server.use(http.get(`${API}/comercial/interesados/:id/conversacion`, () => HttpResponse.json(datos)))
}

beforeEach(() => {
  server.use(
    http.get(`${API}/comercial/embudo`, () => HttpResponse.json({ total: 3, por_etapa: {}, por_origen: {}, conversion: 0.25 })),
    http.get(`${API}/comercial/interesados/recuentos`, () => HttpResponse.json(RECUENTOS)),
    http.get(`${API}/comercial/interesados/:id`, ({ params }) => HttpResponse.json(interesado({ id: String(params.id) }))),
    http.get(`${API}/comercial/interesados`, () =>
      HttpResponse.json(pagina([interesado({ id: 'i0', nombre: null, telefono: '+573004445588', etapa: 'nuevo', siguiente_etapa: 'contactado' }), interesado({})])),
    ),
    http.get(`${API}/auth/equipo`, () => HttpResponse.json([{ id: 'c1', nombre: 'Valentina', rol: 'comercial' }])),
    http.get(`${API}/comercial/conversaciones`, () => HttpResponse.json([])),
    http.get(`${API}/comercial/arbol`, () => HttpResponse.json({ inicio: { mensaje: 'Hola', opciones: {} } })),
  )
  conConversacion({ conversacion: null, mensajes: [] })
})

describe('interesados', () => {
  it('lista los abiertos agrupados por etapa, en el orden del embudo, con los recuentos', async () => {
    const consultas: string[] = []
    server.use(
      http.get(`${API}/comercial/interesados`, ({ request }) => {
        consultas.push(new URL(request.url).search)
        return HttpResponse.json(pagina([interesado({ id: 'i0', nombre: null, telefono: '+573004445588', etapa: 'nuevo' }), interesado({})]))
      }),
    )
    renderizar(<ComercialPage />)
    const lista = await screen.findByRole('list', { name: 'Interesados abiertos, por etapa' })
    expect(consultas[0]).toContain('abiertos=true')
    expect(consultas[0]).toContain('orden=etapa')
    // Sin nombre (el bot no lo pregunta), se nombra por su celular.
    expect(within(lista).getByRole('link', { name: '+57 300 444 5588' })).toBeInTheDocument()
    expect(within(lista).getByText('Nuevo ·')).toBeInTheDocument()
    expect(within(lista).getByText('Contactado ·')).toBeInTheDocument()
    expect(within(lista).getAllByText('WhatsApp').length).toBe(2)
    expect(screen.getByRole('button', { name: 'Afiliados 2' })).toBeInTheDocument()
    expect(screen.getByText(/conversión/)).toHaveTextContent('25')
    // El título no repite el recuento de «Abiertos» (techo 55).
    expect(screen.getByRole('heading', { level: 2, name: 'Interesados' })).toBeInTheDocument()
  })

  it('cambia a perdidos y dice por qué está vacía una vista', async () => {
    const consultas: string[] = []
    server.use(
      http.get(`${API}/comercial/interesados`, ({ request }) => {
        consultas.push(new URL(request.url).search)
        return HttpResponse.json(pagina([]))
      }),
    )
    const user = userEvent.setup()
    renderizar(<ComercialPage />)
    await user.click(await screen.findByRole('button', { name: /^Perdidos/ }))
    await waitFor(() => expect(consultas.some((c) => c.includes('etapa=perdido'))).toBe(true))
    expect(await screen.findByText('Ningún interesado se ha perdido.')).toBeInTheDocument()
  })

  it('sin interesado abierto, la ficha dice qué hacer y «Nuevo interesado» es el verde', async () => {
    renderizar(<ComercialPage />)
    expect(await screen.findByText(/Abre un interesado para ver/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /nuevo interesado/i })).toHaveClass('btn-primario')
  })

  it('registra un interesado sin enviar los campos vacíos y abre su ficha', async () => {
    let enviado: unknown = null
    let listados = 0
    server.use(
      // La recarga del listado tras crear no responde: la ficha se abre igual, sin esperarla.
      http.get(`${API}/comercial/interesados`, async () => {
        if (++listados > 1) await delay('infinite')
        return HttpResponse.json({ items: [], total: 0, limit: 50, offset: 0 })
      }),
      http.post(`${API}/comercial/interesados`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(interesado({ id: 'nuevo', nombre: 'Laura' }), { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<ComercialPage />)
    await user.click(await screen.findByRole('button', { name: /nuevo interesado/i }))
    const ventana = await screen.findByRole('dialog', { name: 'Nuevo interesado' })
    await user.type(within(ventana).getByLabelText('Nombre'), 'Laura')
    await user.type(within(ventana).getByLabelText('Celular'), '3001234567')
    await user.selectOptions(within(ventana).getByLabelText('Cómo llegó'), 'referido')
    await user.click(within(ventana).getByRole('button', { name: 'Guardar interesado' }))
    await waitFor(() => expect(enviado).toEqual({ nombre: 'Laura', telefono: '3001234567', origen: 'referido' }))
    // Cerrar la ventana, recargar el listado y abrir la ficha van encadenados: con la suite entera
    // bajo cobertura, el segundo por defecto de findBy no siempre alcanza (frontend/CLAUDE.md).
    expect(await screen.findByRole('region', { name: 'Interesado abierto' }, { timeout: 5000 })).toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})

describe('ficha del interesado', () => {
  const abrir = () => renderizar(<ComercialPage />, { ruta: '/panel/comercial?interesado=i1' })

  it('dice dónde va en el embudo y lo pasa a la etapa siguiente que dice la API', async () => {
    let enviado: unknown = null
    server.use(
      http.patch(`${API}/comercial/interesados/:id`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(interesado({ etapa: 'cotizado' }))
      }),
    )
    const user = userEvent.setup()
    abrir()
    const ficha = await screen.findByRole('region', { name: 'Interesado abierto' })
    expect(await within(ficha).findByRole('heading', { name: 'Paula Díaz' })).toBeInTheDocument()
    const etapas = within(ficha).getByRole('list', { name: 'Etapas del embudo' })
    expect(within(etapas).getByText('Contactado').closest('li')).toHaveAttribute('aria-current', 'step')
    const pasar = within(ficha).getByRole('button', { name: 'Pasar a cotizado' })
    // Sin nadie esperando en WhatsApp, avanzar es lo que toca: el único verde.
    expect(pasar).toHaveClass('btn-primario')
    expect(screen.getByRole('button', { name: /nuevo interesado/i })).toHaveClass('btn-suave')
    await user.click(pasar)
    await waitFor(() => expect(enviado).toEqual({ etapa: 'cotizado' }))
  })

  it('reasigna el responsable desde la ficha', async () => {
    let enviado: unknown = null
    server.use(
      http.patch(`${API}/comercial/interesados/:id`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(interesado({ responsable_id: 'c1' }))
      }),
    )
    const user = userEvent.setup()
    abrir()
    const responsable = await screen.findByLabelText('Responsable')
    await screen.findByRole('option', { name: 'Valentina' })
    await user.selectOptions(responsable, 'c1')
    await waitFor(() => expect(enviado).toEqual({ responsable_id: 'c1' }))
  })

  it('marca como perdido con su motivo, confirmándolo en rojo', async () => {
    let enviado: unknown = null
    server.use(
      http.post(`${API}/comercial/interesados/:id/perdida`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(interesado({ etapa: 'perdido' }))
      }),
    )
    const user = userEvent.setup()
    abrir()
    await user.click(await screen.findByRole('button', { name: 'Más acciones con Paula Díaz' }))
    await user.click(await screen.findByRole('menuitem', { name: 'Marcar como perdido' }))
    const ventana = await screen.findByRole('dialog', { name: 'Marcar a Paula Díaz como perdido' })
    await user.selectOptions(within(ventana).getByLabelText('Motivo'), 'No responde')
    const confirmar = within(ventana).getByRole('button', { name: 'Marcar como perdido' })
    expect(confirmar).toHaveClass('btn-peligro')
    await user.click(confirmar)
    await waitFor(() => expect(enviado).toEqual({ motivo: 'No responde' }))
  })

  it('un perdido dice por qué y se reactiva', async () => {
    let reactivado = false
    server.use(
      http.get(`${API}/comercial/interesados/:id`, () =>
        HttpResponse.json(interesado({ etapa: 'perdido', siguiente_etapa: null, motivo_perdida: 'Precio' })),
      ),
      http.post(`${API}/comercial/interesados/:id/reactivacion`, () => {
        reactivado = true
        return HttpResponse.json(interesado({}))
      }),
    )
    const user = userEvent.setup()
    abrir()
    expect(await screen.findByText('Perdido: Precio.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /más acciones/i })).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Reactivar' }))
    await waitFor(() => expect(reactivado).toBe(true))
  })

  it('en afiliación no se avanza a mano: se afilia desde Familias', async () => {
    server.use(http.get(`${API}/comercial/interesados/:id`, () => HttpResponse.json(interesado({ etapa: 'en_afiliacion', siguiente_etapa: null, familia_id: 'f1' }))))
    abrir()
    expect(await screen.findByText(/Se afilia desde Familias/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /pasar a/i })).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Abrir su ficha' })).toHaveAttribute('href', '/panel/familias/f1')
  })

  it('muestra su conversación y, si espera a un asesor, contestarle es el verde', async () => {
    let enviado: unknown = null
    let liberada = false
    conConversacion({
      conversacion: conversacion({}),
      mensajes: [mensaje('m1', 'entrante', 'Hola'), mensaje('m2', 'saliente', 'Hola, soy el asistente de TIMU')],
    })
    server.use(
      http.post(`${API}/comercial/conversaciones/:id/mensajes`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ mensaje_id: 'm3' }, { status: 201 })
      }),
      http.post(`${API}/comercial/conversaciones/:id/liberacion`, () => {
        liberada = true
        return HttpResponse.json(conversacion({ estado: 'automatica' }))
      }),
    )
    const user = userEvent.setup()
    abrir()
    const mensajes = await screen.findByRole('list', { name: 'Mensajes con Paula Díaz' })
    expect(within(mensajes).getByText('Escribió:')).toBeInTheDocument()
    expect(within(mensajes).getByText('Hola, soy el asistente de TIMU')).toBeInTheDocument()
    // Desplazada hacia abajo, lo alto se desvanece mientras queden mensajes anteriores (techo 51).
    // jsdom no desplaza: se simula la posición.
    Object.defineProperty(mensajes, 'scrollTop', { configurable: true, value: 120 })
    fireEvent.scroll(mensajes)
    expect(mensajes).toHaveAttribute('data-anteriores', 'true')
    Object.defineProperty(mensajes, 'scrollTop', { configurable: true, value: 0 })
    fireEvent.scroll(mensajes)
    expect(mensajes).not.toHaveAttribute('data-anteriores')
    expect(screen.getByText('Espera a un asesor')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Pasar a cotizado' })).toHaveClass('btn-suave')
    await user.type(screen.getByLabelText('Responder por WhatsApp'), 'Hola Paula, te cuento del plan')
    const enviar = screen.getByRole('button', { name: /enviar/i })
    expect(enviar).toHaveClass('btn-primario')
    await user.click(enviar)
    await waitFor(() => expect(enviado).toEqual({ texto: 'Hola Paula, te cuento del plan' }))
    await user.click(screen.getByRole('button', { name: 'Devolver al asistente' }))
    await waitFor(() => expect(liberada).toBe(true))
  })

  it('sin celular dice que no hay conversación', async () => {
    server.use(http.get(`${API}/comercial/interesados/:id`, () => HttpResponse.json(interesado({ telefono: null, email: 'p@x.co' }))))
    abrir()
    expect(await screen.findByText('Sin celular: no hay conversación de WhatsApp.')).toBeInTheDocument()
  })

  it('dice lo que escribió en la portada, lo más reciente primero (R3-PUB-04)', async () => {
    const mensajes_web = [
      { fecha: '2026-11-10T15:00:00Z', mascota: null, especie: null, mensaje: '¿Atienden en Envigado?' },
      { fecha: '2026-11-17T15:00:00Z', mascota: 'Tomás', especie: 'felino', mensaje: 'Quiero el plan para mi gato.' },
    ]
    server.use(
      http.get(`${API}/comercial/interesados/:id`, () => HttpResponse.json(interesado({ origen: 'web', datos: { mensajes_web } }))),
    )
    abrir()
    const lista = await screen.findByRole('list', { name: 'Mensajes de la web de Paula Díaz' })
    const [reciente, viejo] = within(lista).getAllByRole('listitem')
    expect(reciente).toHaveTextContent('Tomás, gato')
    expect(reciente).toHaveTextContent('Quiero el plan para mi gato.')
    expect(viejo).toHaveTextContent('¿Atienden en Envigado?')
    expect(screen.getByText('Página web')).toBeInTheDocument()
  })

  it('sin mensajes de la web no muestra el bloque', async () => {
    abrir()
    await screen.findByRole('heading', { level: 2, name: 'Paula Díaz' })
    expect(screen.queryByRole('heading', { name: 'Lo que escribió en la página web' })).not.toBeInTheDocument()
  })

  it('explica por qué no se pudo cargar o cambiar la etapa', async () => {
    server.use(
      http.patch(`${API}/comercial/interesados/:id`, () => HttpResponse.json({ detail: 'Etapa inválida' }, { status: 422 })),
      http.get(`${API}/comercial/interesados/:id/conversacion`, () => HttpResponse.json({ detail: 'Caído' }, { status: 503 })),
    )
    const user = userEvent.setup()
    abrir()
    expect(await screen.findByText('No fue posible cargar la conversación.')).toBeInTheDocument()
    await user.click(await screen.findByRole('button', { name: 'Pasar a cotizado' }))
    expect(await screen.findByText('Etapa inválida')).toBeInTheDocument()
  })
})

describe('conversaciones', () => {
  it('pide las que esperan asesor y lleva a la ficha del interesado', async () => {
    const consultas: string[] = []
    server.use(
      http.get(`${API}/comercial/conversaciones`, ({ request }) => {
        consultas.push(new URL(request.url).search)
        return HttpResponse.json([conversacion({ datos: { ciudad: 'Cali', mascotas: ['perro', 'gato'], codigo_postal: '760001' }, interesado_nombre: 'Paula Díaz' })])
      }),
    )
    const user = userEvent.setup()
    renderizar(<ComercialPage />)
    await user.click(await screen.findByRole('tab', { name: 'Conversaciones' }))
    // Cada dato con su nombre en palabras, también las capturas propias del guion.
    expect(await screen.findByText('Ciudad: Cali · Mascotas: perro, gato · Codigo postal: 760001')).toBeInTheDocument()
    // Nombrada por el interesado, con su celular debajo.
    expect(screen.getByText('Paula Díaz')).toBeInTheDocument()
    expect(screen.getByText('+57 300 555 1234')).toBeInTheDocument()
    expect(consultas[0]).toContain('estado=con_asesor')
    await user.click(screen.getByRole('button', { name: 'Todas' }))
    await waitFor(() => expect(consultas.at(-1)).toBe(''))
    // La ficha vive en la pestaña Interesados: abrir la conversación la trae a la vista.
    await user.click(await screen.findByRole('link', { name: 'Abrir conversación' }))
    expect(screen.getByRole('tab', { name: 'Interesados' })).toHaveAttribute('aria-selected', 'true')
    const ficha = screen.getByRole('region', { name: 'Interesado abierto' })
    expect(await within(ficha).findByRole('heading', { level: 2, name: 'Paula Díaz' })).toBeInTheDocument()
  })

  it('la de una familia afiliada se responde aquí mismo', async () => {
    let enviado: unknown = null
    server.use(
      http.get(`${API}/comercial/conversaciones`, () => HttpResponse.json([conversacion({ interesado_id: null })])),
      http.post(`${API}/comercial/conversaciones/:id/mensajes`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ mensaje_id: 'm3' }, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<ComercialPage />)
    await user.click(await screen.findByRole('tab', { name: 'Conversaciones' }))
    await user.click(await screen.findByRole('button', { name: 'Responder' }))
    const ventana = await screen.findByRole('dialog', { name: 'Responder a +57 300 555 1234' })
    await user.type(within(ventana).getByLabelText('Mensaje'), 'Hola')
    await user.click(within(ventana).getByRole('button', { name: 'Enviar' }))
    await waitFor(() => expect(enviado).toEqual({ texto: 'Hola' }))
  })

  it('dice por qué está vacía', async () => {
    const user = userEvent.setup()
    renderizar(<ComercialPage />)
    await user.click(await screen.findByRole('tab', { name: 'Conversaciones' }))
    expect(await screen.findByText(/Nadie espera a un asesor/)).toBeInTheDocument()
  })
})

describe('guion del asistente', () => {
  async function abrirGuion() {
    const user = userEvent.setup()
    renderizar(<ComercialPage />)
    await user.click(await screen.findByRole('tab', { name: 'Guion del asistente' }))
    return user
  }

  it('rechaza un JSON inválido sin llamar a la API', async () => {
    let llamadas = 0
    server.use(
      http.put(`${API}/comercial/arbol`, () => {
        llamadas += 1
        return HttpResponse.json({ version: 2 })
      }),
    )
    const user = await abrirGuion()
    const nodos = await screen.findByLabelText('Pasos (JSON)')
    await user.clear(nodos)
    await user.type(nodos, 'no es json')
    await user.click(screen.getByRole('button', { name: 'Publicar versión' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('El guion no es un JSON válido')
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
    const user = await abrirGuion()
    await screen.findByLabelText('Pasos (JSON)')
    await user.type(screen.getByLabelText('Qué cambia en esta versión'), ' Menú más corto ')
    await user.click(screen.getByRole('button', { name: 'Publicar versión' }))
    await waitFor(() => expect(enviado).toEqual({ nodos: { inicio: { mensaje: 'Hola', opciones: {} } }, nota: 'Menú más corto' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Versión publicada')
  })

  it('muestra por qué el backend rechazó el guion', async () => {
    server.use(http.put(`${API}/comercial/arbol`, () => HttpResponse.json({ detail: 'El nodo inicio no existe' }, { status: 422 })))
    const user = await abrirGuion()
    await screen.findByLabelText('Pasos (JSON)')
    await user.click(screen.getByRole('button', { name: 'Publicar versión' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('El nodo inicio no existe')
  })

  it('solo administración lo ve', async () => {
    server.use(http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'comercial' })))
    renderizar(<ComercialPage />)
    await screen.findByRole('tab', { name: 'Conversaciones' })
    await waitFor(() => expect(screen.queryByRole('tab', { name: 'Guion del asistente' })).not.toBeInTheDocument())
  })
})
