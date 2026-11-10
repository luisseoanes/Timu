import { useState } from 'react'

/** Igual que el backend: JPG, PNG o WEBP de hasta 5 MB. */
const FORMATOS = 'image/jpeg,image/png,image/webp'
const MAX_BYTES = 5 * 1024 * 1024

/**
 * Foto con sus acciones: subirla, cambiarla o quitarla. Solo presentación: quien la usa
 * decide qué hace cada acción y le pasa si está ocupada y el error del servidor.
 */
export function FotoEditable({
  url,
  alt,
  editable,
  ocupada,
  error,
  onSubir,
  onQuitar,
}: {
  url: string | null | undefined
  alt: string
  editable: boolean
  ocupada: boolean
  error: string | null
  onSubir: (foto: File) => void
  onQuitar: () => void
}) {
  const [aviso, setAviso] = useState<string | null>(null)

  function elegir(e: React.ChangeEvent<HTMLInputElement>) {
    const foto = e.target.files?.[0]
    e.target.value = ''
    if (!foto) return
    if (foto.size > MAX_BYTES) {
      setAviso('La foto pesa más de 5 MB. Elige una más liviana.')
      return
    }
    setAviso(null)
    onSubir(foto)
  }

  return (
    <div className="foto-editable">
      {url ? (
        <img className="foto-editable-imagen" src={url} alt={alt} />
      ) : (
        <div className="foto-editable-imagen" aria-hidden="true">
          Sin foto
        </div>
      )}
      {editable && (
        <div className="acciones">
          <label className="btn btn-suave">
            {ocupada ? 'Guardando…' : url ? 'Cambiar foto' : 'Subir foto'}
            <input className="sr-only" type="file" accept={FORMATOS} onChange={elegir} disabled={ocupada} />
          </label>
          {url && (
            <button className="btn btn-plano" type="button" disabled={ocupada} onClick={onQuitar}>
              Quitar foto
            </button>
          )}
        </div>
      )}
      {(aviso || error) && (
        <p className="error" role="alert">
          {aviso ?? error}
        </p>
      )}
    </div>
  )
}
