import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'

/**
 * Único punto de contacto con la API.
 *
 * La sesión viaja en una cookie httpOnly que pone el backend al iniciar sesión, así
 * que aquí no se guarda ni se lee ningún token: `localStorage` es legible desde
 * JavaScript y una XSS se llevaría la sesión, con historia clínica de por medio.
 * `withCredentials` es lo que hace que el navegador envíe esa cookie.
 */
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api/v1',
  withCredentials: true,
})

// Rutas que no se reintentan tras renovar: o son la propia sesión o no la necesitan.
const SIN_RENOVACION = ['/auth/login', '/auth/refresh', '/auth/logout']

type Reintento = InternalAxiosRequestConfig & { _renovada?: boolean }

/**
 * El access token dura poco (F1-AUT-01) y lo sostiene una cookie de renovación que
 * rota en cada uso. Si varias peticiones vencen a la vez, todas esperan la MISMA
 * renovación: presentar dos veces el refresh ya rotado se interpreta como robo y el
 * backend cierra todas las sesiones del usuario.
 */
let renovacionEnCurso: Promise<void> | null = null

function renovarSesion(): Promise<void> {
  renovacionEnCurso ??= api
    .post('/auth/refresh')
    .then(() => undefined)
    .finally(() => {
      renovacionEnCurso = null
    })
  return renovacionEnCurso
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as Reintento | undefined
    const url = original?.url ?? ''
    const renovable =
      error.response?.status === 401 &&
      original !== undefined &&
      !original._renovada &&
      !SIN_RENOVACION.some((ruta) => url.endsWith(ruta))

    if (renovable) {
      original._renovada = true
      try {
        await renovarSesion()
        return await api.request(original)
      } catch {
        // La renovación falló: la sesión terminó de verdad. Se cae a la redirección.
      }
    }

    // Sesión expirada o ausente: devolver al ingreso. La cookie la limpia el backend.
    const enLogin = window.location.pathname === '/login'
    if (error.response?.status === 401 && !enLogin && !url.endsWith('/auth/me')) {
      window.location.assign('/login')
    }
    return Promise.reject(error)
  },
)
