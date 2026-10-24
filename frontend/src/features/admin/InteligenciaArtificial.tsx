import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'
import { fechaHora, porcentaje } from '@/lib/formato'
import type { PromptRead } from '@/types'

import {
  useActivarPrompt,
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
          <h3>Gasto del mes</h3>
        </div>
        <Consulta consulta={consumo} cargando="Calculando…" error="No fue posible consultar el gasto.">
          {(c) => {
            const uso = c.presupuesto_usd ? c.gasto_usd / c.presupuesto_usd : 0
            return (
              <div className="pila">
                <div className="indicadores">
                  <div className="indicador">
                    <span className="indicador-titulo">Gastado</span>
                    <strong className="indicador-valor numero">US$ {c.gasto_usd.toFixed(2)}</strong>
                    <span className="indicador-detalle">de US$ {c.presupuesto_usd.toFixed(2)} · {porcentaje(uso)}</span>
                  </div>
                  <div className="indicador">
                    <span className="indicador-titulo">Disponible</span>
                    <strong className="indicador-valor numero">US$ {c.disponible_usd.toFixed(2)}</strong>
                    <span className="indicador-detalle">Al agotarse, la IA se apaga sola hasta el mes siguiente</span>
                  </div>
                </div>
                <div className="barra-presupuesto" role="meter" aria-label="Presupuesto de IA usado" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(uso * 100)}>
                  <span style={{ width: `${Math.min(100, uso * 100)}%` }} />
                </div>
              </div>
            )
          }}
        </Consulta>
      </section>

      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Prompts</h3>
          <div className="acciones">
            <button className="btn btn-plano" type="button" disabled={sembrar.isPending} onClick={() => sembrar.mutate()}>
              Cargar versiones iniciales
            </button>
            <button className="btn btn-primario" type="button" onClick={() => setNuevo(true)}>
              <Icono nombre="mas" size={16} /> Nueva versión
            </button>
          </div>
        </div>
        <p className="apagado" style={{ marginBottom: 'var(--e4)' }}>
          Una versión nueva queda en borrador. Sólo se activa después de pasar sus casos de prueba.
        </p>
        <Consulta consulta={prompts} cargando="Cargando…" error="No fue posible cargar los prompts." vacio="No hay prompts. Carga las versiones iniciales." estaVacio={(d) => d.length === 0}>
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
                    {USOS[c.prompt_codigo]} · «{c.entrada}» → <span className="codigo">{JSON.stringify(c.esperado)}</span>
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
              <table className="tabla">
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Uso</th>
                    <th>Estado</th>
                    <th>Tokens</th>
                    <th>Costo</th>
                  </tr>
                </thead>
                <tbody>
                  {d.slice(0, 30).map((q) => (
                    <tr key={q.id}>
                      <td className="numero">{fechaHora(q.created_at)}</td>
                      <td>
                        {USOS[q.prompt_codigo] ?? q.prompt_codigo}
                        {q.prompt_version && <span className="apagado"> v{q.prompt_version}</span>}
                      </td>
                      <td>
                        <span className={`distintivo distintivo-${q.estado === 'ok' ? 'ok' : q.estado === 'error' ? 'peligro' : 'neutro'}`}>{q.estado}</span>
                        {q.error && <div className="apagado">{q.error}</div>}
                      </td>
                      <td className="numero">
                        {q.tokens_entrada} / {q.tokens_salida}
                      </td>
                      <td className="numero">US$ {q.costo_usd.toFixed(4)}</td>
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
    <div className="pila" style={{ gap: 'var(--e2)', paddingBlock: 'var(--e3)', borderBottom: '1px solid var(--linea)' }}>
      <div className="acciones">
        <strong>
          {USOS[p.codigo] ?? p.codigo} · v{p.version}
        </strong>
        <span className={`distintivo distintivo-${p.estado === 'activo' ? 'ok' : p.estado === 'borrador' ? 'alerta' : 'neutro'}`}>{p.estado}</span>
        {p.nota && <span className="apagado">{p.nota}</span>}
        {p.estado === 'borrador' && (
          <div className="acciones" style={{ marginLeft: 'auto' }}>
            <button className="btn btn-suave" type="button" disabled={evaluar.isPending} onClick={() => evaluar.mutate(p.id)}>
              {evaluar.isPending ? 'Evaluando…' : 'Correr casos'}
            </button>
            <button className="btn btn-primario" type="button" disabled={!aprobado || activar.isPending} onClick={() => activar.mutate(p.id)}>
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
          <textarea className="input codigo" name="esperado" rows={3} defaultValue={'{"alcance": "fuera"}'} required />
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
