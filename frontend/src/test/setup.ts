import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterAll, afterEach, beforeAll, expect } from 'vitest'

import { server } from './server'

// La API se simula con MSW a nivel de red, no haciendo mock de axios: así se
// prueba también que el cliente arma bien la petición.
//
// Una petición sin handler hace FALLAR la prueba. Con `onUnhandledRequest: 'error'` MSW
// solo imprime un aviso y la prueba sigue en verde aunque la pantalla haya recibido un
// error de red que nadie simuló: la prueba deja de describir lo que de verdad pasó.
const sinHandler: string[] = []

beforeAll(() =>
  server.listen({
    onUnhandledRequest(peticion, imprimir) {
      sinHandler.push(`${peticion.method} ${new URL(peticion.url).pathname}`)
      imprimir.error()
    },
  }),
)
afterEach(() => {
  // Primero se desmonta: así ninguna consulta en vuelo llega cuando ya no hay handlers.
  cleanup()
  server.resetHandlers()
  const pendientes = sinHandler.splice(0)
  expect(pendientes, 'peticiones sin handler de MSW: simúlalas en la prueba o en src/test/handlers.ts').toEqual([])
})
afterAll(() => server.close())
