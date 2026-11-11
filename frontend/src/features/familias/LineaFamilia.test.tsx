import { screen, waitFor, within } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

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
  return { tipo: 'cuota', referencia_id: `e${n}`, fecha: dentroDe(dias), estado, titulo, mascota: null, ...extra }
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
  )

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
})
