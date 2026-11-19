import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'

import { AliadasPage } from './AliadasPage'
import { sesionDe } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { ClinicaRead } from '@/types'

// Sección 12: esta pantalla se prueba con el perfil que la usa (docs/perfiles-y-permisos.md).
beforeEach(() => server.use(sesionDe('operaciones')))

const API = '*/api/v1'

const CLINICA: ClinicaRead = {
  id: 'cl1',
  nombre: 'Clínica Norte',
  ciudad: 'Medellín',
  activa: true,
  tipo: 'clinica',
  tipo_nombre: 'Clínica veterinaria',
  en_portada: false,
  atiende_24h: false,
  orden_portada: 0,
}

const EN_PORTADA: ClinicaRead = {
  ...CLINICA,
  en_portada: true,
  atiende_24h: true,
  barrio: 'Laureles',
  horario: 'Lunes a domingo, las 24 horas',
  orden_portada: 3,
  logo_url: 'https://almacen.local/logo.png',
}

beforeEach(() =>
  server.use(
    http.get(`${API}/aliadas/remisiones/recuentos`, () => HttpResponse.json({ emitida: 0, utilizada: 0, anulada: 0, todas: 0 })),
    http.get(`${API}/aliadas/remisiones`, () => HttpResponse.json([])),
    http.get(`${API}/aliadas/:id/convenios`, () => HttpResponse.json([])),
  ),
)

async function abrirClinica() {
  const user = userEvent.setup()
  renderizar(<AliadasPage />, { ruta: '/panel/aliadas?clinica=cl1' })
  await user.click(await screen.findByRole('tab', { name: 'Clínicas y convenios' }))
  const ficha = await screen.findByRole('region', { name: 'Clínica abierta' })
  await within(ficha).findByRole('heading', { level: 2, name: 'Clínica Norte' })
  const bloque = within(ficha).getByRole('region', { name: 'En la portada' })
  return { user, bloque }
}

describe('Aliadas: cómo sale una clínica en la portada', () => {
  it('dice que no sale cuando no está en la portada', async () => {
    server.use(http.get(`${API}/aliadas`, () => HttpResponse.json([CLINICA])))
    const { bloque } = await abrirClinica()
    expect(within(bloque).getByText(/^No sale en la portada/)).toBeInTheDocument()
  })

  it('muestra lo que dice de ella la portada, con su logo', async () => {
    server.use(http.get(`${API}/aliadas`, () => HttpResponse.json([EN_PORTADA])))
    const { bloque } = await abrirClinica()
    expect(within(bloque).getByRole('img', { name: 'Logo de Clínica Norte' })).toHaveAttribute('src', EN_PORTADA.logo_url)
    expect(within(bloque).getByText('Clínica veterinaria')).toBeInTheDocument()
    expect(within(bloque).getByText('24 horas')).toBeInTheDocument()
    expect(within(bloque).getByText('Laureles')).toBeInTheDocument()
    expect(within(bloque).getByText(/^Sin escribir: la portada solo dice su nombre/)).toBeInTheDocument()
  })

  it('guarda lo que dice la portada y sube el logo elegido', async () => {
    const cambios: unknown[] = []
    let logo = ''
    server.use(
      http.get(`${API}/aliadas`, () => HttpResponse.json([CLINICA])),
      http.patch(`${API}/aliadas/cl1`, async ({ request }) => {
        cambios.push(await request.json())
        return HttpResponse.json(EN_PORTADA)
      }),
      http.put(`${API}/aliadas/cl1/logo`, async ({ request }) => {
        // jsdom no deja leer el multipart con formData() ni manda el contenido: se mira el campo.
        logo = await request.text()
        return HttpResponse.json(EN_PORTADA)
      }),
    )
    const { user, bloque } = await abrirClinica()
    await user.click(within(bloque).getByRole('button', { name: 'Editar cómo sale en la portada' }))
    const modal = await screen.findByRole('dialog', { name: 'Clínica Norte en la portada' })
    await user.click(within(modal).getByLabelText('Mostrarla en la portada'))
    await user.selectOptions(within(modal).getByLabelText('Qué es'), 'especialista')
    await user.click(within(modal).getByLabelText('Atiende las 24 horas'))
    await user.type(within(modal).getByLabelText('Barrio'), 'Laureles')
    await user.clear(within(modal).getByLabelText('Lugar en la red'))
    await user.type(within(modal).getByLabelText('Lugar en la red'), '3')
    await user.upload(within(modal).getByLabelText('Logo (JPG, PNG o WEBP de hasta 2 MB)'), new File(['png-del-logo'], 'logo.png', { type: 'image/png' }))
    expect(within(modal).getByText('logo.png: se sube al guardar.')).toBeInTheDocument()
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    await waitFor(() => expect(logo).toContain('name="logo"'))
    expect(cambios).toEqual([
      { en_portada: true, tipo: 'especialista', atiende_24h: true, barrio: 'Laureles', horario: null, presentacion: null, orden_portada: 3 },
    ])
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('quita el logo', async () => {
    let quitado = false
    server.use(
      http.get(`${API}/aliadas`, () => HttpResponse.json([EN_PORTADA])),
      http.delete(`${API}/aliadas/cl1/logo`, () => {
        quitado = true
        return HttpResponse.json({ ...EN_PORTADA, logo_url: null })
      }),
    )
    const { user, bloque } = await abrirClinica()
    await user.click(within(bloque).getByRole('button', { name: 'Editar cómo sale en la portada' }))
    const modal = await screen.findByRole('dialog')
    await user.click(within(modal).getByRole('button', { name: 'Quitar logo' }))
    await waitFor(() => expect(quitado).toBe(true))
  })

  it('dice el error de la API sin cerrar la ventana', async () => {
    server.use(
      http.get(`${API}/aliadas`, () => HttpResponse.json([CLINICA])),
      http.patch(`${API}/aliadas/cl1`, () => HttpResponse.json({ detail: 'La ciudad no existe' }, { status: 422 })),
    )
    const { user, bloque } = await abrirClinica()
    await user.click(within(bloque).getByRole('button', { name: 'Editar cómo sale en la portada' }))
    const modal = await screen.findByRole('dialog')
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('La ciudad no existe')
  })

  it('quien no lleva la red de aliadas no ve sus clínicas: Atención solo emite remisiones', async () => {
    server.use(sesionDe('atencion_cliente'))
    renderizar(<AliadasPage />, { ruta: '/panel/aliadas?clinica=cl1' })
    expect(await screen.findByRole('tab', { name: 'Remisiones' })).toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: 'Clínicas y convenios' })).not.toBeInTheDocument()
  })
})
