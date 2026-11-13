import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes, useLocation } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { FamiliaDetallePage } from './FamiliaDetallePage'
import { FamiliasPage } from './FamiliasPage'
import { FAMILIA } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { EstacionRead, LineaFamiliaRead } from '@/types'

/** Fecha ISO a `dias` de hoy: la línea sitúa «hoy» con el reloj del navegador. */
function dentroDe(dias: number): string {
  const d = new Date()
  d.setDate(d.getDate() + dias)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

let n = 0
function estacion(dias: number, estado: EstacionRead['estado'], titulo: string, extra: Partial<EstacionRead> = {}): EstacionRead {
  n += 1
  return { tipo: 'cuota', referencia_id: `e${n}`, fecha: dentroDe(dias), estado, titulo, mascota: null, mascota_id: null, ...extra }
}

const LINEA: LineaFamiliaRead = {
  familia_id: FAMILIA.id,
  planes: [{ plan_id: 'p1', nombre: 'Mi Amigo Fiel', color: 'verde', mascotas: ['Luna'] }],
  estaciones: [
    estacion(-150, 'hecha', 'Cuota de junio'),
    estacion(-120, 'hecha', 'Cuota de julio'),
    estacion(-90, 'hecha', 'Cuota de agosto'),
    estacion(-60, 'vencida', 'Cuota de septiembre'),
    estacion(-30, 'hecha', 'Cuota de octubre'),
    estacion(10, 'proxima', 'Cuota de diciembre'),
    estacion(40, 'futura', 'Vacuna', { tipo: 'preventivo', mascota: 'Luna' }),
  ],
}

const conLinea = () =>
  server.use(
    http.get('*/api/v1/afiliaciones/lineas', () => HttpResponse.json([LINEA])),
    http.get('*/api/v1/familias/:id/linea', () => HttpResponse.json(LINEA)),
  )

function Ubicacion() {
  return <p data-testid="ubicacion">{useLocation().pathname}</p>
}

function abrirFicha() {
  return renderizar(
    <Routes>
      <Route path="/familias/:id" element={<FamiliaDetallePage />} />
      <Route path="/servicios/:id" element={<Ubicacion />} />
    </Routes>,
    { ruta: `/familias/${FAMILIA.id}` },
  )
}

describe('Familias con la línea de metro', () => {
  it('cada fila muestra el plan con su color y resume la línea', async () => {
    conLinea()
    renderizar(<FamiliasPage />)
    const fila = (await screen.findByRole('link', { name: FAMILIA.titular_nombre })).closest('li')!
    expect(await within(fila).findByText('Mi Amigo Fiel')).toBeInTheDocument()
    expect(fila.querySelector('.marcador-plan')).toHaveAttribute('data-color', 'verde')
    expect(within(fila).getByRole('img')).toHaveAccessibleName(/^1 vencida, próxima: Cuota de diciembre el /)
    // Lo vencido se lee también sin distinguir el rojo del punto.
    expect(within(fila).getByText('1 vencida')).toBeInTheDocument()
  })

  it('una familia sin plan dibuja su línea en gris, no con el color de un plan', async () => {
    server.use(http.get('*/api/v1/afiliaciones/lineas', () => HttpResponse.json([{ ...LINEA, planes: [] }])))
    renderizar(<FamiliasPage />)
    const fila = (await screen.findByRole('link', { name: FAMILIA.titular_nombre })).closest('li')!
    await waitFor(() => expect(fila.querySelector('.linea-mini')).toHaveAttribute('data-color', 'ninguno'))
  })

  it('bajo la línea quedan a la vista las mascotas con su plan y la cartera', async () => {
    conLinea()
    abrirFicha()
    const mascotas = await screen.findByRole('region', { name: 'Mascotas' })
    expect(within(mascotas).getByText('Luna')).toBeInTheDocument()
    // La especie con su nombre del catálogo, no con el código.
    expect(await within(mascotas).findByText(/^Perro/)).toBeInTheDocument()
    expect(within(mascotas).getByText('Mi Amigo Fiel')).toBeInTheDocument()
    expect(await screen.findByRole('region', { name: 'Cartera' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Datos' })).toHaveAttribute('aria-selected', 'true')
  })

  it('un servicio de la línea se atiende en su propia ficha', async () => {
    server.use(
      http.get('*/api/v1/familias/:id/linea', () =>
        HttpResponse.json({
          ...LINEA,
          estaciones: [estacion(5, 'proxima', 'Consulta', { tipo: 'servicio', referencia_id: 's9', mascota: 'Luna' })],
        }),
      ),
    )
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('button', { name: 'Abrir consulta de Luna' }))
    expect(await screen.findByTestId('ubicacion')).toHaveTextContent('/servicios/s9')
  })

  it('sin familia abierta explica qué aparecerá al elegir una', async () => {
    renderizar(<FamiliasPage />)
    expect(await screen.findByText(/Elige una familia para ver su línea/)).toBeInTheDocument()
  })

  it('el enlace a la familia conserva la búsqueda del listado', async () => {
    renderizar(
      <Routes>
        <Route path="/familias" element={<FamiliasPage />} />
      </Routes>,
      { ruta: '/familias?q=Ana' },
    )
    expect(await screen.findByRole('link', { name: FAMILIA.titular_nombre })).toHaveAttribute(
      'href',
      `/familias/${FAMILIA.id}?q=Ana`,
    )
  })

  it('la acción principal lleva a donde se atiende lo próximo', async () => {
    conLinea()
    const user = userEvent.setup()
    abrirFicha()
    await user.click(await screen.findByRole('button', { name: 'Ver cuota de diciembre' }))
    expect(screen.getByRole('tab', { name: 'Cartera' })).toHaveAttribute('aria-selected', 'true')
  })

  it('activar una estación abre su sección', async () => {
    conLinea()
    const user = userEvent.setup()
    abrirFicha()
    const linea = await screen.findByRole('list', { name: 'Línea de la familia' })
    await user.click(within(linea).getByRole('button', { name: /^Vacuna de Luna, programada, / }))
    expect(screen.getByRole('tab', { name: 'Mascotas' })).toHaveAttribute('aria-selected', 'true')
  })

  it('marca hoy, rotula lo vencido y pliega las hechas antiguas hasta que se piden', async () => {
    conLinea()
    const user = userEvent.setup()
    abrirFicha()
    const linea = await screen.findByRole('list', { name: 'Línea de la familia' })
    expect(within(linea).getByText('Hoy').closest('li')).toHaveAttribute('aria-current', 'date')
    expect(within(linea).getByRole('button', { name: /^Cuota de septiembre, vencida/ })).toBeInTheDocument()
    // Tres hechas antes de hoy: se pliegan las dos más antiguas y queda la de octubre.
    expect(within(linea).queryByRole('button', { name: /^Cuota de junio/ })).not.toBeInTheDocument()
    await user.click(within(linea).getByRole('button', { name: '3 hechas' }))
    await waitFor(() => expect(within(linea).getByRole('button', { name: /^Cuota de junio, hecha/ })).toBeInTheDocument())
  })

  it('una familia sin nada en la ventana lo dice en vez de dibujar una línea vacía', async () => {
    abrirFicha()
    expect(await screen.findByText(/Sin cuotas, preventivos ni servicios/)).toBeInTheDocument()
  })
})

describe('parada con varios eventos el mismo día', () => {
  it('rotula la primera y cuántas más, y el botón las nombra todas', async () => {
    server.use(
      http.get('*/api/v1/familias/:id/linea', () =>
        HttpResponse.json({
          ...LINEA,
          estaciones: [
            estacion(20, 'proxima', 'Vacuna', { tipo: 'preventivo', mascota: 'Luna' }),
            estacion(20, 'futura', 'Desparasitación interna', { tipo: 'preventivo', mascota: 'Luna' }),
            estacion(20, 'futura', 'Vacuna', { tipo: 'preventivo', mascota: 'Kira' }),
          ],
        }),
      ),
    )
    abrirFicha()
    const linea = await screen.findByRole('list', { name: 'Línea de la familia' })
    expect(within(linea).getByText('Vacuna y 2 más')).toBeInTheDocument()
    expect(
      within(linea).getByRole('button', {
        name: /^Vacuna de Luna y Desparasitación interna de Luna y Vacuna de Kira, próxima, /,
      }),
    ).toBeInTheDocument()
  })
})
