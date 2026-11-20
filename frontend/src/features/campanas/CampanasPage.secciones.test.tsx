import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import type { ReactElement } from 'react'
import { beforeEach, describe, expect, it } from 'vitest'

import { CampanasPage } from './CampanasPage'
import { ConfiguracionEncuestas } from './Encuestas'
import { EncuestasPage } from './EncuestasPage'
import { MensajesPage } from './MensajesPage'
import { PlantillasWhatsApp } from './PlantillasWhatsApp'
import { resumenFiltros } from './segmento'
import { PLAN as PLAN_TIMU, USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { CampanaRead, MensajeRead, PlanRead } from '@/types'

const API = '*/api/v1'
const como = (rol: string) => http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol }))
const pagina = (items: unknown[]) => ({ items, total: items.length, limit: 25, offset: 0 })

const CAMPANA: CampanaRead = {
  id: 'c1',
  nombre: 'Renovación noviembre',
  canal: 'whatsapp',
  plantilla: 'recordatorio_renovacion',
  variables: ['titular_nombre'],
  segmento_id: null,
  segmento: {},
  estado: 'borrador',
  programada_para: null,
  recurrencia: 'ninguna',
  proxima_ejecucion: null,
}

const PLANTILLA = {
  id: 'p1',
  nombre: 'recordatorio_renovacion',
  idioma: 'es',
  version: 1,
  categoria: 'utility',
  cuerpo: 'Hola {{1}}, tu plan se renueva pronto.',
  variables: ['1'],
  estado_aprobacion: 'aprobada',
  activa: true,
}

const PLAN: PlanRead = { ...PLAN_TIMU, id: 'pl1' }

const base = [
  http.get(`${API}/campanas`, () => HttpResponse.json([CAMPANA])),
  http.get(`${API}/segmentos`, () => HttpResponse.json([])),
  http.get(`${API}/comunicaciones/plantillas`, () => HttpResponse.json([PLANTILLA])),
  http.get(`${API}/planes`, () => HttpResponse.json([PLAN])),
  http.get(`${API}/encuestas`, () => HttpResponse.json({ items: [], total: 0, limit: 20, offset: 0 })),
]

// Los handlers comunes van primero; los `server.use` de cada prueba los sustituyen.
beforeEach(() => server.use(...base))

function detalle(
  cambios: Partial<CampanaRead> = {},
  { resultados = { audiencia: 0 }, ejecuciones = [] }: { resultados?: Record<string, number>; ejecuciones?: unknown[] } = {},
) {
  server.use(http.get(`${API}/campanas`, () => HttpResponse.json([{ ...CAMPANA, ...cambios }])),
    http.get(`${API}/campanas/c1/previsualizacion`, () =>
      HttpResponse.json({ audiencia: 5, excluidos_por_baja: 1, se_enviaran: 4, ejemplos: [] }),
    ),
    http.get(`${API}/campanas/c1/resultados`, () => HttpResponse.json(resultados)),
    http.get(`${API}/campanas/c1/ejecuciones`, () => HttpResponse.json(ejecuciones)),
  )
}

/** La campaña abierta vive en la URL: se lee en su ficha, junto al listado. */
async function abrirDetalle() {
  const user = userEvent.setup()
  renderizar(<CampanasPage />, { ruta: '/panel/campanas?campana=c1' })
  const ficha = await screen.findByRole('region', { name: 'Campaña abierta' })
  await within(ficha).findByRole('heading', { level: 2 })
  return { user, modal: ficha }
}

// Lo que salió de Campañas (Sección 12, docs/perfiles-y-permisos.md): las encuestas y los mensajes
// tienen su módulo, y la configuración de las encuestas y las plantillas viven en Administración.
const MUDADAS: Record<string, () => ReactElement> = {
  Encuestas: () => (
    <>
      <EncuestasPage />
      <ConfiguracionEncuestas />
    </>
  ),
  Mensajes: () => <MensajesPage />,
  'Plantillas de WhatsApp': () => <PlantillasWhatsApp />,
}

async function abrirPestana(nombre: string) {
  const user = userEvent.setup()
  const mudada = MUDADAS[nombre]
  if (mudada) {
    renderizar(mudada())
    return user
  }
  renderizar(<CampanasPage />)
  await user.click(await screen.findByRole('tab', { name: nombre }))
  return user
}

// Las campañas son de Comercial.
beforeEach(() => server.use(como('comercial')))

describe('campañas', () => {
  it('dice cuándo sale y cada cuánto se repite', async () => {
    server.use(http.get(`${API}/campanas`, () =>
        HttpResponse.json([{ ...CAMPANA, recurrencia: 'semanal', proxima_ejecucion: '2026-11-10T14:00:00Z', estado: 'programada' }]),
      ),
    )
    renderizar(<CampanasPage />)
    expect(await screen.findByText(/9:00 a\. m\. · cada semana/)).toBeInTheDocument()
  })

  it('sin campañas dice qué hacer, y si no carga explica por qué', async () => {
    server.use(http.get(`${API}/campanas`, () => HttpResponse.json([])))
    const { unmount } = renderizar(<CampanasPage />)
    expect(await screen.findByText('Aún no hay campañas. Crea una con «Nueva campaña».')).toBeInTheDocument()
    unmount()
    server.use(http.get(`${API}/campanas`, () => HttpResponse.json({ detail: 'Sin conexión' }, { status: 503 })))
    renderizar(<CampanasPage />)
    expect(await screen.findByRole('alert')).toHaveTextContent('No fue posible cargar las campañas. Sin conexión')
  })

  it('operaciones ve las campañas pero no las crea, programa ni gestiona plantillas', async () => {
    detalle()
    server.use(como('operaciones'))
    const { modal } = await abrirDetalle()
    expect(screen.queryByRole('button', { name: /nueva campaña/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: 'Plantillas de WhatsApp' })).not.toBeInTheDocument()
    expect(await within(modal).findByText(/Le llega a/)).toHaveTextContent('Le llega a 4 de 5 familias · 1 se dieron de baja de los mensajes.')
    expect(within(modal).queryByRole('button', { name: 'Enviar ahora' })).not.toBeInTheDocument()
  })

  it('muestra los resultados y las veces que salió una campaña enviada', async () => {
    detalle(
      { estado: 'finalizada' },
      {
        resultados: { audiencia: 40, excluidos: 2, encolados: 0, enviados: 38, entregados: 36, leidos: 30, respondidos: 7, fallidos: 2 },
        ejecuciones: [{ id: 'e1', iniciada_en: '2026-11-01T14:00:00Z' }, { id: 'e2', iniciada_en: '2026-10-01T14:00:00Z' }],
      },
    )
    const { modal } = await abrirDetalle()
    expect(await within(modal).findByText('Respondidos')).toBeInTheDocument()
    expect(within(modal).getByText('36')).toBeInTheDocument()
    expect(within(modal).getByText('No se enviaron')).toBeInTheDocument()
    expect(within(modal).getByText(/Ha salido/)).toHaveTextContent('Ha salido 2 veces; la última, el 1 nov a las 9:00 a. m.')
    expect(within(modal).queryByRole('button', { name: 'Enviar ahora' })).not.toBeInTheDocument()
    // Ya salió: hay destinatarios que descargar.
    expect(within(modal).getByRole('button', { name: /destinatarios en csv/i })).toBeInTheDocument()
  })

  it('un borrador que nunca salió no ofrece descargar destinatarios', async () => {
    detalle()
    const { modal } = await abrirDetalle()
    expect(await within(modal).findByText(/Todavía no ha salido/)).toBeInTheDocument()
    expect(within(modal).queryByRole('button', { name: /destinatarios en csv/i })).not.toBeInTheDocument()
  })

  it('dice la plantilla como la llama el equipo, con el código de Meta debajo', async () => {
    detalle({ plantilla_titulo: 'Recordatorio de renovación' })
    const { modal } = await abrirDetalle()
    const plantilla = within(modal).getByText('Plantilla').nextElementSibling as HTMLElement
    expect(plantilla).toHaveTextContent('Recordatorio de renovación')
    expect(within(plantilla).getByText('recordatorio_renovacion')).toHaveClass('campana-plantilla-codigo')
  })

  it('sin enviar dice qué aparecerá en sus resultados', async () => {
    detalle()
    const { modal } = await abrirDetalle()
    expect(await within(modal).findByText(/Todavía no ha salido/)).toBeInTheDocument()
  })

  it('programa el envío en hora de Colombia con su recurrencia, con un solo verde', async () => {
    let enviado: unknown = null
    detalle()
    server.use(
      http.post(`${API}/campanas/c1/programacion`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ ...CAMPANA, estado: 'programada' })
      }),
    )
    const { user, modal } = await abrirDetalle()
    // Con la ficha abierta, «Nueva campaña» deja el verde a la ficha.
    expect(screen.getByRole('button', { name: /nueva campaña/i })).toHaveClass('btn-suave')
    await user.type(within(modal).getByLabelText('Enviar el'), '2026-11-15T09:30')
    await user.selectOptions(within(modal).getByLabelText('Repetir'), 'mensual')
    await user.click(within(modal).getByRole('button', { name: 'Programar envío' }))
    await waitFor(() => expect(enviado).toEqual({ cuando: '2026-11-15T09:30:00-05:00', recurrencia: 'mensual' }))
    expect(await within(modal).findByRole('status')).toHaveTextContent('Campaña programada.')
  })

  it('cancela una campaña programada tras confirmarlo en rojo', async () => {
    let cancelada = false
    detalle({ estado: 'programada' })
    server.use(
      http.post(`${API}/campanas/c1/cancelacion`, () => {
        cancelada = true
        return HttpResponse.json({ ...CAMPANA, estado: 'cancelada' })
      }),
    )
    const { user, modal } = await abrirDetalle()
    await user.click(within(modal).getByRole('button', { name: 'Cancelar campaña' }))
    const ventana = await screen.findByRole('dialog', { name: `Cancelar «${CAMPANA.nombre}»` })
    const confirmar = within(ventana).getByRole('button', { name: 'Cancelar campaña' })
    expect(confirmar).toHaveClass('btn-peligro')
    await user.click(confirmar)
    await waitFor(() => expect(cancelada).toBe(true))
  })

  it('explica por qué no se pudo programar', async () => {
    detalle()
    server.use(
      http.post(`${API}/campanas/c1/programacion`, () =>
        HttpResponse.json({ detail: 'La plantilla dejó de estar aprobada' }, { status: 409 }),
      ),
    )
    const { user, modal } = await abrirDetalle()
    await user.click(within(modal).getByRole('button', { name: 'Enviar ahora' }))
    await user.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Enviar ahora' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('La plantilla dejó de estar aprobada')
  })

  it('explica por qué no se pudo descargar el CSV de destinatarios', async () => {
    detalle({ estado: 'finalizada' }, { ejecuciones: [{ id: 'e1', iniciada_en: '2026-11-01T14:00:00Z' }] })
    const { user, modal } = await abrirDetalle()
    server.use(
      http.get(`${API}/campanas/c1/resultados`, ({ request }) =>
        new URL(request.url).searchParams.get('formato') === 'csv'
          ? HttpResponse.json({ detail: 'Export no disponible' }, { status: 503 })
          : HttpResponse.json({ audiencia: 0 }),
      ),
    )
    await user.click(await within(modal).findByRole('button', { name: /destinatarios en csv/i }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('No fue posible descargar los destinatarios.')
  })

  it('explica por qué no se pudo calcular la audiencia', async () => {
    detalle()
    server.use(
      http.get(`${API}/campanas/c1/previsualizacion`, () => HttpResponse.json({ detail: 'Segmento inválido' }, { status: 422 })),
    )
    const { modal } = await abrirDetalle()
    expect(await within(modal).findByRole('alert')).toHaveTextContent('No fue posible calcular la audiencia. Segmento inválido')
  })
})

describe('nueva campaña', () => {
  async function abrirNueva() {
    const user = userEvent.setup()
    renderizar(<CampanasPage />)
    await user.click(await screen.findByRole('button', { name: /nueva campaña/i }))
    return { user, modal: await screen.findByRole('dialog') }
  }

  it('solo ofrece plantillas aprobadas y activas', async () => {
    server.use(http.get(`${API}/comunicaciones/plantillas`, () =>
        HttpResponse.json([
          { ...PLANTILLA, id: 'p2', nombre: 'pendiente_meta', estado_aprobacion: 'enviada' },
          { ...PLANTILLA, id: 'p3', nombre: 'apagada', activa: false },
        ]),
      ),
    )
    const { modal } = await abrirNueva()
    expect(await within(modal).findByRole('option', { name: 'No hay plantillas aprobadas' })).toBeInTheDocument()
    expect(within(modal).queryByRole('option', { name: 'pendiente_meta' })).not.toBeInTheDocument()
    expect(within(modal).getByRole('button', { name: 'Crear campaña' })).toBeDisabled()
  })

  it('con un segmento guardado no envía filtros y la variable puede ser un texto fijo', async () => {
    let enviado: unknown = null
    detalle()
    server.use(http.get(`${API}/segmentos`, () => HttpResponse.json([{ id: 'sg1', nombre: 'Morosos', descripcion: null, filtros: {} }])),
      http.post(`${API}/campanas`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(CAMPANA, { status: 201 })
      }),
    )
    const { user, modal } = await abrirNueva()
    await user.type(within(modal).getByLabelText('Nombre'), ' Cobro ')
    await waitFor(() => expect(within(modal).getByRole('option', { name: 'recordatorio_renovacion' })).toBeInTheDocument())
    await user.selectOptions(within(modal).getByLabelText('Plantilla'), 'recordatorio_renovacion')
    expect(within(modal).getByText('Hola {{1}}, tu plan se renueva pronto.')).toBeInTheDocument()
    await user.selectOptions(within(modal).getByLabelText('Audiencia'), 'sg1')
    expect(within(modal).queryByRole('button', { name: 'Contar audiencia' })).not.toBeInTheDocument()
    await user.selectOptions(within(modal).getByLabelText('Se llena con'), 'texto')
    await user.type(within(modal).getByLabelText('Texto fijo (si aplica)'), 'amigo')
    await user.click(within(modal).getByRole('button', { name: 'Crear campaña' }))
    await waitFor(() =>
      expect(enviado).toEqual({ nombre: 'Cobro', plantilla: 'recordatorio_renovacion', variables: ['texto:amigo'], segmento_id: 'sg1' }),
    )
  })

  it('arma los filtros con ciudades, planes y umbrales, y se pueden quitar', async () => {
    detalle()
    let enviado: Record<string, unknown> | null = null
    let contado: unknown = null
    server.use(http.post(`${API}/segmentos/previsualizacion`, async ({ request }) => {
        contado = await request.json()
        return HttpResponse.json({ total: 3, muestra: [{ titular: 'Ana' }, { titular: 'Beto' }, { titular: 'Carla' }, { titular: 'Dani' }] })
      }),
      http.post(`${API}/campanas`, async ({ request }) => {
        enviado = (await request.json()) as Record<string, unknown>
        return HttpResponse.json(CAMPANA, { status: 201 })
      }),
    )
    const { user, modal } = await abrirNueva()
    await user.type(within(modal).getByLabelText('Nombre'), 'Reactivación')
    await waitFor(() => expect(within(modal).getByRole('option', { name: 'recordatorio_renovacion' })).toBeInTheDocument())
    await user.selectOptions(within(modal).getByLabelText('Plantilla'), 'recordatorio_renovacion')
    const ciudades = within(modal).getByRole('group', { name: 'Ciudades' })
    await user.click(await within(ciudades).findByRole('button', { name: 'Bogotá' }))
    await user.click(await within(within(modal).getByRole('group', { name: 'Planes' })).findByRole('button', { name: 'Colita Feliz' }))
    const activa = within(modal).getByRole('button', { name: 'Activa' })
    await user.click(activa)
    await user.click(activa)
    expect(activa).toHaveAttribute('aria-pressed', 'false')
    await user.type(within(modal).getByLabelText('Días de mora mínimos'), '30')
    await user.type(within(modal).getByLabelText('Sin servicio hace (días)'), '90')
    const renuevan = within(modal).getByLabelText('Renuevan en (días)')
    await user.type(renuevan, '15')
    await user.clear(renuevan)
    await user.type(within(modal).getByLabelText('Mascotas mínimas'), '2')
    await user.click(within(modal).getByRole('button', { name: 'Contar audiencia' }))
    expect(await within(modal).findByRole('status')).toHaveTextContent('3 familias · Ana, Beto, Carla…')
    expect(contado).toMatchObject({ ciudades: ['Bogotá'], planes: ['colita_feliz'], dias_mora_min: 30, sin_servicio_dias: 90, mascotas_min: 2 })
    await user.click(within(modal).getByRole('button', { name: 'Crear campaña' }))
    await waitFor(() =>
      expect(enviado?.segmento).toEqual({
        ciudades: ['Bogotá'],
        planes: ['colita_feliz'],
        estados: [],
        dias_mora_min: 30,
        sin_servicio_dias: 90,
        mascotas_min: 2,
      }),
    )
  })

  it('segmenta por especie, zona, edad y preventivos (6.16, 6.18)', async () => {
    detalle()
    let contado: unknown = null
    server.use(
      http.post(`${API}/segmentos/previsualizacion`, async ({ request }) => {
        contado = await request.json()
        return HttpResponse.json({ total: 2, muestra: [{ titular: 'Ana' }, { titular: 'Beto' }] })
      }),
    )
    const { user, modal } = await abrirNueva()
    const especies = within(modal).getByRole('group', { name: 'Especies' })
    await user.click(await within(especies).findByRole('button', { name: 'Gato' }))
    await user.type(within(modal).getByLabelText('Barrios (separados por coma)'), 'Chapinero, El Poblado')
    await user.type(within(modal).getByLabelText('Mascota de al menos (años)'), '7')
    await user.click(within(modal).getByLabelText('Con un preventivo vencido'))
    await user.type(within(modal).getByLabelText('Con un preventivo que vence en (días)'), '30')
    await user.click(within(within(modal).getByRole('group', { name: 'Tipos de preventivo' })).getByRole('button', { name: 'Vacunas' }))
    await user.click(within(modal).getByRole('button', { name: 'Contar audiencia' }))
    expect(await within(modal).findByRole('status')).toHaveTextContent('2 familias')
    expect(contado).toMatchObject({
      especies: ['gato'],
      barrios: ['Chapinero', 'El Poblado'],
      edad_min_anios: 7,
      preventivo_vencido: true,
      preventivo_en_dias: 30,
      tipos_preventivo: ['vacuna'],
    })
    expect(
      resumenFiltros({ barrios: ['Chapinero'], edad_min_anios: 7, preventivo_vencido: true, tipos_preventivo: ['vacuna'] }),
    ).toBe('Chapinero · mascotas de 7 años o más · con un preventivo vencido (vacunas)')
  })

  it('explica por qué no pudo contar la audiencia ni crear la campaña', async () => {
    server.use(http.post(`${API}/segmentos/previsualizacion`, () => HttpResponse.json({ detail: 'Filtro inválido' }, { status: 422 })),
      http.post(`${API}/campanas`, () => HttpResponse.json({ detail: 'Ya existe una campaña con ese nombre' }, { status: 409 })),
    )
    const { user, modal } = await abrirNueva()
    await user.click(within(modal).getByRole('button', { name: 'Contar audiencia' }))
    expect(await within(modal).findByText('Filtro inválido')).toBeInTheDocument()
    await user.type(within(modal).getByLabelText('Nombre'), 'Repetida')
    await waitFor(() => expect(within(modal).getByRole('option', { name: 'recordatorio_renovacion' })).toBeInTheDocument())
    await user.selectOptions(within(modal).getByLabelText('Plantilla'), 'recordatorio_renovacion')
    await user.click(within(modal).getByRole('button', { name: 'Crear campaña' }))
    expect(await within(modal).findByText('Ya existe una campaña con ese nombre')).toBeInTheDocument()
  })
})

describe('segmentos', () => {
  it('describe cada segmento por su descripción o por sus filtros', async () => {
    server.use(http.get(`${API}/segmentos`, () =>
        HttpResponse.json([
          { id: 's1', nombre: 'Con descripción', descripcion: 'Familias VIP', filtros: {} },
          { id: 's2', nombre: 'Todas', descripcion: null, filtros: {} },
          {
            id: 's3',
            nombre: 'Morosos de Bogotá',
            descripcion: null,
            filtros: { estados: ['en_mora'], ciudades: ['Bogotá'], dias_mora_min: 30, renovacion_en_dias: 15 },
          },
        ]),
      ),
    )
    await abrirPestana('Segmentos')
    expect(await screen.findByText('Familias VIP')).toBeInTheDocument()
    expect(screen.getByText('Todas las familias')).toBeInTheDocument()
    expect(screen.getByText('En mora · Bogotá · mora de 30 días o más · renuevan en 15 días o menos')).toBeInTheDocument()
  })

  it('guarda un segmento con sus filtros', async () => {
    let enviado: unknown = null
    server.use(http.post(`${API}/segmentos`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ id: 's9', nombre: 'Morosos', descripcion: null, filtros: {} }, { status: 201 })
      }),
    )
    const user = await abrirPestana('Segmentos')
    // El vacío explica qué es un segmento y cómo se crea (techo 57).
    expect(await screen.findByText(/Crea el primero con «Nuevo segmento»/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /nuevo segmento/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nombre'), ' Morosos ')
    await user.click(within(modal).getByRole('button', { name: 'En mora' }))
    await user.click(within(modal).getByRole('button', { name: 'Guardar segmento' }))
    await waitFor(() => expect(enviado).toEqual({ nombre: 'Morosos', filtros: { estados: ['en_mora'] } }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('explica por qué no se pudo guardar el segmento', async () => {
    server.use(http.post(`${API}/segmentos`, () => HttpResponse.json({ detail: 'Nombre repetido' }, { status: 409 })))
    const user = await abrirPestana('Segmentos')
    await user.click(await screen.findByRole('button', { name: /nuevo segmento/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nombre'), 'Morosos')
    await user.type(within(modal).getByLabelText('Descripción'), 'Con mora')
    await user.click(within(modal).getByRole('button', { name: 'Guardar segmento' }))
    expect(await within(modal).findByText('Nombre repetido')).toBeInTheDocument()
  })

  it('operaciones no crea segmentos', async () => {
    server.use(como('operaciones'))
    await abrirPestana('Segmentos')
    await screen.findByText(/los crea mercadeo/)
    expect(screen.queryByRole('button', { name: /nuevo segmento/i })).not.toBeInTheDocument()
  })
})

describe('encuestas', () => {
  // El análisis es de Gerencia (Sección 12); Atención trabaja las novedades (la última prueba).
  beforeEach(() => server.use(como('gerencia')))

  const resumen = (cambios = {}) =>
    http.get(`${API}/encuestas/resumen`, () =>
      HttpResponse.json({ enviadas: 0, respondidas: 0, tasa_respuesta: 0, promedio: null, por_responsable: [], por_tipo_servicio: [], ...cambios }),
    )

  it('sin respuestas no inventa un promedio y desglosa por tipo cuando hay', async () => {
    server.use(
      resumen(),
      http.get(`${API}/encuestas/configuracion`, () => HttpResponse.json([])),
    )
    const { unmount } = renderizar(<EncuestasPage />)
    const user = userEvent.setup()
    expect(await screen.findByText('—')).toBeInTheDocument()
    expect(await screen.findByText('Aún nadie ha respondido la encuesta.')).toBeInTheDocument()
    await user.click(screen.getByLabelText('Sólo calificaciones de 3 o menos'))
    expect(await screen.findByText('Nadie ha calificado con 3 o menos.')).toBeInTheDocument()
    unmount()
    server.use(resumen({ promedio: 4.2, respondidas: 5, enviadas: 6, por_tipo_servicio: [{ tipo_servicio: 'consulta_domiciliaria', promedio: 4.5, respuestas: 4 }] }))
    await abrirPestana('Encuestas')
    expect(await screen.findByText('4,5 / 5 · 4 resp.')).toBeInTheDocument()
  })

  it('filtra las calificaciones bajas', async () => {
    const maximos: (string | null)[] = []
    server.use(resumen(),
      http.get(`${API}/encuestas/configuracion`, () => HttpResponse.json([])),
      http.get(`${API}/encuestas`, ({ request }) => {
        maximos.push(new URL(request.url).searchParams.get('puntaje_max'))
        return HttpResponse.json({
          items: [{ id: 'e1', servicio_id: 's1', familia_id: 'f1', responsable_id: null, tipo: 'satisfaccion', estado: 'respondida', programada_para: '', enviada_en: null, respondida_en: '2026-10-22T15:00:00Z', canal_respuesta: 'enlace', puntaje: 5, como_sigue: null, comentario: null, tarea_id: null }],
          total: 1,
          limit: 20,
          offset: 0,
        })
      }),
    )
    const user = await abrirPestana('Encuestas')
    expect(await screen.findByText('Sin comentario')).toBeInTheDocument()
    await user.click(screen.getByLabelText('Sólo calificaciones de 3 o menos'))
    await waitFor(() => expect(maximos).toEqual([null, '3']))
  })

  it('la administración ajusta la configuración general', async () => {
    let enviado: unknown = null
    server.use(resumen(),
      http.get(`${API}/encuestas/configuracion`, () =>
        HttpResponse.json([
          { id: 'cf1', tipo_servicio_codigo: null, encuesta_activa: true, demora_horas: 2, plantilla_encuesta: 'encuesta_v2', seguimiento_dias: 7, plantilla_seguimiento: 'seguimiento_v2', umbral_alerta: 3, comentario: 'nota' },
        ]),
      ),
      http.put(`${API}/encuestas/configuracion`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ id: 'cf1' })
      }),
    )
    const user = await abrirPestana('Encuestas')
    const horas = await screen.findByLabelText('Horas después del servicio')
    await user.clear(horas)
    await user.type(horas, '4')
    await user.clear(screen.getByLabelText('Seguimiento a los (días)'))
    await user.click(screen.getByLabelText('Enviar encuesta después de cada servicio'))
    await user.click(screen.getByRole('button', { name: 'Guardar' }))
    await waitFor(() =>
      expect(enviado).toEqual({
        tipo_servicio_codigo: null,
        encuesta_activa: false,
        demora_horas: 4,
        plantilla_encuesta: 'encuesta_v2',
        seguimiento_dias: null,
        plantilla_seguimiento: 'seguimiento_v2',
        umbral_alerta: 3,
        comentario: 'nota',
      }),
    )
    expect(await screen.findByText('Guardado.')).toBeInTheDocument()
  })

  it('explica por qué no se pudo guardar la configuración', async () => {
    server.use(resumen(),
      http.get(`${API}/encuestas/configuracion`, () => HttpResponse.json([])),
      http.put(`${API}/encuestas/configuracion`, () => HttpResponse.json({ detail: 'Umbral fuera de rango' }, { status: 422 })),
    )
    const user = await abrirPestana('Encuestas')
    await user.click(await screen.findByRole('button', { name: 'Guardar' }))
    expect(await screen.findByText('Umbral fuera de rango')).toBeInTheDocument()
  })

  it('Atención entra en las novedades, sin el análisis ni la configuración', async () => {
    const maximos: (string | null)[] = []
    const pedidos: string[] = []
    server.use(
      como('atencion_cliente'),
      http.get(`${API}/encuestas/resumen`, () => {
        pedidos.push('resumen')
        return HttpResponse.json({})
      }),
      http.get(`${API}/encuestas`, ({ request }) => {
        maximos.push(new URL(request.url).searchParams.get('puntaje_max'))
        return HttpResponse.json({ items: [], total: 0, limit: 20, offset: 0 })
      }),
    )
    renderizar(<EncuestasPage />)
    expect(await screen.findByText('Nadie ha calificado con 3 o menos.')).toBeInTheDocument()
    expect(screen.getByLabelText('Sólo calificaciones de 3 o menos')).toBeChecked()
    expect(maximos).toEqual(['3'])
    expect(pedidos).toEqual([])
    expect(screen.queryByText('Satisfacción del mes')).not.toBeInTheDocument()
    expect(screen.queryByText('Configuración general')).not.toBeInTheDocument()
  })
})

describe('mensajes y bajas', () => {
  // Atención al cliente quita las bajas, a pedido de la familia.
  beforeEach(() => server.use(como('atencion_cliente')))

  const MENSAJE: MensajeRead = {
    id: 'm1',
    familia_id: 'f1',
    canal: 'whatsapp',
    direccion: 'saliente',
    destino: '573001112233',
    plantilla: 'recordatorio_cuota',
    contenido: 'Su cuota vence mañana',
    estado: 'fallido',
    intentos: 5,
    error: 'Número inválido',
    masivo: false,
    enviado_en: null,
    entregado_en: null,
    leido_en: null,
    created_at: '2026-10-24T13:00:00Z',
  }

  function conMensajes(mensajes: MensajeRead[], bajas: unknown[] = []) {
    server.use(http.get(`${API}/comunicaciones/mensajes`, () => HttpResponse.json(pagina(mensajes))),
      http.get(`${API}/comunicaciones/bajas`, () => HttpResponse.json(bajas)),
    )
  }

  it('distingue entrantes y salientes y muestra el error de los fallidos', async () => {
    conMensajes([MENSAJE, { ...MENSAJE, id: 'm2', direccion: 'entrante', destino: null, plantilla: null, contenido: 'Gracias', estado: 'recibido', error: null }])
    await abrirPestana('Mensajes')
    expect(await screen.findByText('Número inválido')).toBeInTheDocument()
    expect(screen.getByText('Plantilla «recordatorio_cuota»')).toBeInTheDocument()
    // La dirección en palabras, no con flechas.
    expect(screen.getByText('Le escribimos a')).toBeInTheDocument()
    expect(screen.getByText('Escribió')).toBeInTheDocument()
  })

  it('busca por texto o número, por quién escribió y por fechas, y se quitan los filtros', async () => {
    const pedidos: URLSearchParams[] = []
    server.use(
      http.get(`${API}/comunicaciones/bajas`, () => HttpResponse.json([])),
      http.get(`${API}/comunicaciones/mensajes`, ({ request }) => {
        pedidos.push(new URL(request.url).searchParams)
        return HttpResponse.json(pagina([]))
      }),
    )
    const user = await abrirPestana('Mensajes')
    const buscador = await screen.findByLabelText('Buscar en el mensaje o el número')
    // Con menos de tres caracteres no se busca.
    await user.type(buscador, 'va')
    await user.type(buscador, 'cuna')
    await waitFor(() => expect(pedidos.at(-1)?.get('q')).toBe('vacuna'))
    expect(pedidos.some((p) => p.get('q') === 'va')).toBe(false)
    await user.selectOptions(screen.getByLabelText('Quién escribió'), 'entrante')
    await user.type(screen.getByLabelText('Desde'), '2026-11-01')
    await waitFor(() => expect(pedidos.at(-1)?.get('desde')).toBe('2026-11-01'))
    expect(pedidos.at(-1)?.get('direccion')).toBe('entrante')
    expect(await screen.findByText('Ningún mensaje coincide con la búsqueda.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Quitar filtros' }))
    await waitFor(() => expect(pedidos.at(-1)?.get('q')).toBeNull())
    expect(pedidos.at(-1)?.get('direccion')).toBeNull()
    expect(screen.getByLabelText('Buscar en el mensaje o el número')).toHaveValue('')
  })

  it('un mensaje abre la conversación entera con su número, marcado y en orden', async () => {
    const entrante = { ...MENSAJE, id: 'm0', direccion: 'entrante', plantilla: null, contenido: '¿Cuándo vence mi cuota?', estado: 'recibido', error: null, created_at: '2026-10-24T12:00:00Z' }
    const conversacion: string[] = []
    server.use(
      http.get(`${API}/comunicaciones/bajas`, () => HttpResponse.json([])),
      http.get(`${API}/comunicaciones/mensajes`, ({ request }) => {
        const destino = new URL(request.url).searchParams.get('destino')
        if (destino) conversacion.push(destino)
        // La API los da del más nuevo al más viejo; la ventana los pone en orden.
        return HttpResponse.json(pagina(destino ? [MENSAJE, entrante] : [MENSAJE]))
      }),
    )
    const user = await abrirPestana('Mensajes')
    await user.click(await screen.findByRole('button', { name: /^Ver la conversación con/ }))
    const ventana = await screen.findByRole('dialog', { name: /^Conversación con/ })
    const burbujas = await within(ventana).findAllByRole('listitem')
    expect(burbujas.map((b) => b.querySelector('p')?.textContent)).toEqual(['¿Cuándo vence mi cuota?', 'Su cuota vence mañana'])
    expect(burbujas[1]).toHaveAttribute('aria-current', 'true')
    expect(conversacion).toEqual(['573001112233'])
    expect(within(ventana).getByRole('link', { name: 'Ver la familia' })).toHaveAttribute('href', '/panel/familias/f1')
  })

  it('filtra por estado y muestra el vacío', async () => {
    const estados: (string | null)[] = []
    server.use(http.get(`${API}/comunicaciones/bajas`, () => HttpResponse.json([])),
      http.get(`${API}/comunicaciones/mensajes`, ({ request }) => {
        estados.push(new URL(request.url).searchParams.get('estado'))
        return HttpResponse.json(pagina([]))
      }),
    )
    const user = await abrirPestana('Mensajes')
    expect(await screen.findByText('No hay mensajes.')).toBeInTheDocument()
    expect(await screen.findByText('Nadie se ha dado de baja.')).toBeInTheDocument()
    await user.selectOptions(screen.getByLabelText('Estado del mensaje'), 'fallido')
    await waitFor(() => expect(estados).toEqual([null, 'fallido']))
  })

  it('da de baja un celular y luego la quita', async () => {
    let alta: unknown = null
    let quitado = ''
    conMensajes([], [{ id: 'b1', destino: '+573009998877', canal: 'whatsapp', motivo: null, created_at: '2026-10-20T10:00:00Z' }])
    server.use(
      http.post(`${API}/comunicaciones/bajas`, async ({ request }) => {
        alta = await request.json()
        return HttpResponse.json({ id: 'b2', destino: '573001112233', canal: 'whatsapp', motivo: null, created_at: '' }, { status: 201 })
      }),
      http.delete(`${API}/comunicaciones/bajas/:destino`, ({ params }) => {
        quitado = String(params.destino)
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const user = await abrirPestana('Mensajes')
    const celular = screen.getByLabelText('Celular a dar de baja')
    await user.type(celular, ' 573001112233 ')
    await user.click(screen.getByRole('button', { name: 'Agregar' }))
    await waitFor(() => expect(alta).toEqual({ telefono: '573001112233' }))
    await waitFor(() => expect(celular).toHaveValue(''))
    await user.click(await screen.findByRole('button', { name: 'Quitar la baja de +57 300 999 8877' }))
    await waitFor(() => expect(quitado).toBe('+573009998877'))
  })

  it('explica por qué no se pudo dar de baja', async () => {
    conMensajes([])
    server.use(http.post(`${API}/comunicaciones/bajas`, () => HttpResponse.json({ detail: 'Celular inválido' }, { status: 422 })))
    const user = await abrirPestana('Mensajes')
    await user.type(screen.getByLabelText('Celular a dar de baja'), '123')
    await user.click(screen.getByRole('button', { name: 'Agregar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Celular inválido')
  })
})

describe('plantillas de WhatsApp', () => {
  it('registra el estado de aprobación de Meta y la activa o desactiva', async () => {
    const cambios: unknown[] = []
    server.use(http.patch(`${API}/comunicaciones/plantillas/p1/estado`, async ({ request }) => {
        cambios.push(await request.json())
        return HttpResponse.json(PLANTILLA)
      }),
    )
    const user = await abrirPestana('Plantillas de WhatsApp')
    await user.selectOptions(await screen.findByLabelText('Aprobación de recordatorio_renovacion'), 'pausada')
    await user.click(screen.getByLabelText('recordatorio_renovacion activa'))
    await waitFor(() =>
      expect(cambios).toEqual([{ estado_aprobacion: 'pausada' }, { estado_aprobacion: 'aprobada', activa: false }]),
    )
  })

  it('explica por qué no se pudo cambiar el estado', async () => {
    server.use(http.patch(`${API}/comunicaciones/plantillas/p1/estado`, () => HttpResponse.json({ detail: 'Transición no válida' }, { status: 409 })),
    )
    const user = await abrirPestana('Plantillas de WhatsApp')
    await user.selectOptions(await screen.findByLabelText('Aprobación de recordatorio_renovacion'), 'borrador')
    expect(await screen.findByRole('alert')).toHaveTextContent('Transición no válida')
  })

  it('registra una plantilla con sus variables sin repetir', async () => {
    let enviado: unknown = null
    server.use(http.get(`${API}/comunicaciones/plantillas`, () => HttpResponse.json([])),
      http.post(`${API}/comunicaciones/plantillas`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(PLANTILLA, { status: 201 })
      }),
    )
    const user = await abrirPestana('Plantillas de WhatsApp')
    expect(await screen.findByText('No hay plantillas.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /nueva plantilla/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nombre para el equipo'), 'Promoción de vacunas')
    await user.type(within(modal).getByLabelText('Código en Meta'), 'promo_vacunas')
    await user.selectOptions(within(modal).getByLabelText('Categoría'), 'marketing')
    await user.type(within(modal).getByLabelText(/^Texto/), 'Hola {{{{1}}, {{{{2}} y otra vez {{{{1}}')
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    await waitFor(() =>
      expect(enviado).toEqual({
        nombre: 'promo_vacunas',
        titulo: 'Promoción de vacunas',
        categoria: 'marketing',
        cuerpo: 'Hola {{1}}, {{2}} y otra vez {{1}}',
        variables: ['1', '2'],
      }),
    )
  })

  it('edita el texto de la versión más reciente como una versión nueva, con el código fijo', async () => {
    const V1 = { ...PLANTILLA, id: 'p1', version: 1, titulo: 'Recordatorio de renovación' }
    const V2 = { ...V1, id: 'p2', version: 2, cuerpo: 'Hola {{1}}, tu plan vence.', estado_aprobacion: 'borrador', activa: false }
    let enviado: unknown = null
    server.use(
      http.get(`${API}/comunicaciones/plantillas`, () => HttpResponse.json([V2, V1])),
      http.post(`${API}/comunicaciones/plantillas`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ ...V2, version: 3 }, { status: 201 })
      }),
    )
    const user = await abrirPestana('Plantillas de WhatsApp')
    // Solo la versión más reciente se edita: la vieja ya no lleva el botón.
    const editar = await screen.findAllByRole('button', { name: 'Editar el texto de Recordatorio de renovación' })
    expect(editar).toHaveLength(1)
    await user.click(editar[0])
    const modal = await screen.findByRole('dialog', { name: 'Editar «Recordatorio de renovación»' })
    expect(within(modal).getByText(/queda como versión 3, en borrador/)).toBeInTheDocument()
    expect(within(modal).getByLabelText('Código en Meta')).toHaveAttribute('readonly')
    const texto = within(modal).getByLabelText(/^Texto/)
    expect(texto).toHaveValue('Hola {{1}}, tu plan vence.')
    await user.clear(texto)
    await user.type(texto, 'Hola {{{{1}}, tu plan vence el {{{{2}}.')
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    await waitFor(() =>
      expect(enviado).toMatchObject({ nombre: V1.nombre, titulo: 'Recordatorio de renovación', cuerpo: 'Hola {{1}}, tu plan vence el {{2}}.', variables: ['1', '2'] }),
    )
  })

  it('el Inicio del administrador abre la ventana con el código y el nombre que citan las reglas', async () => {
    let enviado: unknown = null
    server.use(
      http.post(`${API}/comunicaciones/plantillas`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(PLANTILLA, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<PlantillasWhatsApp />, { ruta: '/panel/admin?pestana=plantillas&nueva=aviso_mora&titulo=Aviso+de+mora' })
    const modal = await screen.findByRole('dialog', { name: 'Nueva plantilla de WhatsApp' })
    expect(within(modal).getByLabelText('Código en Meta')).toHaveValue('aviso_mora')
    expect(within(modal).getByLabelText('Nombre para el equipo')).toHaveValue('Aviso de mora')
    await user.type(within(modal).getByLabelText(/^Texto/), 'Hola {{{{1}}, tu cuota está en mora.')
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    await waitFor(() => expect(enviado).toMatchObject({ nombre: 'aviso_mora', titulo: 'Aviso de mora', variables: ['1'] }))
    // Al guardar se cierra y no vuelve a abrirse sola.
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('explica por qué no se pudo registrar la plantilla', async () => {
    server.use(http.post(`${API}/comunicaciones/plantillas`, () => HttpResponse.json({ detail: 'Nombre repetido' }, { status: 409 })),
    )
    const user = await abrirPestana('Plantillas de WhatsApp')
    await user.click(await screen.findByRole('button', { name: /nueva plantilla/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Código en Meta'), 'promo')
    await user.type(within(modal).getByLabelText(/^Texto/), 'Hola')
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('Nombre repetido')
  })
})
