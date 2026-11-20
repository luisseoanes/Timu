import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'

import { AliadasPage } from './AliadasPage'
import { FAMILIA, USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { ClinicaRead, FamiliaRead, RemisionRead } from '@/types'

const API = '*/api/v1'
const LUNA = FAMILIA.mascotas![0]!
const como = (rol: string) => http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol }))

const CLINICA: ClinicaRead = {
  id: 'cl1',
  nombre: 'Clínica Norte',
  ciudad: 'Bogotá',
  activa: true,
  nit: '900123',
  telefono: '6011234',
  servicios: 'Rayos X y hospitalización',
}

const CONVENIO = {
  id: 'cv1',
  clinica_id: 'cl1',
  beneficio: 'Radiografía',
  cobertura_pct: 80,
  tarifa: '120000.00',
  tope_cubierto: '200000.00',
  vigente_desde: '2026-01-01',
  activo: true,
}

const REMISION: RemisionRead = {
  id: 'r1',
  codigo: 'REM7K2Q',
  clinica_id: 'cl1',
  familia_id: 'f1',
  mascota_id: 'm1',
  servicio_id: 's1',
  motivo: 'Radiografía de cadera',
  beneficio_aplicado: 'Radiografía',
  cobertura_pct: 80,
  tope_cubierto: null,
  vence_en: '2026-11-10',
  estado: 'utilizada',
  fecha_atencion: '2026-10-30',
  valor_atencion: '150000.00',
  valor_cubierto: '120000.00',
  created_at: '2026-10-24T10:00:00Z',
  vencida: false,
  titular: 'Ana Ruiz',
  mascota: 'Luna',
  clinica: 'Clínica Norte',
}

beforeEach(() =>
  server.use(
    http.get(`${API}/aliadas/remisiones/recuentos`, () => HttpResponse.json({ emitida: 1, utilizada: 1, anulada: 0, todas: 2 })),
    http.get(`${API}/aliadas`, () => HttpResponse.json([CLINICA])),
    http.get(`${API}/aliadas/remisiones`, () => HttpResponse.json([])),
    http.get(`${API}/aliadas/:id/convenios`, () => HttpResponse.json([CONVENIO])),
  ),
)

async function abrirPestana(nombre: string) {
  const user = userEvent.setup()
  renderizar(<AliadasPage />)
  await user.click(await screen.findByRole('tab', { name: nombre }))
  return user
}

describe('remisiones', () => {
  // Las emite y anula Atención al cliente (6.22, docs/perfiles-y-permisos.md).
  beforeEach(() => server.use(como('atencion_cliente')))

  it('una utilizada dice cuándo se atendió y lo que cubrió, y ya no se anula', async () => {
    server.use(http.get(`${API}/aliadas/remisiones`, () => HttpResponse.json([REMISION])))
    renderizar(<AliadasPage />, { ruta: '/panel/aliadas?vista=utilizada' })
    // Dice de quién es: el titular y la mascota llevan a la familia.
    const fila = (await screen.findByRole('link', { name: 'Ana Ruiz · Luna' })).closest('tr')!
    expect(within(fila).getByText('REM7K2Q')).toBeInTheDocument()
    expect(within(fila).getByText(/^Cubrió\s\$\s120\.000$/)).toBeInTheDocument()
    expect(within(fila).getByText('30 oct')).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Atendida' })).toBeInTheDocument()
    expect(within(fila).queryByRole('button', { name: /anular/i })).not.toBeInTheDocument()
  })

  it('desde la ficha de una clínica muestra solo las suyas, sin columna de acciones si no se anula', async () => {
    const pedidas: (string | null)[] = []
    server.use(
      http.get(`${API}/aliadas/remisiones`, ({ request }) => {
        pedidas.push(new URL(request.url).searchParams.get('clinica_id'))
        return HttpResponse.json([REMISION])
      }),
    )
    const user = userEvent.setup()
    renderizar(<AliadasPage />, { ruta: '/panel/aliadas?pestana=remisiones&vista=utilizada&remisiones_de=cl1' })
    expect(await screen.findByText(/Solo las de Clínica Norte/)).toBeInTheDocument()
    await waitFor(() => expect(pedidas).toContain('cl1'))
    // En Utilizadas no se anula nada: la columna de acciones no existe (techo 61).
    expect(screen.queryByRole('columnheader', { name: 'Acciones' })).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Ver las de todas' }))
    expect(screen.queryByText(/Solo las de/)).not.toBeInTheDocument()
    await waitFor(() => expect(pedidas.at(-1)).toBeNull())
  })

  it('las vistas llevan su recuento, piden su estado y dicen su vacío', async () => {
    const estados: (string | null)[] = []
    server.use(
      http.get(`${API}/aliadas/remisiones`, ({ request }) => {
        estados.push(new URL(request.url).searchParams.get('estado'))
        return HttpResponse.json([])
      }),
    )
    const user = userEvent.setup()
    renderizar(<AliadasPage />)
    expect(await screen.findByText(/No hay remisiones por usar/)).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: 'Por usar 1' })).toHaveAttribute('aria-pressed', 'true')
    await user.click(screen.getByRole('button', { name: 'Todas 2' }))
    await waitFor(() => expect(estados).toEqual(['emitida', null]))
    expect(await screen.findByText('Aún no se ha emitido ninguna remisión.')).toBeInTheDocument()
  })

  it('una vencida lo dice con icono y palabra', async () => {
    server.use(
      http.get(`${API}/aliadas/remisiones`, () =>
        HttpResponse.json([{ ...REMISION, estado: 'emitida', fecha_atencion: null, valor_cubierto: null, vencida: true }]),
      ),
    )
    renderizar(<AliadasPage />)
    const fila = (await screen.findByRole('link', { name: 'Ana Ruiz · Luna' })).closest('tr')!
    expect(within(fila).getByText('Venció el')).toBeInTheDocument()
    expect(within(fila).getByText('10 nov')).toBeInTheDocument()
  })

  it('anular confirma en rojo, y explica por qué no se pudo', async () => {
    server.use(
      http.get(`${API}/aliadas/remisiones`, () => HttpResponse.json([{ ...REMISION, estado: 'emitida' }])),
      http.post(`${API}/aliadas/remisiones/r1/anulacion`, () => HttpResponse.json({ detail: 'Ya fue utilizada' }, { status: 409 })),
    )
    const user = userEvent.setup()
    renderizar(<AliadasPage />)
    await user.click(await screen.findByRole('button', { name: 'Anular la remisión REM7K2Q' }))
    const modal = await screen.findByRole('dialog', { name: 'Anular la remisión REM7K2Q' })
    await user.type(within(modal).getByLabelText('Motivo'), 'Error de digitación')
    const confirmar = within(modal).getByRole('button', { name: 'Anular remisión' })
    expect(confirmar).toHaveClass('btn-peligro')
    await user.click(confirmar)
    expect(await within(modal).findByRole('alert')).toHaveTextContent('Ya fue utilizada')
    // «Mantenerla» olvida el intento: al volver a abrirla no arrastra el error.
    await user.click(within(modal).getByRole('button', { name: 'Mantenerla' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: 'Anular la remisión REM7K2Q' }))
    expect(within(await screen.findByRole('dialog')).queryByRole('alert')).not.toBeInTheDocument()
  })

  it('emite una remisión a una aliada de la ciudad con su convenio y da el código', async () => {
    let enviado: unknown = null
    const ciudades: (string | null)[] = []
    const familia: FamiliaRead = { ...FAMILIA, mascotas: [LUNA, { ...LUNA, id: 'm2', nombre: 'Tom', activa: false }] }
    server.use(
      http.get(`${API}/familias`, () => HttpResponse.json({ items: [familia], total: 1, limit: 6, offset: 0 })),
      http.get(`${API}/aliadas`, ({ request }) => {
        ciudades.push(new URL(request.url).searchParams.get('ciudad'))
        return HttpResponse.json([CLINICA])
      }),
      http.get(`${API}/aliadas/cl1/convenios`, () =>
        HttpResponse.json([CONVENIO, { ...CONVENIO, id: 'cv2', beneficio: 'Vencido', activo: false }]),
      ),
      http.post(`${API}/aliadas/remisiones`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ ...REMISION, codigo: 'REM9X', estado: 'emitida' }, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<AliadasPage />)
    await user.click(await screen.findByRole('button', { name: /emitir remisión/i }))
    const modal = await screen.findByRole('dialog')
    expect(within(modal).getByRole('button', { name: 'Emitir' })).toBeDisabled()
    expect(within(modal).getByLabelText('Mascota')).toHaveDisplayValue('Elige primero la familia')
    await user.type(within(modal).getByRole('searchbox'), 'Ana')
    await user.click(await within(modal).findByRole('button', { name: /ana ruiz/i }))
    expect(within(modal).queryByRole('option', { name: 'Tom' })).not.toBeInTheDocument()
    // No elige la mascota por nadie.
    expect(within(modal).getByLabelText('Mascota')).toHaveDisplayValue('Elige la mascota')
    await user.selectOptions(within(modal).getByLabelText('Mascota'), LUNA.id)
    await waitFor(() => expect(ciudades).toContain('Bogotá'))
    await user.selectOptions(await within(modal).findByLabelText('Clínica en Bogotá'), 'cl1')
    await waitFor(() => expect(within(modal).getByRole('option', { name: 'Radiografía · 80%' })).toBeInTheDocument())
    expect(within(modal).queryByRole('option', { name: /Vencido/ })).not.toBeInTheDocument()
    await user.selectOptions(within(modal).getByLabelText('Convenio'), 'cv1')
    await user.type(within(modal).getByLabelText('Motivo de la remisión'), ' Radiografía de cadera ')
    await user.click(within(modal).getByRole('button', { name: 'Emitir' }))
    await waitFor(() =>
      expect(enviado).toEqual({ clinica_id: 'cl1', mascota_id: LUNA.id, motivo: 'Radiografía de cadera', convenio_id: 'cv1' }),
    )
    expect(await within(modal).findByRole('status')).toHaveTextContent('Remisión emitida con código REM9X')
    expect(within(modal).queryByRole('button', { name: 'Emitir' })).not.toBeInTheDocument()
  })

  it('dice cuándo la familia no tiene mascotas activas', async () => {
    server.use(
      http.get(`${API}/familias`, () =>
        HttpResponse.json({ items: [{ ...FAMILIA, mascotas: [{ ...LUNA, activa: false }] }], total: 1, limit: 6, offset: 0 }),
      ),
    )
    const user = userEvent.setup()
    renderizar(<AliadasPage />)
    await user.click(await screen.findByRole('button', { name: /emitir remisión/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByRole('searchbox'), 'Ana')
    await user.click(await within(modal).findByRole('button', { name: /ana ruiz/i }))
    expect(within(modal).getByLabelText('Mascota')).toHaveDisplayValue('La familia no tiene mascotas activas')
  })

  it('avisa si no hay aliadas en la ciudad de la familia', async () => {
    server.use(http.get(`${API}/aliadas`, ({ request }) =>
      HttpResponse.json(new URL(request.url).searchParams.get('ciudad') ? [] : [CLINICA]),
    ))
    const user = userEvent.setup()
    renderizar(<AliadasPage />)
    await user.click(await screen.findByRole('button', { name: /emitir remisión/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByRole('searchbox'), 'Ana')
    await user.click(await within(modal).findByRole('button', { name: /ana ruiz/i }))
    expect(await within(modal).findByRole('option', { name: 'No hay aliadas en la ciudad' })).toBeInTheDocument()
  })

  it('explica por qué no se pudo emitir', async () => {
    server.use(
      http.post(`${API}/aliadas/remisiones`, () => HttpResponse.json({ detail: 'La familia está en mora' }, { status: 409 })),
    )
    const user = userEvent.setup()
    renderizar(<AliadasPage />)
    await user.click(await screen.findByRole('button', { name: /emitir remisión/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByRole('searchbox'), 'Ana')
    await user.click(await within(modal).findByRole('button', { name: /ana ruiz/i }))
    await user.selectOptions(within(modal).getByLabelText('Mascota'), LUNA.id)
    await user.selectOptions(await within(modal).findByLabelText('Clínica en Bogotá'), 'cl1')
    await user.type(within(modal).getByLabelText('Motivo de la remisión'), 'Radiografía')
    await user.click(within(modal).getByRole('button', { name: 'Emitir' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('La familia está en mora')
  })
})

describe('clínicas y convenios', () => {
  // La red de aliadas la lleva Operaciones.
  beforeEach(() => server.use(como('operaciones')))

  async function abrirClinica() {
    const user = userEvent.setup()
    renderizar(<AliadasPage />, { ruta: '/panel/aliadas?clinica=cl1' })
    await user.click(await screen.findByRole('tab', { name: 'Clínicas y convenios' }))
    const ficha = await screen.findByRole('region', { name: 'Clínica abierta' })
    await within(ficha).findByRole('heading', { level: 2, name: 'Clínica Norte' })
    return { user, ficha }
  }

  it('sin clínica abierta lo indica, y al abrir una muestra sus datos y convenios', async () => {
    const user = await abrirPestana('Clínicas y convenios')
    expect(await screen.findByText(/Abre una clínica para ver sus datos y sus convenios/)).toBeInTheDocument()
    await user.click(await screen.findByRole('link', { name: 'Clínica Norte' }))
    const ficha = screen.getByRole('region', { name: 'Clínica abierta' })
    expect(await within(ficha).findByText('Rayos X y hospitalización')).toBeInTheDocument()
    const convenio = (await within(ficha).findByText('Radiografía')).closest('tr')!
    expect(within(convenio).getByText(/^80 %\shasta\s\$\s200\.000$/)).toBeInTheDocument()
    expect(within(convenio).getByText('Todos los planes')).toBeInTheDocument()
    expect(within(convenio).getByText('Desde el 1 ene')).toBeInTheDocument()
    // Las remisiones son de Atención al cliente: la ficha de Operaciones no las pide (Sección 12).
    expect(within(ficha).queryByRole('heading', { name: 'Remisiones' })).not.toBeInTheDocument()
  })

  it('Operaciones desactiva una clínica desde el menú', async () => {
    let activa = true
    let cambio: unknown = null
    server.use(
      http.get(`${API}/aliadas`, () => HttpResponse.json([{ ...CLINICA, activa }])),
      http.patch(`${API}/aliadas/cl1`, async ({ request }) => {
        cambio = await request.json()
        activa = false
        return HttpResponse.json({ ...CLINICA, activa: false })
      }),
    )
    const { user, ficha } = await abrirClinica()
    await user.click(within(ficha).getByRole('button', { name: 'Más acciones con Clínica Norte' }))
    await user.click(await screen.findByRole('menuitem', { name: 'Desactivar clínica' }))
    await waitFor(() => expect(cambio).toEqual({ activa: false }))
    expect(await within(ficha).findByText('Inactiva: no recibe remisiones nuevas.')).toBeInTheDocument()
    expect(within(ficha).getByRole('button', { name: /nuevo convenio/i })).toBeDisabled()
  })

  it('Operaciones registra un convenio con su plan', async () => {
    let enviado: unknown = null
    server.use(
      http.get(`${API}/planes`, () => HttpResponse.json([{ id: 'p1', nombre: 'Plan Familiar' }])),
      http.get(`${API}/aliadas/cl1/convenios`, () => HttpResponse.json([])),
      http.post(`${API}/aliadas/cl1/convenios`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(CONVENIO, { status: 201 })
      }),
    )
    const { user, ficha } = await abrirClinica()
    expect(await within(ficha).findByText('Sin convenios: no se le puede remitir hasta registrar uno.')).toBeInTheDocument()
    // Con la ficha abierta, el verde es de ella: «Nueva clínica» pasa a suave.
    expect(screen.getByRole('button', { name: /nueva clínica/i })).toHaveClass('btn-suave')
    await user.click(within(ficha).getByRole('button', { name: /nuevo convenio/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Beneficio'), ' Ecografía ')
    await user.selectOptions(within(modal).getByLabelText('Plan'), 'p1')
    const cobertura = within(modal).getByLabelText('Cobertura (%)')
    await user.clear(cobertura)
    await user.type(cobertura, '70')
    await user.type(within(modal).getByLabelText('Tarifa acordada (COP)'), '90000')
    const desde = within(modal).getByLabelText('Vigente desde')
    await user.clear(desde)
    await user.type(desde, '2026-12-01')
    await user.click(within(modal).getByRole('button', { name: 'Guardar convenio' }))
    await waitFor(() =>
      expect(enviado).toEqual({ beneficio: 'Ecografía', cobertura_pct: 70, tarifa: '90000', vigente_desde: '2026-12-01', plan_id: 'p1' }),
    )
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('explica por qué no se pudo guardar el convenio', async () => {
    server.use(
      http.post(`${API}/aliadas/cl1/convenios`, () => HttpResponse.json({ detail: 'Ya hay un convenio vigente' }, { status: 409 })),
    )
    const { user, ficha } = await abrirClinica()
    await user.click(within(ficha).getByRole('button', { name: /nuevo convenio/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Beneficio'), 'Ecografía')
    await user.type(within(modal).getByLabelText('Tarifa acordada (COP)'), '90000')
    await user.type(within(modal).getByLabelText('Tope cubierto (COP, opcional)'), '100000')
    await user.click(within(modal).getByRole('button', { name: 'Guardar convenio' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('Ya hay un convenio vigente')
  })

  it('registra una clínica nueva sin enviar los campos vacíos como texto, y abre su ficha', async () => {
    let enviado: unknown = null
    server.use(
      http.get(`${API}/aliadas`, () => HttpResponse.json(enviado ? [CLINICA] : [])),
      http.post(`${API}/aliadas`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(CLINICA, { status: 201 })
      }),
    )
    const user = await abrirPestana('Clínicas y convenios')
    expect(await screen.findByText('Aún no hay clínicas aliadas. Registra la primera con «Nueva clínica».')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /nueva clínica/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nombre'), ' Clínica Sur ')
    await user.selectOptions(within(modal).getByLabelText('Ciudad'), 'Bogotá')
    await user.type(within(modal).getByLabelText('Teléfono'), '6017654')
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    await waitFor(() =>
      expect(enviado).toEqual({
        nombre: 'Clínica Sur',
        nit: null,
        ciudad: 'Bogotá',
        direccion: null,
        telefono: '6017654',
        email: null,
        servicios: null,
      }),
    )
    // Lo siguiente es registrar sus convenios: se abre su ficha.
    const titulo = await screen.findByRole('heading', { level: 2, name: 'Clínica Norte' }, { timeout: 5000 })
    expect(titulo.closest('section')).toHaveAccessibleName('Clínica abierta')
  })

  it('explica por qué no se pudo registrar la clínica', async () => {
    server.use(http.post(`${API}/aliadas`, () => HttpResponse.json({ detail: 'NIT repetido' }, { status: 409 })))
    const user = await abrirPestana('Clínicas y convenios')
    await user.click(await screen.findByRole('button', { name: /nueva clínica/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nombre'), 'Clínica Sur')
    await user.selectOptions(within(modal).getByLabelText('Ciudad'), 'Bogotá')
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('NIT repetido')
  })

  it('quien no lleva la red no ve las clínicas ni la liquidación', async () => {
    server.use(como('atencion_cliente'))
    renderizar(<AliadasPage />)
    expect(await screen.findByRole('tab', { name: 'Remisiones' })).toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: 'Clínicas y convenios' })).not.toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: 'Liquidación' })).not.toBeInTheDocument()
  })

  it('Operaciones ve también las inactivas', async () => {
    const pedidas: (string | null)[] = []
    server.use(
      http.get(`${API}/aliadas`, ({ request }) => {
        pedidas.push(new URL(request.url).searchParams.get('incluir_inactivas'))
        return HttpResponse.json([{ ...CLINICA, activa: false, telefono: null }])
      }),
    )
    await abrirPestana('Clínicas y convenios')
    expect(await screen.findByText('Inactiva')).toBeInTheDocument()
    expect(pedidas.at(-1)).toBe('true')
  })

  it('una clínica que no está en el listado lo dice', async () => {
    const user = userEvent.setup()
    renderizar(<AliadasPage />, { ruta: '/panel/aliadas?clinica=otra' })
    await user.click(await screen.findByRole('tab', { name: 'Clínicas y convenios' }))
    expect(await screen.findByText('Esta clínica ya no existe o no la puedes ver.')).toBeInTheDocument()
  })
})

describe('liquidación', () => {
  beforeEach(() => server.use(como('operaciones')))

  const FILA = {
    clinica_id: 'cl1',
    clinica: 'Clínica Norte',
    nit: '900123',
    atenciones: 3,
    valor_atenciones: '450000.00',
    valor_cubierto: '360000.00',
    valor_familias: '90000.00',
    detalle: [],
  }

  it('liquida el período elegido por clínica', async () => {
    const periodos: string[] = []
    server.use(
      http.get(`${API}/aliadas/liquidacion`, ({ request }) => {
        const p = new URL(request.url).searchParams
        periodos.push(`${p.get('desde')}..${p.get('hasta')}`)
        return HttpResponse.json([FILA, { ...FILA, clinica_id: 'cl2', clinica: 'Sin NIT', nit: null }])
      }),
    )
    const user = await abrirPestana('Liquidación')
    expect(await screen.findByText('NIT 900123')).toBeInTheDocument()
    expect(screen.getByText('Sin NIT')).toBeInTheDocument()
    // Con más de una clínica, el total del período.
    const total = screen.getByText('Total').closest('tr')!
    expect(within(total).getByText('6')).toBeInTheDocument()
    expect(within(total).getByText(/^\$\s720\.000$/)).toBeInTheDocument()
    const desde = screen.getByLabelText('Desde')
    await user.clear(desde)
    await user.type(desde, '2026-09-01')
    const hasta = screen.getByLabelText('Hasta')
    await user.clear(hasta)
    await user.type(hasta, '2026-09-30')
    await waitFor(() => expect(periodos).toContain('2026-09-01..2026-09-30'))
  })

  it('cada clínica abre ahí mismo el detalle de sus atenciones, sin descargar el CSV', async () => {
    const detalle = [
      { codigo: 'ABCD2345', fecha_atencion: '2026-11-06', beneficio: 'Radiografía', valor_atencion: '180000.00', valor_cubierto: '144000.00' },
      { codigo: 'EFGH6789', fecha_atencion: '2026-11-14', beneficio: null, valor_atencion: '270000.00', valor_cubierto: '216000.00' },
    ]
    server.use(http.get(`${API}/aliadas/liquidacion`, () => HttpResponse.json([{ ...FILA, detalle }])))
    const user = await abrirPestana('Liquidación')
    const abrir = await screen.findByRole('button', { name: 'Clínica Norte' })
    expect(abrir).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByRole('table', { name: 'Atenciones de Clínica Norte' })).not.toBeInTheDocument()
    await user.click(abrir)
    expect(abrir).toHaveAttribute('aria-expanded', 'true')
    const tabla = screen.getByRole('table', { name: 'Atenciones de Clínica Norte' })
    const filas = within(tabla).getAllByRole('row').slice(1)
    expect(filas).toHaveLength(2)
    expect(within(filas[0]).getByText('ABCD2345')).toBeInTheDocument()
    expect(within(filas[0]).getByText('Radiografía')).toBeInTheDocument()
    // Lo que paga la familia: el valor menos lo que cubre TIMU.
    expect(within(filas[0]).getByText(/^\$\s36\.000$/)).toBeInTheDocument()
    expect(within(filas[1]).getByText('—')).toBeInTheDocument()
    await user.click(abrir)
    expect(screen.queryByRole('table', { name: 'Atenciones de Clínica Norte' })).not.toBeInTheDocument()
  })

  it('sin atenciones lo dice y explica si el CSV falla', async () => {
    server.use(
      http.get(`${API}/aliadas/liquidacion`, ({ request }) =>
        new URL(request.url).searchParams.get('formato') === 'csv'
          ? HttpResponse.json({ detail: 'No disponible' }, { status: 503 })
          : HttpResponse.json([]),
      ),
    )
    const user = await abrirPestana('Liquidación')
    expect(await screen.findByText('Ninguna aliada reportó atenciones en el período.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Descargar CSV' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('No fue posible descargar la liquidación.')
  })
})
