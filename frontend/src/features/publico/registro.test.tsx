import { fireEvent, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { CompletarRegistroPage, RegistroResultadoPage } from './CompletarRegistroPage'
import { RegistroPage } from './RegistroPage'
import { sinSesion } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const API = '*/api/v1'
const REGISTRO = `${API}/afiliaciones/registro`
const TOKEN = 'tk-0123456789abcdefghij'

const plan = (id: string, nombre: string, especies: string[], valor: string) => ({
  id,
  codigo: id,
  nombre,
  descripcion: null,
  especies,
  tarifas: [{ peludos: 1, valor }],
  tarifas_periodicidad: [],
  beneficios: [],
})
const PLANES = [
  plan('p-gato', 'Colita Feliz', ['felino'], '35500.00'),
  plan('p-perro', 'Mi Amigo Fiel', ['canino'], '71000.00'),
]
const PELUDOS_COTIZADOS = [
  { especie: 'felino', plan_id: 'p-gato', plan_nombre: 'Colita Feliz', valor_mensual: '30500.00' },
  { especie: 'canino', plan_id: 'p-perro', plan_nombre: 'Mi Amigo Fiel', valor_mensual: '61000.00' },
]
const opcion = (periodicidad: string, meses: number, valor_periodo: string) => ({
  periodicidad,
  meses,
  tarifa_de: 2,
  peludos: PELUDOS_COTIZADOS,
  valor_mensual: '91500.00',
  valor_periodo,
  descuento: false,
  ahorro: '0.00',
})
const COTIZACION = [opcion('mensual', 1, '91500.00'), opcion('trimestral', 3, '274500.00')]

const REGISTRO_PAGADO = {
  estado: 'pagada',
  ciudad: 'Medellin',
  periodicidad: 'mensual',
  valor_inicial: '91500.00',
  contacto_nombre: 'Ana Ruiz',
  contacto_telefono: '+573001234567',
  contacto_email: 'ana@correo.co',
  estado_pago: 'aprobado',
  peludos: [
    { posicion: 1, nombre: 'Luna', especie: 'felino', plan_id: 'p-gato', valor_mensual: '30500.00' },
    { posicion: 2, nombre: 'Max', especie: 'canino', plan_id: 'p-perro', valor_mensual: '61000.00' },
  ],
}

let asignar: ReturnType<typeof vi.fn>

beforeEach(() => {
  window.sessionStorage.clear()
  asignar = vi.fn()
  // En una página pública: el cliente no manda al ingreso por la falta de sesión.
  vi.stubGlobal('location', { ...window.location, pathname: '/afiliacion', assign: asignar })
})
afterEach(() => vi.unstubAllGlobals())

describe('Registro en línea', () => {
  function catalogo() {
    const cotizaciones: unknown[] = []
    server.use(
      sinSesion,
      http.get(`${REGISTRO}/ciudades`, () => HttpResponse.json(['Bogota', 'Medellin'])),
      http.get(`${REGISTRO}/planes`, () => HttpResponse.json(PLANES)),
      http.post(`${REGISTRO}/cotizacion`, async ({ request }) => {
        cotizaciones.push(await request.json())
        return HttpResponse.json(COTIZACION)
      }),
    )
    return cotizaciones
  }

  async function hastaLosPeludos(user: ReturnType<typeof userEvent.setup>) {
    renderizar(<RegistroPage />, { ruta: '/afiliacion' })
    await screen.findByRole('option', { name: 'Medellin' })
    await user.selectOptions(screen.getByLabelText('¿En qué ciudad vives?'), 'Medellin')
    await user.click(screen.getByRole('button', { name: 'Continuar' }))
    await user.click(await screen.findByRole('button', { name: 'Confirmo que solo voy a afiliar perros o gatos' }))
  }

  it('lleva de la ciudad al pago con un plan por peludo y el precio del backend', async () => {
    const cotizaciones = catalogo()
    let enviado: Record<string, unknown> | null = null
    server.use(
      http.post(REGISTRO, async ({ request }) => {
        enviado = (await request.json()) as Record<string, unknown>
        return HttpResponse.json(
          { referencia: 'AFI-1', valor: '274500.00', enlace_pago: 'https://checkout.wompi.co/p/?reference=AFI-1', token: TOKEN },
          { status: 201 },
        )
      }),
    )
    const user = userEvent.setup()
    await hastaLosPeludos(user)

    await user.type(screen.getByLabelText('Nombre'), 'Luna')
    await user.selectOptions(screen.getByLabelText('Especie'), 'felino')
    await user.click(screen.getByRole('button', { name: /otro peludo/i }))
    await user.type(screen.getAllByLabelText('Nombre')[1]!, 'Max')
    await user.click(screen.getByRole('button', { name: 'Elegir planes' }))

    // Cada peludo solo ve los planes de su especie.
    const luna = await screen.findByLabelText(/Luna · Gato/)
    expect(screen.queryByRole('option', { name: /Mi Amigo Fiel/ })).toBeInTheDocument()
    expect(luna.querySelectorAll('option:not([disabled])')).toHaveLength(1)
    await user.selectOptions(luna, 'p-gato')
    await user.selectOptions(screen.getByLabelText(/Max · Perro/), 'p-perro')
    expect(await screen.findByText(/cada uno paga la tarifa de 2/)).toBeInTheDocument()
    expect(cotizaciones.at(-1)).toEqual({
      ciudad: 'Medellin',
      peludos: [
        { especie: 'felino', plan_id: 'p-gato' },
        { especie: 'canino', plan_id: 'p-perro' },
      ],
    })
    await user.click(screen.getByRole('button', { name: 'Elegir forma de pago' }))

    await user.click(screen.getByRole('radio', { name: /trimestral/i }))
    expect(screen.getByRole('list', { name: 'Resumen de la afiliación' })).toHaveTextContent('Luna · Colita Feliz')
    await user.type(screen.getByLabelText('Tu nombre'), 'Ana Ruiz')
    await user.type(screen.getByLabelText('Celular (WhatsApp)'), '3001234567')
    await user.type(screen.getByLabelText('Correo'), 'ana@correo.co')
    await user.click(screen.getByLabelText(/acepto las condiciones/i))
    await user.click(screen.getByLabelText(/autorizo el tratamiento/i))
    await user.click(screen.getByRole('button', { name: /^pagar/i }))

    await waitFor(() => expect(asignar).toHaveBeenCalledWith('https://checkout.wompi.co/p/?reference=AFI-1'))
    expect(enviado).toEqual({
      ciudad: 'Medellin',
      peludos: [
        { nombre: 'Luna', especie: 'felino', plan_id: 'p-gato' },
        { nombre: 'Max', especie: 'canino', plan_id: 'p-perro' },
      ],
      periodicidad: 'trimestral',
      contacto: { nombre: 'Ana Ruiz', telefono: '3001234567', email: 'ana@correo.co' },
      acepta_condiciones: true,
      acepta_tratamiento_datos: true,
    })
    // El token queda en esta pestaña para seguir al volver de la pasarela.
    expect(window.sessionStorage.getItem('timu-registro')).toBe(TOKEN)
  })

  it('sin cobertura en la ciudad solo informa', async () => {
    catalogo()
    const user = userEvent.setup()
    renderizar(<RegistroPage />, { ruta: '/afiliacion' })
    await screen.findByRole('option', { name: 'Medellin' })
    await user.selectOptions(screen.getByLabelText('¿En qué ciudad vives?'), 'otra')
    expect(screen.getByRole('status')).toHaveTextContent('Por ahora solo atendemos en Bogota y Medellin')
    expect(screen.getByRole('button', { name: 'Continuar' })).toBeDisabled()
  })

  it('pide un nombre distinto para cada peludo', async () => {
    catalogo()
    const user = userEvent.setup()
    await hastaLosPeludos(user)
    await user.type(screen.getByLabelText('Nombre'), 'Luna')
    await user.click(screen.getByRole('button', { name: /otro peludo/i }))
    await user.type(screen.getAllByLabelText('Nombre')[1]!, ' luna')
    expect(screen.getByRole('alert')).toHaveTextContent('Cada peludo necesita un nombre distinto')
    await user.click(screen.getByRole('button', { name: 'Elegir planes' }))
    expect(screen.queryByLabelText(/Luna · Gato/)).not.toBeInTheDocument()
  })

  it('el error del backend se muestra y no lleva a la pasarela', async () => {
    catalogo()
    server.use(http.post(REGISTRO, () => HttpResponse.json({ detail: 'Por ahora no tenemos cobertura' }, { status: 422 })))
    const user = userEvent.setup()
    await hastaLosPeludos(user)
    await user.type(screen.getByLabelText('Nombre'), 'Max')
    await user.click(screen.getByRole('button', { name: 'Elegir planes' }))
    await user.selectOptions(await screen.findByLabelText(/Max · Perro/), 'p-perro')
    await user.click(screen.getByRole('button', { name: 'Elegir forma de pago' }))
    await screen.findByRole('radio', { name: /mensual/i })
    await user.type(screen.getByLabelText('Tu nombre'), 'Ana Ruiz')
    await user.type(screen.getByLabelText('Celular (WhatsApp)'), '3001234567')
    await user.type(screen.getByLabelText('Correo'), 'ana@correo.co')
    await user.click(screen.getByLabelText(/acepto las condiciones/i))
    await user.click(screen.getByLabelText(/autorizo el tratamiento/i))
    await user.click(screen.getByRole('button', { name: /^pagar/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Por ahora no tenemos cobertura')
    expect(asignar).not.toHaveBeenCalled()
  })
})

describe('Regreso de la pasarela', () => {
  function abrir() {
    return renderizar(
      <Routes>
        <Route path="/afiliacion/resultado" element={<RegistroResultadoPage />} />
        <Route path="/afiliacion/completar" element={<p>Formulario de la familia</p>} />
      </Routes>,
      { ruta: '/afiliacion/resultado' },
    )
  }

  function consulta(respuesta: Record<string, unknown>) {
    const tokens: unknown[] = []
    server.use(
      sinSesion,
      http.post(`${REGISTRO}/consulta`, async ({ request }) => {
        tokens.push(await request.json())
        return HttpResponse.json(respuesta)
      }),
    )
    return tokens
  }

  it('sin el token de esta pestaña remite al enlace enviado', async () => {
    server.use(sinSesion)
    abrir()
    expect(await screen.findByText(/te enviamos un enlace por correo y WhatsApp/)).toBeInTheDocument()
  })

  it('espera la confirmación sin pedir datos todavía', async () => {
    window.sessionStorage.setItem('timu-registro', TOKEN)
    const tokens = consulta({ ...REGISTRO_PAGADO, estado: 'pendiente_pago', estado_pago: 'pendiente' })
    abrir()
    expect(await screen.findByRole('status')).toHaveTextContent('La pasarela aún no confirma el pago')
    expect(tokens).toEqual([{ token: TOKEN }])
  })

  it('con el pago confirmado sigue al formulario', async () => {
    window.sessionStorage.setItem('timu-registro', TOKEN)
    consulta(REGISTRO_PAGADO)
    abrir()
    expect(await screen.findByText('Formulario de la familia')).toBeInTheDocument()
  })

  it('con el pago rechazado ofrece volver a intentarlo', async () => {
    window.sessionStorage.setItem('timu-registro', TOKEN)
    consulta({ ...REGISTRO_PAGADO, estado: 'pendiente_pago', estado_pago: 'rechazado' })
    const user = userEvent.setup()
    abrir()
    expect(await screen.findByRole('alert')).toHaveTextContent('La pasarela no aprobó el pago')
    await user.click(screen.getByRole('link', { name: 'Intentar de nuevo' }))
    expect(window.sessionStorage.getItem('timu-registro')).toBeNull()
  })
})

describe('Formulario posterior al pago', () => {
  function abrir(ruta = `/afiliacion/completar?token=${TOKEN}`) {
    return renderizar(
      <Routes>
        <Route path="/afiliacion/completar" element={<CompletarRegistroPage />} />
      </Routes>,
      { ruta },
    )
  }

  function consulta(respuesta: Record<string, unknown> = REGISTRO_PAGADO) {
    server.use(
      sinSesion,
      http.post(`${REGISTRO}/consulta`, () => HttpResponse.json(respuesta)),
    )
  }

  async function llenar(user: ReturnType<typeof userEvent.setup>, clave = 'clave-segura-1') {
    await user.type(screen.getByLabelText('Número de documento'), '52111222')
    await user.type(screen.getByLabelText('Barrio'), 'El Poblado')
    await user.type(screen.getByLabelText('Dirección'), 'Calle 10 # 43-20')
    const nombres = screen.getAllByLabelText('Nombre')
    await user.clear(nombres[0]!)
    await user.type(nombres[0]!, 'Lunita')
    screen.getAllByLabelText('Fecha de nacimiento (aproximada)').forEach((campo, i) =>
      fireEvent.change(campo, { target: { value: i === 0 ? '2022-05-01' : '2020-01-15' } }),
    )
    const pesos = screen.getAllByLabelText('Peso en kg')
    await user.type(pesos[0]!, '4.2')
    await user.type(pesos[1]!, '18')
    await user.type(screen.getByLabelText('Contraseña'), 'clave-segura-1')
    await user.type(screen.getByLabelText('Repite la contraseña'), clave)
  }

  it('activa la afiliación, sube las fotos y abre el portal', async () => {
    consulta()
    let enviado: Record<string, unknown> | null = null
    const fotos: string[] = []
    server.use(
      http.post(`${REGISTRO}/completar`, async ({ request }) => {
        enviado = (await request.json()) as Record<string, unknown>
        return HttpResponse.json({ estado: 'completada', mensaje: 'Tu afiliacion esta activa' })
      }),
      http.get(`${API}/portal/mi-familia`, () =>
        HttpResponse.json({ mascotas: [{ id: 'm1', nombre: 'Lunita' }, { id: 'm2', nombre: 'Max' }] }),
      ),
      http.put(`${API}/portal/mascotas/:id/foto`, ({ params }) => {
        fotos.push(String(params.id))
        return HttpResponse.json({})
      }),
    )
    const user = userEvent.setup()
    abrir()
    expect(await screen.findByLabelText('Nombre completo')).toHaveValue('Ana Ruiz')
    expect(screen.getByLabelText('Correo')).toHaveValue('ana@correo.co')
    expect(screen.getByLabelText('Ciudad')).toHaveValue('Medellin')
    expect(window.sessionStorage.getItem('timu-registro')).toBe(TOKEN)
    await llenar(user)
    await user.click(screen.getByRole('button', { name: /agregar contacto/i }))
    await user.type(screen.getByLabelText('Nombre del contacto 1'), 'Pedro Ruiz')
    await user.type(screen.getByLabelText('Celular del contacto 1'), '3109876543')
    const [fotoLuna] = screen.getAllByLabelText('Foto (opcional)')
    await user.upload(fotoLuna!, new File(['foto'], 'luna.jpg', { type: 'image/jpeg' }))
    await user.click(screen.getByRole('button', { name: 'Activar mi afiliación' }))

    await waitFor(() => expect(asignar).toHaveBeenCalledWith('/portal'))
    expect(fotos).toEqual(['m1'])
    expect(enviado).toEqual({
      token: TOKEN,
      titular: {
        titular_nombre: 'Ana Ruiz',
        tipo_documento: 'CC',
        documento: '52111222',
        telefono: '+573001234567',
        email: 'ana@correo.co',
        barrio: 'El Poblado',
        direccion: 'Calle 10 # 43-20',
      },
      contactos: [{ nombre: 'Pedro Ruiz', telefono: '3109876543' }],
      clave: 'clave-segura-1',
      peludos: [
        { posicion: 1, nombre: 'Lunita', fecha_nacimiento: '2022-05-01', peso_kg: 4.2 },
        { posicion: 2, nombre: 'Max', fecha_nacimiento: '2020-01-15', peso_kg: 18 },
      ],
    })
    expect(window.sessionStorage.getItem('timu-registro')).toBeNull()
  })

  it('si el equipo debe revisarlo, lo dice y no abre el portal', async () => {
    consulta()
    server.use(
      http.post(`${REGISTRO}/completar`, () =>
        HttpResponse.json({ estado: 'revision', mensaje: 'Nuestro equipo revisa tu afiliacion' }),
      ),
    )
    const user = userEvent.setup()
    abrir()
    await screen.findByLabelText('Nombre completo')
    await llenar(user)
    await user.click(screen.getByRole('button', { name: 'Activar mi afiliación' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Nuestro equipo revisa tu afiliacion')
    expect(asignar).not.toHaveBeenCalled()
  })

  it('no envía si las contraseñas no coinciden', async () => {
    consulta()
    const user = userEvent.setup()
    abrir()
    await screen.findByLabelText('Nombre completo')
    await llenar(user, 'otra-clave-9')
    await user.click(screen.getByRole('button', { name: 'Activar mi afiliación' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Las contraseñas no coinciden')
  })

  it('con la afiliación ya activa no repite el formulario', async () => {
    window.sessionStorage.setItem('timu-registro', TOKEN)
    consulta({ ...REGISTRO_PAGADO, estado: 'completada' })
    abrir('/afiliacion/completar')
    expect(await screen.findByRole('status')).toHaveTextContent('Tu afiliación ya está activa')
    expect(screen.queryByLabelText('Nombre completo')).not.toBeInTheDocument()
  })

  it('un enlace inválido lo dice', async () => {
    server.use(
      sinSesion,
      http.post(`${REGISTRO}/consulta`, () => HttpResponse.json({ detail: 'El enlace no es valido' }, { status: 404 })),
    )
    abrir()
    expect(await screen.findByRole('alert')).toHaveTextContent('El enlace no es valido')
  })
})
