import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it, vi } from 'vitest'

import { GestionarPreventivo } from './AccionesPreventivo'
import { FAMILIA } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { EventoBandeja } from '@/types'

const API = '*/api/v1'

const EVENTO: EventoBandeja = {
  id: 'e1',
  mascota_id: 'm1',
  esquema_codigo: 'can_rabia',
  tipo: 'vacuna',
  tipo_servicio_codigo: 'vacunacion',
  dosis_numero: 1,
  es_refuerzo: true,
  estado: 'programado',
  fecha_programada: '2099-01-10',
  fecha_aplicacion: null,
  proxima_fecha: null,
  producto: null,
  lote: null,
  peso_kg: null,
  aplicado_por_nombre: null,
  requiere_autorizacion: true,
  autorizado: false,
  medio_autorizacion: null,
  autorizado_en: null,
  notificado_en: null,
  servicio_id: null,
  nombre: 'Antirrábica canina',
  mascota_nombre: 'Luna',
  especie: 'canino',
  siguiente: 'autorizar',
  visita: null,
}
const MICHI: EventoBandeja = { ...EVENTO, id: 'e2', mascota_id: 'm2', mascota_nombre: 'Michi', nombre: 'Triple felina' }

/** La bandeja de la familia, que es lo que lee la acción de la estación. */
function conBandeja(eventos: EventoBandeja[], consultas: string[] = []) {
  server.use(
    http.get(`${API}/preventivos/bandeja`, ({ request }) => {
      consultas.push(new URL(request.url).search)
      const items = eventos.length ? [{ familia_id: FAMILIA.id, titular_nombre: FAMILIA.titular_nombre, ciudad: 'Bogotá', telefono: '+573001112233', eventos }] : []
      return HttpResponse.json({ items, total: items.length, limit: 20, offset: 0 })
    }),
  )
}

describe('GestionarPreventivo (desde la estación de la línea de una familia)', () => {
  it('pide de una vez lo que falta autorizar en la estación, con el nombre de cada esquema', async () => {
    let enviado: unknown = null
    const consultas: string[] = []
    conBandeja([EVENTO, MICHI, { ...EVENTO, id: 'e3', nombre: 'Polivalente canina' }], consultas)
    server.use(
      http.post(`${API}/preventivos/autorizaciones`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json([])
      }),
    )
    const cerrar = vi.fn()
    const user = userEvent.setup()
    renderizar(<GestionarPreventivo familiaId={FAMILIA.id} eventoIds={['e1', 'e2']} onCerrar={cerrar} />)
    const ventana = await screen.findByRole('dialog', { name: `Autorización de ${FAMILIA.titular_nombre}` })
    expect(consultas[0]).toContain(`familia_id=${FAMILIA.id}`)
    expect(ventana).toHaveTextContent('Antes de agendar la visita, la familia tiene que autorizarlo')
    // Solo los de la estación, y nombrados por su esquema.
    expect(within(ventana).getByRole('checkbox', { name: /^Luna · Antirrábica canina, refuerzo/ })).toBeChecked()
    expect(within(ventana).getByRole('checkbox', { name: /Michi · Triple felina/ })).toBeChecked()
    expect(within(ventana).queryByRole('checkbox', { name: /Polivalente/ })).not.toBeInTheDocument()
    await user.click(within(ventana).getByRole('button', { name: 'La familia autorizó los 2' }))
    await waitFor(() => expect(enviado).toEqual({ eventos: ['e1', 'e2'], medio: 'whatsapp', aprobado: true }))
    await waitFor(() => expect(cerrar).toHaveBeenCalled())
  })

  it('autorizado, agenda la visita en la ciudad de la familia', async () => {
    // El tipo de servicio de la visita lo dice la API, no un mapa copiado en el panel (DEU-23).
    conBandeja([{ ...EVENTO, autorizado: true, siguiente: 'agendar', tipo_servicio_codigo: 'desparasitacion' }])
    server.use(
      http.get(`${API}/agenda/disponibilidad`, ({ request }) => {
        expect(new URL(request.url).searchParams.get('ciudad')).toBe('Bogotá')
        expect(new URL(request.url).searchParams.get('tipo_codigo')).toBe('desparasitacion')
        return HttpResponse.json([])
      }),
    )
    renderizar(<GestionarPreventivo familiaId={FAMILIA.id} eventoIds={['e1']} onCerrar={() => {}} />)
    const ventana = await screen.findByRole('dialog', { name: 'Agendar Antirrábica canina de Luna' })
    expect(ventana).toHaveTextContent('Toca el')
    expect(await within(ventana).findByText('No hay franjas ese día. Prueba con otro.')).toBeInTheDocument()
    expect(within(ventana).getByRole('button', { name: 'Elige una franja' })).toBeDisabled()
  })

  it('con la visita ya agendada, lleva a ella', async () => {
    conBandeja([{ ...EVENTO, autorizado: true, servicio_id: 's1', siguiente: 'visita' }])
    renderizar(<GestionarPreventivo familiaId={FAMILIA.id} eventoIds={['e1']} onCerrar={() => {}} />)
    expect(await screen.findByRole('link', { name: 'Abrir la visita' })).toHaveAttribute('href', '/panel/servicios/s1')
  })

  it('dice si los preventivos ya no están pendientes', async () => {
    conBandeja([])
    renderizar(<GestionarPreventivo familiaId={FAMILIA.id} eventoIds={['e1', 'e2']} onCerrar={() => {}} />)
    expect(await screen.findByText('Estos preventivos ya no están pendientes: se aplicaron o se cancelaron.')).toBeInTheDocument()
  })

  it('avisa si no puede cargarlos', async () => {
    server.use(http.get(`${API}/preventivos/bandeja`, () => HttpResponse.json({ detail: 'Caído' }, { status: 503 })))
    renderizar(<GestionarPreventivo familiaId={FAMILIA.id} eventoIds={['e1']} onCerrar={() => {}} />)
    expect(await screen.findByRole('alert')).toHaveTextContent('No fue posible cargar los preventivos.')
  })
})
