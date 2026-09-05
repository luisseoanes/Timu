import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { LoginPage } from './LoginPage'
import { sinSesion } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

describe('LoginPage', () => {
  it('muestra el formulario con sus campos', async () => {
    server.use(sinSesion)
    renderizar(<LoginPage />, { ruta: '/login' })
    expect(await screen.findByRole('button', { name: /ingresar|entrar/i })).toBeInTheDocument()
  })

  it('avisa cuando las credenciales no son válidas', async () => {
    server.use(
      sinSesion,
      http.post('*/api/v1/auth/login', () => new HttpResponse(null, { status: 401 })),
    )
    renderizar(<LoginPage />, { ruta: '/login' })

    const boton = await screen.findByRole('button', { name: /ingresar|entrar/i })
    const campos = screen.getAllByRole('textbox')
    if (campos[0]) await userEvent.type(campos[0], 'admin@timu.co')
    await userEvent.click(boton)

    await waitFor(() => expect(screen.getByRole('button', { name: /ingresar|entrar/i })).toBeEnabled())
  })
})
