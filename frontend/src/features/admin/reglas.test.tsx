import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { AdminPage } from './AdminPage'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { EventoDeReglas } from '@/types'

const API = '*/api/v1'

const base = [
  http.get(`${API}/auth/usuarios/recuentos`, () => HttpResponse.json({ equipo: 0, aliadas: 0, familias: 0, inactivos: 0 })),
  http.get(`${API}/auth/usuarios`, () => HttpResponse.json({ items: [], total: 0, limit: 25, offset: 0 })),
]

const REGLA = {
  id: 'rg1',
  codigo: 'alerta_mora_25',
  nombre: 'Aviso de mora a los 25 días',
  descripcion: null,
  evento: 'cartera.alerta',
  condicion: { op: 'gte', campo: 'dias_mora', valor: 25 },
  accion: { tipo: 'notificar', plantilla: 'aviso_congelamiento', clave: 'mora_25' },
  prioridad: 75,
  detener: false,
  plan_id: null,
  vigente_desde: null,
  vigente_hasta: null,
  activa: true,
  condicion_texto: 'Días de mora: al menos 25',
  accion_texto: 'Envía un aviso por WhatsApp (plantilla aviso_congelamiento)',
  evento_nombre: 'Avisos escalonados de mora',
  retirada: null,
  campos_condicion: [{ campo: 'dias_mora', nombre: 'Días de mora', numerico: true }],
}

const NUMERO = [
  { valor: 'gte', nombre: 'al menos' },
  { valor: 'gt', nombre: 'más de' },
  { valor: 'lte', nombre: 'como mucho' },
]
const OPCION = [
  { valor: 'eq', nombre: 'es' },
  { valor: 'ne', nombre: 'no es' },
  { valor: 'in', nombre: 'es uno de' },
  { valor: 'nin', nombre: 'no es ninguno de' },
]

// Lo que da `GET /reglas/eventos` (reglas/router.py: `eventos`) para dos eventos.
const EVENTOS: EventoDeReglas[] = [
  {
    evento: 'cartera.alerta',
    nombre: 'Avisos escalonados de mora',
    cuando: 'Cada día, en cada contrato con una cuota vencida.',
    admite_plan: false,
    campos: [{ campo: 'dias_mora', nombre: 'Días de mora', tipo: 'numero', operadores: NUMERO, opciones: null }],
    acciones: [
      {
        tipo: 'notificar',
        nombre: 'Avisar por WhatsApp',
        parametros: [
          {
            nombre: 'plantilla',
            etiqueta: 'Plantilla de WhatsApp',
            tipo: 'opcion',
            requerido: true,
            por_defecto: null,
            opciones: [
              { valor: 'aviso_congelamiento', nombre: 'aviso_congelamiento · sin registrar' },
              { valor: 'cuota_vencida', nombre: 'Cuota vencida' },
            ],
          },
        ],
      },
    ],
    planes: [],
  },
  {
    evento: 'servicio.elegibilidad',
    nombre: 'Restricciones para agendar',
    cuando: 'Al agendar un servicio: cada regla que se cumple lo impide y dice su motivo.',
    admite_plan: true,
    campos: [
      {
        campo: 'familia.ciudad',
        nombre: 'Ciudad de la familia',
        tipo: 'opcion',
        operadores: OPCION,
        opciones: [
          { valor: 'Bogotá', nombre: 'Bogotá' },
          { valor: 'Medellín', nombre: 'Medellín' },
        ],
      },
      {
        campo: 'familia.estado',
        nombre: 'Estado de la familia',
        tipo: 'opcion',
        operadores: OPCION,
        opciones: [
          { valor: 'activa', nombre: 'Al día' },
          { valor: 'en_mora', nombre: 'En mora' },
          { valor: 'congelada', nombre: 'Congelada' },
        ],
      },
    ],
    acciones: [
      {
        tipo: 'rechazar',
        nombre: 'No permitirlo',
        parametros: [{ nombre: 'motivo', etiqueta: 'Motivo que se le dice al equipo', tipo: 'texto', requerido: true, por_defecto: null, opciones: null }],
      },
    ],
    planes: [{ id: 'p1', nombre: 'Mi Amigo Fiel' }],
  },
]

/** `POST /reglas/describir`: guarda cada borrador y responde lo que diría el motor. */
function describir(borradores: unknown[], respuesta = { condicion_texto: 'Días de mora: al menos 20', accion_texto: 'Envía por WhatsApp «Cuota vencida»' }) {
  return http.post(`${API}/reglas/describir`, async ({ request }) => {
    borradores.push(await request.json())
    return HttpResponse.json(respuesta)
  })
}

/** Abre la ficha de la regla (`?regla=rg1`) y espera a su título. */
async function abrirFicha(ruta = '/panel/admin?regla=rg1', titulo = REGLA.nombre) {
  const user = userEvent.setup()
  renderizar(<AdminPage />, { ruta })
  await user.click(await screen.findByRole('tab', { name: 'Reglas' }))
  const ficha = await screen.findByRole('region', { name: 'Regla abierta' })
  await within(ficha).findByRole('heading', { level: 2, name: titulo })
  return { user, ficha }
}

/** Abre «Nueva regla» en «Restricciones para agendar». */
async function abrirNueva() {
  const user = userEvent.setup()
  renderizar(<AdminPage />)
  await user.click(await screen.findByRole('tab', { name: 'Reglas' }))
  await user.click(await screen.findByRole('button', { name: 'Nueva regla' }))
  const modal = await screen.findByRole('dialog', { name: 'Nueva regla' })
  await user.selectOptions(await within(modal).findByLabelText('Cuándo se revisa'), 'servicio.elegibilidad')
  return modal
}

describe('Administración: reglas', () => {
  it('agrupa por evento, dice en palabras cuándo aplica y qué hace, y desactiva', async () => {
    const cambios: unknown[] = []
    server.use(
      ...base,
      http.get(`${API}/reglas`, () => HttpResponse.json([REGLA])),
      http.patch(`${API}/reglas/rg1`, async ({ request }) => {
        cambios.push(await request.json())
        return HttpResponse.json(REGLA)
      }),
    )
    const user = userEvent.setup()
    renderizar(<AdminPage />)
    await user.click(await screen.findByRole('tab', { name: 'Reglas' }))
    // El grupo, por el nombre del evento que da la API.
    expect(
      await screen.findByText((_, el) => el?.classList.contains('servicios-dia-rotulo') === true && el.textContent === 'Avisos escalonados de mora · 1'),
    ).toBeInTheDocument()
    expect(screen.getByText('Días de mora: al menos 25')).toBeInTheDocument()
    // Sin una regla abierta, crear una es la acción verde.
    expect(screen.getByRole('button', { name: 'Nueva regla' })).toHaveClass('btn-primario')
    await user.click(screen.getByRole('link', { name: 'Aviso de mora a los 25 días' }))
    const ficha = screen.getByRole('region', { name: 'Regla abierta' })
    expect(await within(ficha).findByText(REGLA.accion_texto)).toBeInTheDocument()
    // Con la ficha abierta, el verde es «Editar regla».
    expect(screen.getByRole('button', { name: 'Nueva regla' })).toHaveClass('btn-suave')
    await user.click(within(ficha).getByRole('button', { name: 'Más acciones con Aviso de mora a los 25 días' }))
    await user.click(await screen.findByRole('menuitem', { name: 'Desactivar regla' }))
    await waitFor(() => expect(cambios).toEqual([{ activa: false }]))
  })

  it('edita por campos, dice la regla en palabras mientras se escribe y conserva la clave del aviso', async () => {
    const cambios: unknown[] = []
    const borradores: unknown[] = []
    server.use(
      ...base,
      http.get(`${API}/reglas`, () => HttpResponse.json([REGLA])),
      http.get(`${API}/reglas/eventos`, () => HttpResponse.json(EVENTOS)),
      describir(borradores),
      http.patch(`${API}/reglas/rg1`, async ({ request }) => {
        cambios.push(await request.json())
        return HttpResponse.json(REGLA)
      }),
    )
    const { user, ficha } = await abrirFicha()
    await user.click(within(ficha).getByRole('button', { name: 'Editar regla' }))
    const modal = await screen.findByRole('dialog', { name: 'Editar «Aviso de mora a los 25 días»' })
    const valor = await within(modal).findByRole('spinbutton', { name: 'Valor de la condición 1' })
    expect(valor).toHaveValue(25)
    expect(within(modal).getByRole('combobox', { name: 'Comparación de la condición 1' })).toHaveDisplayValue('al menos')
    await user.clear(valor)
    await user.type(valor, '20')
    await user.selectOptions(within(modal).getByLabelText('Plantilla de WhatsApp'), 'cuota_vencida')
    // La frase la rehace la API con lo escrito, sin guardar.
    const palabras = within(modal).getByRole('region', { name: 'La regla en palabras' })
    expect(await within(palabras).findByText('Envía por WhatsApp «Cuota vencida»')).toBeInTheDocument()
    await waitFor(() =>
      expect(borradores.at(-1)).toEqual({
        evento: 'cartera.alerta',
        condicion: { campo: 'dias_mora', op: 'gte', valor: 20 },
        accion: { tipo: 'notificar', plantilla: 'cuota_vencida' },
      }),
    )
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    await waitFor(() => expect(cambios).toHaveLength(1))
    // Sin la clave: la API conserva la que tenía y no repite avisos ya enviados.
    expect(cambios[0]).toEqual({
      nombre: 'Aviso de mora a los 25 días',
      descripcion: null,
      condicion: { campo: 'dias_mora', op: 'gte', valor: 20 },
      accion: { tipo: 'notificar', plantilla: 'cuota_vencida' },
      prioridad: 75,
      detener: false,
      plan_id: null,
      vigente_desde: null,
      vigente_hasta: null,
    })
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('crea una regla: elige cuándo se revisa, la escribe por campos y abre la regla creada', async () => {
    const creadas: unknown[] = []
    const CREADA = {
      ...REGLA,
      id: 'rg2',
      nombre: 'Sin domicilio en Medellín',
      evento: 'servicio.elegibilidad',
      evento_nombre: 'Restricciones para agendar',
    }
    let reglas = [REGLA]
    server.use(
      ...base,
      http.get(`${API}/reglas`, () => HttpResponse.json(reglas)),
      http.get(`${API}/reglas/eventos`, () => HttpResponse.json(EVENTOS)),
      describir([], { condicion_texto: 'Ciudad de la familia: Medellín', accion_texto: 'No lo permite: Al día primero' }),
      http.post(`${API}/reglas`, async ({ request }) => {
        creadas.push(await request.json())
        reglas = [REGLA, CREADA]
        return HttpResponse.json(CREADA, { status: 201 })
      }),
    )
    const modal = await abrirNueva()
    expect(within(modal).getByText(/^Al agendar un servicio/)).toBeInTheDocument()
    const user = userEvent.setup()
    await user.click(within(modal).getByLabelText('Nombre'))
    await user.paste('Sin domicilio en Medellín')
    expect(within(modal).getByText('Sin condiciones: aplica siempre.')).toBeInTheDocument()
    await user.click(within(modal).getByRole('button', { name: 'Añadir una condición' }))
    await user.selectOptions(within(modal).getByRole('combobox', { name: 'Valor de la condición 1' }), 'Medellín')
    await user.click(within(modal).getByLabelText('Motivo que se le dice al equipo'))
    await user.paste('Al día primero')
    await user.selectOptions(within(modal).getByLabelText('Planes'), 'p1')
    expect(await within(modal).findByText('No lo permite: Al día primero')).toBeInTheDocument()

    await user.click(within(modal).getByRole('button', { name: 'Crear regla' }))
    await waitFor(() => expect(creadas).toHaveLength(1))
    expect(creadas[0]).toEqual({
      nombre: 'Sin domicilio en Medellín',
      descripcion: null,
      evento: 'servicio.elegibilidad',
      condicion: { campo: 'familia.ciudad', op: 'eq', valor: 'Medellín' },
      accion: { tipo: 'rechazar', motivo: 'Al día primero' },
      prioridad: 100,
      detener: false,
      plan_id: 'p1',
      vigente_desde: null,
      vigente_hasta: null,
    })
    // Se abre la regla creada: lo siguiente es probarla. Se espera al título y no a la región: la
    // ficha vacía lleva el mismo nombre y se sustituye por la abierta.
    const titulo = await screen.findByRole('heading', { level: 2, name: 'Sin domicilio en Medellín' }, { timeout: 5000 })
    expect(titulo.closest('section')).toHaveAccessibleName('Regla abierta')
  })

  it('une condiciones con «al menos una» y compara con varios valores', async () => {
    const borradores: { condicion?: unknown }[] = []
    server.use(
      ...base,
      http.get(`${API}/reglas`, () => HttpResponse.json([REGLA])),
      http.get(`${API}/reglas/eventos`, () => HttpResponse.json(EVENTOS)),
      describir(borradores),
    )
    const modal = await abrirNueva()
    const user = userEvent.setup()
    await user.click(within(modal).getByRole('button', { name: 'Añadir una condición' }))
    await user.selectOptions(within(modal).getByRole('combobox', { name: 'Valor de la condición 1' }), 'Medellín')
    // La siguiente propone el dato que aún no se compara.
    await user.click(within(modal).getByRole('button', { name: 'Otra condición' }))
    expect(within(modal).getByRole('combobox', { name: 'Dato de la condición 2' })).toHaveDisplayValue('Estado de la familia')
    await user.selectOptions(within(modal).getByRole('combobox', { name: 'Comparación de la condición 2' }), 'in')
    const valores = within(modal).getByRole('group', { name: /Valor de la condición 2/ })
    await user.click(within(valores).getByRole('checkbox', { name: 'En mora' }))
    await user.click(within(valores).getByRole('checkbox', { name: 'Congelada' }))
    await user.selectOptions(within(modal).getByLabelText('Aplica si se cumplen'), 'alguna')
    await user.click(within(modal).getByLabelText('Motivo que se le dice al equipo'))
    await user.paste('Al día primero')
    await waitFor(() =>
      expect(borradores.at(-1)?.condicion).toEqual({
        alguna: [
          { campo: 'familia.ciudad', op: 'eq', valor: 'Medellín' },
          { campo: 'familia.estado', op: 'in', valor: ['en_mora', 'congelada'] },
        ],
      }),
    )
  })

  it('quita una condición, y sin ninguna la regla aplica siempre', async () => {
    const borradores: unknown[] = []
    server.use(
      ...base,
      http.get(`${API}/reglas`, () => HttpResponse.json([REGLA])),
      http.get(`${API}/reglas/eventos`, () => HttpResponse.json(EVENTOS)),
      describir(borradores, { condicion_texto: 'Siempre', accion_texto: REGLA.accion_texto }),
    )
    const { user, ficha } = await abrirFicha()
    await user.click(within(ficha).getByRole('button', { name: 'Editar regla' }))
    const modal = await screen.findByRole('dialog')
    await user.click(await within(modal).findByRole('button', { name: 'Quitar la condición 1' }))
    expect(within(modal).getByText('Sin condiciones: aplica siempre.')).toBeInTheDocument()
    expect(await within(modal).findByText('Siempre')).toBeInTheDocument()
    expect(borradores.at(-1)).toMatchObject({ condicion: {} })
  })

  it('una condición con grupos dentro de grupos se lee y se conserva al guardar', async () => {
    const cambios: Record<string, unknown>[] = []
    const ANIDADA = {
      ...REGLA,
      condicion: { todas: [{ campo: 'dias_mora', op: 'gte', valor: 5 }, { no: { campo: 'dias_mora', op: 'gt', valor: 30 } }] },
      condicion_texto: 'Días de mora: al menos 5 y No se cumple: Días de mora: más de 30',
    }
    server.use(
      ...base,
      http.get(`${API}/reglas`, () => HttpResponse.json([ANIDADA])),
      http.get(`${API}/reglas/eventos`, () => HttpResponse.json(EVENTOS)),
      describir([]),
      http.patch(`${API}/reglas/rg1`, async ({ request }) => {
        cambios.push((await request.json()) as Record<string, unknown>)
        return HttpResponse.json(ANIDADA)
      }),
    )
    const { user, ficha } = await abrirFicha()
    await user.click(within(ficha).getByRole('button', { name: 'Editar regla' }))
    const modal = await screen.findByRole('dialog')
    expect(await within(modal).findByText(/grupos dentro de grupos/)).toBeInTheDocument()
    expect(within(modal).queryByRole('button', { name: /condición/ })).not.toBeInTheDocument()
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    await waitFor(() => expect(cambios).toHaveLength(1))
    expect(cambios[0]).not.toHaveProperty('condicion')
  })

  it('dice lo que la API objeta del borrador y el error al guardar', async () => {
    server.use(
      ...base,
      http.get(`${API}/reglas`, () => HttpResponse.json([REGLA])),
      http.get(`${API}/reglas/eventos`, () => HttpResponse.json(EVENTOS)),
      http.post(`${API}/reglas/describir`, () => HttpResponse.json({ detail: '«Gotham» no está en el catálogo' }, { status: 422 })),
      http.patch(`${API}/reglas/rg1`, () => HttpResponse.json({ detail: '«Gotham» no está en el catálogo' }, { status: 422 })),
    )
    const { user, ficha } = await abrirFicha()
    await user.click(within(ficha).getByRole('button', { name: 'Editar regla' }))
    const modal = await screen.findByRole('dialog')
    const palabras = await within(modal).findByRole('region', { name: 'La regla en palabras' })
    expect(await within(palabras).findByText('«Gotham» no está en el catálogo')).toBeInTheDocument()
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('«Gotham» no está en el catálogo')
  })

  it('mientras falta un valor, no pide la regla en palabras', async () => {
    const borradores: unknown[] = []
    server.use(
      ...base,
      http.get(`${API}/reglas`, () => HttpResponse.json([REGLA])),
      http.get(`${API}/reglas/eventos`, () => HttpResponse.json(EVENTOS)),
      describir(borradores),
    )
    const { user, ficha } = await abrirFicha()
    await user.click(within(ficha).getByRole('button', { name: 'Editar regla' }))
    const modal = await screen.findByRole('dialog')
    await user.clear(await within(modal).findByRole('spinbutton', { name: 'Valor de la condición 1' }))
    expect(within(modal).getByText('Completa cada condición y lo que hace para leer la regla entera.')).toBeInTheDocument()
    const antes = borradores.length
    await new Promise((r) => setTimeout(r, 400))
    expect(borradores).toHaveLength(antes)
  })

  it('si no cargan los datos de las reglas, lo dice, ofrece reintentar y no deja guardar', async () => {
    server.use(
      ...base,
      http.get(`${API}/reglas`, () => HttpResponse.json([REGLA])),
      http.get(`${API}/reglas/eventos`, () => new HttpResponse(null, { status: 503 })),
    )
    const { user, ficha } = await abrirFicha()
    await user.click(within(ficha).getByRole('button', { name: 'Editar regla' }))
    const modal = await screen.findByRole('dialog')
    expect(await within(modal).findByRole('alert', {}, { timeout: 5000 })).toHaveTextContent('No fue posible cargar los datos de las reglas.')
    expect(within(modal).getByRole('button', { name: 'Guardar' })).toBeDisabled()
    // Un fallo pasajero se puede reintentar sin cerrar la ventana.
    expect(within(modal).getByRole('button', { name: 'Reintentar' })).toBeInTheDocument()
  })

  it('prueba la regla abierta con sus datos por nombre y dice en palabras qué aplicaría', async () => {
    const pruebas: unknown[] = []
    server.use(
      ...base,
      http.get(`${API}/reglas`, () => HttpResponse.json([REGLA])),
      http.post(`${API}/reglas/probar`, async ({ request }) => {
        const cuerpo = (await request.json()) as { contexto: { dias_mora?: number } }
        pruebas.push(cuerpo)
        return HttpResponse.json(
          (cuerpo.contexto.dias_mora ?? 0) >= 25
            ? [{ regla: 'alerta_mora_25', nombre: 'Aviso de mora a los 25 días', accion: {}, accion_texto: REGLA.accion_texto }]
            : [],
        )
      }),
    )
    const { user, ficha } = await abrirFicha()
    const probar = within(ficha).getByRole('region', { name: 'Probar esta regla' })
    await user.type(within(probar).getByLabelText('Días de mora'), '30')
    await user.click(within(probar).getByRole('button', { name: 'Probar' }))
    expect(await within(probar).findByRole('status')).toHaveTextContent('Esta regla aplica.')
    expect(within(probar).getByRole('list', { name: 'Reglas que aplicarían' })).toHaveTextContent(REGLA.accion_texto)
    expect(pruebas[0]).toEqual({ evento: 'cartera.alerta', contexto: { dias_mora: 30 } })
    const dias = within(probar).getByLabelText('Días de mora')
    await user.clear(dias)
    await user.type(dias, '3')
    await user.click(within(probar).getByRole('button', { name: 'Probar' }))
    expect(await within(probar).findByText('Esta regla no aplica con estos datos.')).toBeInTheDocument()
    expect(within(probar).getByText('Ninguna regla de este evento aplicaría.')).toBeInTheDocument()
  })

  it('una regla de un evento retirado dice por qué y no se edita', async () => {
    server.use(
      ...base,
      http.get(`${API}/reglas`, () =>
        HttpResponse.json([{ ...REGLA, evento: 'plan.mascota', evento_nombre: 'Precio por mascota', retirada: 'Lo sustituyen las tarifas por número de peludos' }]),
      ),
    )
    const { ficha } = await abrirFicha()
    expect(within(ficha).getByText(/^Evento retirado: lo sustituyen las tarifas/)).toBeInTheDocument()
    expect(within(ficha).queryByRole('button', { name: 'Editar regla' })).not.toBeInTheDocument()
    expect(within(ficha).queryByRole('region', { name: 'Probar esta regla' })).not.toBeInTheDocument()
  })

  it('una regla en la URL abre su pestaña', async () => {
    server.use(...base, http.get(`${API}/reglas`, () => HttpResponse.json([REGLA])))
    renderizar(<AdminPage />, { ruta: '/panel/admin?regla=rg1' })
    expect(await screen.findByRole('heading', { level: 2, name: REGLA.nombre })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Reglas' })).toHaveAttribute('aria-selected', 'true')
  })
})
