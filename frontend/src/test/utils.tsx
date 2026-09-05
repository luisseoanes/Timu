import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import type { ReactElement, ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'

import { AuthProvider } from '@/features/auth/AuthContext'

/** Cliente nuevo por prueba y sin reintentos: una prueba no debe esperar backoff. */
export function crearQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 }, mutations: { retry: false } },
  })
}

export function envolver(ui: ReactNode, { ruta = '/' } = {}) {
  return (
    <QueryClientProvider client={crearQueryClient()}>
      <MemoryRouter initialEntries={[ruta]}>
        <AuthProvider>{ui}</AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

export function renderizar(ui: ReactElement, opciones?: { ruta?: string }) {
  return render(envolver(ui, opciones))
}
