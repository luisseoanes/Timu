import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { CompletarRegistroPage } from './CompletarRegistroPage'
import { RegistroResultadoPage } from './ResultadoRegistroPage'
import { RegistroPage } from './RegistroPage'
import { sinSesion } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const API = '*/api/v1'
const REGISTRO = `${API}/afiliaciones/registro`
const TOKEN = 'tk-0123456789abcdefghij'

const beneficio = (tipo_servicio_codigo: string, nombre: string, texto: string) => ({
  tipo_servicio_codigo,
  nombre,
  cupo: 1,
  periodo_cupo: 'mensual',
  cobertura_pct: 100,
  copago: '0.00',
  texto,
})
const plan = (id: string, nombre: string, especies: string[], valor: string, color: string, beneficios = [] as unknown[]) => ({
  id,
  codigo: id,
  nombre,
  descripcion: null,
  especies,
  color,
  tarifas: [
    { peludos: 1, valor },
    { peludos: 2, valor: String(Number(valor) - 5000) },
  ],
  tarifas_periodicidad: [],
  beneficios,
  carencia: null,
  exclusiones: null,
  terminos_url: null,
})
const PLANES = [
  plan('p-gato', 'Colita Feliz', ['felino'], '35500.00', 'naranja'),
  plan('p-perro', 'Mi Amigo Fiel', ['canino'], '71000.00', 'verde'),
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
  ciudad: 'Medellín',
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

/** El WhatsApp de TIMU que ofrece el registro a quien tiene una duda. */
const CONTACTO = http.get(`${REGISTRO}/contacto`, () => HttpResponse.json({ whatsapp: '+573001112233' }))

let asignar: ReturnType<typeof vi.fn>

beforeEach(() => {
  window.sessionStorage.clear()
  asignar = vi.fn()
  // En una página pública: el cliente no manda al ingreso por la falta de sesión.
  vi.stubGlobal('location', { ...window.location, pathname: '/afiliacion', assign: asignar })
})
afterEach(() => vi.unstubAllGlobals())

describe('Registro en línea', () => {
  function catalogo(planes: unknown[] = PLANES) {
    const cotizaciones: unknown[] = []
    server.use(
      sinSesion,
      CONTACTO,
      http.get(`${REGISTRO}/ciudades`, () => HttpResponse.json(['Bogotá', 'Medellín'])),
      http.get(`${REGISTRO}/planes`, () => HttpResponse.json(planes)),
      http.post(`${REGISTRO}/cotizacion`, async ({ request }) => {
        cotizaciones.push(await request.json())
        return HttpResponse.json(COTIZACION)
      }),
    )
    return cotizaciones
  }

  /** La ciudad, la confirmación de la especie y la primera ficha abierta. */
  async function hastaLaManada(user: ReturnType<typeof userEvent.setup>) {
    renderizar(<RegistroPage />, { ruta: '/afiliacion' })
    await screen.findByRole('option', { name: 'Medellín' })
    await user.selectOptions(screen.getByLabelText('¿En qué ciudad vives?'), 'Medellín')
    await user.click(await screen.findByRole('button', { name: 'Confirmo que solo voy a afiliar perros o gatos' }))
    return screen.findByRole('region', { name: /^Peludo 1/ })
  }

  async function pagar(user: ReturnType<typeof userEvent.setup>) {
    await user.type(screen.getByLabelText('Tu nombre'), 'Ana Ruiz')
    await user.type(screen.getByLabelText('Celular (WhatsApp)'), '3001234567')
    await user.type(screen.getByLabelText('Correo'), 'ana@correo.co')
    await user.click(screen.getByLabelText(/acepto las condiciones/i))
    await user.click(screen.getByLabelText(/autorizo el tratamiento/i))
    await user.click(screen.getByRole('button', { name: /^pagar/i }))
  }

  it('arma la manada con un plan por peludo, ve el total de la familia y paga lo que cobra el backend', async () => {
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
    const primero = await hastaLaManada(user)
    await user.type(within(primero).getByLabelText('Nombre'), 'Luna')
    await user.click(within(primero).getByRole('radio', { name: 'Gato' }))
    // Cada peludo solo ve los planes de su especie.
    expect(within(primero).getAllByRole('radio', { name: /Colita Feliz|Mi Amigo Fiel/ })).toHaveLength(1)
    await user.click(within(primero).getByRole('radio', { name: /Colita Feliz/ }))
    expect(screen.getByRole('button', { name: 'Elegir cómo pagar' })).toBeEnabled()

    await user.click(screen.getByRole('button', { name: 'Otro peludo' }))
    const segundo = screen.getByRole('region', { name: /^Peludo 2/ })
    await user.type(within(segundo).getByLabelText('Nombre'), 'Max')
    // Con dos peludos, cada plan dice la tarifa de dos.
    await user.click(within(segundo).getByRole('radio', { name: /Mi Amigo Fiel.*66\.000/ }))
    const resumen = screen.getByRole('complementary', { name: 'Tu afiliación' })
    await waitFor(() => expect(resumen).toHaveTextContent(/2 peludos · tarifa de 2\s*\$\s91\.500 al mes/))
    expect(cotizaciones.at(-1)).toEqual({
      ciudad: 'Medellín',
      peludos: [
        { especie: 'felino', plan_id: 'p-gato' },
        { especie: 'canino', plan_id: 'p-perro' },
      ],
    })
    await user.click(screen.getByRole('button', { name: 'Elegir cómo pagar' }))

    expect(await screen.findByRole('heading', { level: 1, name: '¿Cómo quieres pagar?' })).toBeInTheDocument()
    await user.click(screen.getByRole('radio', { name: /trimestral/i }))
    expect(resumen).toHaveTextContent('Luna')
    await pagar(user)

    await waitFor(() => expect(asignar).toHaveBeenCalledWith('https://checkout.wompi.co/p/?reference=AFI-1'))
    expect(enviado).toEqual({
      ciudad: 'Medellín',
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

  it('el plan elegido dice lo que cubre y sus condiciones, y el comparador pone los planes lado a lado', async () => {
    const CONSULTA = beneficio('consulta_domiciliaria', 'Consulta domiciliaria', '1 al mes')
    const ALIADA = beneficio('atencion_aliada', 'Atención en clínica aliada', 'Sin tope de usos · cubre el 40\u00a0%')
    catalogo([
      { ...plan('p-basico', 'Colita Feliz', [], '35500.00', 'naranja', [CONSULTA]), exclusiones: 'Excluye preexistencias.' },
      {
        ...plan('p-fiel', 'Mi Amigo Fiel', [], '69000.00', 'verde', [ALIADA, CONSULTA]),
        carencia: 'Sin periodo de carencia.',
        exclusiones: 'Excluye preexistencias.',
        terminos_url: 'https://timu.com.co/terminos',
      },
    ])
    const user = userEvent.setup()
    const ficha = await hastaLaManada(user)
    expect(within(ficha).getByText('Elige un plan para ver todo lo que cubre y sus condiciones.')).toBeInTheDocument()
    await user.click(within(ficha).getByRole('radio', { name: /Mi Amigo Fiel/ }))
    expect(within(ficha).getByText('Atención en clínica aliada')).toBeInTheDocument()
    expect(within(ficha).getByText(/^Sin tope de usos · cubre el 40\s%$/)).toBeInTheDocument()
    expect(within(ficha).getByText('Sin periodo de carencia.')).toBeInTheDocument()
    expect(within(ficha).getByRole('link', { name: 'Términos y condiciones de Mi Amigo Fiel' })).toHaveAttribute(
      'href',
      'https://timu.com.co/terminos',
    )

    await user.click(within(ficha).getByRole('button', { name: 'Comparar los 2 planes' }))
    const tabla = within(ficha).getByRole('table', { name: /Lo que cubre cada plan/ })
    const fila = within(tabla).getByRole('row', { name: /Atención en clínica aliada/ })
    // Un servicio que el plan no trae se dice, no se deja en blanco.
    // Cada valor lleva su plan (visible al apilarse en el celular): se compara el valor.
    const valor = (c: HTMLElement) => c.querySelector(':scope > span:last-child')?.textContent ?? c.textContent
    expect(within(fila).getAllByRole('cell').map(valor)).toEqual([
      'Atención en clínica aliada',
      'No incluye',
      'Sin tope de usos · cubre el 40\u00a0%',
    ])
    expect(within(tabla).getByRole('row', { name: /Carencia/ })).toHaveTextContent('—')
    // Lo que es igual en los planes se dice una vez.
    expect(within(tabla).getByRole('row', { name: /Consulta domiciliaria/ })).toHaveTextContent('1 al mes · igual en los 2')
  })

  it('promete ahorro solo cuando algún periodo lo da', async () => {
    catalogo()
    // Con un peludo, el trimestral de TIMU trae descuento: la frase lo dice y la opción, cuánto.
    server.use(
      http.post(`${REGISTRO}/cotizacion`, () =>
        HttpResponse.json([
          opcion('mensual', 1, '69000.00'),
          { ...opcion('trimestral', 3, '201800.00'), descuento: true, ahorro: '5200.00' },
        ]),
      ),
    )
    const user = userEvent.setup()
    const ficha = await hastaLaManada(user)
    await user.type(within(ficha).getByLabelText('Nombre'), 'Toby')
    await user.click(within(ficha).getByRole('radio', { name: /Mi Amigo Fiel/ }))
    await user.click(await screen.findByRole('button', { name: 'Elegir cómo pagar' }))
    expect(await screen.findByText(/Pagando por varios meses ahorras\./)).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: /Trimestral/ }).closest('label')).toHaveTextContent(/Ahorras\s\$\s5\.200/)
  })

  it('sin cobertura en la ciudad solo informa', async () => {
    catalogo()
    const user = userEvent.setup()
    renderizar(<RegistroPage />, { ruta: '/afiliacion' })
    await screen.findByRole('option', { name: 'Medellín' })
    await user.selectOptions(screen.getByLabelText('¿En qué ciudad vives?'), 'otra')
    expect(screen.getByRole('status')).toHaveTextContent('Por ahora solo atendemos en Bogotá y Medellín')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.queryByRole('region', { name: /^Peludo 1/ })).not.toBeInTheDocument()
  })

  it('pide un nombre distinto para cada peludo y no deja seguir', async () => {
    catalogo()
    const user = userEvent.setup()
    const primero = await hastaLaManada(user)
    await user.type(within(primero).getByLabelText('Nombre'), 'Luna')
    await user.click(within(primero).getByRole('radio', { name: /Mi Amigo Fiel/ }))
    await user.click(screen.getByRole('button', { name: 'Otro peludo' }))
    const segundo = screen.getByRole('region', { name: /^Peludo 2/ })
    await user.type(within(segundo).getByLabelText('Nombre'), ' luna')
    await user.click(within(segundo).getByRole('radio', { name: /Mi Amigo Fiel/ }))
    expect(within(segundo).getByLabelText('Nombre')).toHaveAccessibleDescription('Otro peludo ya se llama así: cada uno necesita su nombre.')
    expect(screen.getByRole('button', { name: 'Elegir cómo pagar' })).toBeDisabled()
  })

  it('cambiar de ciudad limpia los planes elegidos: cada ciudad vende los suyos', async () => {
    catalogo()
    const user = userEvent.setup()
    const ficha = await hastaLaManada(user)
    await user.click(within(ficha).getByRole('radio', { name: /Mi Amigo Fiel/ }))
    await user.selectOptions(screen.getByLabelText('¿En qué ciudad vives?'), 'Bogotá')
    await waitFor(() => expect(within(screen.getByRole('region', { name: /^Peludo 1/ })).getByRole('radio', { name: /Mi Amigo Fiel/ })).not.toBeChecked())
    expect(screen.getByRole('complementary', { name: 'Tu afiliación' })).toHaveTextContent('Tu manada en Bogotá')
  })

  it('el error del backend se muestra y no lleva a la pasarela', async () => {
    catalogo()
    server.use(http.post(REGISTRO, () => HttpResponse.json({ detail: 'Por ahora no tenemos cobertura' }, { status: 422 })))
    const user = userEvent.setup()
    const ficha = await hastaLaManada(user)
    await user.type(within(ficha).getByLabelText('Nombre'), 'Max')
    await user.click(within(ficha).getByRole('radio', { name: /Mi Amigo Fiel/ }))
    await user.click(await screen.findByRole('button', { name: 'Elegir cómo pagar' }))
    await screen.findByRole('radio', { name: /mensual/i })
    await pagar(user)
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
      CONTACTO,
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
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('La pasarela aún no confirma el pago'))
    expect(screen.getByRole('heading', { level: 1, name: 'Estamos confirmando tu pago' })).toBeInTheDocument()
    expect(tokens).toEqual([{ token: TOKEN }])
  })

  it('con el pago confirmado sigue al formulario', async () => {
    window.sessionStorage.setItem('timu-registro', TOKEN)
    consulta(REGISTRO_PAGADO)
    abrir()
    expect(await screen.findByText('Formulario de la familia')).toBeInTheDocument()
  })

  it('con el pago rechazado reintenta en el mismo registro', async () => {
    window.sessionStorage.setItem('timu-registro', TOKEN)
    consulta({ ...REGISTRO_PAGADO, estado: 'pendiente_pago', estado_pago: 'rechazado' })
    let enviado: unknown = null
    server.use(
      http.post(`${REGISTRO}/reintentar`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ referencia: 'AFI-2', enlace_pago: 'https://checkout.wompi.co/p/?reference=AFI-2' })
      }),
    )
    const user = userEvent.setup()
    abrir()
    expect(await screen.findByRole('alert')).toHaveTextContent('La pasarela no aprobó el pago')
    // El título dice lo que pasó (antes decía «Estamos confirmando tu pago» también aquí).
    expect(screen.getByRole('heading', { level: 1, name: 'Tu pago no se aprobó' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /intentar de nuevo/i }))
    await waitFor(() => expect(asignar).toHaveBeenCalledWith('https://checkout.wompi.co/p/?reference=AFI-2'))
    expect(enviado).toEqual({ token: TOKEN })
    // El token sigue en la pestaña: al volver se consulta el pago nuevo.
    expect(window.sessionStorage.getItem('timu-registro')).toBe(TOKEN)
    // Si el problema sigue, hay a quién escribir.
    expect(screen.getByRole('link', { name: /Si el problema sigue, escríbenos por WhatsApp/ })).toHaveAttribute('href', 'https://wa.me/573001112233')
  })

  it('si ya no se puede reintentar, ofrece empezar de nuevo', async () => {
    window.sessionStorage.setItem('timu-registro', TOKEN)
    consulta({ ...REGISTRO_PAGADO, estado: 'pendiente_pago', estado_pago: 'rechazado' })
    server.use(
      http.post(`${REGISTRO}/reintentar`, () =>
        HttpResponse.json({ detail: 'Este registro ya no espera un pago' }, { status: 422 }),
      ),
    )
    const user = userEvent.setup()
    abrir()
    await user.click(await screen.findByRole('button', { name: /intentar de nuevo/i }))
    expect(await screen.findByText(/Este registro ya no espera un pago/)).toBeInTheDocument()
    await user.click(screen.getByRole('link', { name: 'Empezar de nuevo' }))
    expect(window.sessionStorage.getItem('timu-registro')).toBeNull()
    expect(asignar).not.toHaveBeenCalled()
  })

  it('un registro cerrado sin pago no dice que se recibió', async () => {
    window.sessionStorage.setItem('timu-registro', TOKEN)
    consulta({ ...REGISTRO_PAGADO, estado: 'cancelada', estado_pago: 'anulado' })
    abrir()
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Se cerró porque no recibimos el pago'))
    expect(screen.queryByText(/Recibimos tu pago/)).not.toBeInTheDocument()
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
    expect(screen.getByLabelText('Ciudad')).toHaveValue('Medellín')
    expect(window.sessionStorage.getItem('timu-registro')).toBe(TOKEN)
    await llenar(user)
    await user.click(screen.getByRole('button', { name: /agregar contacto/i }))
    await user.type(screen.getByLabelText('Nombre del contacto 1'), 'Pedro Ruiz')
    await user.type(screen.getByLabelText('Celular del contacto 1'), '3109876543')
    const [fotoLuna] = screen.getAllByLabelText('Foto (opcional)')
    await user.upload(fotoLuna!, new File(['foto'], 'luna.jpg', { type: 'image/jpeg' }))
    // El botón propio dice el archivo elegido y pasa a «Cambiar foto».
    expect(screen.getByText('luna.jpg')).toBeInTheDocument()
    expect(screen.getAllByText('Cambiar foto')).toHaveLength(1)
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
    expect(await screen.findByRole('heading', { level: 1, name: 'Tu afiliación ya está activa' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Ir al ingreso' })).toBeInTheDocument()
    expect(screen.queryByLabelText('Nombre completo')).not.toBeInTheDocument()
  })

  it('un enlace inválido lo dice', async () => {
    server.use(
      sinSesion,
      http.post(`${REGISTRO}/consulta`, () => HttpResponse.json({ detail: 'El enlace no es valido' }, { status: 404 })),
    )
    abrir()
    expect(await screen.findByRole('heading', { level: 1, name: 'Este enlace no sirve' })).toBeInTheDocument()
    // En palabras propias, no con el texto del servidor.
    expect(screen.getByRole('alert')).toHaveTextContent('El enlace no es válido o ya se usó.')
  })
})
