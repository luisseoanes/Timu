import { useId, useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Insignia } from '@/components/Distintivo'
import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'
import { estado } from '@/lib/estados'
import type { FamiliaParaSuprimir } from '@/types'

import { useAnonimizar, useParaSuprimir } from './api'

/** Supresión de datos (Ley 1581): quien la pide queda sin datos personales en la plataforma. El
 * administrador la hace sin abrir la ficha (decidido con el usuario el 2026-11-19): busca por el
 * documento y ve solo el nombre del titular, cuántas mascotas tiene y su estado. */
export function Supresion() {
  const id = useId()
  const [escrito, setEscrito] = useState('')
  const [documento, setDocumento] = useState('')
  const familia = useParaSuprimir(documento)
  const [confirmando, setConfirmando] = useState<FamiliaParaSuprimir | null>(null)

  return (
    <section className="tarjeta pila" aria-labelledby={`${id}-titulo`}>
      <div className="tarjeta-cabeza">
        <h3 id={`${id}-titulo`}>Supresión de datos</h3>
      </div>
      <p className="apagado">
        Cuando una familia pide que se borren sus datos (Ley 1581), se anonimiza: sus datos personales se sustituyen
        y no se puede deshacer. El historial de pagos y de atención se conserva sin nombres.
      </p>
      <form
        className="supresion-busqueda"
        onSubmit={(e) => {
          e.preventDefault()
          setDocumento(escrito.trim())
        }}
      >
        <div className="campo">
          <label htmlFor={`${id}-documento`}>Documento del titular</label>
          <input
            id={`${id}-documento`}
            className="input"
            inputMode="numeric"
            autoComplete="off"
            value={escrito}
            onChange={(e) => setEscrito(e.target.value)}
            placeholder="1020304050"
          />
        </div>
        <button className="btn btn-secundario" type="submit" disabled={escrito.trim().length < 3}>
          Buscar
        </button>
      </form>
      {documento && (
        <Consulta
          consulta={familia}
          cargando="Buscando…"
          error={mensajeError(familia.error, 'No fue posible buscar la familia.')}
        >
          {(f) => (
            <div className="fila">
              <div className="fila-cuerpo">
                <strong>{f.titular_nombre}</strong>
                <span>
                  {f.mascotas === 1 ? '1 mascota' : `${f.mascotas} mascotas`} · {estado('afiliacion', f.estado).label}
                </span>
                {/* La base no anonimiza con un contrato vigente: no se ofrece lo que acabaría en error. */}
                {!f.anonimizada && f.con_contrato_vigente && (
                  <span>Tiene un contrato vigente: Atención al cliente lo cancela antes de anonimizar.</span>
                )}
              </div>
              {f.anonimizada ? (
                <Insignia tono="neutro">Ya anonimizada</Insignia>
              ) : f.con_contrato_vigente ? (
                <Insignia tono="alerta">Contrato vigente</Insignia>
              ) : (
                <button className="btn btn-peligro" type="button" onClick={() => setConfirmando(f)}>
                  Anonimizar
                </button>
              )}
            </div>
          )}
        </Consulta>
      )}
      <Confirmar familia={confirmando} onCerrar={() => setConfirmando(null)} />
    </section>
  )
}

function Confirmar({ familia, onCerrar }: { familia: FamiliaParaSuprimir | null; onCerrar: () => void }) {
  const anonimizar = useAnonimizar()
  function cerrar() {
    anonimizar.reset()
    onCerrar()
  }
  return (
    <Modal
      abierto={familia !== null}
      onCambio={(v) => !v && cerrar()}
      titulo={`Anonimizar a ${familia?.titular_nombre ?? ''}`}
      descripcion="Sus datos personales y los de sus mascotas se sustituyen ahora y no se pueden recuperar."
      pie={
        <>
          <button className="btn btn-secundario" type="button" onClick={cerrar}>
            No anonimizar
          </button>
          <button
            className="btn btn-peligro"
            type="button"
            disabled={anonimizar.isPending}
            onClick={() => familia && anonimizar.mutate(familia.id, { onSuccess: cerrar })}
          >
            {anonimizar.isPending ? 'Anonimizando…' : 'Anonimizar'}
          </button>
        </>
      }
    >
      {anonimizar.isError && (
        <p className="error" role="alert">
          {mensajeError(anonimizar.error, 'No fue posible anonimizar la familia.')}
        </p>
      )}
    </Modal>
  )
}
