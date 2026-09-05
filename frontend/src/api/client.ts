import axios from 'axios'

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

// Sesión expirada o ausente: devolver al ingreso. La cookie la limpia el backend.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const enLogin = window.location.pathname === '/login'
    if (error.response?.status === 401 && !enLogin) {
      window.location.assign('/login')
    }
    return Promise.reject(error)
  },
)
