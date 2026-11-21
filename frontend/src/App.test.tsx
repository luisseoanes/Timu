import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import App from './App'
import { sesionDe } from '@/test/handlers'
import { server } from '@/test/server'

// El paquete va partido (auditoría de R4-CIE-02): cada módulo del panel carga al abrirse, dentro de su
// layout, que no desaparece mientras llega.
describe('App', () => {
  afterEach(() => window.history.pushState({}, '', '/'))

  it('una pantalla del panel carga al abrirse, con la barra del panel ya a la vista', async () => {
    server.use(sesionDe('atencion_cliente'))
    window.history.pushState({}, '', '/panel/tareas')
    render(<App />)
    expect(await screen.findByRole('heading', { level: 1, name: 'Tareas' })).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: 'Módulos' })).toBeInTheDocument()
    expect(await screen.findByRole('heading', { level: 2, name: 'Tareas' })).toBeInTheDocument()
  })

})
