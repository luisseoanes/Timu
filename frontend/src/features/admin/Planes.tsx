import { useId, useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useCiudades, useEspecies, useTiposServicio } from '@/features/catalogos'
import { mensajeError } from '@/lib/errores'
import { moneda } from '@/lib/formato'
import type { ColorPlan, Periodicidad, PlanRead } from '@/types'

import {
  useActualizarPlan,
  useCrearPlan,
  useGuardarBeneficios,
  useGuardarCiudades,
  useGuardarTarifas,
  usePlanesAdmin,
  type Beneficio,
  type Tarifas,
} from './api'

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
                  <span className="marcador-plan" data-color={p.color} aria-hidden="true" />
                  <h4>{p.nombre}</h4>
                  {!p.activo && <span className="distintivo distintivo-neutro">Inactivo</span>}
                </div>
                <strong className="indicador-valor numero">{moneda(tarifa(p, 1))}</strong>
                <span className="apagado">por peludo al mes · {p.ciudades.join(', ') || 'sin ciudades'}</span>
                <dl className="ficha" aria-label={`Tarifas de ${p.nombre}`}>
                  {p.tarifas.map((t) => (
                    <div key={t.peludos}>
                      <dt>{ETIQUETA_PELUDOS[t.peludos - 1]}</dt>
                      <dd className="numero">{moneda(t.valor)}</dd>
                    </div>
                  ))}
                  {p.tarifas_periodicidad.map((t) => (
                    <div key={t.periodicidad}>
                      <dt>{PERIODOS[t.periodicidad]} (1 peludo)</dt>
                      <dd className="numero">{moneda(t.valor)}</dd>
                    </div>
                  ))}
                </dl>
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
  const [aviso, setAviso] = useState<string | null>(null)
  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          crear.reset()
          setAviso(null)
          onCerrar()
        }
      }}
      titulo="Nuevo plan"
      descripcion="Cada peludo paga la tarifa de su plan según cuántos peludos tiene la afiliación, aunque estén en planes distintos."
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
          const datos = leerPlan(d)
          if (datos.ciudades.length === 0) {
            setAviso('Elige al menos una ciudad donde se vende el plan.')
            return
          }
          setAviso(null)
          crear.mutate(
            {
              codigo: String(d.get('codigo')).trim(),
              nombre: String(d.get('nombre')).trim(),
              descripcion: String(d.get('descripcion') ?? '').trim() || undefined,
              especies: d.getAll('especies').map(String),
              color: String(d.get('color')) as ColorPlan,
              ...datos,
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
        <label className="campo ancho">
          <span>Descripción</span>
          <textarea className="input" name="descripcion" rows={2} />
        </label>
        <CampoColor />
        <CampoEspecies />
        <CamposPlan />
        {(aviso || crear.isError) && (
          <p className="error ancho" role="alert">
            {aviso ?? mensajeError(crear.error, 'No fue posible crear el plan.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

const ETIQUETA_PELUDOS = ['1 peludo', '2 peludos (c/u)', '3 peludos (c/u)', '4 o más (c/u)']
const PERIODOS: Record<Periodicidad, string> = { mensual: 'Mensual', trimestral: 'Trimestral', semestral: 'Semestral', anual: 'Anual' }
const LARGOS = ['trimestral', 'semestral', 'anual'] as const

function tarifa(plan: PlanRead, peludos: number): string {
  return plan.tarifas.find((t) => t.peludos === peludos)?.valor ?? '0'
}

function valorLargo(plan: PlanRead | undefined, periodo: Periodicidad): number | string {
  const valor = plan?.tarifas_periodicidad.find((t) => t.periodicidad === periodo)?.valor
  return valor ? Number(valor) : ''
}

function leerPlan(d: FormData): { ciudades: string[]; tarifas: Tarifas } {
  const largo = (campo: string) => String(d.get(campo) ?? '').trim() || undefined
  return {
    ciudades: d.getAll('ciudades').map(String),
    tarifas: {
      por_peludos: [1, 2, 3, 4].map((n) => String(d.get(`tarifa_${n}`))) as Tarifas['por_peludos'],
      trimestral: largo('trimestral'),
      semestral: largo('semestral'),
      anual: largo('anual'),
    },
  }
}

const COLORES: Record<ColorPlan, string> = { verde: 'Verde', naranja: 'Naranja', azul: 'Azul' }

/** El color con el que la interfaz reconoce el plan (manual de marca, secciones 4 y 10). */
function CampoColor({ actual = 'verde' }: { actual?: ColorPlan }) {
  const id = useId()
  return (
    <div className="campo">
      <label htmlFor={id}>Color del plan</label>
      <select className="input" id={id} name="color" defaultValue={actual} aria-describedby={`${id}-ayuda`}>
        {(Object.keys(COLORES) as ColorPlan[]).map((c) => (
          <option key={c} value={c}>
            {COLORES[c]}
          </option>
        ))}
      </select>
      <span className="campo-ayuda" id={`${id}-ayuda`}>
        Uno de los colores del logo; así se reconoce el plan en el panel y en el portal.
      </span>
    </div>
  )
}

function CampoEspecies() {
  const especies = useEspecies()
  return (
    <fieldset className="ancho acciones">
      <legend>Especies (ninguna marcada = todas)</legend>
      {especies.data
        ?.filter((e) => e.activa)
        .map((e) => (
          <label key={e.codigo} className="acciones">
            <input type="checkbox" name="especies" value={e.codigo} />
            <span>{e.nombre}</span>
          </label>
        ))}
    </fieldset>
  )
}

/** Ciudades donde se vende, las cuatro tarifas por número de peludos y los periodos largos. */
function CamposPlan({ plan }: { plan?: PlanRead }) {
  const ciudades = useCiudades()
  return (
    <>
      <fieldset className="ancho acciones">
        <legend>Ciudades donde se vende</legend>
        {ciudades.data
          ?.filter((c) => c.activa)
          .map((c) => (
            <label key={c.nombre} className="acciones">
              <input type="checkbox" name="ciudades" value={c.nombre} defaultChecked={plan?.ciudades.includes(c.nombre)} />
              <span>{c.nombre}</span>
            </label>
          ))}
      </fieldset>
      <fieldset className="ancho formulario">
        <legend className="ancho">Valor mensual por peludo (COP)</legend>
        {ETIQUETA_PELUDOS.map((etiqueta, i) => (
          <label key={etiqueta} className="campo">
            <span>{etiqueta}</span>
            <input
              className="input"
              name={`tarifa_${i + 1}`}
              type="number"
              min={1}
              required
              defaultValue={plan ? Number(tarifa(plan, i + 1)) : undefined}
            />
          </label>
        ))}
      </fieldset>
      <fieldset className="ancho formulario">
        <legend className="ancho">Pago por periodo con un solo peludo (COP, total; vacío = sin descuento)</legend>
        {LARGOS.map((periodo) => (
          <label key={periodo} className="campo">
            <span>{PERIODOS[periodo]}</span>
            <input
              className="input"
              name={periodo}
              type="number"
              min={1}
              defaultValue={valorLargo(plan, periodo)}
            />
          </label>
        ))}
      </fieldset>
    </>
  )
}

function EditarPlan({ plan, onCerrar }: { plan: PlanRead; onCerrar: () => void }) {
  const tipos = useTiposServicio()
  const actualizar = useActualizarPlan()
  const guardarBeneficios = useGuardarBeneficios()
  const guardarTarifas = useGuardarTarifas()
  const guardarCiudades = useGuardarCiudades()
  const [aviso, setAviso] = useState<string | null>(null)
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
  const error = actualizar.error ?? guardarCiudades.error ?? guardarTarifas.error ?? guardarBeneficios.error
  const guardando = actualizar.isPending || guardarCiudades.isPending || guardarTarifas.isPending || guardarBeneficios.isPending

  function cambiar(i: number, cambio: Partial<Beneficio>) {
    setBeneficios((a) => a.map((b, j) => (j === i ? { ...b, ...cambio } : b)))
  }

  return (
    <Modal
      abierto
      onCambio={(v) => !v && onCerrar()}
      titulo={`Editar ${plan.nombre}`}
      descripcion="Las tarifas nuevas aplican a afiliaciones nuevas y a los recálculos; las cuotas ya emitidas no cambian."
      pie={
        <button className="btn btn-primario" type="submit" form="editar-plan" disabled={guardando}>
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
          const datos = leerPlan(d)
          if (datos.ciudades.length === 0) {
            setAviso('Elige al menos una ciudad donde se vende el plan.')
            return
          }
          setAviso(null)
          try {
            await actualizar.mutateAsync({ id: plan.id, nombre: String(d.get('nombre')).trim(), color: String(d.get('color')) as ColorPlan })
            await guardarCiudades.mutateAsync({ id: plan.id, ciudades: datos.ciudades })
            await guardarTarifas.mutateAsync({ id: plan.id, tarifas: datos.tarifas })
            await guardarBeneficios.mutateAsync({ id: plan.id, beneficios })
            onCerrar()
          } catch {
            // El error de cada paso lo muestra el aviso de abajo.
          }
        }}
      >
        <div className="formulario">
          <label className="campo ancho">
            <span>Nombre</span>
            <input className="input" name="nombre" defaultValue={plan.nombre} required />
          </label>
          <CampoColor actual={plan.color} />
          <CamposPlan plan={plan} />
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
        {(aviso || error) && (
          <p className="error" role="alert">
            {aviso ?? mensajeError(error, 'No fue posible guardar el plan.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
