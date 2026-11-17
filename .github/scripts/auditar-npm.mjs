// `npm audit` de las herramientas (desarrollo y publicacion) con las excepciones escritas aqui.
//
// Uso: node .github/scripts/auditar-npm.mjs   (en el directorio del package.json que se audita)
//
// Falla si hay un aviso alto o critico que no esta en EXCEPCIONES, y tambien si una excepcion ya no
// aparece: la lista solo encoge, y una excepcion que sobra se borra en vez de quedarse olvidada.
// Las moderadas se listan sin fallar, como `npm audit --audit-level=high`.
//
// npm no tiene un `--ignore-vuln` como pip-audit. Una excepcion solo entra cuando el aviso no tiene
// version corregida (no hay a que actualizar ni que fijar con `overrides`) y nunca para lo que se
// despliega: el paso del panel en produccion sigue con `npm audit --omit=dev`, sin excepciones.
import { execFileSync } from 'node:child_process'

const EXCEPCIONES = {
  // 2026-11-17, decidido con el usuario: ReDoS de picomatch (<= 4.0.7, la ultima publicada), sin
  // version corregida. Solo llega por herramientas: vite y vitest en el panel, semantic-release en
  // la raiz; el panel desplegado no lo incluye. Se borra al salir la version que lo corrige.
  'GHSA-fc5q-39xc-vjpf': 'picomatch: ReDoS con extglobs repetidos, sin versión corregida',
}

const GRAVES = new Set(['high', 'critical'])

let salida
try {
  salida = execFileSync('npm', ['audit', '--json'], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 })
} catch (e) {
  // `npm audit` sale con error si encuentra algo; el informe sigue en stdout.
  salida = e.stdout
}
const informe = JSON.parse(salida)

const avisos = new Map()
for (const [paquete, vuln] of Object.entries(informe.vulnerabilities ?? {})) {
  for (const via of vuln.via) {
    if (typeof via !== 'object') continue
    const id = via.url.split('/').at(-1)
    avisos.set(id, { paquete, gravedad: via.severity, titulo: via.title, rango: via.range })
  }
}

const bloquean = []
for (const [id, a] of avisos) {
  const marca = id in EXCEPCIONES ? 'excepción' : GRAVES.has(a.gravedad) ? 'BLOQUEA' : 'aviso'
  console.log(`${marca.padEnd(9)} ${a.gravedad.padEnd(8)} ${id} ${a.paquete} ${a.rango}: ${a.titulo}`)
  if (marca === 'BLOQUEA') bloquean.push(id)
}

const sobran = Object.keys(EXCEPCIONES).filter((id) => !avisos.has(id))
for (const id of sobran) console.log(`La excepción ${id} ya no aparece en este audit: bórrala de EXCEPCIONES.`)
if (bloquean.length) console.log(`Bloquean: ${bloquean.join(', ')}. Actualiza la dependencia o fija la transitiva con overrides.`)
process.exit(bloquean.length || sobran.length ? 1 : 0)
