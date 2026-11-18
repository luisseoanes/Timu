import { screen } from '@testing-library/react'
import { Route, Routes, useLocation } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { renderizar } from '@/test/utils'

import { AlPanel } from './AlPanel'
import { MODULOS_DEL_PANEL } from './modulos'

function Ubicacion() {
  const l = useLocation()
  return <p>En {l.pathname + l.search}</p>
}

describe('AlPanel', () => {
  it('lleva una dirección antigua del panel a la nueva, con su búsqueda', async () => {
    renderizar(
      <Routes>
        {MODULOS_DEL_PANEL.map((m) => (
          <Route key={m} path={`${m}/*`} element={<AlPanel />} />
        ))}
        <Route path="panel/*" element={<Ubicacion />} />
      </Routes>,
      { ruta: '/familias/f1?seccion=cartera' },
    )
    expect(await screen.findByText('En /panel/familias/f1?seccion=cartera')).toBeInTheDocument()
  })
})
