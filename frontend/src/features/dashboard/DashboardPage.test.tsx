import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { DashboardPage } from './DashboardPage'
import { renderizar } from '@/test/utils'

describe('DashboardPage', () => {
  it('se renderiza con sus widgets de operación', () => {
    const { container } = renderizar(<DashboardPage />)
    expect(container.querySelectorAll('.tarjeta').length).toBeGreaterThan(0)
  })

  it('muestra al menos un encabezado', () => {
    renderizar(<DashboardPage />)
    expect(screen.getAllByRole('heading').length).toBeGreaterThan(0)
  })
})
