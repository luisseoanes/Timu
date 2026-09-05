import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Placeholder } from './Placeholder'
import { renderizar } from '@/test/utils'

describe('Placeholder', () => {
  it('muestra título, detalle y ticket del backlog', () => {
    renderizar(<Placeholder titulo="Cartera" detalle="Mora y congelamiento." ticket="F1-CAR" />)
    expect(screen.getByRole('heading', { name: 'Cartera' })).toBeInTheDocument()
    expect(screen.getByText('Mora y congelamiento.')).toBeInTheDocument()
    expect(screen.getByText('F1-CAR')).toBeInTheDocument()
  })

  it('omite el distintivo cuando no hay ticket', () => {
    renderizar(<Placeholder titulo="Rutas" detalle="Optimización." />)
    expect(screen.queryByText(/^F\d/)).not.toBeInTheDocument()
  })
})
