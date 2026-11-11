import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'
import { fecha } from '@/lib/formato'
import type { CategoriaDocumento, DocumentoRead, FamiliaRead } from '@/types'

import { useActualizarDocumento, useDocumentos, useQuitarDocumento, useSubirDocumento } from './api'

const CATEGORIAS: Record<CategoriaDocumento, string> = {
  identificacion: 'Identificación',
  examen_externo: 'Examen externo',
  otro: 'Otro',
}

const ORIGENES: Record<DocumentoRead['origen'], string> = {
  subido: 'Subido',
  contrato: 'Contrato',
  carnet: 'Carnet',
  adjunto_clinico: 'Adjunto clínico',
  formula: 'Fórmula médica',
}

/** Igual que el backend: PDF o imagen de hasta 10 MB. */
const FORMATOS = 'application/pdf,image/jpeg,image/png,image/webp'
const MAX_BYTES = 10 * 1024 * 1024

function tamano(bytes: number): string {
  return bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`
}

/**
 * 6.1 Documentos de la familia y de sus mascotas: los que sube el equipo y los que genera la
 * plataforma (contratos, carnets, adjuntos y fórmulas de la historia clínica).
 */
export function DocumentosFamilia({ familia }: { familia: FamiliaRead }) {
  const [mascotaId, setMascotaId] = useState('')
  const [subiendo, setSubiendo] = useState(false)
  const [editando, setEditando] = useState<DocumentoRead | null>(null)
  const [quitando, setQuitando] = useState<DocumentoRead | null>(null)
  const documentos = useDocumentos(familia.id, mascotaId || undefined)
  const mascotas = familia.mascotas ?? []
  const editable = !familia.dada_de_baja_en
  const nombreMascota = (id: string | null | undefined) => (id ? (mascotas.find((m) => m.id === id)?.nombre ?? '—') : 'Familia')

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Documentos</h3>
        {editable && (
          <button className="btn btn-suave" type="button" onClick={() => setSubiendo(true)}>
            Subir documento
          </button>
        )}
      </div>
      <div className="formulario">
        <label className="campo">
          <span>Mascota</span>
          <select className="input" value={mascotaId} onChange={(e) => setMascotaId(e.target.value)}>
            <option value="">Todos</option>
            {mascotas.map((m) => (
              <option key={m.id} value={m.id}>
                {m.nombre}
              </option>
            ))}
          </select>
        </label>
      </div>
      <Consulta
        consulta={documentos}
        cargando="Cargando los documentos…"
        error="No fue posible cargar los documentos."
        vacio="No hay documentos."
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <div className="scroll-x">
            <table className="tabla tabla-apilable" aria-label="Documentos">
              <thead>
                <tr>
                  <th>Documento</th>
                  <th>Tipo</th>
                  <th>De</th>
                  <th>Fecha</th>
                  <th>La familia lo ve</th>
                  {editable && <th><span className="sr-only">Acciones</span></th>}
                </tr>
              </thead>
              <tbody>
                {d.map((doc) => (
                  <tr key={doc.archivo_id}>
                    <td data-etiqueta="Documento" className="principal">
                      {doc.url ? (
                        <a href={doc.url} target="_blank" rel="noreferrer">
                          {doc.descripcion ?? doc.nombre}
                        </a>
                      ) : (
                        <span title="El fichero se borró al anonimizar la familia">{doc.descripcion ?? doc.nombre}</span>
                      )}
                      <span className="apagado"> · {tamano(doc.tamano_bytes)}</span>
                    </td>
                    <td data-etiqueta="Tipo">{doc.categoria ? CATEGORIAS[doc.categoria] : ORIGENES[doc.origen]}</td>
                    <td data-etiqueta="De">{nombreMascota(doc.mascota_id)}</td>
                    <td data-etiqueta="Fecha" className="numero">{fecha(doc.creado_en.slice(0, 10))}</td>
                    <td data-etiqueta="La familia lo ve">{doc.visible_familia ? 'Sí' : 'No'}</td>
                    {editable && (
                      <td className="tabla-acciones">
                        {doc.documento_id && (
                          <>
                            <button className="btn btn-plano" type="button" onClick={() => setEditando(doc)}>
                              Editar
                            </button>
                            <button className="btn btn-plano btn-plano-peligro" type="button" onClick={() => setQuitando(doc)}>
                              Quitar
                            </button>
                          </>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Consulta>
      <SubirDocumentoModal familia={familia} abierto={subiendo} onCerrar={() => setSubiendo(false)} />
      <EditarDocumentoModal familiaId={familia.id} documento={editando} onCerrar={() => setEditando(null)} />
      <QuitarDocumentoModal familiaId={familia.id} documento={quitando} onCerrar={() => setQuitando(null)} />
    </section>
  )
}

function CampoCategoria({ valor }: { valor?: CategoriaDocumento }) {
  return (
    <label className="campo">
      <span>Categoría</span>
      <select className="input" name="categoria" required defaultValue={valor ?? ''}>
        <option value="" disabled>
          Selecciona la categoría
        </option>
        {Object.entries(CATEGORIAS).map(([codigo, nombre]) => (
          <option key={codigo} value={codigo}>
            {nombre}
          </option>
        ))}
      </select>
    </label>
  )
}

function SubirDocumentoModal({ familia, abierto, onCerrar }: { familia: FamiliaRead; abierto: boolean; onCerrar: () => void }) {
  const subir = useSubirDocumento(familia.id)
  const [archivo, setArchivo] = useState<File | null>(null)
  const [aviso, setAviso] = useState<string | null>(null)

  function elegir(e: React.ChangeEvent<HTMLInputElement>) {
    const elegido = e.target.files?.[0] ?? null
    subir.reset()
    if (elegido && elegido.size > MAX_BYTES) {
      e.target.value = ''
      setArchivo(null)
      setAviso('El fichero pesa más de 10 MB. Elige uno más liviano.')
      return
    }
    setAviso(null)
    setArchivo(elegido)
  }

  function guardar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    if (!archivo) {
      setAviso('Elige el fichero que vas a subir.')
      return
    }
    subir.mutate(
      {
        archivo,
        categoria: String(d.get('categoria')) as CategoriaDocumento,
        descripcion: String(d.get('descripcion') ?? '').trim() || undefined,
        mascota_id: String(d.get('mascota_id') ?? '') || undefined,
        visible_familia: d.get('visible_familia') === 'on',
      },
      { onSuccess: onCerrar },
    )
  }

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          subir.reset()
          setAviso(null)
          setArchivo(null)
          onCerrar()
        }
      }}
      titulo="Subir documento"
      descripcion="PDF o imagen (JPG, PNG o WEBP) de hasta 10 MB."
      pie={
        <button className="btn btn-primario" type="submit" form="subir-documento" disabled={subir.isPending}>
          {subir.isPending ? 'Subiendo…' : 'Subir'}
        </button>
      }
    >
      <form id="subir-documento" className="formulario" onSubmit={guardar}>
        <label className="campo ancho">
          <span>Fichero</span>
          <input className="input" type="file" accept={FORMATOS} onChange={elegir} />
        </label>
        <CampoCategoria />
        <label className="campo">
          <span>De</span>
          <select className="input" name="mascota_id" defaultValue="">
            <option value="">La familia</option>
            {(familia.mascotas ?? [])
              .filter((m) => m.activa)
              .map((m) => (
                <option key={m.id} value={m.id}>
                  {m.nombre}
                </option>
              ))}
          </select>
        </label>
        <label className="campo ancho">
          <span>Descripción (opcional)</span>
          <input className="input" name="descripcion" maxLength={255} />
        </label>
        <label className="acciones ancho">
          <input type="checkbox" name="visible_familia" />
          <span>La familia lo ve en su portal</span>
        </label>
        {(aviso || subir.isError) && (
          <p className="error ancho" role="alert">
            {aviso ?? mensajeError(subir.error, 'No fue posible subir el documento.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

function EditarDocumentoModal({
  familiaId,
  documento,
  onCerrar,
}: {
  familiaId: string
  documento: DocumentoRead | null
  onCerrar: () => void
}) {
  const actualizar = useActualizarDocumento(familiaId)

  function guardar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!documento?.documento_id) return
    const d = new FormData(e.currentTarget)
    actualizar.mutate(
      {
        id: documento.documento_id,
        categoria: String(d.get('categoria')) as CategoriaDocumento,
        descripcion: String(d.get('descripcion') ?? '').trim() || null,
        visible_familia: d.get('visible_familia') === 'on',
      },
      { onSuccess: onCerrar },
    )
  }

  return (
    <Modal
      abierto={documento !== null}
      onCambio={(v) => {
        if (!v) {
          actualizar.reset()
          onCerrar()
        }
      }}
      titulo={`Editar ${documento?.descripcion ?? documento?.nombre ?? 'documento'}`}
      pie={
        <button className="btn btn-primario" type="submit" form="editar-documento" disabled={actualizar.isPending}>
          {actualizar.isPending ? 'Guardando…' : 'Guardar'}
        </button>
      }
    >
      {documento && (
        <form id="editar-documento" key={documento.archivo_id} className="formulario" onSubmit={guardar}>
          <CampoCategoria valor={documento.categoria ?? undefined} />
          <label className="campo ancho">
            <span>Descripción (opcional)</span>
            <input className="input" name="descripcion" maxLength={255} defaultValue={documento.descripcion ?? ''} />
          </label>
          <label className="acciones ancho">
            <input type="checkbox" name="visible_familia" defaultChecked={documento.visible_familia} />
            <span>La familia lo ve en su portal</span>
          </label>
          {actualizar.isError && (
            <p className="error ancho" role="alert">
              {mensajeError(actualizar.error, 'No fue posible guardar el documento.')}
            </p>
          )}
        </form>
      )}
    </Modal>
  )
}

function QuitarDocumentoModal({
  familiaId,
  documento,
  onCerrar,
}: {
  familiaId: string
  documento: DocumentoRead | null
  onCerrar: () => void
}) {
  const quitar = useQuitarDocumento(familiaId)
  return (
    <Modal
      abierto={documento !== null}
      onCambio={(v) => {
        if (!v) {
          quitar.reset()
          onCerrar()
        }
      }}
      titulo={`Quitar ${documento?.descripcion ?? documento?.nombre ?? 'el documento'}`}
      descripcion="Deja de figurar en la ficha y en el portal de la familia. El fichero se conserva."
      pie={
        <button
          className="btn btn-peligro"
          type="button"
          disabled={quitar.isPending}
          onClick={() => documento?.documento_id && quitar.mutate(documento.documento_id, { onSuccess: onCerrar })}
        >
          {quitar.isPending ? 'Quitando…' : 'Quitar documento'}
        </button>
      }
    >
      {quitar.isError ? (
        <p className="error" role="alert">
          {mensajeError(quitar.error, 'No fue posible quitar el documento.')}
        </p>
      ) : (
        <p>Si te equivocaste, podrás subirlo de nuevo.</p>
      )}
    </Modal>
  )
}
