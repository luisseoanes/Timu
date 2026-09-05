import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Icono } from './Icono'
import { AnilloProgreso } from './AnilloProgreso'

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

describe('AnilloProgreso', () => {
  it('se dibuja con el valor dado', () => {
    const { container } = render(<AnilloProgreso valor={75} />)
    expect(container.querySelector('svg')).toBeTruthy()
  })

  it('tolera los extremos sin romperse', () => {
    for (const valor of [0, 100]) {
      const { container } = render(<AnilloProgreso valor={valor} />)
      expect(container.querySelector('svg')).toBeTruthy()
    }
  })
})
