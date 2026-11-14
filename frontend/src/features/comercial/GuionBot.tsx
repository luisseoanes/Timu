import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { mensajeError } from '@/lib/errores'

import { useArbol, usePublicarArbol } from './api'

/** El guion del asistente de WhatsApp (F3-COM-02): se edita como dato y cada versión queda guardada. */
export function GuionBot() {
  const arbol = useArbol(true)
  const publicar = usePublicarArbol()
  const [texto, setTexto] = useState<string | null>(null)
  const [nota, setNota] = useState('')
  const [errorJson, setErrorJson] = useState<string | null>(null)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Guion del asistente comercial</h3>
      </div>
      <p className="comercial-nota">
        Cada paso tiene su mensaje y sus opciones. Al publicar se valida el guion completo y la versión anterior queda guardada.
      </p>
      <Consulta consulta={arbol} cargando="Cargando el guion…" error="No fue posible cargar el guion.">
        {(nodos) => (
          <form
            className="pila"
            onSubmit={(e) => {
              e.preventDefault()
              setErrorJson(null)
              try {
                const parseado = JSON.parse(texto ?? JSON.stringify(nodos)) as Record<string, unknown>
                publicar.mutate({ nodos: parseado, nota: nota.trim() || undefined })
              } catch {
                setErrorJson('El guion no es un JSON válido: revisa comas, llaves y comillas.')
              }
            }}
          >
            <label className="campo">
              <span>Pasos (JSON)</span>
              <textarea
                className="input codigo"
                rows={18}
                spellCheck={false}
                value={texto ?? JSON.stringify(nodos, null, 2)}
                onChange={(e) => setTexto(e.target.value)}
              />
            </label>
            <label className="campo">
              <span>Qué cambia en esta versión</span>
              <input className="input" value={nota} onChange={(e) => setNota(e.target.value)} />
            </label>
            {(errorJson || publicar.isError) && (
              <p className="error" role="alert">
                {errorJson ?? mensajeError(publicar.error, 'El guion no es válido.')}
              </p>
            )}
            {publicar.isSuccess && (
              <p className="exito" role="status">
                Versión publicada: el asistente ya responde con ella.
              </p>
            )}
            <div className="acciones">
              <button className="btn btn-primario" type="submit" disabled={publicar.isPending}>
                {publicar.isPending ? 'Publicando…' : 'Publicar versión'}
              </button>
            </div>
          </form>
        )}
      </Consulta>
    </section>
  )
}
