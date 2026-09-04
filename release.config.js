/**
 * Configuración de semantic-release para el monorepo TIMU.
 *
 * Un único release por repositorio: backend y panel comparten número de versión y
 * se publican juntos, igual que los despliega docker-compose. El tag es `vX.Y.Z`.
 *
 * El scope del commit es libre y sirve para agrupar las notas: `feat(clinica): …`,
 * `feat(backend): …` o `fix(cartera): …` aparecen todos en el mismo release, cada
 * uno con su scope en negrita delante del asunto. Un commit sin scope también vale.
 *
 * Qué mueve la versión:
 *   feat                    -> minor
 *   fix, perf, revert       -> patch
 *   breaking change         -> minor mientras estemos en 0.x (ver releaseRules)
 *   el resto de tipos       -> no publica
 */

// Secciones del changelog, en español. `hidden` mantiene el tipo disponible para
// escribir commits pero lo deja fuera de las notas del release.
const types = [
  { type: 'feat', section: 'Funcionalidades' },
  { type: 'fix', section: 'Correcciones' },
  { type: 'perf', section: 'Rendimiento' },
  { type: 'revert', section: 'Reversiones' },
  { type: 'refactor', section: 'Refactorizaciones' },
  { type: 'docs', section: 'Documentación', hidden: true },
  { type: 'style', section: 'Estilo', hidden: true },
  { type: 'test', section: 'Pruebas', hidden: true },
  { type: 'build', section: 'Construcción', hidden: true },
  { type: 'ci', section: 'Integración continua', hidden: true },
  { type: 'chore', section: 'Mantenimiento', hidden: true },
]

const presetConfig = { types }

export default {
  branches: ['main'],
  tagFormat: 'v${version}',
  plugins: [
    [
      '@semantic-release/commit-analyzer',
      {
        preset: 'conventionalcommits',
        presetConfig,
        releaseRules: [
          // OJO: mientras la versión sea 0.x, un cambio rompiente sube la minor.
          // Al publicar la 1.0.0 hay que BORRAR esta línea; si se queda, un
          // breaking daría 1.1.0 en lugar de 2.0.0.
          { breaking: true, release: 'minor' },
          { type: 'refactor', release: false },
          { type: 'docs', release: false },
          { type: 'style', release: false },
          { type: 'test', release: false },
          { type: 'build', release: false },
          { type: 'ci', release: false },
          { type: 'chore', release: false },
        ],
      },
    ],
    ['@semantic-release/release-notes-generator', { preset: 'conventionalcommits', presetConfig }],
    [
      '@semantic-release/github',
      {
        successComment: false,
        failComment: false,
        releasedLabels: false,
        addReleases: false,
      },
    ],
  ],
}
