import { expect, type Page } from '@playwright/test'

/**
 * Usuarios de `scripts.datos_demo` y dónde queda guardada la sesión de cada uno.
 *
 * Se ingresa una sola vez por perfil (sesiones.setup.ts) y los recorridos reutilizan la
 * sesión: el backend limita los ingresos por minuto (RATE_LIMIT_LOGIN_POR_MINUTO) y una
 * suite que ingresa en cada prueba acaba rechazada por su propio límite.
 */
export const USUARIOS = {
  // No el administrador: datos_demo crea todo a través de la API como admin justo antes, y
  // el límite general (120 por minuto) se cuenta por usuario. Con el mismo usuario, los
  // primeros recorridos caían en ese minuto y recibían 429.
  equipo: { email: 'comercial@timu.co', clave: 'demo12345' },
  // Por la misma razón, Administración se recorre con un administrador que datos_demo crea
  // solo para esto, no con admin@timu.co.
  admin: { email: 'gerencia@timu.co', clave: 'demo12345' },
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
