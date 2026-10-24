import { useQuery } from '@tanstack/react-query'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it, vi } from 'vitest'

import { api } from '@/api/client'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

import { Consulta } from './Consulta'
import { Distintivo } from './Distintivo'
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
