import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'

import { AdminPage } from './AdminPage'
import { PLAN, USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const API = '*/api/v1'

const OPERADOR = { id: 'u2', email: 'op@timu.co', telefono: null, nombre: 'Carlos Peña', rol: 'operaciones', activo: true }
const RECUENTOS = { equipo: 2, aliadas: 0, familias: 5, inactivos: 1 }

beforeEach(() => {
  server.use(
    http.get(`${API}/auth/usuarios/recuentos`, () => HttpResponse.json(RECUENTOS)),
    http.get(`${API}/auth/usuarios`, () => HttpResponse.json({ items: [], total: 0, limit: 25, offset: 0 })),
  )
})

describe('AdminPage', () => {
  it('el índice agrupa las diez secciones en cuatro apartados y marca la abierta (DEU-76)', async () => {
    renderizar(<AdminPage />, { ruta: '/panel/admin' })
    const indice = await screen.findByRole('navigation', { name: 'Secciones de administración' })
    const apartado = (titulo: string) => within(indice).getByRole('list', { name: titulo })
    const nombres = (titulo: string) => within(apartado(titulo)).getAllByRole('link').map((l) => l.textContent)
    expect(nombres('Equipo')).toEqual(['Usuarios'])
    expect(nombres('Planes y catálogos')).toEqual(['Planes', 'Catálogos'])
    expect(nombres('Automatizaciones')).toEqual(['Reglas', 'Plantillas de WhatsApp', 'Guion del asistente', 'Encuestas', 'Inteligencia artificial'])
    expect(nombres('TIMU y privacidad')).toEqual(['Datos de TIMU', 'Supresión de datos'])
    expect(within(indice).getByRole('link', { name: 'Usuarios' })).toHaveAttribute('aria-current', 'page')
    expect(within(indice).getByRole('link', { name: 'Supresión de datos' })).toHaveAttribute('href', '/panel/admin?pestana=supresion')
  })

  it('en el celular el índice es un selector que abre la sección (DEU-76)', async () => {
    const user = userEvent.setup()
    renderizar(<AdminPage />, { ruta: '/panel/admin' })
    await user.selectOptions(await screen.findByRole('combobox', { name: 'Sección' }), 'Supresión de datos')
    expect(await screen.findByLabelText('Documento del titular')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Supresión de datos' })).toHaveAttribute('aria-current', 'page')
  })

  it('cambia el perfil de un usuario, y no deja cambiarse ni desactivarse a sí mismo', async () => {
    let cambio: unknown = null
    server.use(
      http.get(`${API}/auth/usuarios`, () => HttpResponse.json({ items: [{ ...USUARIO_ADMIN, telefono: null }, OPERADOR], total: 2, limit: 25, offset: 0 })),
      http.patch(`${API}/auth/usuarios/u2`, async ({ request }) => {
        cambio = await request.json()
        return HttpResponse.json({ ...OPERADOR, rol: 'medico' })
      }),
    )
    const user = userEvent.setup()
    renderizar(<AdminPage />)
    const perfil = await screen.findByLabelText('Perfil de Carlos Peña')
    // Una cuenta de clínica aliada necesita su clínica: no se ofrece en la fila.
    expect(within(perfil).queryByRole('option', { name: 'Clínica aliada' })).not.toBeInTheDocument()
    await user.selectOptions(perfil, 'medico')
    // Cambiarlo cierra sus sesiones: nada se envía hasta confirmarlo.
    const ventana = await screen.findByRole('dialog', { name: '¿Carlos Peña pasa a Médico veterinario?' })
    expect(cambio).toBeNull()
    await user.click(within(ventana).getByRole('button', { name: 'Cambiar el perfil' }))
    await waitFor(() => expect(cambio).toEqual({ rol: 'medico' }))
    const yo = screen.getByText('Tú').closest('tr')!
    expect(within(yo).queryByRole('combobox')).not.toBeInTheDocument()
    expect(within(yo).queryByRole('button', { name: /desactivar/i })).not.toBeInTheDocument()
  })

  it('las vistas llevan su recuento y piden su grupo, con la búsqueda', async () => {
    const pedidas: string[] = []
    server.use(
      http.get(`${API}/auth/usuarios`, ({ request }) => {
        const p = new URL(request.url).searchParams
        pedidas.push(`${p.get('grupo')}|${p.get('q') ?? ''}`)
        return HttpResponse.json({ items: [], total: 0, limit: 25, offset: 0 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<AdminPage />)
    expect(await screen.findByText('No hay nadie activo en el equipo.')).toBeInTheDocument()
    await user.click(await screen.findByRole('button', { name: 'Familias 5' }))
    expect(await screen.findByText('Ninguna familia tiene acceso al portal todavía.')).toBeInTheDocument()
    await user.type(screen.getByLabelText('Buscar usuarios'), 'ana')
    await waitFor(() => expect(pedidas).toContain('familias|ana'))
    expect(pedidas[0]).toBe('equipo|')
    expect(await screen.findByText('Nadie de esta vista coincide con la búsqueda.')).toBeInTheDocument()
  })

  it('desactiva tras confirmarlo en rojo y reactiva desde inactivos', async () => {
    const cambios: unknown[] = []
    server.use(
      http.get(`${API}/auth/usuarios`, ({ request }) =>
        HttpResponse.json({
          items: [new URL(request.url).searchParams.get('grupo') === 'inactivos' ? { ...OPERADOR, activo: false } : OPERADOR],
          total: 1,
          limit: 25,
          offset: 0,
        }),
      ),
      http.patch(`${API}/auth/usuarios/u2`, async ({ request }) => {
        cambios.push(await request.json())
        return HttpResponse.json(OPERADOR)
      }),
    )
    const user = userEvent.setup()
    renderizar(<AdminPage />)
    await user.click(await screen.findByRole('button', { name: 'Desactivar a Carlos Peña' }))
    const ventana = await screen.findByRole('dialog', { name: 'Desactivar a Carlos Peña' })
    expect(cambios).toEqual([])
    const confirmar = within(ventana).getByRole('button', { name: 'Desactivar' })
    expect(confirmar).toHaveClass('btn-peligro')
    await user.click(confirmar)
    await waitFor(() => expect(cambios).toEqual([{ activo: false }]))
    await user.click(screen.getByRole('button', { name: 'Inactivos 1' }))
    await user.click(await screen.findByRole('button', { name: 'Activar a Carlos Peña' }))
    await waitFor(() => expect(cambios).toEqual([{ activo: false }, { activo: true }]))
  })

  it('gestiona a todo el equipo: en la fila y al crear se ofrecen los seis perfiles', async () => {
    // Sección 12: Gerencia y Atención al cliente también se crean y se cambian desde aquí.
    const PERFILES = ['Administración', 'Gerencia', 'Comercial', 'Atención al cliente', 'Operaciones', 'Médico veterinario']
    const ATENCION = { ...OPERADOR, id: 'u3', nombre: 'Mariana Ortiz', rol: 'atencion_cliente' }
    let cambio: unknown = null
    server.use(
      http.get(`${API}/auth/usuarios`, () => HttpResponse.json({ items: [ATENCION], total: 1, limit: 25, offset: 0 })),
      http.patch(`${API}/auth/usuarios/u3`, async ({ request }) => {
        cambio = await request.json()
        return HttpResponse.json({ ...ATENCION, rol: 'gerencia' })
      }),
    )
    const user = userEvent.setup()
    renderizar(<AdminPage />)
    const perfil = await screen.findByLabelText('Perfil de Mariana Ortiz')
    expect(within(perfil).getAllByRole('option').map((o) => o.textContent)).toEqual(PERFILES)
    await user.selectOptions(perfil, 'gerencia')
    const ventana = await screen.findByRole('dialog', { name: '¿Mariana Ortiz pasa a Gerencia?' })
    await user.click(within(ventana).getByRole('button', { name: 'Cambiar el perfil' }))
    await waitFor(() => expect(cambio).toEqual({ rol: 'gerencia' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: /nuevo usuario/i }))
    const modal = await screen.findByRole('dialog')
    expect(within(within(modal).getByLabelText('Perfil')).getAllByRole('option').map((o) => o.textContent)).toEqual([
      ...PERFILES,
      'Clínica aliada',
    ])
  })

  it('crea un usuario de clínica aliada con su clínica', async () => {
    let creado: unknown = null
    server.use(
      http.get(`${API}/auth/usuarios`, () => HttpResponse.json({ items: [], total: 0, limit: 200, offset: 0 })),
      http.get(`${API}/aliadas`, () => HttpResponse.json([{ id: 'cl1', nombre: 'Clínica Norte', ciudad: 'Bogotá', activa: true }])),
      http.post(`${API}/auth/usuarios`, async ({ request }) => {
        creado = await request.json()
        return HttpResponse.json({}, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<AdminPage />)
    await user.click(await screen.findByRole('button', { name: /nuevo usuario/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nombre'), 'Recepción Norte')
    await user.type(within(modal).getByLabelText('Correo'), 'norte@aliada.co')
    await user.selectOptions(within(modal).getByLabelText('Perfil'), 'aliada')
    await user.type(within(modal).getByLabelText('Contraseña inicial'), 'segura1234')
    await waitFor(() => expect(within(modal).getByRole('option', { name: 'Clínica Norte' })).toBeInTheDocument())
    await user.selectOptions(within(modal).getByLabelText('Clínica aliada'), 'cl1')
    await user.click(within(modal).getByRole('button', { name: 'Crear usuario' }))
    await waitFor(() =>
      expect(creado).toEqual({ nombre: 'Recepción Norte', email: 'norte@aliada.co', rol: 'aliada', password: 'segura1234', clinica_aliada_id: 'cl1' }),
    )
  })

  it('muestra los planes con sus beneficios', async () => {
    server.use(
      http.get(`${API}/auth/usuarios`, () => HttpResponse.json({ items: [], total: 0, limit: 200, offset: 0 })),
      http.get(`${API}/planes`, () =>
        HttpResponse.json([
          {
            ...PLAN,
            beneficios: [{ id: 'b1', tipo_servicio_codigo: 'consulta_domiciliaria', cupo: 6, periodo_cupo: 'anual', cobertura_pct: 100, copago: '0' }],
          },
        ]),
      ),
    )
    const user = userEvent.setup()
    renderizar(<AdminPage />)
    await user.click(await screen.findByRole('link', { name: 'Planes' }))
    await user.click(await screen.findByRole('link', { name: 'Colita Feliz' }))
    const ficha = screen.getByRole('region', { name: 'Plan abierto' })
    const beneficio = (await within(ficha).findByText('6 al año')).closest('tr')!
    expect(within(beneficio).getByRole('cell', { name: /consulta/i })).toBeInTheDocument()
  })

  it('una versión de prompt sólo se activa si pasa todos sus casos', async () => {
    server.use(
      http.get(`${API}/auth/usuarios`, () => HttpResponse.json({ items: [], total: 0, limit: 200, offset: 0 })),
      http.get(`${API}/ia/consumo`, () => HttpResponse.json({ mes: '2026-10', gasto_usd: 12.5, presupuesto_usd: 50, disponible_usd: 37.5, por_prompt: [] })),
      http.get(`${API}/ia/prompts`, () =>
        HttpResponse.json([{ id: 'pr1', codigo: 'comercial_guion', version: 2, sistema: 'Eres el asesor…', estado: 'borrador', nota: null, evaluado_en: null, evaluacion: {} }]),
      ),
      http.get(`${API}/ia/casos`, () => HttpResponse.json([])),
      http.get(`${API}/ia/consultas`, () => HttpResponse.json([])),
      http.post(`${API}/ia/prompts/pr1/evaluacion`, () =>
        HttpResponse.json({ total: 2, aprobados: 1, detalle: [{ caso: 'Precio', aprobado: false, motivo: 'alcance distinto' }], en: '' }),
      ),
    )
    const user = userEvent.setup()
    renderizar(<AdminPage />)
    await user.click(await screen.findByRole('link', { name: 'Inteligencia artificial' }))
    expect(await screen.findByText(/^US\$\s12,50$/)).toBeInTheDocument()
    const activar = await screen.findByRole('button', { name: 'Activar' })
    expect(activar).toBeDisabled()
    await user.click(screen.getByRole('button', { name: 'Correr casos' }))
    expect(await screen.findByText(/1 de 2 casos aprobados · Precio: alcance distinto/)).toBeInTheDocument()
    expect(activar).toBeDisabled()
  })
})
