import { screen } from '@testing-library/react'
import { Route, Routes, useLocation } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { renderizar } from '@/test/utils'

import { DIRECCIONES_VIEJAS } from './modulos'
import { DeLaWebVieja } from './WebVieja'

function Ubicacion() {
  const l = useLocation()
  return <p>En {l.pathname + l.hash}</p>
}

function abrir(ruta: string) {
  renderizar(
    <Routes>
      {DIRECCIONES_VIEJAS.map((d) => (
        <Route key={d} path={d} element={<DeLaWebVieja />} />
      ))}
      <Route path="/" element={<Ubicacion />} />
      <Route path="/planes/:plan" element={<Ubicacion />} />
    </Routes>,
    { ruta },
  )
}

describe('DeLaWebVieja (R3-PUB-04)', () => {
  it.each([
    ['/planes/', 'En /#planes'],
    ['/aliados/', 'En /#aliadas'],
    ['/nosotros/', 'En /#nosotros'],
    ['/contactanos/', 'En /#contacto'],
    ['/service/plan-mi-amigo-fiel/', 'En /planes/mi-amigo-fiel'],
    ['/service/otra-cosa/', 'En /'],
  ])('%s lleva a su sitio nuevo', async (vieja, nueva) => {
    abrir(vieja)
    expect(await screen.findByText(nueva)).toBeInTheDocument()
  })
})
