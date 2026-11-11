import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { MarcaTimu } from './MarcaTimu'
import color from '@/assets/marca/timu-color.svg'
import compactoBlanco from '@/assets/marca/timu-compacto-blanco.svg'

describe('MarcaTimu', () => {
  it('muestra el logo completo a color con el lema como nombre accesible', () => {
    render(<MarcaTimu />)
    expect(screen.getByRole('img', { name: 'TIMU · Medicina veterinaria prepagada' })).toHaveAttribute('src', color)
  })

  it('en su versión compacta sobre la marca, es el logotipo en blanco sin lema', () => {
    render(<MarcaTimu claro compacta />)
    const logo = screen.getByRole('img', { name: 'TIMU' })
    expect(logo).toHaveAttribute('src', compactoBlanco)
    expect(logo).toHaveClass('marca-compacta')
  })
})
