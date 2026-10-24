import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { PortalLayout } from './PortalLayout'
import { PortalMascota, PortalMascotas } from './PortalPages'
import { FAMILIA, USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const API = '*/api/v1'
const LUNA = FAMILIA.mascotas![0]!

function abrir(ruta: string) {
  return renderizar(
    <Routes>
      <Route path="/portal" element={<PortalLayout />}>
        <Route path="mascotas" element={<PortalMascotas />} />
        <Route path="mascotas/:mascotaId" element={<PortalMascota />} />
      </Route>
    </Routes>,
    { ruta },
  )
}

describe('Portal: navegación y mascotas', () => {
  it('navega entre las secciones del portal', async () => {
    server.use(
      http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'familia' })),
      http.get(`${API}/portal/mi-familia`, () => HttpResponse.json(FAMILIA)),
    )
    const user = userEvent.setup()
    abrir('/portal/mascotas')
    const nav = screen.getByRole('navigation', { name: 'Portal' })
    expect(nav).toHaveTextContent('Citas')
    await user.click(await screen.findByRole('link', { name: /luna/i }))
    expect(await screen.findByRole('heading', { name: 'Luna' })).toBeInTheDocument()
  })

  it('muestra el carnet y la historia de la mascota, y descarga el PDF', async () => {
    server.use(
      http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'familia' })),
      http.get(`${API}/portal/mi-familia`, () => HttpResponse.json(FAMILIA)),
      http.get(`${API}/portal/mascotas/:id/carnet`, () =>
        HttpResponse.json({
          mascota: { id: LUNA.id, nombre: 'Luna', especie: 'Canino', raza: null, fecha_nacimiento: null },
          aplicados: [{ id: 'a1', tipo: 'vacuna', nombre: 'Rabia', dosis: 1, refuerzo: false, fecha_programada: '2026-09-01', fecha_aplicacion: '2026-09-01', producto: null, lote: null, proxima_fecha: null }],
          vencidos: [{ id: 'v1', tipo: 'vacuna', nombre: 'Polivalente', dosis: 2, refuerzo: false, fecha_programada: '2026-10-01', fecha_aplicacion: null, producto: null, lote: null, proxima_fecha: null }],
          proximos: [],
        }),
      ),
      http.post(`${API}/portal/mascotas/:id/carnet/pdf`, () => HttpResponse.json({ codigo: 'K7M2', url: 'https://s3/c.pdf' })),
      http.get(`${API}/portal/mascotas/:id/historia`, () =>
        HttpResponse.json([{ id: 'h1', fecha: '2026-10-04', tipo: 'domiciliaria', motivo: 'Rasca el oído', diagnostico: 'Otitis', tratamiento: 'Gotas', examen_fisico: null, estado: 'firmada' }]),
      ),
    )
    const user = userEvent.setup()
    abrir(`/portal/mascotas/${LUNA.id}`)
    expect(await screen.findByText(/1 preventivo\(s\) vencido\(s\): Polivalente/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /descargar pdf/i }))
    expect(await screen.findByRole('link', { name: 'abrir el carnet' })).toHaveAttribute('href', 'https://s3/c.pdf')
    await user.click(screen.getByRole('tab', { name: 'Historia clínica' }))
    expect(await screen.findByText('Diagnóstico: Otitis')).toBeInTheDocument()
  })
})
