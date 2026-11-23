import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { AdminPage } from './AdminPage'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { DatosTimuRead } from '@/types'

const API = '*/api/v1'

const base = [
  http.get(`${API}/auth/usuarios/recuentos`, () => HttpResponse.json({ equipo: 0, aliadas: 0, familias: 0, inactivos: 0 })),
  http.get(`${API}/auth/usuarios`, () => HttpResponse.json({ items: [], total: 0, limit: 25, offset: 0 })),
]

const DATOS: DatosTimuRead = {
  id: 'd1',
  razon_social: 'TIMU S.A.S.',
  nit: '901635168-2',
  presentacion: 'Integramos profesionales de salud para perros y gatos.',
  mision: null,
  vision: 'En 2027 estaremos a nivel nacional.',
  valores: ['Confianza', 'Empatía'],
  clinica_nombre: 'TIMU clínica veterinaria',
  clinica_direccion: 'Calle 35 # 66a 51',
  clinica_barrio: 'Laureles',
  clinica_ciudad: 'Medellín',
  clinica_horario: 'Lunes a viernes de 9:00 a. m. a 6:00 p. m.',
  horario_atencion: null,
  telefonos: ['+573016244775'],
  whatsapp: '+573000000000',
  correo: 'administracion@timu.com.co',
  redes: [{ nombre: 'Instagram', url: 'https://www.instagram.com/timu/' }],
  politica_datos_url: null,
}

async function abrir(datos: DatosTimuRead = DATOS) {
  server.use(...base, http.get(`${API}/institucional`, () => HttpResponse.json(datos)))
  const user = userEvent.setup()
  renderizar(<AdminPage />, { ruta: '/panel/admin' })
  await user.click(await screen.findByRole('link', { name: 'Datos de TIMU' }))
  const ficha = (await screen.findByRole('heading', { name: 'Lo que dice la portada de TIMU' })).closest('section')!
  return { user, ficha }
}

describe('Administración: datos de TIMU', () => {
  it('muestra lo que dice la portada y lo que falta escribir', async () => {
    const { ficha } = await abrir()
    expect(within(ficha).getByText('Confianza · Empatía')).toBeInTheDocument()
    expect(within(ficha).getByText('Calle 35 # 66a 51, Laureles, Medellín')).toBeInTheDocument()
    expect(within(ficha).getByRole('link', { name: 'Instagram' })).toHaveAttribute('href', 'https://www.instagram.com/timu/')
    const mision = within(ficha).getByText('Misión').closest('div')!
    expect(mision).toHaveTextContent('Sin escribir: la portada no la muestra.')
    expect(within(ficha).getByText(/^Sin enlace: el formulario de contacto/)).toBeInTheDocument()
  })

  it('guarda lo escrito, con los valores y teléfonos uno por línea y las redes', async () => {
    const guardados: unknown[] = []
    server.use(
      http.put(`${API}/institucional`, async ({ request }) => {
        guardados.push(await request.json())
        return HttpResponse.json(DATOS)
      }),
    )
    const { user, ficha } = await abrir()
    await user.click(within(ficha).getByRole('button', { name: 'Editar' }))
    const modal = await screen.findByRole('dialog', { name: 'Editar los datos de TIMU' })
    await user.type(within(modal).getByLabelText('Misión'), 'Cuidar a cada peludo.')
    await user.type(within(modal).getByLabelText('Valores'), '\nServicio')
    await user.clear(within(modal).getByLabelText('Presentación'))
    await user.click(within(modal).getByRole('button', { name: 'Quitar la red 1' }))
    await user.click(within(modal).getByRole('button', { name: 'Otra red' }))
    await user.type(within(modal).getByLabelText('Nombre de la red 1'), 'Facebook')
    await user.type(within(modal).getByLabelText('Enlace de la red 1'), 'www.facebook.com/timu')
    await user.type(within(modal).getByLabelText('Enlace a la política de tratamiento de datos'), 'https://timu.com.co/datos')
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    await waitFor(() => expect(guardados).toHaveLength(1))
    expect(guardados[0]).toMatchObject({
      presentacion: null,
      mision: 'Cuidar a cada peludo.',
      valores: ['Confianza', 'Empatía', 'Servicio'],
      telefonos: ['+573016244775'],
      clinica_ciudad: 'Medellín',
      redes: [{ nombre: 'Facebook', url: 'https://www.facebook.com/timu' }],
      politica_datos_url: 'https://timu.com.co/datos',
      nit: '901635168-2',
    })
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('dice el error de la API sin cerrar la ventana', async () => {
    server.use(http.put(`${API}/institucional`, () => HttpResponse.json({ detail: 'Telefono no valido' }, { status: 422 })))
    const { user, ficha } = await abrir()
    await user.click(within(ficha).getByRole('button', { name: 'Editar' }))
    const modal = await screen.findByRole('dialog')
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('Telefono no valido')
  })

  it('dice si no pudo consultarlos', async () => {
    server.use(...base, http.get(`${API}/institucional`, () => HttpResponse.json({ detail: 'caído' }, { status: 500 })))
    const user = userEvent.setup()
    renderizar(<AdminPage />, { ruta: '/panel/admin' })
    await user.click(await screen.findByRole('link', { name: 'Datos de TIMU' }))
    expect(await screen.findByText(/No fue posible consultar los datos de TIMU/)).toBeInTheDocument()
  })
})
