import { useId, useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'
import { dolares, fechaHora, porcentaje } from '@/lib/formato'
import type { PromptRead } from '@/types'

import {
  useActivarPrompt,
  useCambiarTopeIA,
  useCasos,
  useConsultasIA,
  useConsumoIA,
  useCrearCaso,
  useCrearPrompt,
  useEvaluarPrompt,
  usePrompts,
  useSembrarPrompts,
  type EvaluacionPrompt,
} from './api'

const USOS: Record<string, string> = {
  comercial_guion: 'Atención comercial por WhatsApp',
  veterinario_borrador: 'Borrador para la atención virtual',
}

/** El tope mensual, que Administración cambia sin desplegar (decidido con el usuario el 2026-11-20).
 * Siempre hay uno: se sube o se baja, no se quita (el asistente de WhatsApp contesta con IA a quien
 * escriba), y la API exige US$ 1 como mínimo. */
function CambiarTope({ tope }: { tope: number }) {
  const id = useId()
  const cambiar = useCambiarTopeIA()
  const [valor, setValor] = useState(String(tope))
  const numero = Number(valor)
  const valido = valor.trim() !== '' && Number.isFinite(numero) && numero >= 1
  return (
    <form
      className="campo-con-accion"
      onSubmit={(e) => {
        e.preventDefault()
        if (valido) cambiar.mutate(Math.round(numero * 100) / 100)
      }}
    >
      <div className="campo">
        <label htmlFor={`${id}-tope`}>Tope mensual (US$)</label>
        <input
          id={`${id}-tope`}
          className="input numero"
          type="number"
          inputMode="decimal"
          min={1}
          step={0.01}
          required
          value={valor}
          onChange={(e) => {
            setValor(e.target.value)
            cambiar.reset()
          }}
        />
      </div>
      <button className="btn btn-secundario" type="submit" disabled={!valido || numero === tope || cambiar.isPending}>
        {cambiar.isPending ? 'Guardando…' : 'Guardar'}
      </button>
      {cambiar.isError && (
        <p className="error" role="alert">
          {mensajeError(cambiar.error, 'No fue posible guardar el tope.')}
        </p>
      )}
    </form>
  )
}

/** Capa de IA con control (F4-IAA): prompts versionados, evaluación antes de activar y gasto. */
export function InteligenciaArtificial() {
  const consumo = useConsumoIA()
  const prompts = usePrompts()
  const casos = useCasos()
  const consultas = useConsultasIA()
  const sembrar = useSembrarPrompts()
  const [nuevo, setNuevo] = useState(false)
  const [nuevoCaso, setNuevoCaso] = useState(false)

  return (
    <div className="pila">
      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Tope de gasto de la IA</h3>
        </div>
        <Consulta consulta={consumo} cargando="Calculando…" error="No fue posible consultar el gasto.">
          {(c) => {
            const uso = c.presupuesto_usd ? c.gasto_usd / c.presupuesto_usd : 0
            return (
              <div className="pila">
                {/* No es el saldo de la cuenta del proveedor (Google Cloud factura por su lado). */}
                <p className="apagado">
                  Lo calcula la plataforma con lo que cuesta cada consulta que hace; no es el saldo de la cuenta del
                  proveedor. Al llegar al tope, la IA se apaga hasta el mes siguiente.
                </p>
                <div className="indicadores">
                  <div className="indicador">
                    <span className="indicador-titulo">Gastado</span>
                    <strong className="indicador-valor numero">{dolares(c.gasto_usd)}</strong>
                    <span className="indicador-detalle">de {dolares(c.presupuesto_usd)} · {porcentaje(uso)}</span>
                    {/* La barra junto a la cifra que mide (techo 64). */}
                    <div className="barra-presupuesto" role="meter" aria-label="Presupuesto de IA usado" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(uso * 100)}>
                      <span style={{ width: `${Math.min(100, uso * 100)}%` }} />
                    </div>
                  </div>
                  <div className="indicador">
                    <span className="indicador-titulo">Queda antes del tope</span>
                    <strong className="indicador-valor numero">{dolares(c.disponible_usd)}</strong>
                    <span className="indicador-detalle">Este mes</span>
                  </div>
                </div>
                {/* `key`: tras guardar, el campo vuelve a partir del tope guardado. */}
                <CambiarTope key={c.presupuesto_usd} tope={c.presupuesto_usd} />
              </div>
            )
          }}
        </Consulta>
      </section>

      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Prompts</h3>
          {/* Sin prompts, lo que toca es cargar las versiones iniciales: ese es el verde. */}
          {prompts.data?.length === 0 ? (
            <div className="acciones">
              <button className="btn btn-suave" type="button" onClick={() => setNuevo(true)}>
                <Icono nombre="mas" size={16} /> Nueva versión
              </button>
              <button className="btn btn-primario" type="button" disabled={sembrar.isPending} onClick={() => sembrar.mutate()}>
                {sembrar.isPending ? 'Cargando…' : 'Cargar versiones iniciales'}
              </button>
            </div>
          ) : (
            <button className="btn btn-primario" type="button" onClick={() => setNuevo(true)}>
              <Icono nombre="mas" size={16} /> Nueva versión
            </button>
          )}
        </div>
        <p className="admin-nota">Una versión nueva queda en borrador. Solo se activa después de pasar sus casos de prueba.</p>
        {sembrar.isError && (
          <p className="error" role="alert">
            {mensajeError(sembrar.error, 'No fue posible cargar las versiones iniciales.')}
          </p>
        )}
        <Consulta consulta={prompts} cargando="Cargando…" error="No fue posible cargar los prompts." vacio="No hay prompts todavía. Carga las versiones iniciales para empezar." estaVacio={(d) => d.length === 0}>
          {(d) => d.map((p) => <FilaPrompt key={p.id} prompt={p} />)}
        </Consulta>
      </section>

      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Casos de prueba</h3>
          <button className="btn btn-suave" type="button" onClick={() => setNuevoCaso(true)}>
            <Icono nombre="mas" size={16} /> Nuevo caso
          </button>
        </div>
        <Consulta consulta={casos} cargando="Cargando…" error="No fue posible cargar los casos." vacio="Sin casos: no se podrá activar ninguna versión." estaVacio={(d) => d.length === 0}>
          {(d) =>
            d.map((c) => (
              <div key={c.id} className="fila">
                <div className="fila-cuerpo">
                  <strong>{c.nombre}</strong>
                  <span>
                    {USOS[c.prompt_codigo]} · «{c.entrada}» → {c.esperado_texto}
                  </span>
                </div>
              </div>
            ))
          }
        </Consulta>
      </section>

      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Últimas consultas</h3>
        </div>
        <Consulta consulta={consultas} cargando="Cargando…" error="No fue posible cargar las consultas." vacio="Aún no se ha consultado la IA." estaVacio={(d) => d.length === 0}>
          {(d) => (
            <div className="scroll-x">
              <table className="tabla tabla-apilable bandeja-tabla">
                <thead>
                  <tr>
                    <th>Uso</th>
                    <th>Cuándo</th>
                    <th>Resultado</th>
                    <th>Tokens (entrada / salida)</th>
                    <th>Costo</th>
                  </tr>
                </thead>
                <tbody>
                  {d.slice(0, 30).map((q) => (
                    <tr key={q.id}>
                      <td className="principal" data-etiqueta="Uso">
                        {USOS[q.prompt_codigo] ?? q.prompt_codigo}
                        {q.prompt_version && (
                          <div className="bandeja-detalle">
                            <span className="numero">Versión {q.prompt_version}</span>
                          </div>
                        )}
                        {q.error && <div className="error">{q.error}</div>}
                      </td>
                      <td data-etiqueta="Cuándo">
                        <span className="numero sin-cortes">{fechaHora(q.created_at)}</span>
                      </td>
                      <td data-etiqueta="Resultado">
                        <Distintivo dominio="consulta_ia" valor={q.estado} />
                      </td>
                      <td data-etiqueta="Tokens (entrada / salida)">
                        <span className="numero sin-cortes">
                          {q.tokens_entrada} / {q.tokens_salida}
                        </span>
                      </td>
                      <td data-etiqueta="Costo">
                        <span className="numero sin-cortes">{dolares(q.costo_usd, 4)}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Consulta>
      </section>
      <NuevoPrompt abierto={nuevo} onCerrar={() => setNuevo(false)} />
      <NuevoCaso abierto={nuevoCaso} onCerrar={() => setNuevoCaso(false)} />
    </div>
  )
}

function FilaPrompt({ prompt: p }: { prompt: PromptRead }) {
  const evaluar = useEvaluarPrompt()
  const activar = useActivarPrompt()
  const evaluacion = (evaluar.data ?? (p.evaluado_en ? p.evaluacion : null)) as EvaluacionPrompt | null
  const aprobado = evaluacion !== null && evaluacion.total > 0 && evaluacion.aprobados === evaluacion.total

  return (
    <div className="ia-prompt">
      <div className="ia-prompt-cabeza">
        <strong>
          {USOS[p.codigo] ?? p.codigo} · <span className="numero">versión {p.version}</span>
        </strong>
        <Distintivo dominio="prompt" valor={p.estado} />
        {p.nota && <span className="apagado">{p.nota}</span>}
        {p.estado === 'borrador' && (
          // El verde de la pestaña es «Nueva versión»: activar una se hace con un botón suave.
          <div className="acciones ia-prompt-acciones">
            <button className="btn btn-plano btn-accion" type="button" disabled={evaluar.isPending} onClick={() => evaluar.mutate(p.id)}>
              {evaluar.isPending ? 'Evaluando…' : 'Correr casos'}
            </button>
            <button className="btn btn-suave" type="button" disabled={!aprobado || activar.isPending} onClick={() => activar.mutate(p.id)}>
              Activar
            </button>
          </div>
        )}
      </div>
      <details>
        <summary className="apagado">Ver instrucciones</summary>
        <pre className="codigo bloque-codigo">{p.sistema}</pre>
      </details>
      {evaluacion && (
        <p className={aprobado ? 'aviso-ok' : 'aviso-error'} role="status">
          {evaluacion.aprobados} de {evaluacion.total} casos aprobados
          {!aprobado &&
            evaluacion.detalle
              .filter((x) => !x.aprobado)
              .map((x) => ` · ${x.caso}: ${x.motivo}`)
              .join('')}
        </p>
      )}
      {(evaluar.isError || activar.isError) && (
        <p className="error" role="alert">
          {mensajeError(evaluar.error ?? activar.error, 'No fue posible completar la acción.')}
        </p>
      )}
    </div>
  )
}

function NuevoPrompt({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const crear = useCrearPrompt()
  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          crear.reset()
          onCerrar()
        }
      }}
      titulo="Nueva versión de prompt"
      pie={
        <button className="btn btn-primario" type="submit" form="nuevo-prompt" disabled={crear.isPending}>
          Guardar borrador
        </button>
      }
    >
      <form
        id="nuevo-prompt"
        className="pila"
        onSubmit={(e) => {
          e.preventDefault()
          const d = new FormData(e.currentTarget)
          crear.mutate(
            { codigo: String(d.get('codigo')), sistema: String(d.get('sistema')), nota: String(d.get('nota') ?? '').trim() || undefined },
            { onSuccess: onCerrar },
          )
        }}
      >
        <label className="campo">
          <span>Uso</span>
          <select className="input" name="codigo">
            {Object.entries(USOS).map(([c, l]) => (
              <option key={c} value={c}>{l}</option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Instrucciones del sistema</span>
          <textarea className="input" name="sistema" rows={10} required />
        </label>
        <label className="campo">
          <span>Qué cambia en esta versión</span>
          <input className="input" name="nota" />
        </label>
        {crear.isError && (
          <p className="error" role="alert">
            {mensajeError(crear.error, 'No fue posible guardar.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

function NuevoCaso({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const crear = useCrearCaso()
  const [errorJson, setErrorJson] = useState<string | null>(null)
  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          crear.reset()
          onCerrar()
        }
      }}
      titulo="Nuevo caso de prueba"
      descripcion="Una entrada y lo que se espera de la respuesta. Se corre antes de activar cada versión."
      pie={
        <button className="btn btn-primario" type="submit" form="nuevo-caso" disabled={crear.isPending}>
          Guardar caso
        </button>
      }
    >
      <form
        id="nuevo-caso"
        className="pila"
        onSubmit={(e) => {
          e.preventDefault()
          setErrorJson(null)
          const d = new FormData(e.currentTarget)
          try {
            crear.mutate(
              {
                prompt_codigo: String(d.get('prompt_codigo')),
                nombre: String(d.get('nombre')).trim(),
                entrada: String(d.get('entrada')).trim(),
                esperado: JSON.parse(String(d.get('esperado'))) as Record<string, unknown>,
              },
              { onSuccess: onCerrar },
            )
          } catch {
            setErrorJson('Lo esperado no es un JSON válido.')
          }
        }}
      >
        <label className="campo">
          <span>Uso</span>
          <select className="input" name="prompt_codigo">
            {Object.entries(USOS).map(([c, l]) => (
              <option key={c} value={c}>{l}</option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Nombre</span>
          <input className="input" name="nombre" required />
        </label>
        <label className="campo">
          <span>Entrada</span>
          <textarea className="input" name="entrada" rows={3} required />
        </label>
        <label className="campo">
          <span>Esperado (JSON)</span>
          <textarea className="input codigo" name="esperado" rows={3} defaultValue={'{"campo": "alcance", "igual": "fuera"}'} required />
        </label>
        {(errorJson || crear.isError) && (
          <p className="error" role="alert">
            {errorJson ?? mensajeError(crear.error, 'No fue posible guardar el caso.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
