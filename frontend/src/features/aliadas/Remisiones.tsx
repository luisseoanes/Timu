import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { SelectorFamilia } from '@/features/familias'
import { mensajeError } from '@/lib/errores'
import { fecha, moneda } from '@/lib/formato'
import type { FamiliaRead, RemisionRead } from '@/types'

import {
  useAnularRemision,
  useClinicas,
  useConvenios,
  useEmitirRemision,
  useRemisiones,
} from './api'

export function Remisiones() {
  const [estado, setEstado] = useState('emitida')
  const remisiones = useRemisiones({ estado: estado || undefined })
  const clinicas = useClinicas(undefined, true)
  const [nueva, setNueva] = useState(false)
  const [anulando, setAnulando] = useState<RemisionRead | null>(null)
  const nombreClinica = (id: string) => clinicas.data?.find((c) => c.id === id)?.nombre ?? '…'

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Remisiones a clínicas aliadas</h3>
        <div className="acciones">
          <select className="input" style={{ width: 'auto' }} value={estado} onChange={(e) => setEstado(e.target.value)} aria-label="Estado de la remisión">
            <option value="emitida">Emitidas</option>
            <option value="utilizada">Utilizadas</option>
            <option value="anulada">Anuladas</option>
            <option value="">Todas</option>
          </select>
          <button className="btn btn-primario" type="button" onClick={() => setNueva(true)}>
            <Icono nombre="mas" size={16} /> Emitir remisión
          </button>
        </div>
      </div>
      <Consulta
        consulta={remisiones}
        cargando="Cargando remisiones…"
        error="No fue posible cargar las remisiones."
        vacio="No hay remisiones en este estado."
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <div className="scroll-x">
            <table className="tabla">
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Clínica</th>
                  <th>Motivo</th>
                  <th>Cobertura</th>
                  <th>Vence</th>
                  <th>Estado</th>
                  <th><span className="sr-only">Acciones</span></th>
                </tr>
              </thead>
              <tbody>
                {d.map((r) => (
                  <tr key={r.id}>
                    <td className="principal numero">
                      <Link to={`/familias/${r.familia_id}`}>{r.codigo}</Link>
                    </td>
                    <td>{nombreClinica(r.clinica_id)}</td>
                    <td>{r.motivo}</td>
                    <td className="numero">
                      {r.cobertura_pct}%{r.tope_cubierto ? ` hasta ${moneda(r.tope_cubierto)}` : ''}
                    </td>
                    <td className="numero">{fecha(r.vence_en)}</td>
                    <td>
                      <Distintivo dominio="remision" valor={r.estado} />
                      {r.valor_cubierto && <div className="apagado numero">Cubierto {moneda(r.valor_cubierto)}</div>}
                    </td>
                    <td>
                      {r.estado === 'emitida' && (
                        <button className="btn btn-plano" type="button" onClick={() => setAnulando(r)}>
                          Anular
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Consulta>
      <NuevaRemision abierto={nueva} onCerrar={() => setNueva(false)} />
      <AnularRemision remision={anulando} onCerrar={() => setAnulando(null)} />
    </section>
  )
}

function NuevaRemision({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const emitir = useEmitirRemision()
  const [familia, setFamilia] = useState<FamiliaRead | null>(null)
  const [clinicaId, setClinicaId] = useState('')
  const clinicas = useClinicas(familia?.ciudad)
  const convenios = useConvenios(clinicaId || null)

  function cerrar() {
    emitir.reset()
    setFamilia(null)
    setClinicaId('')
    onCerrar()
  }

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => !v && cerrar()}
      titulo="Emitir remisión"
      descripcion="La clínica valida el código y reporta la atención; el beneficio se aplica según el convenio."
      pie={
        !emitir.isSuccess && (
          <button className="btn btn-primario" type="submit" form="nueva-remision" disabled={!familia || !clinicaId || emitir.isPending}>
            Emitir
          </button>
        )
      }
    >
      {emitir.isSuccess ? (
        <p className="aviso-ok" role="status">
          Remisión emitida con código <strong className="numero">{emitir.data.codigo}</strong>. La familia lo recibe por WhatsApp.
        </p>
      ) : (
        <form
          id="nueva-remision"
          className="formulario"
          onSubmit={(e) => {
            e.preventDefault()
            const d = new FormData(e.currentTarget)
            emitir.mutate({
              clinica_id: clinicaId,
              mascota_id: String(d.get('mascota_id')),
              motivo: String(d.get('motivo')).trim(),
              convenio_id: String(d.get('convenio_id') ?? '') || undefined,
            })
          }}
        >
          <div className="ancho">
            <SelectorFamilia valor={familia} onCambio={setFamilia} />
          </div>
          <label className="campo">
            <span>Mascota</span>
            <select className="input" name="mascota_id" required disabled={!familia}>
              {(familia?.mascotas ?? [])
                .filter((m) => m.activa)
                .map((m) => (
                  <option key={m.id} value={m.id}>{m.nombre}</option>
                ))}
            </select>
          </label>
          <label className="campo">
            <span>Clínica{familia ? ` en ${familia.ciudad}` : ''}</span>
            <select className="input" value={clinicaId} onChange={(e) => setClinicaId(e.target.value)} required disabled={!familia}>
              <option value="" disabled>
                {clinicas.data?.length === 0 ? 'No hay aliadas en la ciudad' : 'Elige la clínica'}
              </option>
              {clinicas.data?.map((c) => (
                <option key={c.id} value={c.id}>{c.nombre}</option>
              ))}
            </select>
          </label>
          <label className="campo">
            <span>Convenio</span>
            <select className="input" name="convenio_id" disabled={!clinicaId}>
              <option value="">El que aplique por plan</option>
              {convenios.data
                ?.filter((c) => c.activo)
                .map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.beneficio} · {c.cobertura_pct}%
                  </option>
                ))}
            </select>
          </label>
          <label className="campo ancho">
            <span>Motivo de la remisión</span>
            <textarea className="input" name="motivo" rows={2} required minLength={3} />
          </label>
          {emitir.isError && (
            <p className="error ancho" role="alert">
              {mensajeError(emitir.error, 'No fue posible emitir la remisión.')}
            </p>
          )}
        </form>
      )}
    </Modal>
  )
}

function AnularRemision({ remision, onCerrar }: { remision: RemisionRead | null; onCerrar: () => void }) {
  const anular = useAnularRemision()
  return (
    <Modal
      abierto={remision !== null}
      onCambio={(v) => {
        if (!v) {
          anular.reset()
          onCerrar()
        }
      }}
      titulo={`Anular remisión ${remision?.codigo ?? ''}`}
      pie={
        <button className="btn btn-primario" type="submit" form="anular-remision" disabled={anular.isPending}>
          Anular
        </button>
      }
    >
      <form
        id="anular-remision"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const motivo = String(new FormData(e.currentTarget).get('motivo')).trim()
          if (remision) anular.mutate({ id: remision.id, motivo }, { onSuccess: onCerrar })
        }}
      >
        <label className="campo ancho">
          <span>Motivo</span>
          <textarea className="input" name="motivo" rows={2} required minLength={3} />
        </label>
        {anular.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(anular.error, 'No fue posible anular.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
