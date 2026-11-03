import { test as preparar } from '@playwright/test'

import { ingresar, sesion, USUARIOS, type Perfil } from './sesiones'

// Ingresa por el formulario real con cada perfil y guarda la sesión (cookies httpOnly)
// para que los recorridos empiecen ya autenticados.
for (const perfil of Object.keys(USUARIOS) as Perfil[]) {
  preparar(`ingresa como ${perfil}`, async ({ page }) => {
    await ingresar(page, perfil)
    await page.context().storageState({ path: sesion(perfil) })
  })
}
