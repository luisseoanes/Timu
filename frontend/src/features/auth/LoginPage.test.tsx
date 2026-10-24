import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { LoginPage } from './LoginPage'
import { RecuperarPage, RestablecerPage } from './RecuperarPage'
import { USUARIO_ADMIN, sinSesion } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const API = '*/api/v1'

function abrirLogin() {
  return renderizar(
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<p>Panel del equipo</p>} />
      <Route path="/portal" element={<p>Portal de la familia</p>} />
    </Routes>,
    { ruta: '/login' },
  )
}

describe('LoginPage', () => {
  it('muestra el ingreso del equipo con sus campos etiquetados', async () => {
    server.use(sinSesion)
    abrirLogin()
    expect(await screen.findByRole('heading', { name: 'Bienvenido de nuevo' })).toBeInTheDocument()
    expect(screen.getByLabelText('Correo')).toBeInTheDocument()
    expect(screen.getByLabelText('Contraseña')).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /familias/i })).toBeInTheDocument()
  })

  it('ingresa con correo y contraseña y lleva al panel', async () => {
    let cuerpo = ''
    server.use(
      sinSesion,
      http.post(`${API}/auth/login`, async ({ request }) => {
        cuerpo = await request.text()
        return HttpResponse.json({ usuario: USUARIO_ADMIN })
      }),
    )
    const user = userEvent.setup()
    abrirLogin()
    await user.type(await screen.findByLabelText('Correo'), 'admin@timu.co')
    await user.type(screen.getByLabelText('Contraseña'), 'cambiar123')
    await user.click(screen.getByRole('button', { name: 'Ingresar' }))
    expect(await screen.findByText('Panel del equipo')).toBeInTheDocument()
    expect(cuerpo).toBe('username=admin%40timu.co&password=cambiar123')
  })

  it('avisa cuando las credenciales no son válidas', async () => {
    server.use(sinSesion, http.post(`${API}/auth/login`, () => new HttpResponse(null, { status: 401 })))
    const user = userEvent.setup()
    abrirLogin()
    await user.type(await screen.findByLabelText('Correo'), 'admin@timu.co')
    await user.type(screen.getByLabelText('Contraseña'), 'mala')
    await user.click(screen.getByRole('button', { name: 'Ingresar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('no coinciden')
  })

  it('muestra la causa del servidor cuando no es un problema de credenciales', async () => {
    server.use(
      sinSesion,
      http.post(`${API}/auth/login`, () =>
        HttpResponse.json({ detail: 'Demasiados intentos, espera un minuto' }, { status: 429 }),
      ),
    )
    const user = userEvent.setup()
    abrirLogin()
    await user.type(await screen.findByLabelText('Correo'), 'admin@timu.co')
    await user.type(screen.getByLabelText('Contraseña'), 'x')
    await user.click(screen.getByRole('button', { name: 'Ingresar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Demasiados intentos')
  })

  it('deja ver la contraseña escrita', async () => {
    server.use(sinSesion)
    const user = userEvent.setup()
    abrirLogin()
    const campo = await screen.findByLabelText('Contraseña')
    expect(campo).toHaveAttribute('type', 'password')
    await user.click(screen.getByRole('button', { name: 'Mostrar contraseña' }))
    expect(campo).toHaveAttribute('type', 'text')
  })

  it('una familia entra al portal con el código que recibe por WhatsApp', async () => {
    const pedidos: unknown[] = []
    server.use(
      sinSesion,
      http.post(`${API}/auth/codigo`, async ({ request }) => {
        pedidos.push(await request.json())
        return HttpResponse.json({ detail: 'Enviado' })
      }),
      http.post(`${API}/auth/codigo/verificacion`, async ({ request }) => {
        pedidos.push(await request.json())
        return HttpResponse.json({ usuario: { ...USUARIO_ADMIN, rol: 'familia' } })
      }),
    )
    const user = userEvent.setup()
    abrirLogin()
    await user.click(await screen.findByRole('tab', { name: /familias/i }))
    await user.type(screen.getByLabelText('Celular registrado'), '3001112233')
    await user.click(screen.getByRole('button', { name: 'Recibir código' }))
    await user.type(await screen.findByLabelText('Código'), '123456')
    await user.click(screen.getByRole('button', { name: 'Entrar al portal' }))
    expect(await screen.findByText('Portal de la familia')).toBeInTheDocument()
    expect(pedidos).toEqual([{ telefono: '3001112233' }, { telefono: '3001112233', codigo: '123456' }])
  })

  it('avisa si el código no es válido', async () => {
    server.use(
      sinSesion,
      http.post(`${API}/auth/codigo`, () => HttpResponse.json({ detail: 'Enviado' })),
      http.post(`${API}/auth/codigo/verificacion`, () =>
        HttpResponse.json({ detail: 'Codigo invalido o vencido' }, { status: 400 }),
      ),
    )
    const user = userEvent.setup()
    abrirLogin()
    await user.click(await screen.findByRole('tab', { name: /familias/i }))
    await user.type(screen.getByLabelText('Celular registrado'), '3001112233')
    await user.click(screen.getByRole('button', { name: 'Recibir código' }))
    await user.type(await screen.findByLabelText('Código'), '000000')
    await user.click(screen.getByRole('button', { name: 'Entrar al portal' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Codigo invalido')
    await user.click(screen.getByRole('button', { name: 'Cambiar número' }))
    expect(screen.getByLabelText('Celular registrado')).toBeInTheDocument()
  })

  it('quien ya tiene sesión no ve el ingreso', async () => {
    abrirLogin()
    expect(await screen.findByText('Panel del equipo')).toBeInTheDocument()
  })
})

describe('Recuperación de contraseña', () => {
  it('pide el enlace y confirma sin revelar si la cuenta existe', async () => {
    let enviado: unknown = null
    server.use(
      sinSesion,
      http.post(`${API}/auth/recuperar`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ detail: 'ok' })
      }),
    )
    const user = userEvent.setup()
    renderizar(<RecuperarPage />, { ruta: '/recuperar' })
    await user.type(await screen.findByLabelText('Correo o celular'), 'ana@example.com')
    await user.click(screen.getByRole('button', { name: 'Enviar enlace' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Si hay una cuenta')
    expect(enviado).toEqual({ identificador: 'ana@example.com' })
  })

  it('define la contraseña nueva con el token del enlace', async () => {
    let enviado: unknown = null
    server.use(
      sinSesion,
      http.post(`${API}/auth/restablecer`, async ({ request }) => {
        enviado = await request.json()
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<RestablecerPage modo="activar" />, { ruta: '/activar?token=abc' })
    expect(await screen.findByRole('heading', { name: 'Activa tu cuenta' })).toBeInTheDocument()
    await user.type(screen.getByLabelText('Contraseña nueva'), 'segura1234')
    await user.type(screen.getByLabelText('Confirma la contraseña'), 'segura1234')
    await user.click(screen.getByRole('button', { name: 'Activar cuenta' }))
    expect(await screen.findByRole('status')).toHaveTextContent('quedó guardada')
    expect(enviado).toEqual({ token: 'abc', password: 'segura1234' })
  })

  it('no deja enviar si las contraseñas no coinciden ni sin token', async () => {
    server.use(sinSesion)
    const user = userEvent.setup()
    renderizar(<RestablecerPage modo="restablecer" />, { ruta: '/restablecer' })
    expect(await screen.findByRole('alert')).toHaveTextContent('enlace está incompleto')
    await user.type(screen.getByLabelText('Contraseña nueva'), 'segura1234')
    await user.type(screen.getByLabelText('Confirma la contraseña'), 'otra')
    expect(screen.getByText('Las contraseñas no coinciden.')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Guardar contraseña' })).toBeDisabled())
  })
})
