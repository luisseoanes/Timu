import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Icono } from './Icono'

describe('Icono', () => {
  it('es decorativo por defecto: no lo anuncia el lector de pantalla', () => {
    const { container } = render(<Icono nombre="familias" />)
    const svg = container.querySelector('svg')
    expect(svg).toBeTruthy()
    expect(svg).toHaveAttribute('aria-hidden', 'true')
  })

  it('respeta el tamaño que se le pide', () => {
    const { container } = render(<Icono nombre="cerrar" size={32} />)
    expect(container.querySelector('svg')).toHaveAttribute('width', '32')
  })
})
