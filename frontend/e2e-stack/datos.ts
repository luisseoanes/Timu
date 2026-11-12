import { expect, type APIRequestContext } from '@playwright/test'

/** Hoy y los días siguientes en Colombia, como `YYYY-MM-DD`. */
function dias(cuantos: number): string[] {
  const formato = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Bogota' })
  return Array.from({ length: cuantos }, (_, n) => formato.format(new Date(Date.now() + n * 86_400_000)))
}

/**
 * El día de la ruta que deja `scripts.datos_demo` para la médica de prueba, y la dirección de
 * Rutas que lo abre. No siempre es hoy: datos_demo la pone en el primer día con cupo, y no se
 * agenda en el pasado ni en domingo. Con `responsable`, solo cuentan las rutas de esa persona.
 */
export async function rutaDemo(request: APIRequestContext, responsable?: string): Promise<{ dia: string; url: string }> {
  const hoy = dias(1)[0]
  for (const dia of dias(7)) {
    const respuesta = await request.get('/api/v1/rutas', { params: { fecha: dia, ...(responsable ? { responsable_id: responsable } : {}) } })
    expect(respuesta.ok(), `GET /rutas respondió ${respuesta.status()}`).toBeTruthy()
    const rutas = (await respuesta.json()) as { paradas: unknown[] }[]
    if (rutas.some((r) => r.paradas.length > 0)) return { dia, url: dia === hoy ? '/rutas' : `/rutas?dia=${dia}` }
  }
  throw new Error('datos_demo no dejó ninguna ruta en la próxima semana')
}
