import { expect, test } from '@playwright/test'

import { sesion } from './sesiones'

/**
 * Recorridos contra el stack real, con los usuarios de `scripts.datos_demo`. Nada se
 * intercepta: si un contrato entre panel y API se rompe, o el entorno no quedó bien
 * levantado, falla aquí y no en producción. El ingreso de cada perfil ya lo hizo
 * sesiones.setup.ts por el formulario real.
 */

test.describe('equipo', () => {
  test.use({ storageState: sesion('equipo') })

  test('busca una familia en el panel y abre su ficha con sus mascotas', async ({ page }) => {
    await page.goto('/')
    // El h1 es el título del módulo (AppLayout); el saludo cuelga de él.
    await expect(page.getByRole('heading', { level: 2, name: /^Hola/ })).toBeVisible()
    await page.getByRole('link', { name: 'Familias' }).first().click()
    await page.getByRole('link', { name: 'Ana Ruiz' }).click()
    await expect(page.getByRole('heading', { name: 'Ana Ruiz' })).toBeVisible()
    await page.getByRole('tab', { name: 'Mascotas' }).click()
    await expect(page.getByRole('tabpanel', { name: 'Mascotas' }).getByText('Luna')).toBeVisible()
    // La sesión vive en cookies httpOnly: el navegador no guarda credenciales a la vista.
    expect(await page.evaluate(() => window.localStorage.length)).toBe(0)
  })

  test('una ventana abierta queda por encima de la línea y de las barras', async ({ page }) => {
    // En el celular la ficha de una mascota es una hoja que sube desde abajo sobre la línea.
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/')
    const familias = await (await page.request.get('/api/v1/familias', { params: { q: 'Ana Ruiz' } })).json()
    await page.goto(`/familias/${familias.items[0].id}`)
    await expect(page.locator('.parada-punto').first()).toBeVisible()
    await page.getByRole('tab', { name: 'Mascotas' }).click()
    await page.getByRole('button', { name: 'Ficha' }).first().click()
    await expect(page.getByRole('dialog')).toBeVisible()
    const encima = await page.evaluate(() => {
      // Radix quita los eventos de puntero a todo lo que queda fuera de la ventana, y
      // elementFromPoint se los salta: se devuelven mientras se mide el orden de pintado.
      const antes = document.body.style.pointerEvents
      document.body.style.pointerEvents = 'auto'
      const tapan = [...document.querySelectorAll('.parada-punto, .linea-hoy, .barra-marca, .barra-inferior')].flatMap((e) => {
        const r = e.getBoundingClientRect()
        const [x, y] = [r.left + r.width / 2, r.top + r.height / 2]
        if (r.width === 0 || y < 0 || y > window.innerHeight) return []
        return document.elementFromPoint(x, y)?.closest('[role="dialog"], .velo') ? [] : [e.className]
      })
      document.body.style.pointerEvents = antes
      return tapan
    })
    expect(encima, 'elementos pintados sobre la ventana').toEqual([])
  })

  test('en un formulario cada control conserva su altura aunque el vecino lleve ayuda', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/familias')
    await page.getByRole('button', { name: 'Nueva familia' }).click()
    const ventana = page.getByRole('dialog', { name: 'Nueva familia' })
    await expect(ventana).toBeVisible()
    // «Sexo» comparte fila con «Fecha de nacimiento», que lleva un texto de ayuda debajo.
    const sexo = await ventana.getByLabel('Sexo (opcional)').boundingBox()
    const peso = await ventana.getByLabel('Peso (kg)').boundingBox()
    expect(Math.round(sexo!.height)).toBe(Math.round(peso!.height))
  })

  test('la foto de una mascota se sube y su URL firmada abre desde el navegador', async ({ page }) => {
    await page.goto('/')
    // `page.request` comparte las cookies de la sesión del navegador.
    const familias = await (await page.request.get('/api/v1/familias', { params: { q: 'Ana Ruiz' } })).json()
    const mascota = familias.items[0].mascotas[0]
    // PNG de 1×1: el backend valida el tipo por contenido, no por extensión.
    const png = Buffer.from(
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC',
      'base64',
    )
    const subida = await page.request.put(`/api/v1/mascotas/${mascota.id}/foto`, {
      multipart: { foto: { name: 'luna.png', mimeType: 'image/png', buffer: png } },
    })
    expect(subida.ok()).toBeTruthy()
    const { foto_url } = await subida.json()
    // La URL apunta al almacenamiento publicado en el host, no al nombre interno del contenedor.
    expect(foto_url).not.toContain('almacenamiento:8333')
    const imagen = await page.request.get(foto_url)
    expect(imagen.status()).toBe(200)
    expect(imagen.headers()['content-type']).toBe('image/png')
  })
})

test.describe('equipo comercial', () => {
  test.use({ storageState: sesion('equipo') })

  test('la bandeja de conversaciones carga contra la API real', async ({ page }) => {
    // Con la API simulada esto pasaba aunque el panel pedía un estado que la API rechaza.
    const respuesta = page.waitForResponse((r) => r.url().includes('/api/v1/comercial/conversaciones'))
    await page.goto('/comercial')
    await page.getByRole('tab', { name: 'Conversaciones' }).click()
    expect((await respuesta).status()).toBe(200)
    await expect(page.getByRole('alert')).toHaveCount(0)
  })
})

test.describe('familia', () => {
  test.use({ storageState: sesion('familia') })

  test('entra a su portal, ve sus mascotas y no llega al panel del equipo', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveURL(/\/portal/)
    await expect(page.getByRole('heading', { level: 1, name: 'Hola, Ana' })).toBeVisible()
    await page.getByRole('navigation', { name: 'Portal' }).getByRole('link', { name: /mascotas/i }).click()
    await expect(page.getByRole('link', { name: /luna/i })).toBeVisible()
    await page.goto('/familias')
    await expect(page).toHaveURL(/\/portal/)
  })
})

test.describe('clínica aliada', () => {
  test.use({ storageState: sesion('aliada') })

  test('valida una remisión emitida sin consumirla', async ({ page, playwright, baseURL }) => {
    // El código lo consulta el equipo, como haría quien emite la remisión.
    const equipo = await playwright.request.newContext({ baseURL, storageState: sesion('equipo') })
    const remisiones = await (await equipo.get('/api/v1/aliadas/remisiones', { params: { estado: 'emitida' } })).json()
    await equipo.dispose()
    expect(remisiones.length, 'datos_demo debe dejar al menos una remisión emitida').toBeGreaterThan(0)
    const codigo: string = remisiones[0].codigo

    await page.goto('/')
    await expect(page).toHaveURL(/\/aliada/)
    await page.getByLabel('Código de la remisión').fill(codigo.toLowerCase())
    await page.getByRole('button', { name: 'Validar' }).click()
    await expect(page.getByRole('status')).toContainText('Remisión vigente hasta el')
    await expect(page.getByText('Radiografia de cadera por cojera')).toBeVisible()
  })
})
