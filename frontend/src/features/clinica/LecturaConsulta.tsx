import { useState, type ReactNode } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo, Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useAuth } from '@/features/auth'
import { mensajeError } from '@/lib/errores'
import { fecha, fechaHora } from '@/lib/formato'
import { puede } from '@/lib/permisos'

import {
  CAMPOS_CLINICOS,
  urlAdjunto,
  useAdjuntar,
  useAdjuntos,
  useCorregirEntrada,
  useEmitirFormula,
  type DatosEntrada,
  type EntradaHistoria,
  type ItemFormula,
} from './api'

/**
 * Una consulta que se lee: la firmada (que se corrige con una versión nueva y de la que se emite
 * la fórmula), la corregida y el borrador de otro profesional. Con sus adjuntos.
 */
export function LecturaConsulta({ entrada: e, volver, identidad }: { entrada: EntradaHistoria; volver: string; identidad?: ReactNode }) {
  const { usuario } = useAuth()
  const navegar = useNavigate()
  const { state } = useLocation() as { state: { recienFirmada?: boolean } | null }
  const esMedico = puede(usuario, 'medico')
  const firmada = e.estado === 'firmada'
  const [corrigiendo, setCorrigiendo] = useState(false)
  const [formula, setFormula] = useState(false)
  const corregir = useCorregirEntrada(e.id)
  const apartados = CAMPOS_CLINICOS.filter(({ campo }) => e[campo])

  return (
    <section className="ficha-abierta" aria-label="Consulta abierta">
      <header className="ficha-cabeza">
        <Link to={volver} className="btn btn-plano ficha-volver" aria-label="Volver a la historia">
          <Icono nombre="volver" size={16} />
        </Link>
        {identidad}
        <h2 className="consulta-titulo">Consulta del {fecha(e.fecha)}</h2>
        <div className="ficha-datos">
          <Distintivo dominio="historia" valor={e.estado} />
          {e.version && e.version > 1 && <Insignia tono="neutro">Versión {e.version}</Insignia>}
          <span className="apagado">{e.tipo === 'domiciliaria' ? 'Domiciliaria' : 'Presencial'}</span>
        </div>
        {state?.recienFirmada && firmada && e.servicio_id && (
          <p className="aviso-ok" role="status">
            Consulta firmada. Los pasos del servicio quedaron registrados: ya puedes terminar la visita.
          </p>
        )}
        {esMedico && firmada && (
          <div className="ficha-acciones">
            {state?.recienFirmada && e.servicio_id && (
              <Link className="btn btn-primario" to="/rutas">
                Volver a la ruta
              </Link>
            )}
            <button className="btn btn-suave" type="button" onClick={() => setFormula(true)}>
              Emitir fórmula
            </button>
            <button className="btn btn-plano" type="button" onClick={() => setCorrigiendo(true)}>
              Corregir
            </button>
          </div>
        )}
      </header>
      {/* La hora termina en «p. m.»: un punto detrás se leería doble. */}
      {e.firmada_en && <p className="apagado">Firmada el {fechaHora(e.firmada_en)} · Ya no se edita: los cambios van como corrección.</p>}
      {e.estado === 'borrador' && (
        <p className="aviso">Borrador de otro profesional: solo quien lo abrió lo escribe y lo firma.</p>
      )}

      <dl className="consulta-lectura">
        {apartados.map(({ campo, label }) => (
          <div key={campo}>
            <dt>{label}</dt>
            <dd>{e[campo]}</dd>
          </div>
        ))}
      </dl>

      <Adjuntos historiaId={e.id} puedeAdjuntar={esMedico} />

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
            {corregir.isPending ? 'Guardando…' : 'Guardar corrección'}
          </button>
        }
      >
        <form
          id="corregir"
          className="formulario"
          onSubmit={(ev) => {
            ev.preventDefault()
            const d = new FormData(ev.currentTarget)
            const datos: DatosEntrada = {}
            for (const { campo } of CAMPOS_CLINICOS) datos[campo] = String(d.get(campo) ?? '').trim()
            corregir.mutate(datos, {
              onSuccess: (nueva) => {
                setCorrigiendo(false)
                navegar(`/clinica/historias/${nueva.id}`)
              },
            })
          }}
        >
          {CAMPOS_CLINICOS.map(({ campo, label }) => (
            <label key={campo} className="campo ancho">
              <span>{label}</span>
              <textarea
                className="input"
                name={campo}
                rows={campo === 'motivo' ? 2 : 4}
                required={campo === 'motivo'}
                defaultValue={e[campo] ?? ''}
              />
            </label>
          ))}
          {corregir.isError && (
            <p className="error ancho" role="alert">
              {mensajeError(corregir.error, 'No fue posible corregir.')}
            </p>
          )}
        </form>
      </Modal>
      <FormulaModal historiaId={e.id} abierto={formula} onCerrar={() => setFormula(false)} />
    </section>
  )
}

/** Exámenes e imágenes de la consulta. Se abren con su URL firmada, nunca con una pública. */
export function Adjuntos({ historiaId, puedeAdjuntar }: { historiaId: string; puedeAdjuntar: boolean }) {
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
    <section className="bloque" aria-labelledby={`adjuntos-${historiaId}`}>
      <h3 id={`adjuntos-${historiaId}`}>Adjuntos</h3>
      <Consulta
        consulta={adjuntos}
        cargando="Cargando adjuntos…"
        error="No fue posible cargar los adjuntos."
        vacio="Sin exámenes ni imágenes adjuntas."
        estaVacio={(d) => d.length === 0}
      >
        {(d) =>
          d.map((a) => (
            <button key={a.id} type="button" className="fila opcion" onClick={() => void abrir(a.id)}>
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
          className="formulario"
          onSubmit={(ev) => {
            ev.preventDefault()
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
              onChange={(ev) => setArchivo(ev.target.files?.[0] ?? null)}
            />
          </label>
          <label className="campo">
            <span>Descripción</span>
            <input className="input" value={descripcion} onChange={(ev) => setDescripcion(ev.target.value)} />
          </label>
          <div className="acciones ancho">
            <button className="btn btn-secundario" type="submit" disabled={!archivo || adjuntar.isPending}>
              <Icono nombre="subir" size={16} /> {adjuntar.isPending ? 'Subiendo…' : 'Adjuntar'}
            </button>
          </div>
          {adjuntar.isError && (
            <p className="error ancho" role="alert">
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
            {emitir.isPending ? 'Emitiendo…' : 'Emitir fórmula'}
          </button>
        )
      }
    >
      {emitir.isSuccess ? (
        <p className="aviso-ok" role="status">
          Fórmula emitida.{' '}
          <a href={emitir.data.url} target="_blank" rel="noreferrer">
            Abrir PDF
          </a>
        </p>
      ) : (
        <form
          id="formula"
          className="pila"
          onSubmit={(ev) => {
            ev.preventDefault()
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
                <input className="input" value={it.medicamento} onChange={(ev) => cambiar(i, 'medicamento', ev.target.value)} required={i === 0} />
              </label>
              <label className="campo">
                <span>Dosis</span>
                <input className="input" value={it.dosis ?? ''} onChange={(ev) => cambiar(i, 'dosis', ev.target.value)} />
              </label>
              <label className="campo">
                <span>Frecuencia</span>
                <input className="input" value={it.frecuencia ?? ''} onChange={(ev) => cambiar(i, 'frecuencia', ev.target.value)} />
              </label>
              <label className="campo">
                <span>Duración</span>
                <input className="input" value={it.duracion ?? ''} onChange={(ev) => cambiar(i, 'duracion', ev.target.value)} />
              </label>
            </fieldset>
          ))}
          <button className="btn btn-plano" type="button" onClick={() => setItems((a) => [...a, { ...ITEM_VACIO }])}>
            <Icono nombre="mas" size={16} /> Otro medicamento
          </button>
          <label className="campo">
            <span>Indicaciones generales</span>
            <textarea className="input" rows={2} value={indicaciones} onChange={(ev) => setIndicaciones(ev.target.value)} />
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
