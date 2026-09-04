import axios from 'axios'

const TOKEN_KEY = 'timu.token'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api/v1',
})

export const tokenStorage = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
}

api.interceptors.request.use((config) => {
  const token = tokenStorage.get()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Sesion expirada: limpiar y devolver al login.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && window.location.pathname !== '/login') {
      tokenStorage.clear()
      window.location.assign('/login')
    }
    return Promise.reject(error)
  },
)
