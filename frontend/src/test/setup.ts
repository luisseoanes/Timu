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
// Peticiones que salieron y aún no tienen respuesta.
const enVuelo = new Set<string>()
server.events.on('request:start', ({ requestId }) => enVuelo.add(requestId))
server.events.on('request:end', ({ requestId }) => enVuelo.delete(requestId))

/** Deja salir lo que ya estaba saliendo y espera sus respuestas, con un tope. */
async function esperarRed(topeMs = 2000) {
  const fin = Date.now() + topeMs
  do {
    // axios arma la petición en una cadena de promesas: sale uno o dos turnos después.
    await new Promise((r) => setTimeout(r, 0))
  } while (enVuelo.size > 0 && Date.now() < fin)
}

afterEach(async () => {
  // Primero se desmonta; después se deja terminar lo que la prueba ya había pedido, con sus
  // handlers. Sin esa espera, una petición que axios aún armaba salía tras `resetHandlers`, sin
  // handler, y la guarda de abajo se la cobraba a la prueba siguiente: Comercial y Campañas
  // fallaban en 5 de cada 6 ejecuciones locales de la suite con cobertura.
  cleanup()
  await esperarRed()
  server.resetHandlers()
  const pendientes = sinHandler.splice(0)
  expect(pendientes, 'peticiones sin handler de MSW: simúlalas en la prueba o en src/test/handlers.ts').toEqual([])
})
afterAll(() => server.close())
