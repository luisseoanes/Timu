import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'

import { TareasPage } from './TareasPage'
import { sesionDe, USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { TareaListado } from '@/types'

const API = '*/api/v1'

const TAREA: TareaListado = {
  id: 't1',
  titulo: 'Llamar por cuota vencida',
  descripcion: null,
  area: 'cartera',
  prioridad: 'alta',
  estado: 'abierta',
  vence_el: '2026-10-20',
  asignada_a_id: null,
  familia_id: null,
  servicio_id: null,
  contrato_id: null,
  origen: null,
  creada_por_id: null,
  cerrada_en: null,
  resolucion: null,
  created_at: '2026-10-18T10:00:00Z',
  familia: null,
  servicio: null,
  creada_por: null,
  origen_nombre: null,
}

const pagina = (items: unknown[]) => ({ items, total: items.length, limit: 25, offset: 0 })

describe('TareasPage', () => {
  // Las tareas de cartera son de Atención al cliente: la bandeja se abre con su perfil.
  beforeEach(() => server.use(sesionDe('atencion_cliente')))

  it('dice en texto que una tarea está vencida y a quién afecta', async () => {
    server.use(
      http.get(`${API}/tareas`, () =>
        HttpResponse.json(
          pagina([
            {
              ...TAREA,
              familia_id: 'f1',
              servicio_id: 's1',
              familia: { id: 'f1', titular_nombre: 'Carlos Pérez' },
              servicio: { id: 's1', tipo_codigo: 'consulta_domiciliaria', mascota_nombre: 'Toby' },
            },
            { ...TAREA, id: 't2', titulo: 'Revisar contrato', vence_el: '2999-01-10' },
          ]),
        ),
      ),
    )
    renderizar(<TareasPage />)
    const vencida = (await screen.findByText('Llamar por cuota vencida')).closest('tr')!
    // Lo vencido no se dice solo en rojo: lleva la palabra y el icono.
    expect(vencida.querySelector('[data-etiqueta="Vence"]')).toHaveTextContent(/mar 20 oct ·\s*vencida$/)
    expect(within(vencida).getByText('Cartera')).toBeInTheDocument()
    expect(within(vencida).getByRole('link', { name: 'Carlos Pérez' })).toHaveAttribute('href', '/panel/familias/f1')
    expect(await within(vencida).findByRole('link', { name: 'Consulta domiciliaria de Toby' })).toHaveAttribute('href', '/panel/servicios/s1')
    const futura = screen.getByText('Revisar contrato').closest('tr')!
    expect(futura.querySelector('[data-etiqueta="Vence"]')).toHaveTextContent('jue 10 ene')
  })

  it('abre en las pendientes: una tarea iniciada sigue a la vista hasta cerrarla', async () => {
    const pedidas: (string | null)[] = []
    let estado = 'abierta'
    server.use(
      http.get(`${API}/tareas`, ({ request }) => {
        pedidas.push(new URL(request.url).searchParams.get('estado'))
        return HttpResponse.json(pagina([{ ...TAREA, asignada_a_id: USUARIO_ADMIN.id, estado }]))
      }),
      http.post(`${API}/tareas/t1/iniciar`, () => {
        estado = 'en_progreso'
        return HttpResponse.json({ ...TAREA, estado })
      }),
    )
    const user = userEvent.setup()
    renderizar(<TareasPage />)
    expect(await screen.findByText('Llamar por cuota vencida')).toBeInTheDocument()
    expect(screen.getByLabelText('Estado de la tarea')).toHaveValue('pendiente')
    await user.click(screen.getByRole('button', { name: 'Iniciar' }))
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Iniciar' })).not.toBeInTheDocument())
    expect(screen.getByText('Llamar por cuota vencida')).toBeInTheDocument()
    expect(new Set(pedidas)).toEqual(new Set(['pendiente']))
  })

  it('solo se asigna a quien ve el área de la tarea', async () => {
    server.use(
      http.get(`${API}/auth/equipo`, () =>
        HttpResponse.json([
          { id: 'u1', nombre: 'Mariana Ortiz', rol: 'atencion_cliente' },
          { id: 'u2', nombre: 'Valentina Ríos', rol: 'comercial' },
          { id: 'u3', nombre: 'Laura Gómez', rol: 'gerencia' },
          { id: 'u4', nombre: 'Dra. Sara Martínez', rol: 'medico' },
        ]),
      ),
      http.get(`${API}/tareas`, () =>
        HttpResponse.json(pagina([TAREA, { ...TAREA, id: 't2', titulo: 'Cotizar plan', area: 'servicio_cliente', asignada_a_id: 'u4' }])),
      ),
    )
    renderizar(<TareasPage />)
    const cartera = await screen.findByLabelText('Responsable de Llamar por cuota vencida')
    await waitFor(() => expect(within(cartera).getAllByRole('option')).toHaveLength(2))
    expect(within(cartera).getAllByRole('option').map((o) => o.textContent)).toEqual(['Sin asignar', 'Mariana Ortiz'])
    // Quien ya la tenía sigue en la lista aunque no sea de su área, para poder pasarla a otro.
    const comercial = screen.getByLabelText('Responsable de Cotizar plan')
    expect(within(comercial).getAllByRole('option').map((o) => o.textContent)).toEqual([
      'Sin asignar',
      'Mariana Ortiz',
      'Dra. Sara Martínez',
    ])
  })

  it('la tarea de una conversación con el asistente lleva a la conversación', async () => {
    server.use(
      http.get(`${API}/tareas`, () =>
        HttpResponse.json(pagina([{ ...TAREA, titulo: 'WhatsApp +573004445588: pasar a asesor', area: 'comercial', origen: 'conversacion' }])),
      ),
      sesionDe('comercial'),
    )
    renderizar(<TareasPage />)
    expect(await screen.findByRole('link', { name: 'Ver la conversación' })).toHaveAttribute(
      'href',
      '/panel/comercial?pestana=conversaciones',
    )
  })

  it('lista las tareas y se toma una sin asignar', async () => {
    let asignacion: unknown = null
    server.use(
      http.get(`${API}/tareas`, () => HttpResponse.json(pagina([TAREA]))),
      http.get(`${API}/auth/equipo`, () => HttpResponse.json([])),
      http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'atencion_cliente' })),
      http.patch(`${API}/tareas/t1/asignacion`, async ({ request }) => {
        asignacion = await request.json()
        return HttpResponse.json({ ...TAREA, asignada_a_id: USUARIO_ADMIN.id })
      }),
    )
    const user = userEvent.setup()
    renderizar(<TareasPage />)
    const fila = (await screen.findByText('Llamar por cuota vencida')).closest('tr')!
    expect(within(fila).getByText('Alta')).toBeInTheDocument()
    await user.click(within(fila).getByRole('button', { name: 'Tomar' }))
    await waitFor(() => expect(asignacion).toEqual({ usuario_id: USUARIO_ADMIN.id }))
  })

  it('dice quién pidió cada tarea y las pedidas a otra área se siguen sin trabajarlas', async () => {
    const pedidas: (string | null)[] = []
    server.use(
      sesionDe('comercial'),
      http.get(`${API}/tareas`, ({ request }) => {
        pedidas.push(new URL(request.url).searchParams.get('pedidas_por_mi'))
        return HttpResponse.json(
          pagina([
            {
              ...TAREA,
              titulo: 'Revisar la dirección de Ana',
              area: 'operaciones',
              creada_por_id: 'u2',
              creada_por: { id: 'u2', nombre: 'Valentina Ríos', rol: 'comercial' },
            },
            { ...TAREA, id: 't2', titulo: 'Gestionar renovación', area: 'comercial', origen: 'renovacion_30', origen_nombre: 'Gestionar renovación 30 días antes' },
          ]),
        )
      }),
    )
    const user = userEvent.setup()
    renderizar(<TareasPage />)
    await user.click(await screen.findByRole('button', { name: 'Pedidas por mí' }))
    await waitFor(() => expect(pedidas.at(-1)).toBe('true'))
    const pedida = (await screen.findByText('Revisar la dirección de Ana')).closest('tr')!
    expect(within(pedida).getByText('Pedida por Valentina Ríos (Comercial)')).toBeInTheDocument()
    // Es de Operaciones: se sigue, pero ni se toma, ni se cierra, ni se le cambia el responsable.
    expect(within(pedida).queryByRole('button', { name: 'Tomar' })).not.toBeInTheDocument()
    expect(within(pedida).queryByRole('button', { name: 'Cerrar' })).not.toBeInTheDocument()
    expect(within(pedida).queryByRole('combobox')).not.toBeInTheDocument()
    const automatica = screen.getByText('Gestionar renovación').closest('tr')!
    expect(within(automatica).getByText('Automática: «Gestionar renovación 30 días antes»')).toBeInTheDocument()
    expect(within(automatica).getByRole('button', { name: 'Cerrar' })).toBeInTheDocument()
  })

  it('cambia de vista y consulta con el filtro correspondiente', async () => {
    const consultas: string[] = []
    server.use(
      http.get(`${API}/tareas`, ({ request }) => {
        consultas.push(new URL(request.url).search)
        return HttpResponse.json(pagina([]))
      }),
    )
    const user = userEvent.setup()
    renderizar(<TareasPage />)
    expect(await screen.findByText(/no hay tareas en esta vista/i)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Vencidas' }))
    await waitFor(() => expect(consultas.some((c) => c.includes('vencidas=true'))).toBe(true))
  })

  it('cierra una tarea con su resolución', async () => {
    let cierre: unknown = null
    server.use(
      http.get(`${API}/tareas`, () => HttpResponse.json(pagina([TAREA]))),
      http.post(`${API}/tareas/t1/cerrar`, async ({ request }) => {
        cierre = await request.json()
        return HttpResponse.json({ ...TAREA, estado: 'cerrada' })
      }),
    )
    const user = userEvent.setup()
    renderizar(<TareasPage />)
    await user.click(await screen.findByRole('button', { name: 'Cerrar' }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Cómo se resolvió'), 'Pagó por transferencia')
    await user.click(within(modal).getByRole('button', { name: 'Cerrar tarea' }))
    await waitFor(() => expect(cierre).toEqual({ resolucion: 'Pagó por transferencia' }))
  })

  it('crea una tarea', async () => {
    let creada: unknown = null
    server.use(
      http.post(`${API}/tareas`, async ({ request }) => {
        creada = await request.json()
        return HttpResponse.json(TAREA, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<TareasPage />)
    await user.click(await screen.findByRole('button', { name: /nueva tarea/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Qué hay que hacer'), 'Confirmar dirección')
    await user.selectOptions(within(modal).getByLabelText('Prioridad'), 'alta')
    await user.type(within(modal).getByLabelText('Vence en (días)'), '2')
    await user.click(within(modal).getByRole('button', { name: 'Crear tarea' }))
    await waitFor(() =>
      expect(creada).toEqual({ titulo: 'Confirmar dirección', area: 'operaciones', prioridad: 'alta', vence_en_dias: 2 }),
    )
  })

  it('al crear, el responsable se elige solo entre quienes ven el área', async () => {
    let creada: unknown = null
    server.use(
      http.get(`${API}/auth/equipo`, () =>
        HttpResponse.json([
          { id: 'u1', nombre: 'Mariana Ortiz', rol: 'atencion_cliente' },
          { id: 'u3', nombre: 'Carlos Peña', rol: 'operaciones' },
          { id: 'u4', nombre: 'Laura Gómez', rol: 'gerencia' },
        ]),
      ),
      http.post(`${API}/tareas`, async ({ request }) => {
        creada = await request.json()
        return HttpResponse.json(TAREA, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<TareasPage />)
    await user.click(await screen.findByRole('button', { name: /nueva tarea/i }))
    const modal = await screen.findByRole('dialog')
    const responsable = within(modal).getByLabelText('Responsable (opcional)')
    await waitFor(() => expect(within(responsable).getAllByRole('option')).toHaveLength(2))
    expect(within(responsable).getAllByRole('option').map((o) => o.textContent)).toEqual(['La toma alguien del área', 'Carlos Peña'])
    await user.selectOptions(responsable, 'u3')
    // Otra área: el responsable de la anterior ya no vale.
    await user.selectOptions(within(modal).getByLabelText('¿Para qué área?'), 'cartera')
    expect(within(modal).getByLabelText('Responsable (opcional)')).toHaveValue('')
    await user.selectOptions(within(modal).getByLabelText('Responsable (opcional)'), 'u1')
    await user.type(within(modal).getByLabelText('Qué hay que hacer'), 'Llamar a Ana')
    await user.click(within(modal).getByRole('button', { name: 'Crear tarea' }))
    await waitFor(() => expect(creada).toMatchObject({ area: 'cartera', asignada_a_id: 'u1' }))
  })

  it('muestra el error del servidor', async () => {
    server.use(http.get(`${API}/tareas`, () => HttpResponse.json({ detail: 'Sin conexión a la base' }, { status: 503 })))
    renderizar(<TareasPage />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Sin conexión a la base')
  })
})
