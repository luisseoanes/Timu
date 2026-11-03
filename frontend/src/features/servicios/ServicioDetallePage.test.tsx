import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { ServicioDetallePage } from './ServicioDetallePage'
import { FAMILIA, TIPOS_SERVICIO, USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { ServicioRead } from '@/types'

const API = '*/api/v1'

const SERVICIO: ServicioRead = {
  id: 's1',
  familia_id: FAMILIA.id,
  mascota_id: FAMILIA.mascotas![0]!.id,
  tipo_codigo: 'consulta_domiciliaria',
  tipo: 'domiciliario',
  estado: 'agendado',
  ciudad: 'Bogota',
  programado_para: '2026-10-26T14:30:00Z',
  termina_en: '2026-10-26T15:15:00Z',
  requiere_autorizacion: false,
  autorizado: false,
  autorizado_en: null,
  profesional_id: null,
  pendiente_origen_id: null,
  observaciones: null,
  motivo_estado: null,
}

function abrir(cambios: Partial<ServicioRead> = {}) {
  server.use(http.get(`${API}/servicios/s1`, () => HttpResponse.json({ ...SERVICIO, ...cambios })))
  renderizar(
    <Routes>
      <Route path="/servicios/:id" element={<ServicioDetallePage />} />
    </Routes>,
    { ruta: '/servicios/s1' },
  )
  return userEvent.setup()
}

const tarjetaPasos = async () => (await screen.findByRole('heading', { name: 'Pasos de la atención' })).closest('section')!

describe('ficha del servicio', () => {
  it('muestra familia, mascota, observaciones y el motivo del último cambio', async () => {
    abrir({ observaciones: 'Perro nervioso', motivo_estado: 'Reprogramado por lluvia' })
    expect(await screen.findByRole('link', { name: 'Ana Ruiz' })).toHaveAttribute('href', `/familias/${FAMILIA.id}`)
    expect(await screen.findByText('Luna')).toBeInTheDocument()
    expect(screen.getByText('Perro nervioso')).toBeInTheDocument()
    expect(screen.getByText('Motivo del último cambio: Reprogramado por lluvia')).toBeInTheDocument()
    expect(screen.getByText('No requiere')).toBeInTheDocument()
  })

  it('un servicio para toda la familia lo dice', async () => {
    abrir({ mascota_id: null })
    expect(await screen.findByText('Toda la familia')).toBeInTheDocument()
  })

  it('un servicio cerrado no ofrece acciones', async () => {
    abrir({ estado: 'completado' })
    expect(await screen.findByText('El servicio ya está cerrado.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Cancelar servicio' })).not.toBeInTheDocument()
  })

  it('avisa si el servicio no existe', async () => {
    server.use(http.get(`${API}/servicios/s1`, () => HttpResponse.json({ detail: 'Servicio no encontrado' }, { status: 404 })))
    renderizar(
      <Routes>
        <Route path="/servicios/:id" element={<ServicioDetallePage />} />
      </Routes>,
      { ruta: '/servicios/s1' },
    )
    expect(await screen.findByRole('alert')).toHaveTextContent('No fue posible cargar el servicio. Servicio no encontrado')
  })
})

describe('autorización', () => {
  it('quien es clínico autoriza un servicio pendiente', async () => {
    let autorizado = false
    server.use(
      http.post(`${API}/servicios/s1/autorizar`, () => {
        autorizado = true
        return HttpResponse.json({ ...SERVICIO, autorizado: true })
      }),
    )
    const user = abrir({ requiere_autorizacion: true })
    expect(await screen.findByText('Pendiente')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Autorizar servicio' }))
    await waitFor(() => expect(autorizado).toBe(true))
  })

  it('explica por qué no se pudo autorizar', async () => {
    server.use(http.post(`${API}/servicios/s1/autorizar`, () => HttpResponse.json({ detail: 'Solo el médico autoriza' }, { status: 403 })))
    const user = abrir({ requiere_autorizacion: true })
    await user.click(await screen.findByRole('button', { name: 'Autorizar servicio' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Solo el médico autoriza')
  })

  it('ya autorizado muestra cuándo, y quien no es clínico no autoriza', async () => {
    server.use(http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'comercial' })))
    abrir({ requiere_autorizacion: true, autorizado: true, autorizado_en: '2026-10-25T10:00:00Z' })
    expect(await screen.findByText(/^Autorizado /)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Autorizar servicio' })).not.toBeInTheDocument()
  })
})

describe('reprogramar', () => {
  it('envía la nueva fecha en hora de Colombia con su motivo', async () => {
    let enviado: unknown = null
    server.use(
      http.post(`${API}/servicios/s1/reprogramar`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ ...SERVICIO, estado: 'reprogramado' })
      }),
    )
    const user = abrir()
    await user.click(await screen.findByRole('button', { name: 'Reprogramar' }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nueva fecha y hora'), '2026-11-02T09:30')
    await user.type(within(modal).getByLabelText('Motivo'), ' Lluvia ')
    await user.click(within(modal).getByRole('button', { name: 'Reprogramar' }))
    await waitFor(() => expect(enviado).toEqual({ inicio: '2026-11-02T09:30:00-05:00', motivo: 'Lluvia' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('explica por qué no se pudo reprogramar o cancelar', async () => {
    server.use(
      http.post(`${API}/servicios/s1/reprogramar`, () => HttpResponse.json({ detail: 'No hay cupo ese día' }, { status: 409 })),
      http.post(`${API}/servicios/s1/estado`, () => HttpResponse.json({ detail: 'Ya salió en ruta' }, { status: 409 })),
    )
    const user = abrir()
    await user.click(await screen.findByRole('button', { name: 'Reprogramar' }))
    let modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nueva fecha y hora'), '2026-11-02T09:30')
    await user.type(within(modal).getByLabelText('Motivo'), 'Lluvia')
    await user.click(within(modal).getByRole('button', { name: 'Reprogramar' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('No hay cupo ese día')
    await user.keyboard('{Escape}')
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: 'Cancelar servicio' }))
    modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Motivo de la cancelación'), 'Viaje')
    await user.click(within(modal).getByRole('button', { name: 'Confirmar cancelación' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('Ya salió en ruta')
  })
})

describe('pasos de la atención', () => {
  it('fuera de la atención solo se leen', async () => {
    abrir()
    const tarjeta = await tarjetaPasos()
    expect(within(tarjeta).getByText('Se registran durante la atención')).toBeInTheDocument()
    expect(within(tarjeta).queryByRole('button', { name: 'Registrar' })).not.toBeInTheDocument()
  })

  it('un paso registrado muestra sus datos y se edita con ellos prellenados', async () => {
    let enviado: unknown = null
    server.use(
      http.get(`${API}/servicios/:id/pasos`, () =>
        HttpResponse.json([{ paso_codigo: 'valoracion', datos: { hallazgos: 'Otitis leve' }, completado_por_id: null, created_at: '' }]),
      ),
      http.put(`${API}/servicios/s1/pasos/valoracion`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ paso_codigo: 'valoracion', datos: {}, completado_por_id: null, created_at: '' })
      }),
    )
    const user = abrir({ estado: 'en_atencion' })
    const tarjeta = await tarjetaPasos()
    expect(await within(tarjeta).findByText('Registrado')).toBeInTheDocument()
    expect(within(tarjeta).getByText('Otitis leve')).toBeInTheDocument()
    await user.click(within(tarjeta).getByRole('button', { name: 'Editar' }))
    const campo = within(tarjeta).getByLabelText('Hallazgos')
    expect(campo).toHaveValue('Otitis leve')
    await user.type(campo, ' bilateral')
    await user.click(within(tarjeta).getByRole('button', { name: 'Guardar paso' }))
    await waitFor(() => expect(enviado).toEqual({ datos: { hallazgos: 'Otitis leve bilateral' } }))
  })

  it('un paso opcional sin campos se marca hecho, y se puede cancelar la edición', async () => {
    server.use(
      http.get(`${API}/catalogos/tipos-servicio`, () =>
        HttpResponse.json([
          { ...TIPOS_SERVICIO[0]!, pasos: [{ codigo: 'foto', nombre: 'Foto de la mascota', obligatorio: false, campos: [] }] },
        ]),
      ),
      http.put(`${API}/servicios/s1/pasos/foto`, () => HttpResponse.json({ detail: 'El servicio ya cerró' }, { status: 409 })),
    )
    const user = abrir({ estado: 'en_atencion' })
    const tarjeta = await tarjetaPasos()
    expect(within(tarjeta).getByText('Opcional')).toBeInTheDocument()
    await user.click(within(tarjeta).getByRole('button', { name: 'Registrar' }))
    expect(within(tarjeta).getByText(/Este paso no pide datos/)).toBeInTheDocument()
    await user.click(within(tarjeta).getByRole('button', { name: 'Guardar paso' }))
    expect(await within(tarjeta).findByRole('alert')).toHaveTextContent('El servicio ya cerró')
    await user.click(within(tarjeta).getByRole('button', { name: 'Cancelar' }))
    expect(within(tarjeta).getByRole('button', { name: 'Registrar' })).toBeInTheDocument()
  })

  it('un tipo sin pasos definidos no muestra la sección', async () => {
    abrir({ tipo_codigo: 'vacunacion' })
    expect(await screen.findByRole('heading', { name: 'Vacunación' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Pasos de la atención' })).not.toBeInTheDocument()
  })
})

describe('pendientes derivados', () => {
  it('lista los pendientes y crea uno que no requiere autorización', async () => {
    let enviado: unknown = null
    server.use(
      http.get(`${API}/pendientes`, () =>
        HttpResponse.json([
          { id: 'p1', servicio_origen_id: 's1', descripcion: 'Control en 15 días', requiere_autorizacion: false, estado: 'autorizado', autorizado_por_id: null, autorizado_en: null, medio_autorizacion: null, resolucion: null },
        ]),
      ),
      http.post(`${API}/servicios/s1/pendientes`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({}, { status: 201 })
      }),
    )
    const user = abrir()
    expect(await screen.findByText('Control en 15 días')).toBeInTheDocument()
    const nuevo = screen.getByLabelText('Nuevo pendiente')
    await user.type(nuevo, ' Examen de sangre ')
    await user.click(screen.getByLabelText('Requiere autorización de la familia'))
    await user.click(screen.getByRole('button', { name: 'Agregar pendiente' }))
    await waitFor(() => expect(enviado).toEqual({ descripcion: 'Examen de sangre', requiere_autorizacion: false }))
    await waitFor(() => expect(nuevo).toHaveValue(''))
  })

  it('sin pendientes lo dice y explica un rechazo al crear', async () => {
    server.use(
      http.post(`${API}/servicios/s1/pendientes`, () => HttpResponse.json({ detail: 'El servicio está cancelado' }, { status: 422 })),
    )
    const user = abrir()
    expect(await screen.findByText('Esta atención no dejó pendientes.')).toBeInTheDocument()
    await user.type(screen.getByLabelText('Nuevo pendiente'), 'Examen de sangre')
    await user.click(screen.getByRole('button', { name: 'Agregar pendiente' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('El servicio está cancelado')
  })
})
