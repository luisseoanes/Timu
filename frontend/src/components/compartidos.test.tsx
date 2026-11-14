import { useQuery } from '@tanstack/react-query'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it, vi } from 'vitest'

import { api } from '@/api/client'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

import { Consulta } from './Consulta'
import { Distintivo, Insignia } from './Distintivo'
import { Paginacion } from './Paginacion'
import { Pestanas } from './Pestanas'

function Lista() {
  const consulta = useQuery({
    queryKey: ['prueba'],
    queryFn: async () => (await api.get<string[]>('/prueba')).data,
  })
  return (
    <Consulta
      consulta={consulta}
      cargando="Cargando elementos…"
      error="No fue posible cargar los elementos."
      vacio="Todavía no hay elementos."
      estaVacio={(d) => d.length === 0}
    >
      {(datos) => <ul>{datos.map((d) => <li key={d}>{d}</li>)}</ul>}
    </Consulta>
  )
}

describe('Consulta', () => {
  it('muestra la carga y luego los datos', async () => {
    server.use(http.get('*/api/v1/prueba', () => HttpResponse.json(['uno'])))
    renderizar(<Lista />)
    expect(screen.getByText('Cargando elementos…')).toBeInTheDocument()
    expect(await screen.findByText('uno')).toBeInTheDocument()
  })

  it('explica por qué está vacío', async () => {
    server.use(http.get('*/api/v1/prueba', () => HttpResponse.json([])))
    renderizar(<Lista />)
    expect(await screen.findByText('Todavía no hay elementos.')).toBeInTheDocument()
  })

  it('ante un fallo pasajero ofrece reintentar y vuelve a pedir', async () => {
    let pedidos = 0
    server.use(
      http.get('*/api/v1/prueba', () => {
        pedidos += 1
        return pedidos === 1 ? HttpResponse.json({}, { status: 503 }) : HttpResponse.json(['uno'])
      }),
    )
    renderizar(<Lista />)
    const user = userEvent.setup()
    await user.click(await screen.findByRole('button', { name: 'Reintentar' }))
    expect(await screen.findByText('uno')).toBeInTheDocument()
    expect(pedidos).toBe(2)
  })

  it('ante un error firme no ofrece reintentar', async () => {
    server.use(http.get('*/api/v1/prueba', () => HttpResponse.json({ detail: 'Sin permiso' }, { status: 403 })))
    renderizar(<Lista />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Sin permiso')
    expect(screen.queryByRole('button', { name: 'Reintentar' })).not.toBeInTheDocument()
  })

  it('anuncia la carga a los lectores de pantalla', () => {
    server.use(http.get('*/api/v1/prueba', () => new Promise(() => {})))
    renderizar(<Lista />)
    expect(screen.getByRole('status')).toHaveTextContent('Cargando elementos…')
  })

  it('muestra el error con la causa que da el servidor', async () => {
    server.use(
      http.get('*/api/v1/prueba', () =>
        HttpResponse.json({ detail: 'La ciudad no existe' }, { status: 422 }),
      ),
    )
    renderizar(<Lista />)
    const alerta = await screen.findByRole('alert')
    expect(alerta).toHaveTextContent('No fue posible cargar los elementos. La ciudad no existe')
  })
})

describe('Distintivo', () => {
  it('lleva texto además del tono', () => {
    renderizar(<Distintivo dominio="afiliacion" valor="en_mora" />)
    expect(screen.getByText('En mora')).toHaveClass('distintivo-alerta')
  })

  it('cada tono tiene su propio icono, para que el estado no dependa solo del color', () => {
    const tonos = ['ok', 'alerta', 'info', 'peligro', 'neutro'] as const
    renderizar(
      <>
        {tonos.map((tono) => (
          <Insignia key={tono} tono={tono}>
            {tono}
          </Insignia>
        ))}
      </>,
    )
    const trazos = tonos.map((tono) => {
      const insignia = screen.getByText(tono)
      const icono = insignia.querySelector('svg')
      // El icono acompaña, no se anuncia: el significado lo lleva el texto.
      expect(icono).toHaveAttribute('aria-hidden', 'true')
      return icono?.innerHTML
    })
    expect(new Set(trazos).size).toBe(tonos.length)
  })

  it('los estados del camino normal comparten tono pero no icono', () => {
    const estados = ['agendado', 'en_ruta', 'en_atencion'] as const
    renderizar(
      <>
        {estados.map((e) => (
          <Distintivo key={e} dominio="servicio" valor={e} />
        ))}
      </>,
    )
    const insignias = ['Agendado', 'En ruta', 'En atención'].map((t) => screen.getByText(t))
    for (const i of insignias) expect(i).toHaveClass('distintivo-info')
    expect(new Set(insignias.map((i) => i.querySelector('svg')?.innerHTML)).size).toBe(3)
  })

  it('una prioridad alta no lleva la × de lo cancelado', () => {
    renderizar(
      <>
        <Distintivo dominio="prioridad" valor="alta" />
        <Distintivo dominio="servicio" valor="cancelado" />
      </>,
    )
    const [alta, cancelado] = [screen.getByText('Alta'), screen.getByText('Cancelado')]
    expect(alta).toHaveClass('distintivo-peligro')
    expect(alta.querySelector('svg')?.innerHTML).not.toBe(cancelado.querySelector('svg')?.innerHTML)
  })
})

describe('Pestanas', () => {
  it('cambia de sección con el teclado o el clic', async () => {
    renderizar(
      <Pestanas
        etiqueta="Secciones"
        pestanas={[
          { valor: 'a', titulo: 'Datos', contenido: <p>Contenido A</p> },
          { valor: 'b', titulo: 'Pagos', contenido: <p>Contenido B</p> },
        ]}
      />,
    )
    expect(screen.getByText('Contenido A')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('tab', { name: 'Pagos' }))
    await waitFor(() => expect(screen.getByText('Contenido B')).toBeVisible())
  })
})

describe('Paginacion', () => {
  it('no aparece si todo cabe en una página', () => {
    const { container } = renderizar(<Paginacion total={5} limit={50} offset={0} onCambio={() => {}} />)
    expect(container.querySelector('nav')).toBeNull()
  })

  it('avanza y no deja ir antes del inicio', async () => {
    const onCambio = vi.fn()
    renderizar(<Paginacion total={120} limit={50} offset={0} onCambio={onCambio} />)
    expect(screen.getByText('1–50 de 120')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled()
    await userEvent.click(screen.getByRole('button', { name: 'Siguiente' }))
    expect(onCambio).toHaveBeenCalledWith(50)
  })
})
