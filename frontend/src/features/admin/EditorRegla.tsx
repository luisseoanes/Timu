import { useEffect, useId, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'
import type { BorradorRegla, CampoEvento, EventoDeReglas, ReglaRead } from '@/types'

import { useActualizarRegla, useCrearRegla, useEventosReglas, useReglaEnPalabras } from './api'
import {
  accionCompleta,
  armarAccion,
  armarCondicion,
  comparacionCompleta,
  leerCondicion,
  nuevaComparacion,
  parametrosIniciales,
  valorInicial,
  type Comparacion,
  type CondicionEditable,
} from './reglas'

/**
 * Crear o editar una regla por campos (DEU-8): cuándo se revisa, cuándo aplica (comparaciones
 * sobre los datos que da su evento), qué hace y cuándo vale. Arriba, la regla en palabras, que
 * la API rehace con cada cambio: quien la escribe lee lo que va a pasar antes de guardar.
 */
export function EditorRegla({ regla, onCerrar }: { regla?: ReglaRead; onCerrar: () => void }) {
  const eventos = useEventosReglas()
  return (
    <Modal
      abierto
      onCambio={(v) => !v && onCerrar()}
      titulo={regla ? `Editar «${regla.nombre}»` : 'Nueva regla'}
      descripcion={regla ? regla.evento_nombre : 'Elige cuándo se revisa, cuándo aplica y qué hace.'}
      pie={
        <button className="btn btn-primario" type="submit" form="editor-regla" disabled={!eventos.data}>
          {regla ? 'Guardar' : 'Crear regla'}
        </button>
      }
    >
      <Consulta consulta={eventos} cargando="Cargando los datos de las reglas…" error="No fue posible cargar los datos de las reglas.">
        {(datos) => <Formulario eventos={datos} regla={regla} onCerrar={onCerrar} />}
      </Consulta>
    </Modal>
  )
}

function Formulario({ eventos, regla, onCerrar }: { eventos: EventoDeReglas[]; regla?: ReglaRead; onCerrar: () => void }) {
  const id = useId()
  const [params, setParams] = useSearchParams()
  const crear = useCrearRegla()
  const actualizar = useActualizarRegla()
  const guardando = crear.isPending || actualizar.isPending
  const error = crear.error ?? actualizar.error

  const [eventoCodigo, setEventoCodigo] = useState(regla?.evento ?? eventos[0]!.evento)
  const evento = eventos.find((e) => e.evento === eventoCodigo)!
  // Una condición con grupos dentro de grupos se escribió por la API: se lee y se conserva.
  const [condicion, setCondicion] = useState<CondicionEditable | null>(() =>
    regla ? leerCondicion(regla.condicion) : { union: 'todas', comparaciones: [] },
  )
  const [accionTipo, setAccionTipo] = useState(regla?.accion.tipo as string | undefined ?? evento.acciones[0]!.tipo)
  const [parametros, setParametros] = useState(() => parametrosIniciales(evento, accionTipo, regla))

  // Cambiar el evento cambia los datos y las acciones posibles: lo escrito no le sirve al otro.
  const cambiarEvento = (codigo: string) => {
    const otro = eventos.find((e) => e.evento === codigo)!
    setEventoCodigo(codigo)
    setCondicion({ union: 'todas', comparaciones: [] })
    setAccionTipo(otro.acciones[0]!.tipo)
    setParametros(parametrosIniciales(otro, otro.acciones[0]!.tipo))
  }

  const completa =
    (condicion === null || condicion.comparaciones.every(comparacionCompleta)) && accionCompleta(evento, accionTipo, parametros)
  const condicionArmada = condicion ? armarCondicion(condicion, evento.campos) : regla!.condicion
  const accionArmada = armarAccion(evento, accionTipo, parametros)
  const borrador = useRetrasado<BorradorRegla | null>(
    completa ? { evento: eventoCodigo, condicion: condicionArmada, accion: accionArmada } : null,
  )

  return (
    <form
      id="editor-regla"
      className="formulario editor-regla"
      onSubmit={(e) => {
        e.preventDefault()
        const d = new FormData(e.currentTarget)
        const texto = (nombre: string) => String(d.get(nombre) ?? '').trim()
        const datos = {
          nombre: texto('nombre'),
          descripcion: texto('descripcion') || null,
          ...(condicion ? { condicion: condicionArmada } : {}),
          accion: accionArmada,
          prioridad: Number(texto('prioridad')),
          detener: texto('detener') === 'true',
          plan_id: evento.admite_plan ? texto('plan_id') || null : null,
          vigente_desde: texto('vigente_desde') || null,
          vigente_hasta: texto('vigente_hasta') || null,
        }
        if (regla) {
          actualizar.mutate({ id: regla.id, ...datos }, { onSuccess: onCerrar })
          return
        }
        // Se abre la regla creada: lo siguiente es probarla.
        crear.mutate(
          { ...datos, evento: eventoCodigo },
          {
            onSuccess: (creada) => {
              const siguiente = new URLSearchParams(params)
              siguiente.set('regla', creada.id)
              setParams(siguiente)
              onCerrar()
            },
          },
        )
      }}
    >
      <EnPalabras borrador={borrador} completa={completa} />

      {!regla && (
        <div className="campo ancho">
          <label htmlFor={`${id}-evento`}>Cuándo se revisa</label>
          <select id={`${id}-evento`} className="input" value={eventoCodigo} aria-describedby={`${id}-cuando`} onChange={(e) => cambiarEvento(e.target.value)}>
            {eventos.map((e) => (
              <option key={e.evento} value={e.evento}>
                {e.nombre}
              </option>
            ))}
          </select>
          <span className="campo-ayuda" id={`${id}-cuando`}>
            {evento.cuando}
          </span>
        </div>
      )}
      <div className="campo ancho">
        <label htmlFor={`${id}-nombre`}>Nombre</label>
        <input id={`${id}-nombre`} className="input" name="nombre" required minLength={2} maxLength={160} defaultValue={regla?.nombre} />
      </div>

      <CuandoAplica evento={evento} condicion={condicion} texto={regla?.condicion_texto} onCambio={setCondicion} />
      <QueHace
        evento={evento}
        tipo={accionTipo}
        parametros={parametros}
        onTipo={(t) => {
          setAccionTipo(t)
          setParametros(parametrosIniciales(evento, t, regla))
        }}
        onParametro={(nombre, valor) => setParametros((p) => ({ ...p, [nombre]: valor }))}
      />

      <fieldset className="ancho formulario">
        <legend className="ancho">Orden y vigencia</legend>
        <div className="campo">
          <label htmlFor={`${id}-prioridad`}>Prioridad</label>
          <input
            id={`${id}-prioridad`}
            className="input"
            name="prioridad"
            type="number"
            min={0}
            max={10000}
            required
            aria-describedby={`${id}-prioridad-ayuda`}
            defaultValue={regla?.prioridad ?? 100}
          />
          <span className="campo-ayuda" id={`${id}-prioridad-ayuda`}>
            Las de un mismo evento se evalúan de menor a mayor.
          </span>
        </div>
        <div className="campo">
          <label htmlFor={`${id}-detener`}>Si aplica</label>
          <select id={`${id}-detener`} className="input" name="detener" defaultValue={String(regla?.detener ?? false)}>
            <option value="false">Sigue con las siguientes</option>
            <option value="true">No evalúa las siguientes</option>
          </select>
        </div>
        {evento.admite_plan && (
          <div className="campo ancho">
            <label htmlFor={`${id}-plan`}>Planes</label>
            <select id={`${id}-plan`} className="input" name="plan_id" defaultValue={regla?.plan_id ?? ''}>
              <option value="">Todos los planes</option>
              {evento.planes.map((p) => (
                <option key={p.id} value={p.id}>
                  Solo {p.nombre}
                </option>
              ))}
            </select>
          </div>
        )}
        <div className="campo">
          <label htmlFor={`${id}-desde`}>Vale desde</label>
          <input id={`${id}-desde`} className="input" name="vigente_desde" type="date" defaultValue={regla?.vigente_desde ?? ''} />
        </div>
        <div className="campo">
          <label htmlFor={`${id}-hasta`}>Vale hasta</label>
          <input id={`${id}-hasta`} className="input" name="vigente_hasta" type="date" defaultValue={regla?.vigente_hasta ?? ''} />
        </div>
      </fieldset>

      <div className="campo ancho">
        <label htmlFor={`${id}-descripcion`}>Para qué sirve</label>
        <textarea id={`${id}-descripcion`} className="input" name="descripcion" rows={2} maxLength={2000} defaultValue={regla?.descripcion ?? ''} />
      </div>

      {error && !guardando && (
        <p className="error ancho" role="alert">
          {mensajeError(error, regla ? 'No fue posible guardar la regla.' : 'No fue posible crear la regla.')}
        </p>
      )}
    </form>
  )
}

/** El valor después de 300 ms sin cambios: la regla en palabras no se pide a cada tecla. */
function useRetrasado<T>(valor: T): T {
  const clave = JSON.stringify(valor)
  const [retrasado, setRetrasado] = useState(valor)
  useEffect(() => {
    const t = setTimeout(() => setRetrasado(JSON.parse(clave) as T), 300)
    return () => clearTimeout(t)
  }, [clave])
  return retrasado
}

/** La regla como la va a leer el equipo, o lo que la API le objeta. */
function EnPalabras({ borrador, completa }: { borrador: BorradorRegla | null; completa: boolean }) {
  const palabras = useReglaEnPalabras(borrador)
  return (
    <section className="ancho regla-en-palabras" aria-label="La regla en palabras" aria-live="polite">
      <div className="regla-en-palabras-caja">
        {!completa ? (
          <p className="apagado">Completa cada condición y lo que hace para leer la regla entera.</p>
        ) : palabras.isError ? (
          <p className="error">{mensajeError(palabras.error, 'No fue posible leer la regla.')}</p>
        ) : palabras.data ? (
          <dl>
            <div>
              <dt>Cuándo aplica</dt>
              <dd>{palabras.data.condicion_texto}</dd>
            </div>
            <div>
              <dt>Qué hace</dt>
              <dd>{palabras.data.accion_texto}</dd>
            </div>
          </dl>
        ) : (
          <p className="apagado">Leyendo la regla…</p>
        )}
      </div>
    </section>
  )
}

function CuandoAplica({
  evento,
  condicion,
  texto,
  onCambio,
}: {
  evento: EventoDeReglas
  condicion: CondicionEditable | null
  texto?: string
  onCambio: (c: CondicionEditable) => void
}) {
  const id = useId()
  if (condicion === null) {
    return (
      <fieldset className="ancho formulario">
        <legend className="ancho">Cuándo aplica</legend>
        <p className="ancho">{texto}</p>
        <p className="admin-nota ancho">Esta condición tiene grupos dentro de grupos y se escribió fuera del panel: aquí no se edita, y al guardar se conserva tal cual.</p>
      </fieldset>
    )
  }
  const { comparaciones } = condicion
  const cambiar = (i: number, c: Comparacion) => onCambio({ ...condicion, comparaciones: comparaciones.map((x, j) => (j === i ? c : x)) })
  // Una condición nueva propone el primer dato que aún no se compara.
  const siguiente = evento.campos.find((c) => !comparaciones.some((x) => x.campo === c.campo)) ?? evento.campos[0]!
  return (
    <fieldset className="ancho regla-condicion">
      <legend>Cuándo aplica</legend>
      {comparaciones.length > 1 && (
        <div className="campo regla-union">
          <label htmlFor={`${id}-union`}>Aplica si se cumplen</label>
          <select id={`${id}-union`} className="input" value={condicion.union} onChange={(e) => onCambio({ ...condicion, union: e.target.value as CondicionEditable['union'] })}>
            <option value="todas">Todas las condiciones</option>
            <option value="alguna">Al menos una</option>
          </select>
        </div>
      )}
      {comparaciones.length === 0 ? (
        <p className="admin-nota">Sin condiciones: aplica siempre.</p>
      ) : (
        <ol className="regla-comparaciones">
          {comparaciones.map((c, i) => (
            <FilaComparacion
              key={i}
              numero={i + 1}
              campos={evento.campos}
              comparacion={c}
              onCambio={(nueva) => cambiar(i, nueva)}
              onQuitar={() => onCambio({ ...condicion, comparaciones: comparaciones.filter((_, j) => j !== i) })}
            />
          ))}
        </ol>
      )}
      <div>
        <button className="btn btn-secundario" type="button" onClick={() => onCambio({ ...condicion, comparaciones: [...comparaciones, nuevaComparacion(siguiente)] })}>
          <Icono nombre="mas" size={16} /> {comparaciones.length === 0 ? 'Añadir una condición' : 'Otra condición'}
        </button>
      </div>
    </fieldset>
  )
}

function FilaComparacion({
  numero,
  campos,
  comparacion: c,
  onCambio,
  onQuitar,
}: {
  numero: number
  campos: CampoEvento[]
  comparacion: Comparacion
  onCambio: (c: Comparacion) => void
  onQuitar: () => void
}) {
  const id = useId()
  const campo = campos.find((x) => x.campo === c.campo)!
  const sufijo = `de la condición ${numero}`
  return (
    <li className="regla-comparacion">
      <div className="campo">
        <label htmlFor={`${id}-campo`}>Dato</label>
        <select
          id={`${id}-campo`}
          className="input"
          aria-label={`Dato ${sufijo}`}
          value={c.campo}
          onChange={(e) => onCambio(nuevaComparacion(campos.find((x) => x.campo === e.target.value)!))}
        >
          {campos.map((x) => (
            <option key={x.campo} value={x.campo}>
              {x.nombre}
            </option>
          ))}
        </select>
      </div>
      <div className="campo">
        <label htmlFor={`${id}-op`}>Comparación</label>
        <select
          id={`${id}-op`}
          className="input"
          aria-label={`Comparación ${sufijo}`}
          value={c.op}
          onChange={(e) => {
            const op = e.target.value
            // De una opción a varias (o al revés) el valor cambia de forma: se conserva lo elegido.
            const varias = op === 'in' || op === 'nin'
            const valor = varias ? (Array.isArray(c.valor) ? c.valor : c.valor ? [c.valor] : []) : Array.isArray(c.valor) ? (c.valor[0] ?? valorInicial(campo, op)) : c.valor
            onCambio({ ...c, op, valor })
          }}
        >
          {campo.operadores.map((o) => (
            <option key={o.valor} value={o.valor}>
              {o.nombre}
            </option>
          ))}
        </select>
      </div>
      <Valor id={`${id}-valor`} etiqueta={`Valor ${sufijo}`} campo={campo} comparacion={c} onCambio={(valor) => onCambio({ ...c, valor })} />
      <button className="btn btn-plano btn-icono regla-quitar" type="button" aria-label={`Quitar la condición ${numero}`} onClick={onQuitar}>
        <Icono nombre="cerrar" size={18} />
      </button>
    </li>
  )
}

function Valor({
  id,
  etiqueta,
  campo,
  comparacion: c,
  onCambio,
}: {
  id: string
  etiqueta: string
  campo: CampoEvento
  comparacion: Comparacion
  onCambio: (valor: string | string[]) => void
}) {
  if (Array.isArray(c.valor)) {
    const elegidos = c.valor
    return (
      <fieldset className="regla-valores">
        <legend>
          Valores <span className="sr-only">{etiqueta}</span>
        </legend>
        {campo.opciones?.map((o) => (
          <label key={o.valor} className="acciones">
            <input
              type="checkbox"
              checked={elegidos.includes(o.valor)}
              onChange={(e) => onCambio(e.target.checked ? [...elegidos, o.valor] : elegidos.filter((v) => v !== o.valor))}
            />
            <span>{o.nombre}</span>
          </label>
        ))}
      </fieldset>
    )
  }
  return (
    <div className="campo">
      <label htmlFor={id}>Valor</label>
      {campo.tipo === 'numero' ? (
        <input id={id} className="input" aria-label={etiqueta} type="number" step="any" required value={c.valor} onChange={(e) => onCambio(e.target.value)} />
      ) : campo.tipo === 'si_no' ? (
        <select id={id} className="input" aria-label={etiqueta} value={c.valor} onChange={(e) => onCambio(e.target.value)}>
          <option value="true">Sí</option>
          <option value="false">No</option>
        </select>
      ) : (
        <select id={id} className="input" aria-label={etiqueta} required value={c.valor} onChange={(e) => onCambio(e.target.value)}>
          <option value="" disabled>
            Elige…
          </option>
          {campo.opciones?.map((o) => (
            <option key={o.valor} value={o.valor}>
              {o.nombre}
            </option>
          ))}
        </select>
      )}
    </div>
  )
}

function QueHace({
  evento,
  tipo,
  parametros,
  onTipo,
  onParametro,
}: {
  evento: EventoDeReglas
  tipo: string
  parametros: Record<string, string>
  onTipo: (tipo: string) => void
  onParametro: (nombre: string, valor: string) => void
}) {
  const id = useId()
  const accion = useMemo(() => evento.acciones.find((a) => a.tipo === tipo)!, [evento, tipo])
  return (
    <fieldset className="ancho formulario">
      <legend className="ancho">Qué hace</legend>
      {evento.acciones.length > 1 ? (
        <div className="campo ancho">
          <label htmlFor={`${id}-tipo`}>Acción</label>
          <select id={`${id}-tipo`} className="input" value={tipo} onChange={(e) => onTipo(e.target.value)}>
            {evento.acciones.map((a) => (
              <option key={a.tipo} value={a.tipo}>
                {a.nombre}
              </option>
            ))}
          </select>
        </div>
      ) : (
        // Una sola acción posible: se dice como un dato con su etiqueta, no como otro título.
        <dl className="ancho regla-accion-unica">
          <dt>Acción</dt>
          <dd>{accion.nombre}</dd>
        </dl>
      )}
      {accion.parametros.map((p) => {
        const valor = parametros[p.nombre] ?? ''
        const control = `${id}-${p.nombre}`
        return (
          // Un texto libre, o una lista con nombres largos («Aviso de mora · aún sin registrar»), a todo el ancho.
          <div key={p.nombre} className={`campo${p.tipo === 'texto' || p.opciones?.some((o) => o.nombre.length > 24) ? ' ancho' : ''}`}>
            <label htmlFor={control}>{p.etiqueta}</label>
            {p.opciones ? (
              <select id={control} className="input" required={p.requerido} value={valor} onChange={(e) => onParametro(p.nombre, e.target.value)}>
                {valor === '' && (
                  <option value="" disabled>
                    Elige…
                  </option>
                )}
                {p.opciones.map((o) => (
                  <option key={o.valor} value={o.valor}>
                    {o.nombre}
                  </option>
                ))}
              </select>
            ) : (
              <input
                id={control}
                className="input"
                type={p.tipo === 'numero' ? 'number' : 'text'}
                min={p.tipo === 'numero' ? 0 : undefined}
                required={p.requerido}
                value={valor}
                onChange={(e) => onParametro(p.nombre, e.target.value)}
              />
            )}
          </div>
        )
      })}
    </fieldset>
  )
}
