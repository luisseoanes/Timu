import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useAuth } from '@/features/auth/AuthContext'
import { mensajeError } from '@/lib/errores'
import { fecha, fechaHora } from '@/lib/formato'
import { puede } from '@/lib/permisos'

import {
  CAMPOS_CLINICOS,
  urlAdjunto,
  useAdjuntar,
  useAdjuntos,
  useCorregirEntrada,
  useEditarEntrada,
  useEmitirFormula,
  useEntrada,
  useFirmarEntrada,
  type DatosEntrada,
  type EntradaHistoria,
  type ItemFormula,
} from './api'

/** Una consulta de la historia clínica: borrador editable, firma, corrección, adjuntos y fórmula. */
export function EntradaPage() {
  const { id = '' } = useParams()
  const entrada = useEntrada(id)
  return (
    <Consulta consulta={entrada} cargando="Cargando la consulta…" error="No fue posible cargar la consulta.">
      {(e) => <DetalleEntrada entrada={e} />}
    </Consulta>
  )
}

function DetalleEntrada({ entrada: e }: { entrada: EntradaHistoria }) {
  const { usuario } = useAuth()
  const navegar = useNavigate()
  const esMedico = puede(usuario, 'medico')
  const borrador = e.estado === 'borrador'
  const [editando, setEditando] = useState(false)
  const [corrigiendo, setCorrigiendo] = useState(false)
  const [formula, setFormula] = useState(false)
  const editar = useEditarEntrada(e.id)
  const firmar = useFirmarEntrada(e.id)
  const corregir = useCorregirEntrada(e.id)

  function datosDe(forma: HTMLFormElement): DatosEntrada {
    const d = new FormData(forma)
    const datos: DatosEntrada = {}
    for (const { campo } of CAMPOS_CLINICOS) datos[campo] = String(d.get(campo) ?? '').trim()
    return datos
  }

  return (
    <div className="pila">
      <div className="detalle-cabeza">
        <Link to={`/clinica/mascotas/${e.mascota_id}`} className="btn btn-plano" aria-label="Volver a la historia">
          <Icono nombre="volver" size={16} />
        </Link>
        <h1>Consulta del {fecha(e.fecha)}</h1>
        <Distintivo dominio="historia" valor={e.estado} />
        {e.version && e.version > 1 && <span className="distintivo distintivo-neutro">Versión {e.version}</span>}
        {esMedico && (
          <div className="acciones" style={{ marginLeft: 'auto' }}>
            {borrador && !editando && (
              <>
                <button className="btn btn-suave" type="button" onClick={() => setEditando(true)}>
                  <Icono nombre="editar" size={16} /> Editar
                </button>
                <button className="btn btn-primario" type="button" disabled={firmar.isPending} onClick={() => firmar.mutate()}>
                  Firmar consulta
                </button>
              </>
            )}
            {e.estado === 'firmada' && (
              <>
                <button className="btn btn-suave" type="button" onClick={() => setFormula(true)}>
                  Emitir fórmula
                </button>
                <button className="btn btn-plano" type="button" onClick={() => setCorrigiendo(true)}>
                  Corregir
                </button>
              </>
            )}
          </div>
        )}
      </div>
      {firmar.isError && (
        <p className="error" role="alert">
          {mensajeError(firmar.error, 'No fue posible firmar.')}
        </p>
      )}
      {e.firmada_en && <p className="apagado">Firmada el {fechaHora(e.firmada_en)}. Ya no se edita: los cambios van como corrección.</p>}

      <div className="con-rail">
        <section className="tarjeta">
          {editando ? (
            <form
              className="formulario"
              onSubmit={(ev) => {
                ev.preventDefault()
                editar.mutate(datosDe(ev.currentTarget), { onSuccess: () => setEditando(false) })
              }}
            >
              <CamposClinicos entrada={e} />
              {editar.isError && (
                <p className="error ancho" role="alert">
                  {mensajeError(editar.error, 'No fue posible guardar.')}
                </p>
              )}
              <div className="acciones ancho">
                <button className="btn btn-primario" type="submit" disabled={editar.isPending}>
                  Guardar cambios
                </button>
                <button className="btn btn-plano" type="button" onClick={() => setEditando(false)}>
                  Cancelar
                </button>
              </div>
            </form>
          ) : (
            <div className="pila">
              {CAMPOS_CLINICOS.map(({ campo, label }) =>
                e[campo] ? (
                  <div key={campo}>
                    <h4 className="subtitulo">{label}</h4>
                    <p style={{ whiteSpace: 'pre-wrap' }}>{e[campo]}</p>
                  </div>
                ) : null,
              )}
            </div>
          )}
        </section>
        <aside className="rail">
          <Adjuntos historiaId={e.id} puedeAdjuntar={esMedico} />
        </aside>
      </div>

      <Modal
        abierto={corrigiendo}
        onCambio={(v) => {
          if (!v) {
            corregir.reset()
            setCorrigiendo(false)
          }
        }}
        titulo="Corregir consulta firmada"
        descripcion="Se crea una nueva versión; la anterior queda guardada como corregida."
        pie={
          <button className="btn btn-primario" type="submit" form="corregir" disabled={corregir.isPending}>
            Guardar corrección
          </button>
        }
      >
        <form
          id="corregir"
          className="formulario"
          onSubmit={(ev) => {
            ev.preventDefault()
            corregir.mutate(datosDe(ev.currentTarget), {
              onSuccess: (nueva) => {
                setCorrigiendo(false)
                navegar(`/clinica/historias/${nueva.id}`)
              },
            })
          }}
        >
          <CamposClinicos entrada={e} />
          {corregir.isError && (
            <p className="error ancho" role="alert">
              {mensajeError(corregir.error, 'No fue posible corregir.')}
            </p>
          )}
        </form>
      </Modal>
      <FormulaModal historiaId={e.id} abierto={formula} onCerrar={() => setFormula(false)} />
    </div>
  )
}

function CamposClinicos({ entrada }: { entrada: EntradaHistoria }) {
  return (
    <>
      {CAMPOS_CLINICOS.map(({ campo, label }) => (
        <label key={campo} className="campo ancho">
          <span>{label}</span>
          <textarea
            className="input"
            name={campo}
            rows={campo === 'motivo' ? 2 : 4}
            required={campo === 'motivo'}
            defaultValue={entrada[campo] ?? ''}
          />
        </label>
      ))}
    </>
  )
}

function Adjuntos({ historiaId, puedeAdjuntar }: { historiaId: string; puedeAdjuntar: boolean }) {
  const adjuntos = useAdjuntos(historiaId)
  const adjuntar = useAdjuntar(historiaId)
  const [archivo, setArchivo] = useState<File | null>(null)
  const [descripcion, setDescripcion] = useState('')
  // Cambiar la key vuelve a montar el input de archivo: es la forma de vaciarlo.
  const [claveArchivo, setClaveArchivo] = useState(0)
  const [errorApertura, setErrorApertura] = useState<string | null>(null)

  async function abrir(id: string) {
    setErrorApertura(null)
    try {
      window.open(await urlAdjunto(id), '_blank', 'noopener')
    } catch (err) {
      setErrorApertura(mensajeError(err, 'No fue posible abrir el adjunto.'))
    }
  }

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Adjuntos</h3>
      </div>
      <Consulta
        consulta={adjuntos}
        cargando="Cargando adjuntos…"
        error="No fue posible cargar los adjuntos."
        vacio="Sin exámenes ni imágenes adjuntas."
        estaVacio={(d) => d.length === 0}
      >
        {(d) =>
          d.map((a) => (
            <button key={a.id} type="button" className="fila opcion" onClick={() => abrir(a.id)}>
              <span className="fila-icono">
                <Icono nombre="descargar" size={16} />
              </span>
              <span className="fila-cuerpo">
                <strong>{a.nombre_archivo}</strong>
                <span>{a.descripcion ?? fechaHora(a.created_at)}</span>
              </span>
            </button>
          ))
        }
      </Consulta>
      {errorApertura && (
        <p className="error" role="alert">
          {errorApertura}
        </p>
      )}
      {puedeAdjuntar && (
        <form
          className="pila"
          style={{ marginTop: 'var(--e4)', gap: 'var(--e2)' }}
          onSubmit={(e) => {
            e.preventDefault()
            if (archivo)
              adjuntar.mutate(
                { archivo, descripcion: descripcion.trim() || undefined },
                {
                  onSuccess: () => {
                    setArchivo(null)
                    setDescripcion('')
                    setClaveArchivo((c) => c + 1)
                  },
                },
              )
          }}
        >
          <label className="campo">
            <span>Archivo (JPG, PNG, WEBP o PDF)</span>
            <input
              key={claveArchivo}
              className="input"
              type="file"
              accept="image/jpeg,image/png,image/webp,application/pdf"
              onChange={(e) => setArchivo(e.target.files?.[0] ?? null)}
            />
          </label>
          <label className="campo">
            <span>Descripción</span>
            <input className="input" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />
          </label>
          <button className="btn btn-suave" type="submit" disabled={!archivo || adjuntar.isPending}>
            <Icono nombre="subir" size={16} /> {adjuntar.isPending ? 'Subiendo…' : 'Adjuntar'}
          </button>
          {adjuntar.isError && (
            <p className="error" role="alert">
              {mensajeError(adjuntar.error, 'No fue posible subir el archivo.')}
            </p>
          )}
        </form>
      )}
    </section>
  )
}

const ITEM_VACIO: ItemFormula = { medicamento: '', dosis: '', frecuencia: '', duracion: '' }

function FormulaModal({ historiaId, abierto, onCerrar }: { historiaId: string; abierto: boolean; onCerrar: () => void }) {
  const emitir = useEmitirFormula(historiaId)
  const [items, setItems] = useState<ItemFormula[]>([{ ...ITEM_VACIO }])
  const [indicaciones, setIndicaciones] = useState('')

  function cambiar(i: number, campo: keyof ItemFormula, valor: string) {
    setItems((actuales) => actuales.map((it, j) => (j === i ? { ...it, [campo]: valor } : it)))
  }

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          emitir.reset()
          setItems([{ ...ITEM_VACIO }])
          onCerrar()
        }
      }}
      titulo="Fórmula médica"
      descripcion="Se genera el PDF firmado; la familia lo ve en su portal."
      pie={
        !emitir.isSuccess && (
          <button className="btn btn-primario" type="submit" form="formula" disabled={emitir.isPending}>
            Emitir fórmula
          </button>
        )
      }
    >
      {emitir.isSuccess ? (
        <p className="aviso-ok" role="status">
          Fórmula emitida. <a href={emitir.data.url} target="_blank" rel="noreferrer">Abrir PDF</a>
        </p>
      ) : (
        <form
          id="formula"
          className="pila"
          onSubmit={(e) => {
            e.preventDefault()
            const limpios = items
              .filter((it) => it.medicamento.trim())
              .map((it) => Object.fromEntries(Object.entries(it).filter(([, v]) => v && String(v).trim())) as unknown as ItemFormula)
            emitir.mutate({ items: limpios, indicaciones: indicaciones.trim() || undefined })
          }}
        >
          {items.map((it, i) => (
            <fieldset key={i} className="formulario">
              <legend className="ancho">Medicamento {i + 1}</legend>
              <label className="campo ancho">
                <span>Medicamento</span>
                <input className="input" value={it.medicamento} onChange={(e) => cambiar(i, 'medicamento', e.target.value)} required={i === 0} />
              </label>
              <label className="campo">
                <span>Dosis</span>
                <input className="input" value={it.dosis ?? ''} onChange={(e) => cambiar(i, 'dosis', e.target.value)} />
              </label>
              <label className="campo">
                <span>Frecuencia</span>
                <input className="input" value={it.frecuencia ?? ''} onChange={(e) => cambiar(i, 'frecuencia', e.target.value)} />
              </label>
              <label className="campo">
                <span>Duración</span>
                <input className="input" value={it.duracion ?? ''} onChange={(e) => cambiar(i, 'duracion', e.target.value)} />
              </label>
            </fieldset>
          ))}
          <button className="btn btn-plano" type="button" onClick={() => setItems((a) => [...a, { ...ITEM_VACIO }])}>
            <Icono nombre="mas" size={16} /> Otro medicamento
          </button>
          <label className="campo">
            <span>Indicaciones generales</span>
            <textarea className="input" rows={2} value={indicaciones} onChange={(e) => setIndicaciones(e.target.value)} />
          </label>
          {emitir.isError && (
            <p className="error" role="alert">
              {mensajeError(emitir.error, 'No fue posible emitir la fórmula.')}
            </p>
          )}
        </form>
      )}
    </Modal>
  )
}
