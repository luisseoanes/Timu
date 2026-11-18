import { useId, useState } from 'react'

import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'
import type { PlanRead } from '@/types'

import { useGuardarAdicionales, type Adicional } from './api'

// Los beneficios adicionales de un plan (R3-PUB-04): lo que da sin ser un tipo de servicio que se
// agenda (el servicio fúnebre, el desparasitante externo, lo de terceros). Un bloque de la ficha
// con su propia ventana, decidido con el usuario: la de «Editar plan» no crece.

/** «Desde los 30 días», como lo dice la portada. */
function desde(dias: number | null): string | null {
  if (dias === null) return null
  if (dias === 0) return 'Desde el primer día'
  if (dias === 1) return 'Desde las 24 horas'
  return `Desde los ${dias} días`
}

export function BloqueAdicionales({ plan }: { plan: PlanRead }) {
  const [editando, setEditando] = useState(false)
  return (
    <section className="bloque" aria-labelledby="plan-adicionales">
      <h3 id="plan-adicionales">Beneficios adicionales</h3>
      {plan.adicionales.length ? (
        <ul className="plan-adicionales" aria-label={`Beneficios adicionales de ${plan.nombre}`}>
          {plan.adicionales.map((a) => (
            <li key={a.id}>
              <span className="plan-adicional-cabeza">
                <strong>{a.nombre}</strong> <span className="numero">· {a.cubre}</span>
              </span>
              {(a.carencia_dias != null || a.tercero) && (
                <span className="apagado">{[desde(a.carencia_dias ?? null), a.tercero ? 'Lo presta un tercero' : null].filter(Boolean).join(' · ')}</span>
              )}
              {a.detalle && <span>{a.detalle}</span>}
            </li>
          ))}
        </ul>
      ) : (
        <p className="admin-nota">Sin adicionales: la portada y el registro solo dicen los beneficios de arriba.</p>
      )}
      <div>
        <button className="btn btn-secundario" type="button" onClick={() => setEditando(true)}>
          Editar adicionales
        </button>
      </div>
      {editando && <EditarAdicionales plan={plan} onCerrar={() => setEditando(false)} />}
    </section>
  )
}

const VACIO: Adicional = { nombre: '', cubre: '', detalle: null, carencia_dias: null, tercero: false }

function EditarAdicionales({ plan, onCerrar }: { plan: PlanRead; onCerrar: () => void }) {
  const guardar = useGuardarAdicionales()
  const [adicionales, setAdicionales] = useState<Adicional[]>(() =>
    plan.adicionales.map((a) => ({ nombre: a.nombre, cubre: a.cubre, detalle: a.detalle ?? null, carencia_dias: a.carencia_dias ?? null, tercero: a.tercero ?? false })),
  )
  const cambiar = (i: number, cambio: Partial<Adicional>) => setAdicionales((l) => l.map((a, j) => (j === i ? { ...a, ...cambio } : a)))
  const mover = (i: number, hacia: number) =>
    setAdicionales((l) => {
      const copia = [...l]
      const [uno] = copia.splice(i, 1)
      copia.splice(i + hacia, 0, uno!)
      return copia
    })

  return (
    <Modal
      abierto
      onCambio={(v) => !v && onCerrar()}
      titulo={`Beneficios adicionales de ${plan.nombre}`}
      descripcion="En el orden en que los dice la portada. Cada uno con lo que cubre, como lo leerá la familia."
      pie={
        <button className="btn btn-primario" type="submit" form="editar-adicionales" disabled={guardar.isPending}>
          Guardar
        </button>
      }
    >
      <form
        id="editar-adicionales"
        className="pila"
        onSubmit={(e) => {
          e.preventDefault()
          guardar.mutate(
            { id: plan.id, adicionales: adicionales.map((a) => ({ ...a, nombre: a.nombre.trim(), cubre: a.cubre.trim(), detalle: a.detalle?.trim() || null })) },
            { onSuccess: onCerrar },
          )
        }}
      >
        {adicionales.length === 0 && <p className="admin-nota">Sin adicionales. Añade el primero.</p>}
        <ol className="plan-adicionales-edicion">
          {adicionales.map((a, i) => (
            <FilaAdicional
              key={i}
              numero={i + 1}
              total={adicionales.length}
              adicional={a}
              onCambio={(c) => cambiar(i, c)}
              onMover={(hacia) => mover(i, hacia)}
              onQuitar={() => setAdicionales((l) => l.filter((_, j) => j !== i))}
            />
          ))}
        </ol>
        <div>
          <button className="btn btn-secundario" type="button" onClick={() => setAdicionales((l) => [...l, { ...VACIO }])}>
            <Icono nombre="mas" size={16} /> Otro beneficio adicional
          </button>
        </div>
        {guardar.isError && (
          <p className="error" role="alert">
            {mensajeError(guardar.error, 'No fue posible guardar los beneficios adicionales.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

function FilaAdicional({
  numero,
  total,
  adicional: a,
  onCambio,
  onMover,
  onQuitar,
}: {
  numero: number
  total: number
  adicional: Adicional
  onCambio: (c: Partial<Adicional>) => void
  onMover: (hacia: number) => void
  onQuitar: () => void
}) {
  const id = useId()
  const nombre = a.nombre.trim() || `el beneficio ${numero}`
  return (
    <li className="formulario plan-adicional-fila">
      <div className="campo">
        <label htmlFor={`${id}-nombre`}>Beneficio</label>
        <input id={`${id}-nombre`} className="input" required minLength={2} maxLength={160} value={a.nombre} onChange={(e) => onCambio({ nombre: e.target.value })} />
      </div>
      <div className="campo">
        <label htmlFor={`${id}-cubre`}>Lo que cubre</label>
        <input
          id={`${id}-cubre`}
          className="input"
          required
          maxLength={160}
          placeholder="100 %, cada 3 meses…"
          value={a.cubre}
          onChange={(e) => onCambio({ cubre: e.target.value })}
        />
      </div>
      <div className="campo">
        <label htmlFor={`${id}-desde`}>Aplica desde (días de afiliada)</label>
        <input
          id={`${id}-desde`}
          className="input"
          type="number"
          min={0}
          value={a.carencia_dias ?? ''}
          onChange={(e) => onCambio({ carencia_dias: e.target.value === '' ? null : Number(e.target.value) })}
        />
      </div>
      <label className="acciones">
        <input type="checkbox" checked={a.tercero} onChange={(e) => onCambio({ tercero: e.target.checked })} />
        <span>Lo presta un tercero</span>
      </label>
      <div className="campo ancho">
        <label htmlFor={`${id}-detalle`}>Detalle</label>
        <textarea id={`${id}-detalle`} className="input" rows={2} maxLength={2000} value={a.detalle ?? ''} onChange={(e) => onCambio({ detalle: e.target.value || null })} />
      </div>
      <div className="ancho acciones plan-adicional-mover">
        <button className="btn btn-plano btn-icono" type="button" aria-label={`Subir ${nombre}`} disabled={numero === 1} onClick={() => onMover(-1)}>
          <Icono nombre="arriba" size={18} />
        </button>
        <button className="btn btn-plano btn-icono" type="button" aria-label={`Bajar ${nombre}`} disabled={numero === total} onClick={() => onMover(1)}>
          <Icono nombre="abajo" size={18} />
        </button>
        <button className="btn btn-plano" type="button" onClick={onQuitar}>
          Quitar
        </button>
      </div>
    </li>
  )
}
