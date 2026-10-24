import { api } from '@/api/client'

/**
 * Descarga un archivo que genera la API (CSV, Excel, PDF). Pasa por el cliente para
 * que viaje la cookie de sesión; el nombre sale de `Content-Disposition` si viene.
 */
export async function descargar(ruta: string, params: Record<string, unknown>, nombrePorDefecto: string) {
  const respuesta = await api.get<Blob>(ruta, { params, responseType: 'blob' })
  const disposicion = String(respuesta.headers['content-disposition'] ?? '')
  const nombre = /filename="?([^";]+)"?/.exec(disposicion)?.[1] ?? nombrePorDefecto
  const url = URL.createObjectURL(respuesta.data)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = nombre
  enlace.click()
  URL.revokeObjectURL(url)
}
