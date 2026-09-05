import { screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { AppLayout } from './AppLayout'
import { renderizar } from '@/test/utils'

describe('AppLayout', () => {
  it('pinta la navegación de módulos', async () => {
    renderizar(<AppLayout />)
    await waitFor(() => expect(screen.getByRole('navigation')).toBeInTheDocument())
  })

  it('ofrece el enlace a familias', async () => {
    renderizar(<AppLayout />)
    await waitFor(() => expect(screen.getByRole('link', { name: /familias/i })).toBeInTheDocument())
  })
})
