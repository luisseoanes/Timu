import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { sinSesion, USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { AliadaPublica, DatosTimuRead, PlanPublico } from '@/types'

import { PlanPage } from './PlanPage'
import { desdeMensual, enlaceAfiliacion, redTimu, rutaDePlan } from './portada'
import { PortadaPage } from './PortadaPage'

const API = '*/api/v1'
const REGISTRO = `${API}/afiliaciones/registro`

const plan = (codigo: string, nombre: string, color: PlanPublico['color'], valores: string[]): PlanPublico => ({
  id: `id-${codigo}`,
  codigo,
  nombre,
  descripcion: null,
  especies: [],
  color,
  tarifas: valores.map((valor, i) => ({ peludos: i + 1, valor })),
  tarifas_periodicidad: [{ periodicidad: 'trimestral', valor: String(Number(valores[0]) * 2.9) }],
  beneficios: [
    {
      tipo_servicio_codigo: 'cirugia',
      nombre: 'Cirugía',
      cupo: null,
      periodo_cupo: 'anual',
      cobertura_pct: 40,
      copago: '0',
      tope_episodio: '850000',
      texto: '40 % hasta $ 850.000 por episodio',
      carencia: 'Desde los 30 días',
      detalle: 'Con anestesia.',
    },
  ],
  adicionales: [{ nombre: 'Servicio fúnebre', cubre: '100 %', detalle: 'Traslado las 24 horas.', carencia: 'Desde los 30 días', tercero: false }],
  carencia: 'Sin periodo de carencia.',
  exclusiones: null,
  terminos_url: null,
})

const PLANES = [
  plan('colita_feliz', 'Colita Feliz', 'naranja', ['35500.00', '30500.00', '26000.00', '24000.00']),
  plan('mi_amigo_fiel', 'Mi Amigo Fiel', 'verde', ['69000.00', '61000.00', '57500.00', '57000.00']),
]

const aliada = (nombre: string, cambios: Partial<AliadaPublica> = {}): AliadaPublica => ({
  id: nombre,
  nombre,
  tipo: 'clinica',
  tipo_nombre: 'Clínica veterinaria',
  atiende_24h: false,
  ciudad: 'Medellín',
  barrio: null,
  direccion: null,
  telefono: null,
  horario: null,
  presentacion: null,
  logo_url: null,
  ...cambios,
})

const ALIADAS = [
  aliada('Cabañitas', { ciudad: 'Bello' }),
  aliada('Mira Bosques', { barrio: 'Laureles' }),
  aliada('Macarena', { barrio: 'Laureles', horario: 'Lunes a sábado' }),
  aliada('Integral Vet', { barrio: 'Aguacatala', atiende_24h: true, telefono: '+573001112233' }),
  aliada('AnesVet', { tipo: 'especialista', tipo_nombre: 'Especialista' }),
]

const DATOS: DatosTimuRead = {
  id: 'd1',
  razon_social: 'TIMU S.A.S.',
  nit: '901635168-2',
  presentacion: 'Integramos profesionales de salud para perros y gatos.',
  mision: null,
  vision: 'En 2027 estaremos a nivel nacional.',
  valores: ['Confianza', 'Empatía'],
  clinica_nombre: 'TIMU clínica veterinaria',
  clinica_direccion: 'Calle 35 # 66a 51',
  clinica_barrio: 'Los Conquistadores, Laureles',
  clinica_ciudad: 'Medellín',
  clinica_horario: 'Lunes a viernes de 9:00 a. m. a 6:00 p. m.',
  horario_atencion: null,
  telefonos: ['+573016244775'],
  whatsapp: '+573000000000',
  correo: 'administracion@timu.com.co',
  redes: [{ nombre: 'Instagram', url: 'https://www.instagram.com/timu/' }],
  politica_datos_url: 'https://timu.com.co/datos.pdf',
}

let pedidas: string[]

beforeEach(() => {
  pedidas = []
  // En una página pública: el cliente no manda al ingreso por la falta de sesión.
  vi.stubGlobal('location', { ...window.location, pathname: '/', assign: vi.fn() })
  server.use(
    sinSesion,
    http.get(`${REGISTRO}/ciudades`, () => HttpResponse.json(['Bogotá', 'Medellín'])),
    http.get(`${REGISTRO}/planes`, ({ request }) => {
      pedidas.push(new URL(request.url).searchParams.get('ciudad') ?? '')
      return HttpResponse.json(PLANES)
    }),
    http.get(`${API}/institucional`, () => HttpResponse.json(DATOS)),
    http.get(`${API}/aliadas/publicas`, () => HttpResponse.json(ALIADAS)),
  )
})
afterEach(() => vi.unstubAllGlobals())

describe('La red y los precios de la portada (portada.ts)', () => {
  it('agrupa en estaciones las aliadas seguidas del mismo barrio y marca la de la clínica de TIMU', () => {
    const { estaciones, servicios } = redTimu(ALIADAS, DATOS)
    expect(estaciones.map((e) => [e.nombre, e.ciudad, e.aliadas.length, e.clinicaTimu])).toEqual([
      ['Bello', null, 1, false],
      ['Laureles', 'Medellín', 2, true],
      ['Aguacatala', 'Medellín', 1, false],
    ])
    expect(servicios.map((a) => a.nombre)).toEqual(['AnesVet'])
  })

  it('sin aliadas en el barrio de la clínica, la clínica abre la línea con su propia estación', () => {
    const { estaciones } = redTimu([aliada('Cabañitas', { ciudad: 'Bello' })], DATOS)
    expect(estaciones[0]).toMatchObject({ nombre: 'Los Conquistadores, Laureles', ciudad: 'Medellín', aliadas: [], clinicaTimu: true })
  })

  it('una aliada sin barrio en un municipio con barrios no inventa su estación: va con los servicios', () => {
    const { estaciones, servicios } = redTimu([...ALIADAS, aliada('Cosmo Pets', { tipo: 'peluqueria' })], DATOS)
    expect(estaciones.map((e) => e.nombre)).not.toContain('Medellín')
    expect(servicios.map((a) => a.nombre)).toEqual(['AnesVet', 'Cosmo Pets'])
  })

  it('sin datos de la clínica, ninguna estación es de intercambio', () => {
    expect(redTimu(ALIADAS, null).estaciones.some((e) => e.clinicaTimu)).toBe(false)
  })

  it('el «desde» es la tarifa más baja con los peludos de la familia, hasta la de 4', () => {
    expect(desdeMensual(PLANES)).toBe('35500.00')
    expect(desdeMensual(PLANES, 2)).toBe('30500.00')
    expect(desdeMensual(PLANES, 9)).toBe('24000.00')
    expect(desdeMensual([])).toBeUndefined()
  })

  it('arma los enlaces de cada plan y de la afiliación con lo elegido', () => {
    expect(rutaDePlan({ codigo: 'mi_amigo_fiel' })).toBe('/planes/mi-amigo-fiel')
    expect(enlaceAfiliacion({ ciudad: 'Medellín', perros: 1, gatos: 2 })).toBe('/afiliacion?ciudad=Medell%C3%ADn&perros=1&gatos=2')
    expect(enlaceAfiliacion({})).toBe('/afiliacion')
  })
})

describe('Portada (R3-PUB-04)', () => {
  it('abre con el titular, los planes de la ciudad de la clínica y la afiliación a un toque', async () => {
    renderizar(<PortadaPage />)
    expect(screen.getByRole('heading', { level: 1, name: 'Tu peludito, bien cuidado.' })).toBeInTheDocument()
    const planes = await screen.findByRole('list', { name: 'Los planes' })
    expect(within(planes).getByRole('link', { name: /Colita Feliz/ })).toHaveAttribute('href', '/planes/colita-feliz')
    expect(within(planes).getByRole('link', { name: /Colita Feliz/ })).toHaveTextContent(/\$\s35\.500/)
    // Hasta que elige, la ciudad es la de la clínica de TIMU (si se vende allí).
    await waitFor(() => expect(pedidas).toContain('Medellín'))
    expect(screen.getByRole('link', { name: 'Ver mis planes' })).toHaveAttribute('href', '/afiliacion?ciudad=Medell%C3%ADn&perros=1')
    const barra = screen.getByRole('banner')
    expect(within(barra).getByRole('link', { name: 'Afiliar a mi peludo' })).toHaveAttribute('href', '/afiliacion')
    expect(within(barra).getByRole('link', { name: 'Ingresar' })).toHaveAttribute('href', '/login')
  })

  it('con la sesión abierta, «Ingresar» lleva a su espacio', async () => {
    server.use(http.get(`${API}/auth/me`, () => HttpResponse.json(USUARIO_ADMIN)))
    renderizar(<PortadaPage />)
    expect(await within(screen.getByRole('banner')).findByRole('link', { name: 'Ir a mi espacio' })).toHaveAttribute('href', '/panel')
  })

  it('«Arma tu plan» cambia el precio por peludo con la manada y lleva lo elegido a la afiliación', async () => {
    const user = userEvent.setup()
    renderizar(<PortadaPage />)
    const arma = await screen.findByRole('form', { name: 'Arma tu plan' })
    expect(await within(arma).findByText(/Tu peludo, desde/)).toHaveTextContent(/\$\s35\.500\s*al mes/)
    // Un perro es el mínimo: no se queda sin peludos.
    expect(within(arma).getByRole('button', { name: 'Un perro menos' })).toBeDisabled()
    await user.click(within(arma).getByRole('button', { name: 'Un gato más' }))
    expect(within(arma).getByText(/2 peludos, desde/)).toHaveTextContent(/\$\s30\.500\s*al mes cada uno/)
    await user.click(within(arma).getByRole('button', { name: 'Un perro menos' }))
    expect(within(arma).getByRole('button', { name: 'Un gato menos' })).toBeDisabled()
    await user.selectOptions(within(arma).getByLabelText('¿Dónde vives?'), 'Bogotá')
    await waitFor(() => expect(pedidas).toContain('Bogotá'))
    expect(within(arma).getByRole('link', { name: 'Ver mis planes' })).toHaveAttribute('href', '/afiliacion?ciudad=Bogot%C3%A1&gatos=1')
  })

  it('compara los planes lado a lado y enlaza todo lo que cubre cada uno', async () => {
    renderizar(<PortadaPage />)
    const tabla = await screen.findByRole('table', { name: 'Lo que cubre cada plan en Medellín' })
    expect(within(tabla).getByRole('row', { name: /Servicio fúnebre/ })).toHaveTextContent('igual en los 2')
    expect(screen.getByRole('link', { name: 'Todo lo que cubre Mi Amigo Fiel' })).toHaveAttribute('href', '/planes/mi-amigo-fiel')
  })

  it('pinta la red con la clínica de TIMU en su estación y los servicios aparte', async () => {
    renderizar(<PortadaPage />)
    const linea = await screen.findByRole('list', { name: 'Estaciones de la red TIMU' })
    const laureles = within(linea).getByRole('heading', { name: /Laureles/ }).closest('li')!
    expect(laureles).toHaveAttribute('data-intercambio', 'true')
    expect(within(laureles).getByText('TIMU clínica veterinaria')).toBeInTheDocument()
    expect(within(laureles).getByText('Macarena')).toBeInTheDocument()
    expect(within(linea).getByText('24 horas')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Especialistas y servicios de la red' }).parentElement).toHaveTextContent('AnesVet')
    // Sin consulta domiciliaria en ningún plan, no hay ramal a casa.
    expect(within(linea).queryByText('Tu casa')).not.toBeInTheDocument()
  })

  it('de la clínica sale el ramal a casa solo si algún plan trae consulta domiciliaria', async () => {
    const domicilio = { ...PLANES[0]!.beneficios[0]!, tipo_servicio_codigo: 'consulta_domiciliaria', nombre: 'Consulta domiciliaria' }
    server.use(http.get(`${REGISTRO}/planes`, () => HttpResponse.json([{ ...PLANES[0], beneficios: [domicilio] }, PLANES[1]])))
    renderizar(<PortadaPage />)
    const linea = await screen.findByRole('list', { name: 'Estaciones de la red TIMU' })
    expect(await within(linea).findByText(/Consulta domiciliaria en Colita Feliz/)).toBeInTheDocument()
  })

  it('dice quiénes son con lo que escribe Administración, y calla lo que falta', async () => {
    renderizar(<PortadaPage />)
    expect(await screen.findByText(DATOS.presentacion!)).toBeInTheDocument()
    expect(screen.getByText('Visión')).toBeInTheDocument()
    expect(screen.queryByText('Misión')).not.toBeInTheDocument()
    expect(within(screen.getByRole('list', { name: 'Nuestros valores' })).getAllByRole('listitem')).toHaveLength(2)
    expect(screen.getByText(/TIMU S\.A\.S\./)).toHaveTextContent('NIT 901635168-2')
  })

  it('dice si no pudo cargar los planes o la red', async () => {
    server.use(
      http.get(`${REGISTRO}/planes`, () => new HttpResponse(null, { status: 503 })),
      http.get(`${API}/aliadas/publicas`, () => new HttpResponse(null, { status: 503 })),
    )
    renderizar(<PortadaPage />)
    expect(await screen.findByText(/No pudimos cargar los planes/)).toBeInTheDocument()
    expect(await screen.findByText(/No pudimos cargar la red de aliadas/)).toBeInTheDocument()
  })

  it('en una ciudad sin planes lo dice en vez de inventar precios', async () => {
    server.use(http.get(`${REGISTRO}/planes`, () => HttpResponse.json([])))
    renderizar(<PortadaPage />)
    expect(await screen.findByText('Aún no vendemos planes en Medellín.')).toBeInTheDocument()
    expect(screen.getByText('Aún no vendemos planes en esta ciudad.')).toBeInTheDocument()
  })
})

describe('Contacto de la portada', () => {
  it('envía el mensaje con la autorización y da las gracias', async () => {
    const enviados: unknown[] = []
    server.use(
      http.post(`${API}/comercial/contacto`, async ({ request }) => {
        enviados.push(await request.json())
        return HttpResponse.json({ recibido: true }, { status: 202 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<PortadaPage />)
    const form = await screen.findByRole('form', { name: 'Déjanos un mensaje' })
    expect(await within(form).findByRole('link', { name: 'Política de tratamiento de datos' })).toHaveAttribute('href', DATOS.politica_datos_url)
    await user.type(within(form).getByLabelText('Tu nombre'), 'Paula Díaz')
    await user.type(within(form).getByLabelText('Celular'), '3005551234')
    await user.selectOptions(within(form).getByLabelText('Tu peludo es'), 'felino')
    await user.type(within(form).getByLabelText('Tu mensaje'), '¿Atienden en Envigado?')
    await user.click(within(form).getByLabelText(/Autorizo a TIMU/))
    await user.click(within(form).getByRole('button', { name: 'Enviar mensaje' }))
    expect(await screen.findByRole('heading', { name: 'Recibimos tu mensaje' })).toBeInTheDocument()
    expect(enviados).toEqual([
      { nombre: 'Paula Díaz', telefono: '3005551234', especie: 'felino', mensaje: '¿Atienden en Envigado?', acepta_datos: true, sitio_web: '' },
    ])
  })

  it('sin celular ni correo pide uno y no envía nada', async () => {
    let enviado = false
    server.use(
      http.post(`${API}/comercial/contacto`, () => {
        enviado = true
        return HttpResponse.json({ recibido: true }, { status: 202 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<PortadaPage />)
    const form = await screen.findByRole('form', { name: 'Déjanos un mensaje' })
    await user.type(within(form).getByLabelText('Tu nombre'), 'Paula')
    await user.type(within(form).getByLabelText('Tu mensaje'), 'Hola')
    await user.click(within(form).getByLabelText(/Autorizo a TIMU/))
    await user.click(within(form).getByRole('button', { name: 'Enviar mensaje' }))
    expect(within(form).getByRole('alert')).toHaveTextContent('Escribe tu celular o tu correo')
    expect(enviado).toBe(false)
  })

  it('dice el error de la API', async () => {
    server.use(http.post(`${API}/comercial/contacto`, () => HttpResponse.json({ detail: 'Telefono no valido' }, { status: 422 })))
    const user = userEvent.setup()
    renderizar(<PortadaPage />)
    const form = await screen.findByRole('form', { name: 'Déjanos un mensaje' })
    await user.type(within(form).getByLabelText('Tu nombre'), 'Paula')
    await user.type(within(form).getByLabelText('Correo'), 'paula@correo.co')
    await user.type(within(form).getByLabelText('Tu mensaje'), 'Hola')
    await user.click(within(form).getByLabelText(/Autorizo a TIMU/))
    await user.click(within(form).getByRole('button', { name: 'Enviar mensaje' }))
    expect(await within(form).findByRole('alert')).toHaveTextContent('Telefono no valido')
  })
})

describe('Página de un plan', () => {
  function abrir(ruta: string) {
    renderizar(
      <Routes>
        <Route path="/planes/:plan" element={<PlanPage />} />
      </Routes>,
      { ruta },
    )
  }

  it('dice todo lo que cubre, los adicionales, lo que paga por peludos y sus condiciones', async () => {
    abrir('/planes/mi-amigo-fiel')
    expect(await screen.findByRole('heading', { level: 1, name: 'Mi Amigo Fiel' })).toBeInTheDocument()
    expect(within(screen.getByRole('list', { name: 'Los servicios de Mi Amigo Fiel' })).getAllByRole('listitem').map((l) => l.textContent)).toEqual(['Cirugía'])
    const cubre = screen.getByRole('heading', { name: 'Lo que cubre' }).parentElement!
    expect(cubre).toHaveTextContent('Cirugía')
    expect(cubre).toHaveTextContent('Desde los 30 días. Con anestesia.')
    const ademas = screen.getByRole('heading', { name: 'Además' }).parentElement!
    expect(ademas).toHaveTextContent('Servicio fúnebre')
    expect(ademas).toHaveTextContent('Desde los 30 días. Traslado las 24 horas.')
    const pagas = screen.getByRole('heading', { name: 'Lo que pagas' }).parentElement!
    expect(pagas).toHaveTextContent(/2 peludos\s*\$\s61\.000 al mes cada uno/)
    expect(pagas).toHaveTextContent(/4 o más peludos/)
    expect(pagas).toHaveTextContent(/3 meses/)
    expect(screen.getByText('Sin periodo de carencia.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Afiliar a mi peludo con Mi Amigo Fiel' })).toHaveAttribute(
      'href',
      '/afiliacion?ciudad=Medell%C3%ADn&plan=id-mi_amigo_fiel',
    )
  })

  it('cambia de ciudad y pide sus precios', async () => {
    const user = userEvent.setup()
    abrir('/planes/colita-feliz')
    await screen.findByRole('heading', { level: 1, name: 'Colita Feliz' })
    await user.selectOptions(screen.getByLabelText('Ciudad'), 'Bogotá')
    await waitFor(() => expect(pedidas).toContain('Bogotá'))
  })

  it('un plan que no se vende lo dice y lleva a los planes', async () => {
    abrir('/planes/plan-viejo')
    expect(await screen.findByRole('heading', { name: 'Este plan no está a la venta en Medellín' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Mira los planes de TIMU' })).toHaveAttribute('href', '/#planes')
  })

  it('dice si no pudo cargar el plan', async () => {
    server.use(http.get(`${REGISTRO}/planes`, () => new HttpResponse(null, { status: 503 })))
    abrir('/planes/colita-feliz')
    expect(await screen.findByText(/No pudimos cargar el plan/)).toBeInTheDocument()
  })
})
