import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useTiposServicio } from '@/features/catalogos/api'
import { mensajeError } from '@/lib/errores'
import { moneda } from '@/lib/formato'
import type { PlanRead } from '@/types'

import { useActualizarPlan, useCrearPlan, useGuardarBeneficios, usePlanesAdmin, type Beneficio } from './api'

export function Planes() {
  const planes = usePlanesAdmin()
  const actualizar = useActualizarPlan()
  const [nuevo, setNuevo] = useState(false)
  const [editando, setEditando] = useState<PlanRead | null>(null)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Planes de afiliación</h3>
        <button className="btn btn-primario" type="button" onClick={() => setNuevo(true)}>
          <Icono nombre="mas" size={16} /> Nuevo plan
        </button>
      </div>
      {actualizar.isError && (
        <p className="error" role="alert">
          {mensajeError(actualizar.error, 'No fue posible actualizar el plan.')}
        </p>
      )}
      <Consulta consulta={planes} cargando="Cargando planes…" error="No fue posible cargar los planes." vacio="No hay planes." estaVacio={(d) => d.length === 0}>
        {(d) => (
          <div className="planes">
            {d.map((p) => (
              <article key={p.id} className="plan" aria-label={p.nombre}>
                <div className="acciones">
                  <h4>{p.nombre}</h4>
                  {!p.activo && <span className="distintivo distintivo-neutro">Inactivo</span>}
                </div>
                <strong className="indicador-valor numero">{moneda(p.valor_mensual)}</strong>
                <span className="apagado">
                  por mes · hasta {p.cupos_mascotas} {p.cupos_mascotas === 1 ? 'mascota' : 'mascotas'}
                  {p.ciudad ? ` · ${p.ciudad}` : ''}
                </span>
                <ul className="beneficios">
                  {p.beneficios.map((b) => (
                    <li key={b.id}>
                      <Icono nombre="check" size={14} /> {b.tipo_servicio_codigo.replace(/_/g, ' ')}
                      {b.cupo ? ` · ${b.cupo} al ${b.periodo_cupo === 'anual' ? 'año' : 'mes'}` : ' · ilimitado'}
                    </li>
                  ))}
                  {p.beneficios.length === 0 && <li className="apagado">Sin beneficios configurados</li>}
                </ul>
                <div className="acciones">
                  <button className="btn btn-suave" type="button" onClick={() => setEditando(p)}>
                    Editar
                  </button>
                  <button className="btn btn-plano" type="button" onClick={() => actualizar.mutate({ id: p.id, activo: !p.activo })}>
                    {p.activo ? 'Desactivar' : 'Activar'}
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </Consulta>
      <NuevoPlan abierto={nuevo} onCerrar={() => setNuevo(false)} />
      {editando && <EditarPlan plan={editando} onCerrar={() => setEditando(null)} />}
    </section>
  )
}

function NuevoPlan({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const crear = useCrearPlan()
  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          crear.reset()
          onCerrar()
        }
      }}
      titulo="Nuevo plan"
      pie={
        <button className="btn btn-primario" type="submit" form="nuevo-plan" disabled={crear.isPending}>
          Crear plan
        </button>
      }
    >
      <form
        id="nuevo-plan"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const d = new FormData(e.currentTarget)
          crear.mutate(
            {
              codigo: String(d.get('codigo')).trim(),
              nombre: String(d.get('nombre')).trim(),
              descripcion: String(d.get('descripcion') ?? '').trim() || undefined,
              valor_mensual: String(d.get('valor_mensual')),
              cupos_mascotas: Number(d.get('cupos_mascotas')),
            },
            { onSuccess: onCerrar },
          )
        }}
      >
        <label className="campo">
          <span>Código</span>
          <input className="input" name="codigo" required pattern="[a-z0-9_]+" />
        </label>
        <label className="campo">
          <span>Nombre</span>
          <input className="input" name="nombre" required />
        </label>
        <label className="campo">
          <span>Valor mensual (COP)</span>
          <input className="input" name="valor_mensual" type="number" min={0} required />
        </label>
        <label className="campo">
          <span>Mascotas incluidas</span>
          <input className="input" name="cupos_mascotas" type="number" min={1} defaultValue={1} required />
        </label>
        <label className="campo ancho">
          <span>Descripción</span>
          <textarea className="input" name="descripcion" rows={2} />
        </label>
        {crear.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(crear.error, 'No fue posible crear el plan.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

function EditarPlan({ plan, onCerrar }: { plan: PlanRead; onCerrar: () => void }) {
  const tipos = useTiposServicio()
  const actualizar = useActualizarPlan()
  const guardarBeneficios = useGuardarBeneficios()
  const [beneficios, setBeneficios] = useState<Beneficio[]>(
    plan.beneficios.map((b) => ({
      tipo_servicio_codigo: b.tipo_servicio_codigo,
      cupo: b.cupo ?? null,
      periodo_cupo: b.periodo_cupo ?? 'anual',
      cobertura_pct: b.cobertura_pct ?? 100,
      copago: String(b.copago ?? '0'),
    })),
  )
  const disponibles = tipos.data?.filter((t) => !beneficios.some((b) => b.tipo_servicio_codigo === t.codigo)) ?? []
  const error = actualizar.error ?? guardarBeneficios.error

  function cambiar(i: number, cambio: Partial<Beneficio>) {
    setBeneficios((a) => a.map((b, j) => (j === i ? { ...b, ...cambio } : b)))
  }

  return (
    <Modal
      abierto
      onCambio={(v) => !v && onCerrar()}
      titulo={`Editar ${plan.nombre}`}
      descripcion="El nuevo valor aplica a las cuotas que se emitan desde ahora; las ya emitidas no cambian."
      pie={
        <button className="btn btn-primario" type="submit" form="editar-plan" disabled={actualizar.isPending || guardarBeneficios.isPending}>
          Guardar
        </button>
      }
    >
      <form
        id="editar-plan"
        className="pila"
        onSubmit={async (e) => {
          e.preventDefault()
          const d = new FormData(e.currentTarget)
          await actualizar.mutateAsync({
            id: plan.id,
            nombre: String(d.get('nombre')).trim(),
            valor_mensual: String(d.get('valor_mensual')),
            cupos_mascotas: Number(d.get('cupos_mascotas')),
          })
          await guardarBeneficios.mutateAsync({ id: plan.id, beneficios })
          onCerrar()
        }}
      >
        <div className="formulario">
          <label className="campo ancho">
            <span>Nombre</span>
            <input className="input" name="nombre" defaultValue={plan.nombre} required />
          </label>
          <label className="campo">
            <span>Valor mensual (COP)</span>
            <input className="input" name="valor_mensual" type="number" min={0} defaultValue={Number(plan.valor_mensual)} required />
          </label>
          <label className="campo">
            <span>Mascotas incluidas</span>
            <input className="input" name="cupos_mascotas" type="number" min={1} defaultValue={plan.cupos_mascotas} required />
          </label>
        </div>
        <h4 className="subtitulo">Beneficios</h4>
        {beneficios.map((b, i) => (
          <fieldset key={b.tipo_servicio_codigo} className="formulario">
            <legend className="ancho">{tipos.data?.find((t) => t.codigo === b.tipo_servicio_codigo)?.nombre ?? b.tipo_servicio_codigo}</legend>
            <label className="campo">
              <span>Cupo (vacío = ilimitado)</span>
              <input
                className="input"
                type="number"
                min={0}
                value={b.cupo ?? ''}
                onChange={(e) => cambiar(i, { cupo: e.target.value ? Number(e.target.value) : null })}
              />
            </label>
            <label className="campo">
              <span>Periodo</span>
              <select className="input" value={b.periodo_cupo} onChange={(e) => cambiar(i, { periodo_cupo: e.target.value as 'mensual' | 'anual' })}>
                <option value="anual">Anual</option>
                <option value="mensual">Mensual</option>
              </select>
            </label>
            <label className="campo">
              <span>Cobertura (%)</span>
              <input className="input" type="number" min={0} max={100} value={b.cobertura_pct} onChange={(e) => cambiar(i, { cobertura_pct: Number(e.target.value) })} />
            </label>
            <label className="campo">
              <span>Copago (COP)</span>
              <input className="input" type="number" min={0} value={b.copago} onChange={(e) => cambiar(i, { copago: e.target.value })} />
            </label>
            <button className="btn btn-plano" type="button" onClick={() => setBeneficios((a) => a.filter((_, j) => j !== i))}>
              Quitar beneficio
            </button>
          </fieldset>
        ))}
        {disponibles.length > 0 && (
          <select
            className="input"
            value=""
            aria-label="Agregar beneficio"
            onChange={(e) =>
              e.target.value &&
              setBeneficios((a) => [...a, { tipo_servicio_codigo: e.target.value, cupo: null, periodo_cupo: 'anual', cobertura_pct: 100, copago: '0' }])
            }
          >
            <option value="">Agregar beneficio…</option>
            {disponibles.map((t) => (
              <option key={t.codigo} value={t.codigo}>{t.nombre}</option>
            ))}
          </select>
        )}
        {error && (
          <p className="error" role="alert">
            {mensajeError(error, 'No fue posible guardar el plan.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
