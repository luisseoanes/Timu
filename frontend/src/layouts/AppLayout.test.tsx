import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes, useLocation } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { AppLayout } from './AppLayout'
import { USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

function Ubicacion() {
  const l = useLocation()
  return <p>En {l.pathname + l.search}</p>
}

function abrir(ruta = '/') {
  return renderizar(
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="*" element={<Ubicacion />} />
      </Route>
    </Routes>,
    { ruta },
  )
}

const comoMedico = () =>
  server.use(http.get('*/api/v1/auth/me', () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'medico' })))

/** Simula una pantalla estrecha: ningún corte de ancho de AppLayout se cumple. */
function enCelular() {
  vi.stubGlobal('matchMedia', (consulta: string) => ({
    matches: false,
    media: consulta,
    addEventListener: () => {},
    removeEventListener: () => {},
  }))
}

async function abrirMenu(nombre: string | RegExp) {
  const user = userEvent.setup()
  await user.click(await screen.findByRole('button', { name: nombre }))
  return screen.findByRole('menu')
}

const textos = (elementos: HTMLElement[]) => elementos.map((e) => e.textContent?.trim())

afterEach(() => vi.unstubAllGlobals())

describe('AppLayout en escritorio', () => {
  it('pone en la barra los módulos que caben y el resto en «Más»', async () => {
    abrir()
    const nav = await screen.findByRole('navigation', { name: 'Módulos' })
    expect(textos(within(nav).getAllByRole('link'))).toEqual([
      'Panel', 'Familias', 'Cartera', 'Servicios', 'Tareas', 'Preventivos', 'Clínica', 'Rutas',
    ])
    const mas = await abrirMenu('Más')
    expect(textos(within(mas).getAllByRole('menuitem'))).toEqual(['Comercial', 'Campañas', 'Aliadas', 'Administración'])
  })

  it('un médico no ve administración ni el embudo comercial', async () => {
    comoMedico()
    abrir()
    const nav = await screen.findByRole('navigation', { name: 'Módulos' })
    expect(nav).toHaveTextContent('Clínica')
    const mas = await abrirMenu('Más')
    expect(textos(within(mas).getAllByRole('menuitem'))).toEqual(['Campañas', 'Aliadas'])
  })

  it('marca «Más» cuando el módulo abierto está dentro', async () => {
    abrir('/aliadas')
    expect(await screen.findByRole('button', { name: 'Más' })).toHaveAttribute('data-activo', 'true')
  })

  it('la cuenta muestra el nombre y el perfil, y cierra la sesión', async () => {
    let salio = false
    server.use(
      http.post('*/api/v1/auth/logout', () => {
        salio = true
        return new HttpResponse(null, { status: 204 })
      }),
    )
    abrir()
    const menu = await abrirMenu(/^Cuenta de /)
    expect(menu).toHaveTextContent('Administración')
    await userEvent.setup().click(within(menu).getByRole('menuitem', { name: 'Cerrar sesión' }))
    await vi.waitFor(() => expect(salio).toBe(true))
  })

  it('titula la página según el módulo activo', async () => {
    abrir('/rutas')
    expect(await screen.findByRole('heading', { name: 'Rutas' })).toBeInTheDocument()
  })

  it('el buscador de la cabecera lleva a familias con la búsqueda', async () => {
    const user = userEvent.setup()
    abrir()
    await user.type(await screen.findByRole('searchbox', { name: 'Buscar familias' }), 'Ana Ruiz{Enter}')
    expect(await screen.findByText('En /familias?q=Ana%20Ruiz')).toBeInTheDocument()
  })
})

describe('AppLayout en el celular', () => {
  it('lleva al médico sus cuatro módulos en la barra inferior y el resto en «Más»', async () => {
    enCelular()
    comoMedico()
    abrir('/rutas')
    const barra = await screen.findByRole('navigation', { name: 'Módulos principales' })
    // En el orden del menú, no en el de prioridad: la barra no se reordena según el perfil.
    expect(textos(within(barra).getAllByRole('link'))).toEqual(['Familias', 'Servicios', 'Clínica', 'Rutas'])
    expect(within(barra).getByRole('link', { name: 'Rutas' })).toHaveAttribute('aria-current', 'page')
    expect(screen.queryByRole('navigation', { name: 'Módulos' })).not.toBeInTheDocument()
    expect(screen.queryByRole('searchbox')).not.toBeInTheDocument()
    const mas = await abrirMenu('Más')
    expect(textos(within(mas).getAllByRole('menuitem'))).toEqual(['Panel', 'Cartera', 'Tareas', 'Preventivos', 'Campañas', 'Aliadas'])
  })
})
