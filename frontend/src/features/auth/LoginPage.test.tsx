import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes, type InitialEntry } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { LoginPage } from './LoginPage'
import { RecuperarPage, RestablecerPage } from './RecuperarPage'
import { USUARIO_ADMIN, sinSesion } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const API = '*/api/v1'

function abrirLogin(ruta: InitialEntry = '/login') {
  return renderizar(
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<p>Panel del equipo</p>} />
      <Route path="/portal" element={<p>Portal de la familia</p>} />
    </Routes>,
    { ruta },
  )
}

describe('LoginPage', () => {
  it('muestra el ingreso del equipo con sus campos etiquetados', async () => {
    server.use(sinSesion)
    abrirLogin()
    expect(await screen.findByRole('heading', { name: 'Hola de nuevo' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /equipo/i })).toHaveAttribute('aria-selected', 'true')
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
    expect(await screen.findByRole('status')).toHaveTextContent('al 300 111 2233')
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

  it('una familia con su cuenta activada entra con su celular y su contraseña', async () => {
    let cuerpo = ''
    server.use(
      sinSesion,
      http.post(`${API}/auth/login`, async ({ request }) => {
        cuerpo = await request.text()
        return HttpResponse.json({ usuario: { ...USUARIO_ADMIN, rol: 'familia' } })
      }),
    )
    const user = userEvent.setup()
    abrirLogin()
    await user.click(await screen.findByRole('tab', { name: /familias/i }))
    await user.click(screen.getByRole('button', { name: 'Ingresar con contraseña' }))
    await user.type(screen.getByLabelText('Correo o celular'), '3001112233')
    await user.type(screen.getByLabelText('Contraseña'), 'clave-familia')
    await user.click(screen.getByRole('button', { name: 'Ingresar' }))
    expect(await screen.findByText('Portal de la familia')).toBeInTheDocument()
    expect(cuerpo).toBe('username=3001112233&password=clave-familia')
  })

  it('quien vuelve al ingreso desde la contraseña de familia puede pedir el código', async () => {
    server.use(sinSesion)
    const user = userEvent.setup()
    abrirLogin()
    await user.click(await screen.findByRole('tab', { name: /familias/i }))
    await user.click(screen.getByRole('button', { name: 'Ingresar con contraseña' }))
    await user.click(screen.getByRole('button', { name: 'Recibir un código por WhatsApp' }))
    expect(screen.getByLabelText('Celular registrado')).toBeInTheDocument()
  })

  it('quien llega desde el portal encuentra abierta la pestaña de familias', async () => {
    server.use(sinSesion)
    abrirLogin({ pathname: '/login', state: { from: '/portal/pagos' } })
    expect(await screen.findByRole('tab', { name: /familias/i })).toHaveAttribute('aria-selected', 'true')
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

  it('saluda con el enlace vigente, define la contraseña y entra a su espacio', async () => {
    const enviado: unknown[] = []
    server.use(
      sinSesion,
      http.post(`${API}/auth/enlace`, async ({ request }) => {
        enviado.push(await request.json())
        return HttpResponse.json({ estado: 'vigente', proposito: 'activacion', nombre: 'Ana' })
      }),
      http.post(`${API}/auth/restablecer`, async ({ request }) => {
        enviado.push(await request.json())
        return HttpResponse.json({ usuario: { ...USUARIO_ADMIN, rol: 'familia' } })
      }),
    )
    const user = userEvent.setup()
    renderizar(
      <Routes>
        <Route path="/activar" element={<RestablecerPage modo="activar" />} />
        <Route path="/portal" element={<p>Portal de la familia</p>} />
      </Routes>,
      { ruta: '/activar?token=abc' },
    )
    expect(await screen.findByRole('heading', { name: 'Hola, Ana' })).toBeInTheDocument()
    expect(screen.getByText('Te damos la bienvenida a la manada TIMU.')).toBeInTheDocument()
    expect(screen.getByLabelText('Contraseña nueva')).toHaveAccessibleDescription('Al menos 8 caracteres.')
    await user.type(screen.getByLabelText('Contraseña nueva'), 'segura1234')
    await user.type(screen.getByLabelText('Confirma la contraseña'), 'segura1234')
    await user.click(screen.getByRole('button', { name: 'Activar mi cuenta' }))
    expect(await screen.findByText('Portal de la familia')).toBeInTheDocument()
    expect(enviado).toEqual([{ token: 'abc' }, { token: 'abc', password: 'segura1234' }])
  })

  it('el enlace de recuperación dice que cierra las otras sesiones', async () => {
    server.use(
      sinSesion,
      http.post(`${API}/auth/enlace`, () =>
        HttpResponse.json({
          estado: 'vigente',
          proposito: 'recuperacion',
          nombre: 'Valentina',
          expira_en: '2026-11-18T14:00:00Z',
        }),
      ),
    )
    renderizar(<RestablecerPage modo="restablecer" />, { ruta: '/restablecer?token=abc' })
    expect(await screen.findByRole('heading', { name: 'Hola, Valentina' })).toBeInTheDocument()
    expect(screen.getByText(/se cierran las sesiones/)).toBeInTheDocument()
    // La vigencia la da la API, en la hora de Colombia (UTC−5).
    expect(screen.getByText(/Este enlace sirve hasta el mié 18 nov a las 9:00/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Guardar y entrar' })).toBeInTheDocument()
  })

  it.each([
    ['usado', 'Este enlace ya se usó'],
    ['vencido', 'Este enlace venció'],
    ['invalido', 'Este enlace no sirve'],
  ])('un enlace %s lo dice de entrada y ofrece otro', async (estado, titulo) => {
    server.use(sinSesion, http.post(`${API}/auth/enlace`, () => HttpResponse.json({ estado })))
    renderizar(<RestablecerPage modo="activar" />, { ruta: '/activar?token=abc' })
    expect(await screen.findByRole('heading', { name: titulo })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Pedir un enlace nuevo' })).toHaveAttribute('href', '/recuperar')
    expect(screen.queryByLabelText('Contraseña nueva')).not.toBeInTheDocument()
  })

  it('sin token no consulta nada y dice que el enlace está incompleto', async () => {
    server.use(sinSesion)
    renderizar(<RestablecerPage modo="restablecer" />, { ruta: '/restablecer' })
    expect(await screen.findByRole('heading', { name: 'El enlace está incompleto' })).toBeInTheDocument()
  })

  it('si no se pudo comprobar el enlace, deja reintentar', async () => {
    let intentos = 0
    server.use(
      sinSesion,
      http.post(`${API}/auth/enlace`, () =>
        ++intentos === 1
          ? new HttpResponse(null, { status: 503 })
          : HttpResponse.json({ estado: 'vigente', proposito: 'activacion', nombre: 'Ana' }),
      ),
    )
    const user = userEvent.setup()
    renderizar(<RestablecerPage modo="activar" />, { ruta: '/activar?token=abc' })
    expect(await screen.findByRole('heading', { name: 'No pudimos comprobar el enlace' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(await screen.findByRole('heading', { name: 'Hola, Ana' })).toBeInTheDocument()
  })

  it('no deja enviar si las contraseñas no coinciden, y avisa si el enlace caducó al guardar', async () => {
    server.use(
      sinSesion,
      http.post(`${API}/auth/enlace`, () =>
        HttpResponse.json({ estado: 'vigente', proposito: 'recuperacion', nombre: 'Ana' }),
      ),
      http.post(`${API}/auth/restablecer`, () =>
        HttpResponse.json({ detail: 'El enlace no es valido', codigo: 'enlace_invalido' }, { status: 400 }),
      ),
    )
    const user = userEvent.setup()
    renderizar(<RestablecerPage modo="restablecer" />, { ruta: '/restablecer?token=abc' })
    await user.type(await screen.findByLabelText('Contraseña nueva'), 'segura1234')
    await user.type(screen.getByLabelText('Confirma la contraseña'), 'otra')
    expect(screen.getByLabelText('Confirma la contraseña')).toHaveAccessibleDescription('Las contraseñas no coinciden.')
    expect(screen.getByRole('button', { name: 'Guardar y entrar' })).toBeDisabled()
    await user.clear(screen.getByLabelText('Confirma la contraseña'))
    await user.type(screen.getByLabelText('Confirma la contraseña'), 'segura1234')
    await user.click(screen.getByRole('button', { name: 'Guardar y entrar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('dejó de servir')
    expect(screen.getByRole('link', { name: 'Pide uno nuevo' })).toHaveAttribute('href', '/recuperar')
  })
})
