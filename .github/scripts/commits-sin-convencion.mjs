/**
 * Avisa de los commits que no siguen Conventional Commits: semantic-release no los
 * puede clasificar, así que el trabajo que traigan no aparecerá en ningún release.
 *
 * El scope es libre —`feat(clinica):`, `fix(backend):` o `feat:` sin scope valen
 * igual—; lo único que se comprueba es que la cabecera tenga la forma
 * `tipo(scope opcional)!?: asunto` con un tipo conocido.
 *
 * Uso:  node .github/scripts/commits-sin-convencion.mjs [rango-de-git]
 * Por defecto revisa desde el último tag de versión; si no hay tags, todo el historial.
 */

import { execFileSync } from 'node:child_process'

const TIPOS = ['feat', 'fix', 'perf', 'revert', 'refactor', 'docs', 'style', 'test', 'build', 'ci', 'chore']

const git = (...args) => execFileSync('git', args, { encoding: 'utf-8' }).trim()

function rangoPorDefecto() {
  const tags = git('tag', '--list', 'v*', '--sort=-creatordate').split('\n').filter(Boolean)
  return tags.length ? `${tags[0]}..HEAD` : 'HEAD'
}

const rango = process.argv[2] ?? rangoPorDefecto()
const asuntos = git('log', '--no-merges', '--pretty=format:%s', rango).split('\n').filter(Boolean)

const cabecera = /^(\w+)(?:\(([^)]+)\))?!?: (.+)$/

const problemas = []
for (const asunto of asuntos) {
  const m = cabecera.exec(asunto)
  if (!m) {
    problemas.push([asunto, 'no tiene la forma «tipo(scope): asunto»'])
  } else if (!TIPOS.includes(m[1])) {
    problemas.push([asunto, `el tipo «${m[1]}» no es uno de: ${TIPOS.join(', ')}`])
  }
}

if (problemas.length === 0) {
  console.log(`Los ${asuntos.length} commit(s) de ${rango} siguen la convención.`)
  process.exit(0)
}

for (const [asunto, motivo] of problemas) {
  console.log(`::warning title=Commit fuera de convención::${asunto} — ${motivo}`)
}
console.log(`\n${problemas.length} commit(s) no se tendrán en cuenta para el release.`)
