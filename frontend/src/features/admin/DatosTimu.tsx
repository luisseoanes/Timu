import { useId, useState, type ReactNode } from 'react'

import { Consulta } from '@/components/Consulta'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useCiudades } from '@/features/catalogos'
import { mensajeError } from '@/lib/errores'
import { telefono } from '@/lib/formato'
import type { DatosTimuRead, Red } from '@/types'

import { useDatosTimu, useGuardarDatosTimu } from './api'

// Lo que dice de TIMU la portada pública (R3-PUB-04): quiénes son, su clínica, cómo se les escribe.
// Ficha de lectura y ventana para editar, como un plan (decidido con el usuario).

function Dato({ titulo, ancho, children }: { titulo: string; ancho?: boolean; children: ReactNode }) {
  return (
    <div className={ancho ? 'ancho' : undefined}>
      <dt>{titulo}</dt>
      <dd>{children}</dd>
    </div>
  )
}

const sinEscribir = (que: string) => <span className="apagado">Sin escribir: la portada no {que}.</span>

export function DatosTimu() {
  const datos = useDatosTimu()
  const [editando, setEditando] = useState(false)
  return (
    <Consulta consulta={datos} cargando="Cargando los datos de TIMU…" error="No fue posible consultar los datos de TIMU.">
      {(d) => (
        <section className="tarjeta pila datos-timu" aria-labelledby="datos-timu">
          <div className="tarjeta-cabeza">
            <h3 id="datos-timu">Lo que dice la portada de TIMU</h3>
            <button className="btn btn-primario" type="button" onClick={() => setEditando(true)}>
              <Icono nombre="editar" size={16} /> Editar
            </button>
          </div>
          <section className="bloque" aria-labelledby="datos-quienes">
            <h4 id="datos-quienes" className="subtitulo">Quiénes somos</h4>
            <dl className="ficha">
              <Dato titulo="Presentación" ancho>{d.presentacion ?? sinEscribir('la muestra')}</Dato>
              <Dato titulo="Misión" ancho>{d.mision ?? sinEscribir('la muestra')}</Dato>
              <Dato titulo="Visión" ancho>{d.vision ?? sinEscribir('la muestra')}</Dato>
              <Dato titulo="Valores" ancho>{d.valores.length ? d.valores.join(' · ') : sinEscribir('los muestra')}</Dato>
            </dl>
          </section>
          <section className="bloque" aria-labelledby="datos-clinica">
            <h4 id="datos-clinica" className="subtitulo">La clínica</h4>
            <dl className="ficha">
              <Dato titulo="Nombre">{d.clinica_nombre ?? sinEscribir('la muestra')}</Dato>
              <Dato titulo="Dónde">
                {d.clinica_direccion
                  ? [d.clinica_direccion, d.clinica_barrio, d.clinica_ciudad].filter(Boolean).join(', ')
                  : sinEscribir('dice dónde está')}
              </Dato>
              <Dato titulo="Horario" ancho>{d.clinica_horario ?? sinEscribir('lo dice')}</Dato>
            </dl>
          </section>
          <section className="bloque" aria-labelledby="datos-contacto">
            <h4 id="datos-contacto" className="subtitulo">Contacto</h4>
            <dl className="ficha">
              <Dato titulo="WhatsApp">{d.whatsapp ? <span className="numero">{telefono(d.whatsapp)}</span> : sinEscribir('ofrece escribir por WhatsApp')}</Dato>
              <Dato titulo="Teléfonos">
                {d.telefonos.length ? (
                  // Cada número entero: con espacios duros no se parte al cambiar de renglón.
                  <span className="numero">{d.telefonos.map((t) => telefono(t).replace(/ /g, '\u00a0')).join(' · ')}</span>
                ) : (
                  sinEscribir('los muestra')
                )}
              </Dato>
              <Dato titulo="Correo">{d.correo ?? sinEscribir('lo muestra')}</Dato>
              <Dato titulo="Horario de atención" ancho>{d.horario_atencion ?? sinEscribir('lo dice')}</Dato>
              <Dato titulo="Redes" ancho>
                {d.redes.length
                  ? d.redes.map((r, i) => (
                      <span key={r.url}>
                        {i > 0 && ' · '}
                        <a href={r.url} target="_blank" rel="noreferrer">
                          {r.nombre}
                        </a>
                      </span>
                    ))
                  : sinEscribir('enlaza ninguna')}
              </Dato>
              <Dato titulo="Política de tratamiento de datos" ancho>
                {d.politica_datos_url ? (
                  <a href={d.politica_datos_url} target="_blank" rel="noreferrer">
                    {d.politica_datos_url}
                  </a>
                ) : (
                  <span className="apagado">Sin enlace: el formulario de contacto solo dice para qué se usan los datos.</span>
                )}
              </Dato>
            </dl>
          </section>
          <section className="bloque" aria-labelledby="datos-empresa">
            <h4 id="datos-empresa" className="subtitulo">La empresa, al pie de la portada</h4>
            <dl className="ficha">
              <Dato titulo="Razón social">{d.razon_social ?? sinEscribir('la dice')}</Dato>
              <Dato titulo="NIT">{d.nit ? <span className="numero">{d.nit}</span> : sinEscribir('lo dice')}</Dato>
            </dl>
          </section>
          {editando && <EditarDatosTimu datos={d} onCerrar={() => setEditando(false)} />}
        </section>
      )}
    </Consulta>
  )
}

/** Una línea por elemento: así se escriben los valores y los teléfonos. */
const lineas = (v: FormDataEntryValue | null) =>
  String(v ?? '')
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean)

function EditarDatosTimu({ datos: d, onCerrar }: { datos: DatosTimuRead; onCerrar: () => void }) {
  const id = useId()
  const guardar = useGuardarDatosTimu()
  const ciudades = useCiudades()
  const [redes, setRedes] = useState<Red[]>(d.redes)
  // Controlado: con `defaultValue` el select se queda en «Sin ciudad» si el catálogo llega después,
  // y al guardar borraría la ciudad. La actual va siempre entre las opciones.
  const [ciudad, setCiudad] = useState(d.clinica_ciudad ?? '')
  const nombresCiudad = [...new Set([...(d.clinica_ciudad ? [d.clinica_ciudad] : []), ...(ciudades.data?.map((c) => c.nombre) ?? [])])].sort((a, b) =>
    a.localeCompare(b, 'es'),
  )
  const campo = (nombre: keyof DatosTimuRead, titulo: string, props: { ancho?: boolean; filas?: number; max?: number; tipo?: string; ayuda?: string } = {}) => {
    const valor = d[nombre]
    const comun = {
      id: `${id}-${nombre}`,
      className: 'input',
      name: nombre,
      maxLength: props.max ?? 255,
      defaultValue: Array.isArray(valor) ? (valor as string[]).join('\n') : ((valor as string | null) ?? ''),
      'aria-describedby': props.ayuda ? `${id}-${nombre}-ayuda` : undefined,
    }
    return (
      <div className={props.ancho ? 'campo ancho' : 'campo'}>
        <label htmlFor={comun.id}>{titulo}</label>
        {props.filas ? <textarea rows={props.filas} {...comun} /> : <input type={props.tipo ?? 'text'} {...comun} />}
        {props.ayuda && (
          <span className="campo-ayuda" id={`${id}-${nombre}-ayuda`}>
            {props.ayuda}
          </span>
        )}
      </div>
    )
  }

  return (
    <Modal
      abierto
      onCambio={(v) => !v && onCerrar()}
      titulo="Editar los datos de TIMU"
      descripcion="Lo que dice la portada pública. Un campo vacío no se muestra."
      pie={
        <button className="btn btn-primario" type="submit" form="datos-timu-form" disabled={guardar.isPending}>
          Guardar
        </button>
      }
    >
      <form
        id="datos-timu-form"
        className="pila"
        onSubmit={(e) => {
          e.preventDefault()
          const f = new FormData(e.currentTarget)
          const texto = (n: string) => String(f.get(n) ?? '').trim() || null
          guardar.mutate(
            {
              presentacion: texto('presentacion'),
              mision: texto('mision'),
              vision: texto('vision'),
              valores: lineas(f.get('valores')),
              clinica_nombre: texto('clinica_nombre'),
              clinica_direccion: texto('clinica_direccion'),
              clinica_barrio: texto('clinica_barrio'),
              clinica_ciudad: texto('clinica_ciudad'),
              clinica_horario: texto('clinica_horario'),
              whatsapp: texto('whatsapp'),
              telefonos: lineas(f.get('telefonos')),
              correo: texto('correo'),
              horario_atencion: texto('horario_atencion'),
              redes: redes.map((r) => ({ nombre: r.nombre.trim(), url: r.url.trim() })).filter((r) => r.nombre || r.url),
              politica_datos_url: texto('politica_datos_url'),
              razon_social: texto('razon_social'),
              nit: texto('nit'),
            },
            { onSuccess: onCerrar },
          )
        }}
      >
        <fieldset className="formulario">
          <legend className="ancho subtitulo">Quiénes somos</legend>
          {campo('presentacion', 'Presentación', { ancho: true, filas: 4, max: 4000 })}
          {campo('mision', 'Misión', { ancho: true, filas: 3, max: 4000 })}
          {campo('vision', 'Visión', { ancho: true, filas: 3, max: 4000 })}
          {campo('valores', 'Valores', { ancho: true, filas: 4, max: 800, ayuda: 'Uno por línea.' })}
        </fieldset>
        <fieldset className="formulario">
          <legend className="ancho subtitulo">La clínica</legend>
          {campo('clinica_nombre', 'Nombre de la clínica')}
          {campo('clinica_direccion', 'Dirección')}
          {campo('clinica_barrio', 'Barrio')}
          <div className="campo">
            <label htmlFor={`${id}-ciudad`}>Ciudad</label>
            <select id={`${id}-ciudad`} className="input" name="clinica_ciudad" value={ciudad} onChange={(e) => setCiudad(e.target.value)}>
              <option value="">Sin ciudad</option>
              {nombresCiudad.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          {campo('clinica_horario', 'Horario de la clínica', { ancho: true })}
        </fieldset>
        <fieldset className="formulario">
          <legend className="ancho subtitulo">Contacto</legend>
          {campo('whatsapp', 'WhatsApp', { tipo: 'tel', max: 20 })}
          {campo('correo', 'Correo', { tipo: 'email', max: 254 })}
          {campo('telefonos', 'Teléfonos', { filas: 3, max: 200, ayuda: 'Uno por línea, hasta seis.' })}
          {campo('horario_atencion', 'Horario de atención', { filas: 3, max: 4000 })}
          <div className="ancho pila">
            <span className="registro-foto-etiqueta">Redes</span>
            {redes.map((r, i) => (
              <div key={i} className="formulario datos-timu-red">
                <div className="campo">
                  <label htmlFor={`${id}-red-${i}-nombre`}>Nombre de la red {i + 1}</label>
                  <input
                    id={`${id}-red-${i}-nombre`}
                    className="input"
                    required
                    minLength={2}
                    maxLength={40}
                    value={r.nombre}
                    onChange={(e) => setRedes((l) => l.map((x, j) => (j === i ? { ...x, nombre: e.target.value } : x)))}
                  />
                </div>
                <div className="campo">
                  <label htmlFor={`${id}-red-${i}-url`}>Enlace de la red {i + 1}</label>
                  <input
                    id={`${id}-red-${i}-url`}
                    className="input"
                    type="url"
                    required
                    pattern="https://.*"
                    maxLength={300}
                    value={r.url}
                    onChange={(e) => setRedes((l) => l.map((x, j) => (j === i ? { ...x, url: e.target.value } : x)))}
                  />
                </div>
                <button className="btn btn-plano" type="button" onClick={() => setRedes((l) => l.filter((_, j) => j !== i))}>
                  Quitar la red {i + 1}
                </button>
              </div>
            ))}
            {redes.length < 8 && (
              <div>
                <button className="btn btn-secundario" type="button" onClick={() => setRedes((l) => [...l, { nombre: '', url: 'https://' }])}>
                  <Icono nombre="mas" size={16} /> Otra red
                </button>
              </div>
            )}
          </div>
          {campo('politica_datos_url', 'Enlace a la política de tratamiento de datos', {
            ancho: true,
            tipo: 'url',
            max: 500,
            ayuda: 'Lo enlaza el formulario de contacto (Ley 1581). Debe empezar por https://.',
          })}
        </fieldset>
        <fieldset className="formulario">
          <legend className="ancho subtitulo">La empresa</legend>
          {campo('razon_social', 'Razón social')}
          {campo('nit', 'NIT', { max: 20 })}
        </fieldset>
        {guardar.isError && (
          <p className="error" role="alert">
            {mensajeError(guardar.error, 'No fue posible guardar los datos de TIMU.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
