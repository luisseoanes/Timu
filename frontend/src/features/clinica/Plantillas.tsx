import * as Menu from '@radix-ui/react-dropdown-menu'
import { useId, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useNombreTipoServicio, useTiposServicio } from '@/features/catalogos'
import { mensajeError } from '@/lib/errores'
import type { PlantillaConsultaRead } from '@/types'

import { useCrearPlantilla, useEditarPlantilla, usePlantillas, useUsoPlantillas } from './api'
import { ESTACIONES, apartadosDePlantilla, enPalabras } from './consulta'

/** Plantillas de consulta en listado con ficha (DEU-15): el equipo médico las lee por apartado,
 * las corrige y las activa o desactiva. No se borran (nada de negocio se borra): la consulta copia
 * sus textos al crearse, así que lo ya registrado no cambia.
 * La abierta vive en la URL (`?plantilla=`). */
export function Plantillas() {
  const [params] = useSearchParams()
  const abierta = params.get('plantilla')
  return (
    <div className="con-ficha" data-abierta={abierta ? 'true' : undefined}>
      <PlantillasLista seleccionada={abierta} />
      {abierta ? (
        <FichaPlantilla key={abierta} codigo={abierta} />
      ) : (
        <section className="ficha-abierta ficha-vacia" aria-label="Plantilla abierta">
          <p>Abre una plantilla para leer lo que prellena en cada apartado de la consulta.</p>
        </section>
      )}
    </div>
  )
}

function usePlantillaEnlace() {
  const [params] = useSearchParams()
  return (codigo: string | null) => {
    const siguiente = new URLSearchParams(params)
    if (codigo) siguiente.set('plantilla', codigo)
    else siguiente.delete('plantilla')
    return `?${siguiente}`
  }
}

function PlantillasLista({ seleccionada }: { seleccionada: string | null }) {
  const plantillas = usePlantillas({ incluirInactivas: true })
  const enlace = usePlantillaEnlace()
  const navegar = useNavigate()
  const [nueva, setNueva] = useState(false)
  return (
    <section className="listado" aria-labelledby="plantillas-titulo">
      <div className="listado-cabeza">
        <h2 id="plantillas-titulo">
          Plantillas {plantillas.data && <span className="apagado numero">{plantillas.data.length}</span>}
        </h2>
        {/* Verde solo sin una plantilla abierta: con la ficha a la vista, el verde es de ella. */}
        <button className={`btn ${seleccionada ? 'btn-suave' : 'btn-primario'}`} type="button" onClick={() => setNueva(true)}>
          <Icono nombre="mas" size={16} /> Nueva plantilla
        </button>
      </div>
      <Consulta
        consulta={plantillas}
        cargando="Cargando las plantillas…"
        error="No fue posible cargar las plantillas."
        vacio="Aún no hay plantillas. Crea la primera con «Nueva plantilla»: agilizan las consultas frecuentes."
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <ul className="listado-filas" aria-label="Plantillas de consulta">
            {d.map((p) => (
              <li key={p.codigo} className="listado-fila" data-seleccionada={p.codigo === seleccionada}>
                <span className="listado-fila-cabeza">
                  {/* El enlace es solo el nombre; ::after lo extiende a toda la fila. */}
                  <Link className="listado-fila-enlace" to={enlace(p.codigo)} aria-current={p.codigo === seleccionada ? 'page' : undefined}>
                    {p.nombre}
                  </Link>
                  {!p.activa && <Insignia tono="neutro">Inactiva</Insignia>}
                </span>
                <span className="apagado">{resumen(p)}</span>
              </li>
            ))}
          </ul>
        )}
      </Consulta>
      <FormularioPlantilla
        abierto={nueva}
        onCerrar={() => setNueva(false)}
        alGuardar={(p) => {
          setNueva(false)
          navegar(enlace(p.codigo))
        }}
      />
    </section>
  )
}

/** «Prellena el motivo de consulta y el tratamiento», en el orden de la consulta. */
function resumen(p: PlantillaConsultaRead): string {
  const { llena, falta } = apartadosDePlantilla(p.campos)
  if (!llena.length) return 'No prellena ningún apartado'
  if (!falta.length) return 'Prellena los cinco apartados'
  return `Prellena ${enPalabras(llena.map((a) => a.enFrase))}`
}

/** Cuánto se ha usado: solo cuentan las consultas firmadas y vigentes. */
function textoDeUso(consultas: number): string {
  if (consultas === 0) return 'Aún sin consultas firmadas'
  return consultas === 1 ? 'Usada en 1 consulta firmada' : `Usada en ${consultas} consultas firmadas`
}

function FichaPlantilla({ codigo }: { codigo: string }) {
  const plantillas = usePlantillas({ incluirInactivas: true })
  const p = plantillas.data?.find((x) => x.codigo === codigo)
  return (
    <section className="ficha-abierta" aria-label="Plantilla abierta">
      <Consulta consulta={plantillas} cargando="Cargando la plantilla…" error="No fue posible cargar la plantilla.">
        {() => (p ? <Ficha plantilla={p} /> : <p className="apagado">Esta plantilla ya no existe.</p>)}
      </Consulta>
    </section>
  )
}

function Ficha({ plantilla: p }: { plantilla: PlantillaConsultaRead }) {
  const enlace = usePlantillaEnlace()
  const editar = useEditarPlantilla()
  const nombreTipo = useNombreTipoServicio()
  const uso = useUsoPlantillas()
  const [editando, setEditando] = useState(false)
  const { llena, falta } = apartadosDePlantilla(p.campos)

  return (
    <>
      <header className="ficha-cabeza">
        <Link to={enlace(null)} className="btn btn-plano ficha-volver" aria-label="Volver a las plantillas">
          <Icono nombre="volver" size={16} />
        </Link>
        <h2>{p.nombre}</h2>
        <div className="ficha-datos">
          <Insignia tono={p.activa ? 'ok' : 'neutro'}>{p.activa ? 'Activa' : 'Inactiva'}</Insignia>
          <span>
            Prellena {llena.length} de {ESTACIONES.length} apartados
          </span>
          {uso.data && <span>{textoDeUso(uso.data[p.codigo] ?? 0)}</span>}
          {p.tipo_servicio_codigo && <span>Para {nombreTipo(p.tipo_servicio_codigo).toLowerCase()}</span>}
        </div>
        <div className="ficha-acciones">
          <button className="btn btn-primario" type="button" onClick={() => setEditando(true)}>
            Editar plantilla
          </button>
          <Menu.Root modal={false}>
            <Menu.Trigger className="btn btn-secundario btn-icono" aria-label={`Más acciones con ${p.nombre}`}>
              <Icono nombre="puntos" size={18} />
            </Menu.Trigger>
            <Menu.Portal>
              <Menu.Content className="menu" align="end" sideOffset={6}>
                {/* Reversible: la consulta deja de ofrecerla y lo ya registrado no cambia. */}
                <Menu.Item className="menu-item" onSelect={() => editar.mutate({ codigo: p.codigo, activa: !p.activa })}>
                  {p.activa ? 'Desactivar plantilla' : 'Activar plantilla'}
                </Menu.Item>
              </Menu.Content>
            </Menu.Portal>
          </Menu.Root>
        </div>
        {!p.activa && (
          <p className="admin-nota">Inactiva: la consulta ya no la ofrece. Las consultas que partieron de ella no cambian.</p>
        )}
        {editar.isError && (
          <p className="error" role="alert">
            {mensajeError(editar.error, 'No fue posible actualizar la plantilla.')}
          </p>
        )}
      </header>

      {llena.length > 0 ? (
        <dl className="consulta-lectura">
          {llena.map(({ campo, titulo }) => (
            <div key={campo}>
              <dt>{titulo}</dt>
              <dd>{p.campos[campo]}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="apagado">No prellena ningún apartado: edítala para darle texto.</p>
      )}
      {llena.length > 0 && falta.length > 0 && (
        <p className="admin-nota">Deja en blanco {enPalabras(falta.map((a) => a.enFrase))}.</p>
      )}

      <FormularioPlantilla abierto={editando} plantilla={p} onCerrar={() => setEditando(false)} alGuardar={() => setEditando(false)} />
    </>
  )
}

/** Crear o editar: el nombre y el texto de cada apartado. El código lo saca la API del nombre. */
function FormularioPlantilla({
  abierto,
  plantilla,
  onCerrar,
  alGuardar,
}: {
  abierto: boolean
  plantilla?: PlantillaConsultaRead
  onCerrar: () => void
  alGuardar: (p: PlantillaConsultaRead) => void
}) {
  const crear = useCrearPlantilla()
  const editar = useEditarPlantilla()
  const guardar = plantilla ? editar : crear
  const id = plantilla ? 'editar-plantilla' : 'nueva-plantilla'
  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          guardar.reset()
          onCerrar()
        }
      }}
      titulo={plantilla ? 'Editar plantilla' : 'Nueva plantilla'}
      descripcion={
        plantilla
          ? 'Los cambios valen para las consultas nuevas; las que ya partieron de ella no cambian.'
          : 'Lo que escribas en cada apartado aparece en la consulta como punto de partida. Deja en blanco lo que no deba prellenar.'
      }
      pie={
        <button className="btn btn-primario" type="submit" form={id} disabled={guardar.isPending}>
          {guardar.isPending ? 'Guardando…' : 'Guardar plantilla'}
        </button>
      }
    >
      <form
        id={id}
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const d = new FormData(e.currentTarget)
          const campos: Record<string, string> = {}
          for (const { campo } of ESTACIONES) {
            const v = String(d.get(campo) ?? '').trim()
            if (v) campos[campo] = v
          }
          const nombre = String(d.get('nombre')).trim()
          const tipo_servicio_codigo = String(d.get('tipo_servicio_codigo') ?? '') || null
          if (plantilla) editar.mutate({ codigo: plantilla.codigo, nombre, tipo_servicio_codigo, campos }, { onSuccess: alGuardar })
          else crear.mutate({ nombre, tipo_servicio_codigo, campos }, { onSuccess: alGuardar })
        }}
      >
        <label className="campo">
          <span>Nombre</span>
          <input className="input" name="nombre" required minLength={3} maxLength={120} defaultValue={plantilla?.nombre} autoFocus />
        </label>
        <CampoTipoDeAtencion actual={plantilla?.tipo_servicio_codigo ?? null} />
        {ESTACIONES.map(({ campo, titulo }) => (
          <label key={campo} className="campo ancho">
            <span>{titulo}</span>
            <textarea className="input" name={campo} rows={3} maxLength={4000} defaultValue={plantilla?.campos[campo] ?? ''} />
          </label>
        ))}
        {guardar.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(guardar.error, 'No fue posible guardar la plantilla.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

/** A qué atención va la plantilla. Vive dentro del formulario: se reinicia cada vez que se abre. */
function CampoTipoDeAtencion({ actual }: { actual: string | null }) {
  const tipos = useTiposServicio()
  const nombreTipo = useNombreTipoServicio()
  const [valor, setValor] = useState(actual ?? '')
  const id = useId()
  const opciones = tipos.data ?? []
  // El que ya tiene sigue a la vista mientras carga el catálogo, o si el catálogo lo retiró.
  const faltaElActual = actual !== null && !opciones.some((t) => t.codigo === actual)
  return (
    <div className="campo">
      <label htmlFor={id}>Tipo de atención</label>
      <select
        id={id}
        className="input"
        name="tipo_servicio_codigo"
        value={valor}
        aria-describedby={`${id}-ayuda`}
        onChange={(e) => setValor(e.target.value)}
      >
        <option value="">Cualquier atención</option>
        {faltaElActual && <option value={actual}>{nombreTipo(actual)}</option>}
        {opciones.map((t) => (
          <option key={t.codigo} value={t.codigo}>
            {t.nombre}
          </option>
        ))}
      </select>
      <small id={`${id}-ayuda`} className="campo-ayuda">
        {valor ? 'En una visita solo se ofrece si es de este tipo.' : 'Se ofrece en cualquier visita.'}
      </small>
    </div>
  )
}
