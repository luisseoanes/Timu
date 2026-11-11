import { expect, test as preparar } from '@playwright/test'

import { ingresar, sesion, USUARIOS, type Perfil } from './sesiones'

// Guarda la sesión (cookies httpOnly) de cada perfil para que los recorridos empiecen ya
// autenticados. El de equipo ingresa por el formulario real; los demás, directamente por la
// API. Ingreso y renovación comparten un límite de 10 por minuto y por IP, y el formulario
// gasta dos (al abrir /login sin sesión, el cliente intenta renovar antes de ingresar). Con
// los cinco perfiles por el formulario eran 10, y el job del stack ya ingresa una vez antes:
// el quinto recibía 429. Así son 2 + 4, más ese ingreso previo: 7 de 10.
for (const perfil of Object.keys(USUARIOS) as Perfil[]) {
  preparar(`ingresa como ${perfil}`, async ({ page }) => {
    if (perfil === 'equipo') {
      await ingresar(page, perfil)
    } else {
      const { email, clave } = USUARIOS[perfil]
      const respuesta = await page.request.post('/api/v1/auth/login', { form: { username: email, password: clave } })
      expect(respuesta.ok(), `ingreso de ${perfil}: ${respuesta.status()}`).toBeTruthy()
    }
    await page.context().storageState({ path: sesion(perfil) })
  })
}
