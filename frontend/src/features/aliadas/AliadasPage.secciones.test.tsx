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
  ciudad: 'Bogota',
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
}

beforeEach(() =>
  server.use(
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
  it('una utilizada muestra lo cubierto y ya no se anula', async () => {
    server.use(http.get(`${API}/aliadas/remisiones`, () => HttpResponse.json([REMISION])))
    renderizar(<AliadasPage />)
    const fila = (await screen.findByRole('link', { name: 'REM7K2Q' })).closest('tr')!
    expect(within(fila).getByText(/Cubierto/)).toBeInTheDocument()
    expect(within(fila).getByText('80%')).toBeInTheDocument()
    expect(within(fila).queryByRole('button', { name: 'Anular' })).not.toBeInTheDocument()
  })

  it('filtra por estado y muestra el vacío', async () => {
    const estados: (string | null)[] = []
    server.use(
      http.get(`${API}/aliadas/remisiones`, ({ request }) => {
        estados.push(new URL(request.url).searchParams.get('estado'))
        return HttpResponse.json([])
      }),
    )
    const user = userEvent.setup()
    renderizar(<AliadasPage />)
    expect(await screen.findByText('No hay remisiones en este estado.')).toBeInTheDocument()
    await user.selectOptions(screen.getByLabelText('Estado de la remisión'), '')
    await waitFor(() => expect(estados).toEqual(['emitida', null]))
  })

  it('explica por qué no se pudo anular', async () => {
    server.use(
      http.get(`${API}/aliadas/remisiones`, () => HttpResponse.json([{ ...REMISION, estado: 'emitida' }])),
      http.post(`${API}/aliadas/remisiones/r1/anulacion`, () => HttpResponse.json({ detail: 'Ya fue utilizada' }, { status: 409 })),
    )
    const user = userEvent.setup()
    renderizar(<AliadasPage />)
    await user.click(await screen.findByRole('button', { name: 'Anular' }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Motivo'), 'Error de digitación')
    await user.click(within(modal).getByRole('button', { name: 'Anular' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('Ya fue utilizada')
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
    await user.type(within(modal).getByRole('searchbox'), 'Ana')
    await user.click(await within(modal).findByRole('button', { name: /ana ruiz/i }))
    expect(within(modal).queryByRole('option', { name: 'Tom' })).not.toBeInTheDocument()
    await waitFor(() => expect(ciudades).toContain('Bogota'))
    await user.selectOptions(await within(modal).findByLabelText('Clínica en Bogota'), 'cl1')
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
    await user.selectOptions(await within(modal).findByLabelText('Clínica en Bogota'), 'cl1')
    await user.type(within(modal).getByLabelText('Motivo de la remisión'), 'Radiografía')
    await user.click(within(modal).getByRole('button', { name: 'Emitir' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('La familia está en mora')
  })
})

describe('clínicas y convenios', () => {
  it('sin clínica elegida lo indica, y al elegir muestra sus servicios y convenios', async () => {
    const user = await abrirPestana('Clínicas y convenios')
    expect(await screen.findByText('Elige una clínica para ver sus convenios.')).toBeInTheDocument()
    expect(screen.getByText('Bogota · 6011234')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /clínica norte/i }))
    expect(await screen.findByText('Rayos X y hospitalización')).toBeInTheDocument()
    expect(await screen.findByText(/80% · tarifa .* · tope/)).toBeInTheDocument()
  })

  it('la administración desactiva una clínica', async () => {
    let cambio: unknown = null
    server.use(
      http.patch(`${API}/aliadas/cl1`, async ({ request }) => {
        cambio = await request.json()
        return HttpResponse.json({ ...CLINICA, activa: false })
      }),
    )
    const user = await abrirPestana('Clínicas y convenios')
    await user.click(await screen.findByRole('button', { name: /clínica norte/i }))
    await user.click(await screen.findByRole('button', { name: 'Desactivar clínica' }))
    await waitFor(() => expect(cambio).toEqual({ activa: false }))
    expect(await screen.findByRole('button', { name: 'Activar clínica' })).toBeInTheDocument()
  })

  it('la administración registra un convenio', async () => {
    let enviado: unknown = null
    server.use(
      http.get(`${API}/aliadas/cl1/convenios`, () => HttpResponse.json([])),
      http.post(`${API}/aliadas/cl1/convenios`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(CONVENIO, { status: 201 })
      }),
    )
    const user = await abrirPestana('Clínicas y convenios')
    await user.click(await screen.findByRole('button', { name: /clínica norte/i }))
    expect(await screen.findByText('Sin convenios.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Nuevo convenio' }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Beneficio'), ' Ecografía ')
    const cobertura = within(modal).getByLabelText('Cobertura (%)')
    await user.clear(cobertura)
    await user.type(cobertura, '70')
    await user.type(within(modal).getByLabelText('Tarifa acordada (COP)'), '90000')
    const desde = within(modal).getByLabelText('Vigente desde')
    await user.clear(desde)
    await user.type(desde, '2026-12-01')
    await user.click(within(modal).getByRole('button', { name: 'Guardar convenio' }))
    await waitFor(() =>
      expect(enviado).toEqual({ beneficio: 'Ecografía', cobertura_pct: 70, tarifa: '90000', vigente_desde: '2026-12-01' }),
    )
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('explica por qué no se pudo guardar el convenio', async () => {
    server.use(
      http.post(`${API}/aliadas/cl1/convenios`, () => HttpResponse.json({ detail: 'Ya hay un convenio vigente' }, { status: 409 })),
    )
    const user = await abrirPestana('Clínicas y convenios')
    await user.click(await screen.findByRole('button', { name: /clínica norte/i }))
    await user.click(await screen.findByRole('button', { name: 'Nuevo convenio' }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Beneficio'), 'Ecografía')
    await user.type(within(modal).getByLabelText('Tarifa acordada (COP)'), '90000')
    await user.type(within(modal).getByLabelText('Tope cubierto (COP, opcional)'), '100000')
    await user.click(within(modal).getByRole('button', { name: 'Guardar convenio' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('Ya hay un convenio vigente')
  })

  it('registra una clínica nueva sin enviar los campos vacíos como texto', async () => {
    let enviado: unknown = null
    server.use(
      http.get(`${API}/aliadas`, () => HttpResponse.json([])),
      http.post(`${API}/aliadas`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json(CLINICA, { status: 201 })
      }),
    )
    const user = await abrirPestana('Clínicas y convenios')
    expect(await screen.findByText('No hay clínicas aliadas registradas.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /nueva clínica/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nombre'), ' Clínica Sur ')
    await user.selectOptions(within(modal).getByLabelText('Ciudad'), 'Bogota')
    await user.type(within(modal).getByLabelText('Teléfono'), '6017654')
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    await waitFor(() =>
      expect(enviado).toEqual({
        nombre: 'Clínica Sur',
        nit: null,
        ciudad: 'Bogota',
        direccion: null,
        telefono: '6017654',
        email: null,
        servicios: null,
      }),
    )
  })

  it('explica por qué no se pudo registrar la clínica', async () => {
    server.use(http.post(`${API}/aliadas`, () => HttpResponse.json({ detail: 'NIT repetido' }, { status: 409 })))
    const user = await abrirPestana('Clínicas y convenios')
    await user.click(await screen.findByRole('button', { name: /nueva clínica/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nombre'), 'Clínica Sur')
    await user.selectOptions(within(modal).getByLabelText('Ciudad'), 'Bogota')
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('NIT repetido')
  })

  it('quien no administra ve solo las clínicas activas y no las gestiona', async () => {
    const pedidas: (string | null)[] = []
    server.use(
      como('operaciones'),
      http.get(`${API}/aliadas`, ({ request }) => {
        pedidas.push(new URL(request.url).searchParams.get('incluir_inactivas'))
        return HttpResponse.json([CLINICA])
      }),
    )
    const user = await abrirPestana('Clínicas y convenios')
    await user.click(await screen.findByRole('button', { name: /clínica norte/i }))
    await screen.findByText('Radiografía')
    expect(screen.queryByRole('button', { name: /nueva clínica/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Nuevo convenio' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Desactivar clínica' })).not.toBeInTheDocument()
    // Remisiones pide también las inactivas para nombrar remisiones antiguas; el listado de
    // clínicas, para quien no administra, solo las activas.
    expect(pedidas.at(-1)).toBeNull()
  })

  it('la administración ve también las inactivas', async () => {
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
})

describe('liquidación', () => {
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
    const desde = screen.getByLabelText('Desde')
    await user.clear(desde)
    await user.type(desde, '2026-09-01')
    const hasta = screen.getByLabelText('Hasta')
    await user.clear(hasta)
    await user.type(hasta, '2026-09-30')
    await waitFor(() => expect(periodos).toContain('2026-09-01..2026-09-30'))
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
    expect(await screen.findByText('No hubo atenciones en aliadas en el período.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /csv/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('No fue posible descargar.')
  })
})
