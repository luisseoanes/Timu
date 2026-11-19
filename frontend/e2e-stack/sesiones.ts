import { expect, type Page } from '@playwright/test'

/**
 * Usuarios de `scripts.datos_demo` y dónde queda guardada la sesión de cada uno.
 *
 * Se ingresa una sola vez por perfil (sesiones.setup.ts) y los recorridos reutilizan la
 * sesión: el backend limita los ingresos por minuto (RATE_LIMIT_LOGIN_POR_MINUTO) y una
 * suite que ingresa en cada prueba acaba rechazada por su propio límite.
 */
export const USUARIOS = {
  // Un usuario por perfil del equipo (Sección 12, docs/perfiles-y-permisos.md): cada pantalla se
  // recorre con el perfil que la usa. Atención al cliente ingresa por el formulario real.
  atencion: { email: 'atencion@timu.co', clave: 'demo12345' },
  admin: { email: 'admin@timu.co', clave: 'cambiar123' },
  gerencia: { email: 'gerencia@timu.co', clave: 'demo12345' },
  comercial: { email: 'comercial@timu.co', clave: 'demo12345' },
  operaciones: { email: 'operaciones@timu.co', clave: 'demo12345' },
  medico: { email: 'medico@timu.co', clave: 'demo12345' },
  familia: { email: 'ana@example.com', clave: 'demo12345' },
  aliada: { email: 'aliada@timu.co', clave: 'demo12345' },
} as const

export type Perfil = keyof typeof USUARIOS

export const sesion = (perfil: Perfil) => `playwright/.auth/${perfil}.json`

export async function ingresar(page: Page, perfil: Perfil) {
  const { email, clave } = USUARIOS[perfil]
  await page.goto('/login')
  await page.getByLabel('Correo').fill(email)
  await page.getByLabel('Contraseña', { exact: true }).fill(clave)
  await page.getByRole('button', { name: 'Ingresar' }).click()
  await expect(page).not.toHaveURL(/\/login/)
}
