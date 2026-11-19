import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { ClinicaPage } from './ClinicaPage'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { PlantillaConsultaRead } from '@/types'

const API = '*/api/v1'

const OTITIS: PlantillaConsultaRead = {
  codigo: 'otitis_externa',
  nombre: 'Otitis externa',
  tipo_servicio_codigo: null,
  campos: { motivo: 'Rasca el oído', diagnostico: 'Otitis externa', tratamiento: 'Limpieza ótica cada 12 h' },
  activa: true,
}
const CONTROL: PlantillaConsultaRead = {
  codigo: 'control_general',
  nombre: 'Control general',
  tipo_servicio_codigo: null,
  campos: {},
  activa: true,
}
const COMPLETA: PlantillaConsultaRead = {
  ...CONTROL,
  codigo: 'gastroenteritis_leve',
  nombre: 'Gastroenteritis leve',
  campos: { motivo: 'Vómito', anamnesis: 'Desde ayer', examen_fisico: 'Alerta', diagnostico: 'Gastroenteritis', tratamiento: 'Dieta blanda' },
}
// La API las da con las inactivas al final.
const RETIRADA: PlantillaConsultaRead = { ...OTITIS, codigo: 'vacunacion', nombre: 'Vacunación anual', activa: false }

/** El listado de la pestaña: la API, con las inactivas incluidas. */
function conPlantillas(plantillas: PlantillaConsultaRead[], pedidas: URLSearchParams[] = []) {
  server.use(
    http.get(`${API}/clinica/plantillas`, ({ request }) => {
      pedidas.push(new URL(request.url).searchParams)
      return HttpResponse.json(plantillas)
    }),
  )
}

async function abrir(ruta = '/panel/clinica') {
  const user = userEvent.setup()
  renderizar(<ClinicaPage />, { ruta })
  if (!ruta.includes('plantilla=')) await user.click(await screen.findByRole('tab', { name: 'Plantillas de consulta' }))
  return user
}

describe('plantillas de consulta', () => {
  it('lista las plantillas con lo que prellenan en palabras, las inactivas al final', async () => {
    const pedidas: URLSearchParams[] = []
    conPlantillas([OTITIS, CONTROL, COMPLETA, RETIRADA], pedidas)
    await abrir()
    const lista = await screen.findByRole('list', { name: 'Plantillas de consulta' })
    const filas = within(lista).getAllByRole('listitem')
    expect(filas.map((f) => within(f).getByRole('link').textContent)).toEqual([
      'Otitis externa',
      'Control general',
      'Gastroenteritis leve',
      'Vacunación anual',
    ])
    expect(filas[0]).toHaveTextContent('Prellena el motivo de consulta, el diagnóstico y el tratamiento')
    expect(filas[1]).toHaveTextContent('No prellena ningún apartado')
    expect(filas[2]).toHaveTextContent('Prellena los cinco apartados')
    expect(within(filas[3]!).getByText('Inactiva')).toBeInTheDocument()
    // El total, con las inactivas, como en el resto de listados.
    expect(screen.getByRole('heading', { name: /Plantillas/ })).toHaveTextContent('Plantillas 4')
    expect(pedidas.some((p) => p.get('incluir_inactivas') === 'true')).toBe(true)
    // Sin una abierta, el verde es crear.
    expect(screen.getByRole('button', { name: /Nueva plantilla/ })).toHaveClass('btn-primario')
  })

  it('dice qué hacer cuando no hay ninguna', async () => {
    conPlantillas([])
    await abrir()
    expect(await screen.findByText(/Aún no hay plantillas. Crea la primera/)).toBeInTheDocument()
  })

  it('avisa si no pudo cargarlas', async () => {
    server.use(http.get(`${API}/clinica/plantillas`, () => HttpResponse.json({ detail: 'x' }, { status: 400 })))
    await abrir()
    expect(await screen.findByRole('alert')).toHaveTextContent(/No fue posible cargar las plantillas/)
  })

  it('abre la plantilla de la URL en su pestaña y la lee por apartado', async () => {
    conPlantillas([OTITIS, CONTROL])
    await abrir('/panel/clinica?plantilla=otitis_externa')
    const ficha = await screen.findByRole('region', { name: 'Plantilla abierta' })
    expect(await within(ficha).findByRole('heading', { name: 'Otitis externa' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Plantillas de consulta' })).toHaveAttribute('aria-selected', 'true')
    expect(within(ficha).getByText('Activa')).toBeInTheDocument()
    expect(within(ficha).getByText('Prellena 3 de 5 apartados')).toBeInTheDocument()
    expect(within(ficha).getByText('Limpieza ótica cada 12 h')).toBeInTheDocument()
    expect(within(ficha).getByText('Deja en blanco la anamnesis y el examen físico.')).toBeInTheDocument()
    // Con la ficha abierta, el verde es de ella.
    expect(screen.getByRole('button', { name: /Nueva plantilla/ })).toHaveClass('btn-suave')
    expect(within(ficha).getByRole('button', { name: 'Editar plantilla' })).toHaveClass('btn-primario')
  })

  it('al cerrar la ficha vuelve al listado sin salir de la pestaña', async () => {
    conPlantillas([OTITIS, CONTROL])
    const user = await abrir('/panel/clinica?plantilla=otitis_externa')
    const ficha = await screen.findByRole('region', { name: 'Plantilla abierta' })
    await user.click(await within(ficha).findByRole('link', { name: 'Volver a las plantillas' }))
    expect(await screen.findByText(/Abre una plantilla para leer/)).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Plantillas de consulta' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('list', { name: 'Plantillas de consulta' })).toBeInTheDocument()
    // Y se puede ir a otra pestaña aunque se acabe de cerrar una ficha.
    server.use(http.get(`${API}/clinica/respuestas-virtuales`, () => HttpResponse.json([])))
    await user.click(screen.getByRole('tab', { name: 'Respuestas aprobadas' }))
    expect(screen.getByRole('tab', { name: 'Respuestas aprobadas' })).toHaveAttribute('aria-selected', 'true')
  })

  it('dice cuánto se ha usado y para qué atención es', async () => {
    conPlantillas([{ ...OTITIS, tipo_servicio_codigo: 'consulta_domiciliaria' }, CONTROL, COMPLETA])
    server.use(
      http.get(`${API}/clinica/plantillas/uso`, () => HttpResponse.json({ otitis_externa: 12, gastroenteritis_leve: 1 })),
    )
    const user = await abrir('/panel/clinica?plantilla=otitis_externa')
    expect(await screen.findByText('Usada en 12 consultas firmadas')).toBeInTheDocument()
    expect(await screen.findByText('Para consulta domiciliaria')).toBeInTheDocument()
    await user.click(screen.getByRole('link', { name: 'Gastroenteritis leve' }))
    expect(await screen.findByText('Usada en 1 consulta firmada')).toBeInTheDocument()
    await user.click(screen.getByRole('link', { name: 'Control general' }))
    expect(await screen.findByText('Aún sin consultas firmadas')).toBeInTheDocument()
  })

  it('conserva un tipo de atención que el catálogo ya no ofrece', async () => {
    let cambios: unknown = null
    conPlantillas([{ ...OTITIS, tipo_servicio_codigo: 'retirado' }])
    server.use(
      http.patch(`${API}/clinica/plantillas/otitis_externa`, async ({ request }) => {
        cambios = await request.json()
        return HttpResponse.json(OTITIS)
      }),
    )
    const user = await abrir('/panel/clinica?plantilla=otitis_externa')
    await user.click(await screen.findByRole('button', { name: 'Editar plantilla' }))
    const modal = await screen.findByRole('dialog')
    expect(within(modal).getByLabelText('Tipo de atención')).toHaveValue('retirado')
    await user.click(within(modal).getByRole('button', { name: 'Guardar plantilla' }))
    await waitFor(() => expect(cambios).toMatchObject({ tipo_servicio_codigo: 'retirado' }))
  })

  it('dice cuando la plantilla abierta ya no existe y cuando no prellena nada', async () => {
    conPlantillas([CONTROL])
    await abrir('/panel/clinica?plantilla=no_existe')
    expect(await screen.findByText('Esta plantilla ya no existe.')).toBeInTheDocument()
    await userEvent.setup().click(screen.getByRole('link', { name: 'Control general' }))
    expect(await screen.findByText(/No prellena ningún apartado: edítala/)).toBeInTheDocument()
  })

  it('crea una plantilla sin pedir el código y abre su ficha', async () => {
    let enviado: unknown = null
    const plantillas = [CONTROL]
    conPlantillas(plantillas)
    server.use(
      http.post(`${API}/clinica/plantillas`, async ({ request }) => {
        enviado = await request.json()
        plantillas.push(OTITIS)
        return HttpResponse.json(OTITIS, { status: 201 })
      }),
    )
    const user = await abrir()
    await user.click(await screen.findByRole('button', { name: /Nueva plantilla/ }))
    const modal = await screen.findByRole('dialog')
    expect(within(modal).queryByLabelText(/Código/)).not.toBeInTheDocument()
    expect(within(modal).queryByLabelText(/Notas internas/)).not.toBeInTheDocument()
    // Pegado, no tecleado: lo que se prueba es lo que se envía, no cada pulsación.
    await user.click(within(modal).getByLabelText('Nombre'))
    await user.paste('Otitis externa')
    await user.click(within(modal).getByLabelText('Diagnóstico'))
    await user.paste(' Otitis externa ')
    await user.click(within(modal).getByRole('button', { name: 'Guardar plantilla' }))
    await waitFor(() =>
      expect(enviado).toEqual({ nombre: 'Otitis externa', tipo_servicio_codigo: null, campos: { diagnostico: 'Otitis externa' } }),
    )
    // Por su título: la ficha vacía y la abierta comparten el nombre de la región.
    expect(await screen.findByRole('heading', { name: 'Otitis externa' }, { timeout: 4000 })).toBeInTheDocument()
  })

  it('edita el texto de la plantilla desde la ventana con lo que ya dice', async () => {
    let cambios: unknown = null
    conPlantillas([OTITIS])
    server.use(
      http.patch(`${API}/clinica/plantillas/otitis_externa`, async ({ request }) => {
        cambios = await request.json()
        return HttpResponse.json(OTITIS)
      }),
    )
    const user = await abrir('/panel/clinica?plantilla=otitis_externa')
    await user.click(await screen.findByRole('button', { name: 'Editar plantilla' }))
    const modal = await screen.findByRole('dialog', { name: 'Editar plantilla' })
    expect(within(modal).getByLabelText('Nombre')).toHaveValue('Otitis externa')
    expect(within(modal).getByLabelText('Motivo de consulta')).toHaveValue('Rasca el oído')
    // La ayuda dice lo que significa lo elegido.
    expect(within(modal).getByLabelText('Tipo de atención')).toHaveAccessibleDescription('Se ofrece en cualquier visita.')
    await user.selectOptions(within(modal).getByLabelText('Tipo de atención'), await within(modal).findByRole('option', { name: 'Consulta domiciliaria' }))
    expect(within(modal).getByLabelText('Tipo de atención')).toHaveAccessibleDescription('En una visita solo se ofrece si es de este tipo.')
    // Vaciar un apartado deja de prellenarlo.
    await user.clear(within(modal).getByLabelText('Diagnóstico'))
    await user.type(within(modal).getByLabelText('Anamnesis'), 'Desde hace tres días')
    await user.click(within(modal).getByRole('button', { name: 'Guardar plantilla' }))
    await waitFor(() =>
      expect(cambios).toEqual({
        nombre: 'Otitis externa',
        tipo_servicio_codigo: 'consulta_domiciliaria',
        campos: { motivo: 'Rasca el oído', anamnesis: 'Desde hace tres días', tratamiento: 'Limpieza ótica cada 12 h' },
      }),
    )
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('explica por qué no se pudo guardar', async () => {
    conPlantillas([OTITIS])
    server.use(
      http.patch(`${API}/clinica/plantillas/otitis_externa`, () =>
        HttpResponse.json({ detail: 'Ya hay una plantilla que se llama «Control general»' }, { status: 409 }),
      ),
    )
    const user = await abrir('/panel/clinica?plantilla=otitis_externa')
    await user.click(await screen.findByRole('button', { name: 'Editar plantilla' }))
    const modal = await screen.findByRole('dialog')
    await user.click(within(modal).getByRole('button', { name: 'Guardar plantilla' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('Ya hay una plantilla que se llama «Control general»')
  })

  it('desactiva y vuelve a activar sin borrar, y dice qué deja de pasar', async () => {
    const cambios: unknown[] = []
    conPlantillas([RETIRADA])
    server.use(
      http.patch(`${API}/clinica/plantillas/vacunacion`, async ({ request }) => {
        cambios.push(await request.json())
        return HttpResponse.json({ ...RETIRADA, activa: true })
      }),
    )
    const user = await abrir('/panel/clinica?plantilla=vacunacion')
    const ficha = await screen.findByRole('region', { name: 'Plantilla abierta' })
    expect(await within(ficha).findByText(/Inactiva: la consulta ya no la ofrece/)).toBeInTheDocument()
    await user.click(within(ficha).getByRole('button', { name: 'Más acciones con Vacunación anual' }))
    await user.click(await screen.findByRole('menuitem', { name: 'Activar plantilla' }))
    await waitFor(() => expect(cambios).toEqual([{ activa: true }]))
  })

  it('ofrece desactivar una plantilla activa', async () => {
    const cambios: unknown[] = []
    conPlantillas([OTITIS])
    server.use(
      http.patch(`${API}/clinica/plantillas/otitis_externa`, async ({ request }) => {
        cambios.push(await request.json())
        return HttpResponse.json({ detail: 'No se pudo' }, { status: 400 })
      }),
    )
    const user = await abrir('/panel/clinica?plantilla=otitis_externa')
    const ficha = await screen.findByRole('region', { name: 'Plantilla abierta' })
    await user.click(await within(ficha).findByRole('button', { name: 'Más acciones con Otitis externa' }))
    await user.click(await screen.findByRole('menuitem', { name: 'Desactivar plantilla' }))
    await waitFor(() => expect(cambios).toEqual([{ activa: false }]))
    expect(await within(ficha).findByRole('alert')).toHaveTextContent('No se pudo')
  })
})
