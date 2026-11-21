import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { MiClinicaPage } from './MiClinicaPage'
import { USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { AtendidasAliada, RemisionVistaAliada } from '@/types'

const API = '*/api/v1'

const VISTA: RemisionVistaAliada = {
  codigo: 'REM7K2Q',
  estado: 'emitida',
  vigente: true,
  vencida: false,
  vence_en: '2026-12-16',
  emitida_en: '2026-11-10',
  atencion_desde: '2026-11-10',
  atencion_hasta: '2026-11-16',
  reportar_hasta: '2026-12-23',
  titular: 'Jorge Ramírez',
  documento_ultimos: '6123',
  mascota: { nombre: 'Rocky', especie: 'canino', especie_nombre: 'Canino', raza: 'Labrador' },
  motivo: 'Radiografía de cadera por cojera',
  beneficio: 'Radiografía',
  cobertura_pct: 80,
  tope_cubierto: '200000.00',
  fecha_atencion: null,
  valor_atencion: null,
  valor_cubierto: null,
  valor_familia: null,
}

const ATENDIDAS: AtendidasAliada = {
  desde: '2026-11-01',
  hasta: '2026-11-30',
  atenciones: 1,
  valor_atenciones: '180000.00',
  valor_cubierto: '144000.00',
  valor_familias: '36000.00',
  items: [
    {
      codigo: 'HEYQCXQH',
      fecha_atencion: '2026-11-04',
      titular: 'Claudia Rincón',
      mascota: 'Mia',
      motivo: 'Limpieza dental bajo anestesia',
      beneficio: 'Odontología',
      valor_atencion: '180000.00',
      valor_cubierto: '144000.00',
      valor_familia: '36000.00',
    },
  ],
}

const VACIO: AtendidasAliada = { ...ATENDIDAS, atenciones: 0, valor_atenciones: '0', valor_cubierto: '0', valor_familias: '0', items: [] }

let periodos: string[] = []

beforeEach(() => {
  // Los meses del selector salen de hoy: se fija la fecha (solo Date, para no frenar MSW).
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date('2026-11-16T15:00:00Z'))
  periodos = []
  server.use(
    http.get(`${API}/auth/me`, () =>
      HttpResponse.json({ ...USUARIO_ADMIN, rol: 'aliada', nombre: 'Recepción Clínica del Norte' }),
    ),
    http.get(`${API}/aliadas/mi-clinica`, () => HttpResponse.json({ nombre: 'Clínica Veterinaria del Norte', ciudad: 'Medellín' })),
    http.get(`${API}/aliadas/mi-clinica/atendidas`, ({ request }) => {
      const url = new URL(request.url)
      periodos.push(`${url.searchParams.get('desde')}..${url.searchParams.get('hasta')}`)
      return HttpResponse.json(url.searchParams.get('desde') === '2026-11-01' ? ATENDIDAS : VACIO)
    }),
  )
})

afterEach(() => {
  vi.useRealTimers()
})

async function validar(codigo: string) {
  const user = userEvent.setup()
  renderizar(<MiClinicaPage />)
  await user.type(screen.getByLabelText('Código de la remisión'), codigo)
  await user.click(screen.getByRole('button', { name: 'Validar' }))
  return user
}

describe('MiClinicaPage', () => {
  it('dice en qué clínica se está y quién ingresó', async () => {
    const user = userEvent.setup()
    renderizar(<MiClinicaPage />)
    expect(await screen.findByText('Clínica Veterinaria del Norte')).toBeInTheDocument()
    await user.click(await screen.findByRole('button', { name: 'RC, cuenta de Recepción Clínica del Norte' }))
    expect(await screen.findByText('Clínica Veterinaria del Norte · Medellín')).toBeInTheDocument()
  })

  it('valida el código y muestra a quién se atiende y qué cubre, con un solo verde', async () => {
    let pedido = ''
    server.use(
      http.get(`${API}/aliadas/mi-clinica/remisiones/:codigo`, ({ params }) => {
        pedido = String(params.codigo)
        return HttpResponse.json(VISTA)
      }),
    )
    renderizar(<MiClinicaPage />)
    // Sin remisión abierta, validar es la acción principal.
    expect(screen.getByRole('button', { name: 'Validar' })).toHaveClass('btn-primario')

    const user = userEvent.setup()
    await user.type(screen.getByLabelText('Código de la remisión'), ' rem7k2q ')
    await user.click(screen.getByRole('button', { name: 'Validar' }))

    expect(await screen.findByText('Se puede atender hasta el 16 dic.')).toBeInTheDocument()
    expect(pedido).toBe('REM7K2Q')
    expect(screen.getByText('Por usar')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Rocky · Canino, Labrador' })).toBeInTheDocument()
    expect(screen.getByText(/Jorge Ramírez,/)).toHaveTextContent('Jorge Ramírez, documento terminado en 6123')
    expect(screen.getByText(/80 % hasta \$\s200\.000/)).toBeInTheDocument()
    // Con una que se puede usar, el verde pasa a reportar.
    expect(screen.getByRole('button', { name: 'Validar' })).toHaveClass('btn-secundario')
    expect(screen.getByRole('button', { name: 'Reportar atención' })).toHaveClass('btn-primario')
    expect(document.querySelectorAll('.btn-primario')).toHaveLength(1)
    // La fecha se puede reportar solo entre lo que dice la API.
    const fecha = screen.getByLabelText('Fecha de la atención')
    expect(fecha).toHaveAttribute('min', '2026-11-10')
    expect(fecha).toHaveAttribute('max', '2026-11-16')
    expect(fecha).toHaveValue('2026-11-16')
  })

  it('pide a la API lo que cubre TIMU antes de reportar y reporta lo escrito', async () => {
    let reporte: unknown = null
    const valores: string[] = []
    server.use(
      http.get(`${API}/aliadas/mi-clinica/remisiones/REM7K2Q`, () => HttpResponse.json(VISTA)),
      http.get(`${API}/aliadas/mi-clinica/remisiones/REM7K2Q/cobertura`, ({ request }) => {
        const valor = new URL(request.url).searchParams.get('valor_atencion') ?? ''
        valores.push(valor)
        const tope = Number(valor) * 0.8 > 200000
        return HttpResponse.json({
          valor_atencion: `${valor}.00`,
          valor_cubierto: tope ? '200000.00' : `${Number(valor) * 0.8}.00`,
          valor_familia: tope ? `${Number(valor) - 200000}.00` : `${Number(valor) * 0.2}.00`,
          con_tope: tope,
        })
      }),
      http.post(`${API}/aliadas/mi-clinica/remisiones/REM7K2Q/atencion`, async ({ request }) => {
        reporte = await request.json()
        return HttpResponse.json({
          ...VISTA,
          estado: 'utilizada',
          vigente: false,
          atencion_desde: null,
          atencion_hasta: null,
          fecha_atencion: '2026-11-16',
          valor_atencion: '320000.00',
          valor_cubierto: '200000.00',
          valor_familia: '120000.00',
        })
      }),
    )
    const user = await validar('REM7K2Q')
    const campo = await screen.findByLabelText('Valor de la atención')
    expect(screen.getByText(/Escribe el valor para ver cuánto cubre TIMU/)).toBeInTheDocument()
    // Sin valor, la validación del navegador lo pide, como la fecha y el resumen.
    expect(campo).toBeRequired()

    await user.type(campo, '$320.000')
    expect(campo).toHaveValue('$ 320.000')
    const reparto = await screen.findByText('Paga la familia')
    expect(reparto.closest('dl')).toHaveTextContent(/TIMU cubre\s*\$\s200\.000/)
    expect(reparto.closest('dl')).toHaveTextContent(/Paga la familia\s*\$\s120\.000/)
    expect(screen.getByText(/Llega al tope de \$\s200\.000/)).toBeInTheDocument()
    // Se pide tras una pausa al escribir, no una vez por tecla.
    expect(valores.at(-1)).toBe('320000')
    expect(valores.length).toBeLessThan(6)

    await user.type(screen.getByLabelText('Resumen clínico'), 'Rx de cadera sin hallazgos')
    await user.click(screen.getByRole('button', { name: 'Reportar atención' }))

    expect(await screen.findByText('Atendida')).toBeInTheDocument()
    expect(reporte).toEqual({ fecha: '2026-11-16', valor_atencion: '320000', resumen: 'Rx de cadera sin hallazgos' })
    const reportado = screen.getByRole('region', { name: 'Lo que se reportó' })
    expect(reportado).toHaveTextContent(/Valor de la atención\s*\$\s320\.000/)
    expect(reportado).toHaveTextContent(/TIMU cubrió\s*\$\s200\.000/)
    expect(reportado).toHaveTextContent(/Pagó la familia\s*\$\s120\.000/)
    // El mostrador queda listo para la siguiente familia.
    expect(screen.getByLabelText('Código de la remisión')).toHaveValue('')
    expect(screen.getByLabelText('Código de la remisión')).toHaveFocus()
    expect(screen.queryByRole('button', { name: 'Reportar atención' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Validar' })).toHaveClass('btn-primario')
    // Lo atendido del mes se recarga para sumarla.
    await waitFor(() => expect(periodos.filter((p) => p === '2026-11-01..2026-11-30').length).toBeGreaterThan(1))
  })

  it('dice el error del servidor al reportar sin cerrar el formulario', async () => {
    server.use(
      http.get(`${API}/aliadas/mi-clinica/remisiones/REM7K2Q`, () => HttpResponse.json(VISTA)),
      http.get(`${API}/aliadas/mi-clinica/remisiones/REM7K2Q/cobertura`, () =>
        HttpResponse.json({ valor_atencion: '1000.00', valor_cubierto: '800.00', valor_familia: '200.00', con_tope: false }),
      ),
      http.post(`${API}/aliadas/mi-clinica/remisiones/REM7K2Q/atencion`, () =>
        HttpResponse.json({ detail: 'La atencion esta fuera de la vigencia de la remision' }, { status: 422 }),
      ),
    )
    const user = await validar('REM7K2Q')
    await user.type(await screen.findByLabelText('Valor de la atención'), '1000')
    await user.type(screen.getByLabelText('Resumen clínico'), 'Consulta general')
    await user.click(screen.getByRole('button', { name: 'Reportar atención' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('fuera de la vigencia')
    expect(screen.getByRole('button', { name: 'Reportar atención' })).toBeEnabled()
  })

  it('una remisión vencida dice cuándo venció y solo deja reportar lo atendido hasta ese día, a propósito', async () => {
    let reporte: unknown = null
    const vencida = {
      ...VISTA,
      codigo: 'KXKQNX86',
      vigente: false,
      vencida: true,
      vence_en: '2026-11-06',
      emitida_en: '2026-10-07',
      atencion_desde: '2026-10-07',
      atencion_hasta: '2026-11-06',
      reportar_hasta: '2026-11-13',
    }
    server.use(
      http.get(`${API}/aliadas/mi-clinica/remisiones/:codigo`, () => HttpResponse.json(vencida)),
      http.get(`${API}/aliadas/mi-clinica/remisiones/KXKQNX86/cobertura`, () =>
        HttpResponse.json({ valor_atencion: '1000.00', valor_cubierto: '800.00', valor_familia: '200.00', con_tope: false }),
      ),
      http.post(`${API}/aliadas/mi-clinica/remisiones/KXKQNX86/atencion`, async ({ request }) => {
        reporte = await request.json()
        return HttpResponse.json({
          ...vencida,
          estado: 'utilizada',
          vencida: false,
          atencion_desde: null,
          atencion_hasta: null,
          fecha_atencion: '2026-11-06',
          valor_atencion: '1000.00',
          valor_cubierto: '800.00',
          valor_familia: '200.00',
        })
      }),
    )
    const user = await validar('KXKQNX86')
    expect(await screen.findByText(/Venció el 6 nov y ya no se puede usar para atender/)).toBeInTheDocument()
    expect(screen.getByText(/se puede reportar hasta el 13 nov/)).toBeInTheDocument()
    expect(screen.getByText('Vencida')).toBeInTheDocument()
    // El formulario no queda abierto: lo normal ante una vencida es no atender.
    expect(screen.queryByLabelText('Valor de la atención')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Validar' })).toHaveClass('btn-primario')

    await user.click(screen.getByRole('button', { name: 'Reportar una atención hecha hasta el 6 nov' }))
    const fecha = screen.getByLabelText('Fecha de la atención')
    expect(fecha).toHaveFocus()
    expect(fecha).toHaveAttribute('min', '2026-10-07')
    expect(fecha).toHaveAttribute('max', '2026-11-06')
    // «Validar» sigue siendo el único verde.
    expect(screen.getByRole('button', { name: 'Reportar atención' })).toHaveClass('btn-secundario')
    expect(document.querySelectorAll('.btn-primario')).toHaveLength(1)

    await user.type(screen.getByLabelText('Valor de la atención'), '1000')
    await user.type(screen.getByLabelText('Resumen clínico'), 'Rx de tórax el 5 de noviembre')
    await user.click(screen.getByRole('button', { name: 'Reportar atención' }))
    expect(await screen.findByText('Atendida')).toBeInTheDocument()
    expect(reporte).toMatchObject({ fecha: '2026-11-06', valor_atencion: '1000' })
  })

  it('una remisión que venció sin usarse y pasó el plazo ya no deja reportar', async () => {
    server.use(
      http.get(`${API}/aliadas/mi-clinica/remisiones/:codigo`, () =>
        HttpResponse.json({
          ...VISTA,
          estado: 'vencida',
          vigente: false,
          vencida: true,
          vence_en: '2026-10-06',
          atencion_desde: null,
          atencion_hasta: null,
          reportar_hasta: null,
        }),
      ),
    )
    await validar('NKENX8LM')
    expect(await screen.findByText(/Venció el 6 oct sin usarse y ya pasó el plazo para reportar/)).toBeInTheDocument()
    expect(screen.queryByText(/se puede reportar hasta/)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Reportar una atención/ })).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Valor de la atención')).not.toBeInTheDocument()
  })

  it('una remisión anulada lo dice', async () => {
    server.use(
      http.get(`${API}/aliadas/mi-clinica/remisiones/:codigo`, () =>
        HttpResponse.json({ ...VISTA, estado: 'anulada', vigente: false, atencion_desde: null, atencion_hasta: null }),
      ),
    )
    await validar('NKENX8LM')
    expect(await screen.findByText('TIMU la anuló y ya no se puede usar.')).toBeInTheDocument()
    expect(screen.queryByLabelText('Valor de la atención')).not.toBeInTheDocument()
  })

  it('un código que no es de la clínica se dice con qué revisar', async () => {
    server.use(
      http.get(`${API}/aliadas/mi-clinica/remisiones/:codigo`, () => HttpResponse.json({ detail: 'Remision no encontrada' }, { status: 404 })),
    )
    await validar('noexiste')
    const alerta = await screen.findByRole('alert')
    expect(alerta).toHaveTextContent('No encontramos la remisión NOEXISTE en esta clínica')
    expect(within(alerta).queryByRole('button', { name: 'Reintentar' })).not.toBeInTheDocument()
  })

  it('ofrece reintentar si el servidor no respondió', async () => {
    let intentos = 0
    server.use(
      http.get(`${API}/aliadas/mi-clinica/remisiones/:codigo`, () => {
        intentos += 1
        return intentos === 1 ? new HttpResponse(null, { status: 503 }) : HttpResponse.json(VISTA)
      }),
    )
    const user = await validar('REM7K2Q')
    const alerta = await screen.findByRole('alert')
    expect(alerta).toHaveTextContent('No pudimos validar la remisión')
    await user.click(within(alerta).getByRole('button', { name: 'Reintentar' }))
    expect(await screen.findByText('Se puede atender hasta el 16 dic.')).toBeInTheDocument()
  })

  it('suma lo atendido del mes y deja ver un mes anterior', async () => {
    const user = userEvent.setup()
    renderizar(<MiClinicaPage />)
    const panel = await screen.findByRole('region', { name: 'Atendidas' })
    expect(await within(panel).findByText('Claudia Rincón · Mia')).toBeInTheDocument()
    const cifras = within(panel).getByText('TIMU cubrió').closest('dl')
    expect(cifras).toHaveTextContent(/TIMU cubrió\s*\$\s144\.000/)
    expect(cifras).toHaveTextContent(/Facturado\s*\$\s180\.000/)
    expect(within(panel).getByText(/HEYQCXQH/)).toBeInTheDocument()

    const mes = within(panel).getByRole('combobox', { name: 'Mes' })
    expect(mes).toHaveValue('2026-11')
    expect(within(mes).getAllByRole('option')).toHaveLength(13)
    await user.selectOptions(mes, '2026-10')
    expect(await within(panel).findByText('No se reportaron atenciones en octubre de 2026.')).toBeInTheDocument()
    expect(periodos).toContain('2026-10-01..2026-10-31')
  })

  it('un mes en curso sin atenciones dice qué va a aparecer', async () => {
    server.use(http.get(`${API}/aliadas/mi-clinica/atendidas`, () => HttpResponse.json(VACIO)))
    renderizar(<MiClinicaPage />)
    expect(await screen.findByText(/Todavía no hay atenciones reportadas este mes/)).toBeInTheDocument()
    // Cuatro ceros no dicen más que la frase.
    expect(screen.queryByText('Facturado')).not.toBeInTheDocument()
  })
})
