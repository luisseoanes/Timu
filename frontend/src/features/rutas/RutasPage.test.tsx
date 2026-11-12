import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'

import { RutasPage } from './RutasPage'
import { hoyISO } from '@/lib/formato'
import { USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { ParadaRead, PorRutearRead, RutaRead } from '@/types'

const API = '*/api/v1'
const MEDICA = { id: 'm1', nombre: 'Dra. Sara', rol: 'medico' }
const YO_MEDICA = { ...USUARIO_ADMIN, id: MEDICA.id, rol: 'medico' }

const FAMILIAS = ['Ana Ruiz', 'Carlos Perez', 'Laura Gomez', 'Jorge Ramirez']
const DIRECCIONES = ['Calle 80 # 15-20', 'Carrera 7 # 120-45', 'Avenida 19 # 100-12', 'Calle 140 # 9-30']

function parada(orden: number, estado: ParadaRead['estado'], extra: Partial<ParadaRead> = {}): ParadaRead {
  return {
    id: `p${orden}`,
    servicio_id: `s${orden}`,
    orden,
    estado,
    latitud: 4.7,
    longitud: -74.05,
    // 15:20 UTC son las 10:20 de la mañana en Bogotá.
    llegada_estimada: '2026-10-24T15:20:00Z',
    llegada_en: estado === 'completada' || estado === 'en_sitio' ? '2026-10-24T13:04:00Z' : null,
    salida_en: estado === 'completada' ? '2026-10-24T13:41:00Z' : null,
    nota: null,
    motivo_omision: estado === 'omitida' ? 'La familia no estaba' : null,
    tipo_codigo: 'consulta_domiciliaria',
    observaciones: 'Portería: anunciarse como TIMU',
    ventana_desde: '2026-10-24T15:00:00Z',
    ventana_hasta: '2026-10-24T16:00:00Z',
    familia: {
      id: `f${orden}`,
      titular_nombre: FAMILIAS[orden - 1],
      telefono: '+573001112233',
      direccion: DIRECCIONES[orden - 1],
      complemento: 'Apto 902',
      barrio: 'Chapinero',
    },
    mascota: { id: `m${orden}`, nombre: 'Max', especie: 'perro', fecha_nacimiento: '2020-09-09', peso_kg: 24 },
    ...extra,
  }
}

function ruta(paradas: ParadaRead[], extra: Partial<RutaRead> = {}): RutaRead {
  return {
    id: 'r1',
    fecha: '2026-10-24',
    ciudad: 'Bogota',
    responsable_id: MEDICA.id,
    estado: 'en_curso',
    distancia_km: 13.8,
    duracion_min: 82,
    inicio_real: null,
    fin_real: null,
    paradas,
    ...extra,
  }
}

const POR_RUTEAR: PorRutearRead = {
  id: 's9',
  familia_id: 'f9',
  ciudad: 'Bogota',
  programado_para: '2026-10-24T19:00:00Z',
  tipo_codigo: 'consulta_domiciliaria',
  observaciones: null,
  ventana_desde: '2026-10-24T19:00:00Z',
  ventana_hasta: '2026-10-24T20:00:00Z',
  familia: { id: 'f9', titular_nombre: 'Marcela Torres', telefono: '+573009998877', direccion: 'Calle 53 # 20-11', complemento: null, barrio: 'Galerías' },
  mascota: { id: 'm9', nombre: 'Simba', especie: 'gato', fecha_nacimiento: null, peso_kg: null },
}

/** El resumen de la ruta propia, leído como texto corrido: va en piezas que se parten por separado. */
const resumenPropio = (texto: string) =>
  screen.getByText((_, el) => el?.tagName === 'P' && el.textContent?.replace(/\s+/g, ' ').trim() === texto)

/** Los pasos obligatorios de una consulta domiciliaria, ya registrados (TIPOS_SERVICIO). */
const PASOS_HECHOS = ['valoracion', 'plan'].map((paso_codigo) => ({
  paso_codigo,
  datos: {},
  completado_por_id: MEDICA.id,
  created_at: '2026-10-24T13:30:00Z',
}))

/** Las rutas que devuelve la API y con qué filtros se pidieron la última vez. */
function conRutas(rutas: RutaRead[], porRutear: PorRutearRead[] = []) {
  const pedido = { rutas: new URLSearchParams(), porRutear: new URLSearchParams() }
  server.use(
    http.get(`${API}/rutas/por-rutear`, ({ request }) => {
      pedido.porRutear = new URL(request.url).searchParams
      return HttpResponse.json(porRutear)
    }),
    http.get(`${API}/rutas`, ({ request }) => {
      pedido.rutas = new URL(request.url).searchParams
      return HttpResponse.json(rutas)
    }),
  )
  return pedido
}

beforeEach(() => {
  server.use(http.get(`${API}/auth/equipo`, () => HttpResponse.json([MEDICA])))
})

describe('la ruta de quien sale a campo', () => {
  beforeEach(() => {
    server.use(http.get(`${API}/auth/me`, () => HttpResponse.json(YO_MEDICA)))
  })

  it('abre en su ruta de hoy: pide solo la suya y la parada que sigue dice a dónde ir y a quién atiende', async () => {
    const pedido = conRutas([ruta([parada(1, 'completada'), parada(2, 'en_camino'), parada(3, 'pendiente')])])
    renderizar(<RutasPage />)

    expect(await screen.findByRole('heading', { name: 'Carrera 7 # 120-45' })).toBeInTheDocument()
    expect(pedido.rutas.get('responsable_id')).toBe(MEDICA.id)
    expect(pedido.rutas.get('fecha')).toBe(hoyISO())
    expect(resumenPropio('1 de 3 paradas · 13,8 km · hasta las 10:20 a. m.')).toBeInTheDocument()
    expect(screen.getByText('Apto 902 · Chapinero')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Carlos Perez' })).toHaveAttribute('href', '/familias/f2')
    expect(screen.getByText(/Max, perro de \d+ años, 24 kg/)).toBeInTheDocument()
    // La franja acordada con la familia, en la parada que toca y en la que falta.
    expect(screen.getAllByText(/franja 10:00 – 11:00 a\.\sm\./)).toHaveLength(2)
    expect(screen.getByRole('link', { name: 'Cómo llegar' })).toHaveAttribute(
      'href',
      'https://www.google.com/maps/dir/?api=1&destination=4.7%2C-74.05',
    )
    expect(screen.getByRole('link', { name: 'Llamar a Carlos Perez' })).toHaveAttribute('href', 'tel:+573001112233')
    // No coordina: ni el listado de todas las rutas ni planear.
    expect(screen.queryByRole('button', { name: /planear rutas/i })).not.toBeInTheDocument()
  })

  it('pliega las paradas hechas y las muestra al pedirlas', async () => {
    conRutas([ruta([parada(1, 'completada', { nota: 'Todo en orden' }), parada(2, 'completada'), parada(3, 'en_camino'), parada(4, 'pendiente')])])
    const user = userEvent.setup()
    renderizar(<RutasPage />)

    const paradas = await screen.findByRole('list', { name: 'Paradas de la ruta' })
    expect(within(paradas).queryByText('Ana Ruiz · Max')).not.toBeInTheDocument()
    const hechas = within(paradas).getByRole('button', { name: '2 hechas' })
    expect(hechas).toHaveAttribute('aria-expanded', 'false')
    await user.click(hechas)
    expect(hechas).toHaveAttribute('aria-expanded', 'true')
    expect(within(paradas).getByText('Ana Ruiz · Max')).toBeInTheDocument()
    expect(within(paradas).getByText('Nota: Todo en orden')).toBeInTheDocument()
    expect(within(paradas).getAllByText('Completada')).toHaveLength(2)
    // La misma pastilla las vuelve a plegar, y el foco sigue en ella.
    await user.click(hechas)
    expect(within(paradas).queryByText('Ana Ruiz · Max')).not.toBeInTheDocument()
    expect(hechas).toHaveFocus()
  })

  it('una ruta terminada muestra todas sus paradas, sin plegar', async () => {
    conRutas([ruta([parada(1, 'completada'), parada(2, 'completada')], { estado: 'finalizada' })])
    renderizar(<RutasPage />)
    expect(await screen.findByText('Carlos Perez · Max')).toBeInTheDocument()
    expect(screen.getByText('Ana Ruiz · Max')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /hechas?$/ })).not.toBeInTheDocument()
  })

  it('inicia su ruta planificada desde la primera parada', async () => {
    let iniciada = false
    conRutas([ruta([parada(1, 'pendiente'), parada(2, 'pendiente')], { estado: 'planificada' })])
    server.use(
      http.post(`${API}/rutas/r1/inicio`, () => {
        iniciada = true
        return HttpResponse.json(ruta([parada(1, 'pendiente'), parada(2, 'pendiente')]))
      }),
    )
    const user = userEvent.setup()
    renderizar(<RutasPage />)
    expect(await screen.findByText('Próxima')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Iniciar ruta' }))
    await waitFor(() => expect(iniciada).toBe(true))
  })

  it('la parada que toca lleva una sola acción de estado: salir hacia la familia y después llegar', async () => {
    const acciones: string[] = []
    conRutas([ruta([parada(1, 'pendiente'), parada(2, 'pendiente')])])
    server.use(
      http.post(`${API}/rutas/paradas/p1/:accion`, ({ params }) => {
        acciones.push(String(params.accion))
        // La pantalla vuelve a pedir las rutas: la parada ya va en camino.
        conRutas([ruta([parada(1, 'en_camino'), parada(2, 'pendiente')])])
        return HttpResponse.json(ruta([parada(1, 'en_camino'), parada(2, 'pendiente')]))
      }),
    )
    const user = userEvent.setup()
    renderizar(<RutasPage />)

    const salir = await screen.findByRole('button', { name: 'Voy en camino' })
    expect(screen.queryByRole('button', { name: 'Llegué' })).not.toBeInTheDocument()
    await user.click(salir)
    await user.click(await screen.findByRole('button', { name: 'Llegué' }))
    expect(screen.queryByRole('button', { name: 'Voy en camino' })).not.toBeInTheDocument()
    await waitFor(() => expect(acciones).toEqual(['en-camino', 'llegada']))
    expect(screen.getByText('En camino')).toBeInTheDocument()
  })

  it('quien ya está en la puerta registra la llegada sin avisar que va en camino', async () => {
    const acciones: string[] = []
    conRutas([ruta([parada(1, 'pendiente')])])
    server.use(
      http.post(`${API}/rutas/paradas/p1/:accion`, ({ params }) => {
        acciones.push(String(params.accion))
        return HttpResponse.json(ruta([parada(1, 'en_sitio')]))
      }),
    )
    const user = userEvent.setup()
    renderizar(<RutasPage />)
    await user.click(await screen.findByRole('button', { name: 'Más acciones con Ana Ruiz' }))
    await user.click(await screen.findByRole('menuitem', { name: 'Ya llegué' }))
    await waitFor(() => expect(acciones).toEqual(['llegada']))
  })

  it('termina la visita con una nota', async () => {
    let cuerpo = ''
    conRutas([ruta([parada(1, 'completada'), parada(2, 'en_sitio')])])
    server.use(
      http.get(`${API}/servicios/s2/pasos`, () => HttpResponse.json(PASOS_HECHOS)),
      http.post(`${API}/rutas/paradas/p2/salida`, async ({ request }) => {
        // En jsdom el parser multipart no acepta el formulario: se lee como texto.
        cuerpo = await request.text()
        return HttpResponse.json(ruta([parada(1, 'completada'), parada(2, 'completada')]))
      }),
    )
    const user = userEvent.setup()
    renderizar(<RutasPage />)
    expect(await screen.findByText(/Llegó 8:04/)).toBeInTheDocument()
    await user.click(await screen.findByRole('button', { name: 'Terminar visita' }))
    const modal = await screen.findByRole('dialog', { name: 'Terminar visita' })
    await user.type(within(modal).getByLabelText('Nota de la visita (opcional)'), 'Todo en orden')
    await user.click(within(modal).getByRole('button', { name: 'Registrar salida' }))
    await waitFor(() => expect(cuerpo).toContain('Todo en orden'))
  })

  it('sin los pasos obligatorios del servicio no ofrece terminar: lleva a registrar la atención y dice qué falta', async () => {
    conRutas([ruta([parada(1, 'en_sitio')])])
    server.use(http.get(`${API}/servicios/s1/pasos`, () => HttpResponse.json([PASOS_HECHOS[0]])))
    renderizar(<RutasPage />)
    const registrar = await screen.findByRole('link', { name: 'Registrar la atención' })
    expect(registrar).toHaveAttribute('href', '/servicios/s1')
    expect(registrar).toHaveClass('btn-primario')
    expect(screen.getByText('Antes de terminar la visita falta registrar: Plan y recomendaciones.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Terminar visita' })).not.toBeInTheDocument()
  })

  it('el fallo al avanzar una parada se dice con la causa del servidor', async () => {
    conRutas([ruta([parada(1, 'en_camino')])])
    server.use(
      http.post(`${API}/rutas/paradas/p1/llegada`, () =>
        HttpResponse.json({ detail: 'La ruta no esta en curso' }, { status: 422 }),
      ),
    )
    const user = userEvent.setup()
    renderizar(<RutasPage />)
    await user.click(await screen.findByRole('button', { name: 'Llegué' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('La ruta no esta en curso')
  })

  it('omite una parada desde su menú, con el motivo, y la confirmación va en rojo', async () => {
    let pedido: unknown = null
    conRutas([ruta([parada(1, 'en_camino'), parada(2, 'pendiente')])])
    server.use(
      http.post(`${API}/rutas/paradas/p1/omision`, async ({ request }) => {
        pedido = await request.json()
        return HttpResponse.json(ruta([parada(1, 'omitida'), parada(2, 'pendiente')]))
      }),
    )
    const user = userEvent.setup()
    renderizar(<RutasPage />)
    await user.click(await screen.findByRole('button', { name: 'Más acciones con Ana Ruiz' }))
    await user.click(await screen.findByRole('menuitem', { name: 'Omitir parada' }))
    const modal = await screen.findByRole('dialog', { name: 'Omitir parada' })
    await user.type(within(modal).getByLabelText('Motivo'), 'La familia no estaba')
    await user.click(within(modal).getByRole('checkbox', { name: /cancelar también el servicio/i }))
    expect(within(modal).getByRole('button', { name: 'Omitir parada' })).toHaveClass('btn-peligro')
    await user.click(within(modal).getByRole('button', { name: 'Omitir parada' }))
    await waitFor(() => expect(pedido).toEqual({ motivo: 'La familia no estaba', cancelar_servicio: true }))
  })

  it('una parada omitida sale de la línea y queda aparte con su motivo', async () => {
    conRutas([ruta([parada(1, 'pendiente'), parada(2, 'omitida')])])
    renderizar(<RutasPage />)
    const paradas = await screen.findByRole('list', { name: 'Paradas de la ruta' })
    expect(within(paradas).queryByText(/Carlos Perez/)).not.toBeInTheDocument()
    const omitidas = screen.getByRole('region', { name: 'Omitidas' })
    expect(within(omitidas).getByText('Carlos Perez · Max')).toBeInTheDocument()
    expect(within(omitidas).getByText(/La familia no estaba/)).toBeInTheDocument()
    expect(resumenPropio('0 de 1 parada · 13,8 km · hasta las 10:20 a. m.')).toBeInTheDocument()
  })

  it('abre una parada que falta para ver su dirección y cómo llegar, sin acción de estado', async () => {
    conRutas([ruta([parada(1, 'en_camino'), parada(2, 'pendiente', { familia: { ...parada(2, 'pendiente').familia, direccion: null, complemento: null } })])])
    const user = userEvent.setup()
    renderizar(<RutasPage />)
    const resumen = await screen.findByRole('button', { name: /Carlos Perez · Max/ })
    expect(resumen).toHaveAttribute('aria-expanded', 'false')
    // El nombre del servicio llega con el catálogo.
    await waitFor(() => expect(resumen).toHaveTextContent('Consulta domiciliaria · Chapinero'))
    await user.click(resumen)
    expect(resumen).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByRole('heading', { name: 'Sin dirección registrada' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Llamar a Carlos Perez' })).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Llegué' })).toHaveLength(1)
  })

  it('el menú de la parada lleva a WhatsApp, al servicio y a la historia clínica de la mascota', async () => {
    conRutas([ruta([parada(1, 'en_camino')])])
    const user = userEvent.setup()
    renderizar(<RutasPage />)
    await user.click(await screen.findByRole('button', { name: 'Más acciones con Ana Ruiz' }))
    expect(await screen.findByRole('menuitem', { name: 'Escribir por WhatsApp' })).toHaveAttribute('href', 'https://wa.me/573001112233')
    expect(screen.getByRole('menuitem', { name: 'Ver el servicio' })).toHaveAttribute('href', '/servicios/s1')
    expect(screen.getByRole('menuitem', { name: 'Historia clínica de Max' })).toHaveAttribute('href', '/clinica/mascotas/m1')
    // Sin haber salido aún, llegar sin avisar no aplica.
    expect(screen.queryByRole('menuitem', { name: 'Ya llegué' })).not.toBeInTheDocument()
  })

  it('sin ruta dice por qué y qué hacer', async () => {
    conRutas([])
    renderizar(<RutasPage />)
    expect(await screen.findByText(/No tienes ruta para hoy\. Operaciones la planea/)).toBeInTheDocument()
  })

  it('con dos rutas el mismo día las muestra por separado y suma su avance', async () => {
    conRutas([
      ruta([parada(1, 'completada')], { estado: 'finalizada' }),
      ruta([parada(2, 'pendiente'), parada(3, 'pendiente')], { id: 'r2', estado: 'planificada', distancia_km: 6.2 }),
    ])
    renderizar(<RutasPage />)
    expect(await screen.findByRole('heading', { name: 'Ruta 1 · 1 de 1 parada · 13,8 km' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Ruta 2 · 0 de 2 paradas · 6,2 km' })).toBeInTheDocument()
    expect(resumenPropio('1 de 3 paradas · 20 km')).toBeInTheDocument()
  })

  it('cambia de día, lo dice en palabras y vuelve a hoy', async () => {
    const pedido = conRutas([])
    const user = userEvent.setup()
    renderizar(<RutasPage />)
    await screen.findByText(/No tienes ruta para hoy/)
    expect(screen.getByText('Hoy')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Día de las rutas'), { target: { value: '2026-10-24' } })
    expect(await screen.findByText(/No tienes ruta para el sábado, 24 de octubre/)).toBeInTheDocument()
    expect(screen.getByText('sáb 24 oct')).toBeInTheDocument()
    expect(pedido.rutas.get('fecha')).toBe('2026-10-24')
    await user.click(screen.getByRole('button', { name: 'Volver a hoy' }))
    expect(await screen.findByText(/No tienes ruta para hoy/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Volver a hoy' })).not.toBeInTheDocument()
  })

  it('si la ruta no carga, avisa y deja reintentar', async () => {
    server.use(http.get(`${API}/rutas`, () => new HttpResponse(null, { status: 503 })))
    renderizar(<RutasPage />)
    const aviso = await screen.findByRole('alert')
    expect(aviso).toHaveTextContent('No fue posible cargar tu ruta.')
    expect(within(aviso).getByRole('button', { name: 'Reintentar' })).toBeInTheDocument()
  })
})

describe('las rutas del día para quien coordina', () => {
  it('lista cada ruta con su responsable, su avance y su línea, y lo que falta por rutear', async () => {
    const pedido = conRutas([ruta([parada(1, 'completada'), parada(2, 'en_sitio')])], [POR_RUTEAR])
    renderizar(<RutasPage />)

    expect(await screen.findByRole('link', { name: 'Dra. Sara' })).toHaveAttribute('href', '/rutas?ruta=r1')
    expect(screen.getByText('1 de 2 paradas · 13,8 km · Bogota')).toBeInTheDocument()
    expect(screen.getByRole('img', { name: /^1 de 2 paradas hechas\. Sigue Carlos Perez/ })).toBeInTheDocument()
    // Sin ciudad elegida se piden las de todas, y cada domicilio dice la suya.
    expect(pedido.rutas.get('ciudad')).toBeNull()
    expect(pedido.rutas.get('responsable_id')).toBeNull()
    const porRutear = screen.getByRole('region', { name: /Por rutear/ })
    expect(await within(porRutear).findByRole('link', { name: 'Marcela Torres · Simba' })).toHaveAttribute('href', '/servicios/s9')
    expect(within(porRutear).getByText('Consulta domiciliaria · Calle 53 # 20-11, Galerías, Bogota')).toBeInTheDocument()
    expect(screen.getByText(/Elige una ruta para ver sus paradas/)).toBeInTheDocument()
  })

  it('sin rutas ni domicilios pendientes dice qué hacer', async () => {
    conRutas([])
    renderizar(<RutasPage />)
    expect(await screen.findByText(/No hay rutas para hoy\. Créalas con «Planear rutas»/)).toBeInTheDocument()
    expect(await screen.findByText('Todos los domicilios agendados del día tienen ruta.')).toBeInTheDocument()
  })

  it('filtra por ciudad', async () => {
    const pedido = conRutas([])
    const user = userEvent.setup()
    renderizar(<RutasPage />)
    await user.selectOptions(await screen.findByLabelText('Filtrar por ciudad'), await screen.findByRole('option', { name: 'Bogota' }))
    expect(await screen.findByText(/No hay rutas para hoy en Bogota/)).toBeInTheDocument()
    expect(pedido.rutas.get('ciudad')).toBe('Bogota')
    expect(pedido.porRutear.get('ciudad')).toBe('Bogota')
  })

  it('abre una ruta por su enlace: su línea a la derecha, y la de otra persona no le quita a planear la acción principal', async () => {
    conRutas([ruta([parada(1, 'completada'), parada(2, 'en_sitio')])])
    server.use(http.get(`${API}/servicios/s2/pasos`, () => HttpResponse.json(PASOS_HECHOS)))
    renderizar(<RutasPage />, { ruta: '/rutas?ruta=r1' })

    expect(await screen.findByRole('heading', { name: 'Dra. Sara' })).toBeInTheDocument()
    const abierta = screen.getByRole('region', { name: 'Ruta abierta' })
    expect(within(abierta).getByText('1 de 2 paradas · 13,8 km · 1 h 22 min')).toBeInTheDocument()
    expect(within(abierta).getByRole('heading', { name: 'Carrera 7 # 120-45' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Dra. Sara' })).toHaveAttribute('aria-current', 'page')
    // Una sola acción verde llena por vista: quien coordina puede avanzar la parada de otra
    // persona, pero su principal es planear.
    expect(screen.getByRole('button', { name: /planear rutas/i })).toHaveClass('btn-primario')
    expect(await within(abierta).findByRole('button', { name: 'Terminar visita' })).toHaveClass('btn-secundario')
    expect(within(abierta).getByRole('link', { name: 'Volver a las rutas' })).toHaveAttribute('href', '/rutas')
  })

  it('con su propia ruta abierta, la acción principal es la de su parada y planear pasa a suave', async () => {
    conRutas([ruta([parada(1, 'en_camino')], { responsable_id: USUARIO_ADMIN.id })])
    renderizar(<RutasPage />, { ruta: '/rutas?ruta=r1' })
    expect(await screen.findByRole('button', { name: 'Llegué' })).toHaveClass('btn-primario')
    expect(screen.getByRole('button', { name: /planear rutas/i })).toHaveClass('btn-suave')
    expect(screen.getByText(/tu ruta/)).toBeInTheDocument()
  })

  it('quien coordina no arranca la ruta de otra persona', async () => {
    conRutas([ruta([parada(1, 'pendiente')], { estado: 'planificada' })])
    renderizar(<RutasPage />, { ruta: '/rutas?ruta=r1' })
    await screen.findByRole('heading', { name: 'Calle 80 # 15-20' })
    expect(screen.queryByRole('button', { name: 'Iniciar ruta' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /planear rutas/i })).toHaveClass('btn-primario')
  })

  it('agrega a la ruta abierta un domicilio de su ciudad que quedó por rutear', async () => {
    let pedido: unknown = null
    conRutas([ruta([parada(1, 'pendiente')], { estado: 'planificada' })], [POR_RUTEAR, { ...POR_RUTEAR, id: 's10', ciudad: 'Medellin' }])
    server.use(
      http.post(`${API}/rutas/r1/paradas`, async ({ request }) => {
        pedido = await request.json()
        return HttpResponse.json(ruta([parada(1, 'pendiente'), parada(2, 'pendiente')]), { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<RutasPage />, { ruta: '/rutas?ruta=r1' })
    await user.click(await screen.findByRole('button', { name: 'Agregar un servicio' }))
    const opciones = await screen.findAllByRole('menuitem')
    expect(opciones).toHaveLength(1)
    expect(opciones[0]).toHaveTextContent('Marcela Torres · Consulta domiciliaria')
    await user.click(opciones[0])
    await waitFor(() => expect(pedido).toEqual({ servicio_id: 's9' }))
  })

  it('cancela una ruta sin arrancar solo tras confirmarlo', async () => {
    let cancelada = false
    conRutas([ruta([parada(1, 'pendiente'), parada(2, 'pendiente')], { estado: 'planificada' })])
    server.use(
      http.post(`${API}/rutas/r1/cancelacion`, () => {
        cancelada = true
        return HttpResponse.json(ruta([], { estado: 'cancelada' }))
      }),
    )
    const user = userEvent.setup()
    renderizar(<RutasPage />, { ruta: '/rutas?ruta=r1' })
    await user.click(await screen.findByRole('button', { name: 'Cancelar ruta' }))
    const modal = await screen.findByRole('dialog', { name: 'Cancelar la ruta' })
    expect(modal).toHaveTextContent('Sus 2 servicios vuelven a quedar por rutear')
    expect(cancelada).toBe(false)
    expect(within(modal).getByRole('button', { name: 'Cancelar la ruta' })).toHaveClass('btn-peligro')
    await user.click(within(modal).getByRole('button', { name: 'Cancelar la ruta' }))
    await waitFor(() => expect(cancelada).toBe(true))
  })

  it('una ruta en curso ya no se cancela', async () => {
    conRutas([ruta([parada(1, 'en_camino')])])
    renderizar(<RutasPage />, { ruta: '/rutas?ruta=r1' })
    await screen.findByRole('heading', { name: 'Dra. Sara' })
    expect(screen.queryByRole('button', { name: 'Cancelar ruta' })).not.toBeInTheDocument()
  })

  it('planea las rutas de una ciudad con quienes salen a campo y espera al optimizador', async () => {
    let pedido: unknown = null
    let consultas = 0
    conRutas([], [POR_RUTEAR])
    server.use(
      http.post(`${API}/rutas/planificaciones`, async ({ request }) => {
        pedido = await request.json()
        return HttpResponse.json({ id: 'pl1', estado: 'pendiente', resultado: {}, error: null })
      }),
      http.get(`${API}/rutas/planificaciones/pl1`, () => {
        consultas += 1
        return HttpResponse.json(
          consultas < 2
            ? { id: 'pl1', estado: 'pendiente', resultado: {}, error: null }
            : // La API cuenta las rutas creadas: es un número, no una lista.
              { id: 'pl1', estado: 'lista', resultado: { rutas: 1, asignados: 3, sin_asignar: [{ servicio_id: 's9', motivo: 'sin_ubicacion' }] }, error: null },
        )
      }),
    )
    const user = userEvent.setup()
    renderizar(<RutasPage />)
    await user.click(await screen.findByRole('button', { name: /planear rutas/i }))
    const modal = await screen.findByRole('dialog', { name: 'Planear rutas' })
    const planear = within(modal).getByRole('button', { name: 'Planear rutas' })
    expect(planear).toBeDisabled()
    // La ciudad sale de lo que falta por rutear: nadie la escribe a mano.
    expect(await within(modal).findByLabelText('Ciudad')).toHaveValue('Bogota')
    await user.click(await within(modal).findByRole('checkbox', { name: /dra. sara/i }))
    await user.click(planear)
    expect(await within(modal).findByText(/Optimizando las rutas/)).toBeInTheDocument()
    expect(await within(modal).findByText('1 ruta creada con 3 servicios.', {}, { timeout: 5000 })).toBeInTheDocument()
    expect(within(modal).getByText(/1 servicio quedó sin ruta: la familia no tiene ubicación/)).toBeInTheDocument()
    expect(pedido).toMatchObject({ fecha: hoyISO(), ciudad: 'Bogota', responsables: ['m1'] })
    await user.click(within(modal).getByRole('button', { name: 'Ver las rutas' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('si el optimizador falla, lo dice con su causa', async () => {
    conRutas([])
    server.use(
      http.post(`${API}/rutas/planificaciones`, () =>
        HttpResponse.json({ id: 'pl2', estado: 'pendiente', resultado: {}, error: null }),
      ),
      http.get(`${API}/rutas/planificaciones/pl2`, () =>
        HttpResponse.json({ id: 'pl2', estado: 'fallida', resultado: {}, error: 'La ciudad Bogota no tiene coordenadas de base' }),
      ),
    )
    const user = userEvent.setup()
    renderizar(<RutasPage />)
    await user.click(await screen.findByRole('button', { name: /planear rutas/i }))
    const modal = await screen.findByRole('dialog', { name: 'Planear rutas' })
    await user.click(await within(modal).findByRole('checkbox', { name: /dra. sara/i }))
    await user.click(within(modal).getByRole('button', { name: 'Planear rutas' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('No fue posible planear: La ciudad Bogota no tiene coordenadas de base')
  })

  it('el comercial ve las rutas, pero no planea, ni cancela, ni avanza paradas', async () => {
    server.use(http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'comercial' })))
    conRutas([ruta([parada(1, 'pendiente')], { estado: 'planificada' })], [POR_RUTEAR])
    const user = userEvent.setup()
    renderizar(<RutasPage />, { ruta: '/rutas?ruta=r1' })
    await screen.findByRole('heading', { name: 'Dra. Sara' })
    expect(screen.queryByRole('button', { name: /planear rutas/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Cancelar ruta' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Agregar un servicio' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Iniciar ruta' })).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Más acciones con Ana Ruiz' }))
    expect(await screen.findByRole('menuitem', { name: 'Ver el servicio' })).toBeInTheDocument()
    expect(screen.queryByRole('menuitem', { name: 'Omitir parada' })).not.toBeInTheDocument()
    expect(screen.queryByRole('menuitem', { name: /historia clínica/i })).not.toBeInTheDocument()
  })
})
