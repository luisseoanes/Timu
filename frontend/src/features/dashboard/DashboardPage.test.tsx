import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { DashboardPage } from './DashboardPage'
import type { Evolucion, Indicadores, MesEvolucion } from './api'
import { USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import { hoyISO } from '@/lib/formato'

const API = '*/api/v1'
const pagina = <T,>(items: T[], total = items.length) => ({ items, total, limit: 1, offset: 0 })

const INDICADORES: Indicadores = {
  periodo: { desde: '2026-10-01', hasta: '2026-10-24', ciudad: null },
  indicadores: {
    afiliaciones: 12,
    retiros: 2,
    vigentes: 340,
    recaudo: 15300000,
    facturado: 18000000,
    recaudo_del_facturado: 0.85,
    mora: { contratos_en_mora: 21, saldo_vencido: 1890000, porcentaje: 0.062 },
    cumplimiento_rutas: { paradas_planeadas: 120, paradas_completadas: 111, cumplimiento: 0.925, puntualidad: 0.8 },
    servicios_por_tipo: { consulta_domiciliaria: 40, vacunacion: 25 },
    satisfaccion: { enviadas: 60, respondidas: 42, promedio: 4.6, tasa_respuesta: 0.7 },
  },
}

/** Un mes de la serie: de noviembre de 2025 a octubre de 2026, que va en curso. */
function mes(anio: number, n: number, parcial = false): MesEvolucion {
  const desde = `${anio}-${String(n).padStart(2, '0')}-01`
  return {
    periodo: { desde, hasta: parcial ? `${anio}-${String(n).padStart(2, '0')}-24` : desde, ciudad: null },
    parcial,
    indicadores: {
      vigentes: anio === 2026 ? 300 + n * 3 : 290 + n - 11,
      recaudo: 1_000_000 * n,
      facturado: 1_100_000 * n,
      mora: { contratos_en_mora: n, saldo_vencido: 0, porcentaje: null },
    },
  }
}

const EVOLUCION: Evolucion = {
  anterior: {
    periodo: { desde: '2026-09-01', hasta: '2026-09-24', ciudad: null },
    indicadores: { ...INDICADORES.indicadores, vigentes: 330, mora: { contratos_en_mora: 18, saldo_vencido: 0, porcentaje: null } },
  },
  meses: [mes(2025, 11), mes(2025, 12), ...Array.from({ length: 9 }, (_, i) => mes(2026, i + 1)), mes(2026, 10, true)],
}

const conDatos = () =>
  server.use(
    http.get(`${API}/dashboard/indicadores`, () => HttpResponse.json(INDICADORES)),
    http.get(`${API}/dashboard/evolucion`, () => HttpResponse.json(EVOLUCION)),
  )

const cifras = () => screen.findByRole('list', { name: 'Cifras del período' })
const cifra = async (nombre: RegExp) => within(await cifras()).getByRole('button', { name: nombre })

describe('Inicio del equipo', () => {
  beforeEach(conDatos)

  it('saluda y muestra las cifras del período en el orden de su perfil', async () => {
    renderizar(<DashboardPage />)
    expect(await screen.findByRole('heading', { level: 1, name: 'Hola, Admin' })).toBeInTheDocument()
    const botones = within(await cifras()).getAllByRole('button')
    expect(botones.map((b) => b.querySelector('.inicio-cifra-titulo')?.textContent)).toEqual([
      'Vigentes', 'Afiliaciones', 'Recaudo', 'En mora', 'Rutas', 'Satisfacción',
    ])
    expect(botones[0]).toHaveTextContent('340')
    expect(botones[4]).toHaveTextContent('93%')
    expect(botones[5]).toHaveTextContent('4,6 / 5')
  })

  it('operaciones ve primero las rutas', async () => {
    server.use(http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'operaciones' })))
    renderizar(<DashboardPage />)
    const [primera] = within(await cifras()).getAllByRole('button')
    expect(primera).toHaveTextContent(/^Rutas/)
  })

  it('dice cuánto cambió cada cifra contra el período comparable, con su tono', async () => {
    renderizar(<DashboardPage />)
    // La comparación va en la línea del saludo, una vez para toda la franja.
    expect(await screen.findByText(/, contra 1 sept – 24 sept$/)).toBeInTheDocument()
    const vigentes = await cifra(/^Vigentes/)
    expect(vigentes).toHaveTextContent(/Sube\s*10 más/)
    expect(vigentes.querySelector('.inicio-variacion')).toHaveAttribute('data-tono', 'buena')
    // Tres contratos más en mora es una mala noticia.
    const mora = await cifra(/^En mora/)
    expect(mora).toHaveTextContent(/Sube\s*3 más/)
    expect(mora.querySelector('.inicio-variacion')).toHaveAttribute('data-tono', 'mala')
  })

  it('una cifra abre su serie de 12 meses, con la tabla de los datos, y Escape la cierra', async () => {
    const user = userEvent.setup()
    renderizar(<DashboardPage />)
    const recaudo = await cifra(/^Recaudo/)
    expect(recaudo).toHaveAttribute('aria-expanded', 'false')
    await user.click(recaudo)
    expect(recaudo).toHaveAttribute('aria-expanded', 'true')
    const serie = screen.getByRole('region', { name: 'Recaudo en los últimos 12 meses' })
    expect(within(serie).getByRole('list', { name: 'Series' })).toHaveTextContent('RecaudoFacturado')
    expect(within(serie).getByText('octubre de 2026, hasta el 24: el mes está en curso.')).toBeInTheDocument()
    // El eje dice el año bajo el primer mes y donde cambia.
    expect(within(serie).getByText('2025')).toBeInTheDocument()
    expect(within(serie).getByText('2026')).toBeInTheDocument()
    await user.click(within(serie).getByText('Ver los datos'))
    const filas = within(serie).getAllByRole('row')
    expect(filas).toHaveLength(13)
    expect(filas[12]).toHaveTextContent(/octubre de 2026, hasta el 24\$\s10\.000\.000\$\s11\.000\.000/)

    // La misma serie no se repite en la columna mientras está abierta arriba.
    expect(screen.queryByRole('region', { name: 'Recaudo contra lo facturado' })).not.toBeInTheDocument()

    await user.keyboard('{Escape}')
    expect(screen.queryByRole('region', { name: /en los últimos 12 meses/ })).not.toBeInTheDocument()
    expect(recaudo).toHaveFocus()
    expect(screen.getByRole('region', { name: 'Recaudo contra lo facturado' })).toBeInTheDocument()
  })

  it('pide la fórmula del indicador solo al abrir su serie', async () => {
    let pedidas = 0
    server.use(
      http.get(`${API}/dashboard/definiciones`, () => {
        pedidas += 1
        return HttpResponse.json([{ codigo: 'mora', nombre: 'Mora al cierre', formula: 'Contratos con cuotas vencidas.', unidad: 'contratos' }])
      }),
    )
    const user = userEvent.setup()
    renderizar(<DashboardPage />)
    await cifras()
    expect(pedidas).toBe(0)
    await user.click(await cifra(/^En mora/))
    expect(await screen.findByText('Contratos con cuotas vencidas.')).toBeInTheDocument()
    expect(pedidas).toBe(1)
  })

  it('el gráfico se recorre con las flechas y anuncia cada mes', async () => {
    const user = userEvent.setup()
    renderizar(<DashboardPage />)
    await user.click(await cifra(/^Vigentes/))
    const grafico = screen.getByRole('group', { name: /Vigentes mes a mes/ })
    grafico.focus()
    await waitFor(() => expect(grafico).toHaveTextContent('octubre de 2026, hasta el 24: Contratos vigentes 330'))
    await user.keyboard('{ArrowLeft}')
    expect(grafico).toHaveTextContent('septiembre de 2026: Contratos vigentes 327')
    await user.keyboard('{Home}')
    expect(grafico).toHaveTextContent('noviembre de 2025: Contratos vigentes 290')
  })

  it('pide la serie con los mismos filtros y vuelve a pedir todo al cambiar la ciudad', async () => {
    const pedidas: URLSearchParams[] = []
    server.use(
      http.get(`${API}/dashboard/evolucion`, ({ request }) => {
        pedidas.push(new URL(request.url).searchParams)
        return HttpResponse.json(EVOLUCION)
      }),
    )
    const user = userEvent.setup()
    renderizar(<DashboardPage />)
    await cifras()
    await waitFor(() => expect(pedidas).toHaveLength(1))
    expect(pedidas[0].getAll('codigos')).toContain('recaudo')
    expect(pedidas[0].get('desde')).toBe(`${hoyISO().slice(0, 8)}01`)
    await user.selectOptions(screen.getByLabelText('Ciudad'), 'Bogota')
    await waitFor(() => expect(pedidas.at(-1)?.get('ciudad')).toBe('Bogota'))
  })

  it('avisa si no se pueden calcular las cifras', async () => {
    server.use(
      http.get(`${API}/dashboard/indicadores`, () => HttpResponse.json({ detail: 'Fallo la consulta' }, { status: 500 })),
    )
    renderizar(<DashboardPage />)
    expect(await screen.findByText(/No fue posible calcular las cifras/)).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Reintentar' })).toHaveLength(1)
  })

  it('los servicios completados llevan el nombre del catálogo', async () => {
    renderizar(<DashboardPage />)
    const barras = await screen.findByRole('region', { name: 'Servicios completados por tipo' })
    expect(await within(barras).findByText('Consulta domiciliaria')).toBeInTheDocument()
    expect(within(barras).getByText('40')).toBeInTheDocument()
  })
})

describe('La línea del día', () => {
  beforeEach(conDatos)

  it('agrupa lo vencido con su ejemplo y solo la primera estación lleva el verde', async () => {
    server.use(
      http.get(`${API}/cartera/contratos`, () =>
        HttpResponse.json(pagina([{ id: 'c1', titular: 'Ana Ruiz', dias_mora: 84 }], 5)),
      ),
      http.get(`${API}/tareas`, () =>
        HttpResponse.json(pagina([{ id: 't1', titulo: 'Llamar a Jorge', vence_el: '2026-11-05' }], 3)),
      ),
      http.get(`${API}/preventivos`, () => HttpResponse.json(pagina([{ id: 'p1', fecha_programada: '2026-11-04' }], 25))),
    )
    renderizar(<DashboardPage />)
    const linea = await screen.findByRole('list', { name: 'El día de la operación' })
    expect(await within(linea).findByText('5 contratos en mora')).toBeInTheDocument()
    expect(within(linea).getByText('El más atrasado: Ana Ruiz, 84 días')).toBeInTheDocument()
    expect(within(linea).getByText('Llamar a Jorge · venció el 5 nov')).toBeInTheDocument()
    expect(within(linea).getByRole('link', { name: 'Ver la mora' })).toHaveClass('btn-primario')
    expect(within(linea).getByRole('link', { name: 'Ver las tareas' })).toHaveClass('btn-secundario')
    expect(within(linea).getByRole('link', { name: 'Ver la mora' })).toHaveAttribute('href', '/cartera?mora=1')
  })

  it('un preventivo por autorizar que aún no llega va después de hoy', async () => {
    server.use(http.get(`${API}/preventivos`, () => HttpResponse.json(pagina([{ id: 'p1', fecha_programada: '2999-01-04' }], 2))))
    renderizar(<DashboardPage />)
    const linea = await screen.findByRole('list', { name: 'El día de la operación' })
    const estaciones = await within(linea).findAllByRole('listitem')
    expect(estaciones[0]).toHaveTextContent(/^Hoy/)
    expect(estaciones[1]).toHaveTextContent('Lo siguiente: 2 preventivos por autorizar')
    // Sin nada vencido, el verde pasa a lo que queda por hacer.
    expect(within(linea).getByRole('link', { name: 'Autorizar' })).toHaveClass('btn-primario')
  })

  it('sin nada vencido ni agendado, la línea dice qué aparecerá', async () => {
    renderizar(<DashboardPage />)
    const linea = await screen.findByRole('list', { name: 'El día de la operación' })
    expect(await within(linea).findByText(/No hay servicios agendados desde hoy/)).toBeInTheDocument()
  })

  it('lo de hoy ya pasado va antes de Hoy; lo que viene lleva su médico y los días siguientes se agrupan', async () => {
    // Solo se congela Date: MSW y los temporizadores de las pruebas siguen funcionando.
    const familia = { id: 'f1', titular_nombre: 'Ana Ruiz' }
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date('2026-11-13T13:00:00Z')) // 8:00 a. m. en Colombia
    server.use(
      http.get(`${API}/auth/equipo`, () => HttpResponse.json([{ id: 'm1', nombre: 'Sara Díaz', rol: 'medico' }])),
      http.get(`${API}/servicios`, () =>
        HttpResponse.json({
          items: [
            { id: 's0', tipo_codigo: 'consulta_domiciliaria', ciudad: 'Medellín', programado_para: '2026-11-13T11:00:00Z', profesional_id: null, familia, mascota: null },
            { id: 's1', tipo_codigo: 'consulta_domiciliaria', ciudad: 'Medellín', programado_para: '2026-11-13T16:00:00Z', profesional_id: 'm1', familia, mascota: { id: 'x', nombre: 'Max', especie: 'perro' } },
            { id: 's2', tipo_codigo: 'consulta_domiciliaria', ciudad: 'Envigado', programado_para: '2026-11-14T15:00:00Z', profesional_id: null, familia, mascota: null },
          ],
          total: 4,
          limit: 20,
          offset: 0,
        }),
      ),
    )
    try {
      renderizar(<DashboardPage />)
      const linea = await screen.findByRole('list', { name: 'El día de la operación' })
      const estaciones = await within(linea).findAllByRole('listitem')
      expect(estaciones.map((e) => e.textContent)).toEqual([
        'Vencido: 1 servicio de hoy sin atenderEl primero estaba para las 6:00 a. m.Ver los servicios',
        expect.stringMatching(/^Hoy/),
        'Lo siguiente: 11:00 a. m.Consulta domiciliaria · MaxAna Ruiz · Medellín · Sara DíazVer',
        'sáb 14 nov1 servicio agendadoConsulta domiciliariaVer la agenda',
        'Y 1 servicio agendado másVer la agenda',
      ])
      expect(within(linea).getByRole('link', { name: 'Ver' })).toHaveAttribute('href', '/servicios/s1')
      for (const agenda of within(linea).getAllByRole('link', { name: 'Ver la agenda' })) {
        expect(agenda).toHaveClass('btn-secundario')
      }
    } finally {
      vi.useRealTimers()
    }
  })

  it('avisa si no puede revisar el día', async () => {
    server.use(http.get(`${API}/cartera/contratos`, () => HttpResponse.json({ detail: 'Caído' }, { status: 503 })))
    renderizar(<DashboardPage />)
    expect(await screen.findByText(/No fue posible revisar el día/)).toBeInTheDocument()
  })
})

describe('Inicio del médico', () => {
  beforeEach(() => {
    server.use(http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, nombre: 'Dra. Sara Díaz', rol: 'medico' })))
  })

  it('ve su jornada: consultas sin firmar, Hoy y las paradas que le faltan', async () => {
    server.use(
      http.get(`${API}/clinica/borradores`, () =>
        HttpResponse.json([
          { id: 'e1', fecha: '2026-11-08' },
          { id: 'e2', fecha: '2026-11-04' },
        ]),
      ),
      http.get(`${API}/rutas`, () =>
        HttpResponse.json([
          {
            id: 'r1',
            estado: 'en_curso',
            paradas: [
              { id: 'p1', orden: 1, estado: 'completada', tipo_codigo: 'consulta_domiciliaria', llegada_estimada: null, familia: { titular_nombre: 'Ana Ruiz', barrio: 'Laureles' }, mascota: { nombre: 'Luna' } },
              { id: 'p2', orden: 2, estado: 'pendiente', tipo_codigo: 'consulta_domiciliaria', llegada_estimada: '2026-11-13T14:30:00Z', familia: { titular_nombre: 'Laura Gómez', barrio: null, direccion: 'Avenida 19 # 100-12' }, mascota: { nombre: 'Nala' } },
            ],
          },
        ]),
      ),
    )
    renderizar(<DashboardPage />)
    expect(await screen.findByRole('heading', { level: 1, name: 'Hola, Sara' })).toBeInTheDocument()
    const linea = await screen.findByRole('list', { name: 'Tu jornada' })
    expect(await within(linea).findByText('2 consultas sin firmar')).toBeInTheDocument()
    expect(within(linea).getByText('La más antigua es del 4 nov')).toBeInTheDocument()
    expect(within(linea).getByRole('link', { name: 'Firmar las consultas' })).toHaveClass('btn-primario')
    expect(within(linea).getByText('Consulta domiciliaria · Nala')).toBeInTheDocument()
    expect(within(linea).getByText('Laura Gómez · Avenida 19 # 100-12')).toBeInTheDocument()
    expect(within(linea).queryByText(/Luna/)).not.toBeInTheDocument()
    expect(within(linea).getByRole('link', { name: 'Abrir mi ruta' })).toHaveClass('btn-secundario')
    expect(screen.queryByRole('list', { name: 'Cifras del período' })).not.toBeInTheDocument()
  })

  it('sin ruta lo dice, y lista sus tareas abiertas', async () => {
    server.use(
      http.get(`${API}/tareas`, ({ request }) =>
        HttpResponse.json(
          new URL(request.url).searchParams.get('vencidas')
            ? pagina([])
            : pagina([{ id: 't1', titulo: 'Llamar a Ana', prioridad: 'alta', vence_el: '2026-10-25', estado: 'abierta' }]),
        ),
      ),
    )
    renderizar(<DashboardPage />)
    expect(await screen.findByText(/No tienes ruta para hoy/)).toBeInTheDocument()
    const tareas = screen.getByRole('region', { name: 'Tus tareas abiertas' })
    expect(await within(tareas).findByText('Llamar a Ana')).toBeInTheDocument()
    expect(within(tareas).getByText('Vence el 25/10/2026')).toBeInTheDocument()
  })
})
