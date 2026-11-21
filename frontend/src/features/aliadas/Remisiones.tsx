import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { SelectorFamilia } from '@/features/familias'
import { mensajeError } from '@/lib/errores'
import { fechaCompacta, moneda } from '@/lib/formato'
import type { FamiliaRead, RecuentosRemisiones, RemisionRead } from '@/types'

import { useAnularRemision, useClinicas, useConvenios, useEmitirRemision, useRecuentosRemisiones, useRemisiones } from './api'
import { cobertura } from './remision'

// Los valores son los del backend (core/enums.py, EstadoRemision); «todas» no filtra.
type Vista = keyof RecuentosRemisiones

const VISTAS: { valor: Vista; label: string; vacio: string }[] = [
  { valor: 'emitida', label: 'Por usar', vacio: 'No hay remisiones por usar. Al emitir una, aparece aquí hasta que la clínica reporte la atención.' },
  { valor: 'utilizada', label: 'Utilizadas', vacio: 'Ninguna clínica ha reportado todavía una atención.' },
  {
    valor: 'vencida',
    label: 'Vencidas',
    vacio: 'Ninguna remisión ha vencido sin usarse. Si la clínica no reporta la atención en el plazo, la remisión vence y libera el cupo del beneficio.',
  },
  { valor: 'anulada', label: 'Anuladas', vacio: 'No se ha anulado ninguna remisión.' },
  { valor: 'todas', label: 'Todas', vacio: 'Aún no se ha emitido ninguna remisión.' },
]

/** Remisiones como bandeja (R2-PAN-10): las que están por usar, primero la que vence antes, con lo
 * que toca hacer en cada fila. La clínica valida el código y reporta la atención desde su portal. */
export function Remisiones() {
  const [params, setParams] = useSearchParams()
  const vista: Vista = VISTAS.find((v) => v.valor === params.get('vista'))?.valor ?? 'emitida'
  // Desde la ficha de una clínica, solo las suyas (`?remisiones_de=`).
  const clinicaId = params.get('remisiones_de') ?? undefined
  const recuentos = useRecuentosRemisiones(clinicaId)
  const remisiones = useRemisiones({ estado: vista === 'todas' ? undefined : vista, clinica_id: clinicaId })
  // Filtradas, todas son de la misma clínica: su nombre sale de ellas, sin otra consulta.
  const nombreClinica = remisiones.data?.[0]?.clinica
  // Solo una remisión por usar se anula: en Utilizadas, Vencidas y Anuladas no hay columna de acciones.
  const conAcciones = vista === 'emitida' || vista === 'todas'

  function verTodas() {
    const siguiente = new URLSearchParams(params)
    siguiente.delete('remisiones_de')
    setParams(siguiente, { replace: true })
  }
  const [nueva, setNueva] = useState(false)
  const [anulando, setAnulando] = useState<RemisionRead | null>(null)

  function cambiarVista(valor: Vista) {
    const siguiente = new URLSearchParams(params)
    siguiente.set('vista', valor)
    setParams(siguiente, { replace: true })
  }

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Remisiones a clínicas aliadas</h3>
        <button className="btn btn-primario" type="button" onClick={() => setNueva(true)}>
          <Icono nombre="mas" size={16} /> Emitir remisión
        </button>
      </div>
      {clinicaId && (
        <p className="aliada-nota remisiones-de">
          Solo las de {nombreClinica ?? 'una clínica'}.{' '}
          <button className="btn btn-plano btn-accion" type="button" onClick={verTodas}>
            Ver las de todas
          </button>
        </p>
      )}
      <div className="filtros bandeja-filtros">
        <div className="segmento bandeja-vistas" role="group" aria-label="Vista de las remisiones">
          {VISTAS.map((v) => (
            <button
              key={v.valor}
              type="button"
              className="segmento-opcion"
              data-state={vista === v.valor ? 'active' : 'inactive'}
              aria-pressed={vista === v.valor}
              onClick={() => cambiarVista(v.valor)}
            >
              {v.label}
              {recuentos.data && (
                <>
                  {' '}
                  <span className="segmento-recuento numero">{recuentos.data[v.valor]}</span>
                </>
              )}
            </button>
          ))}
        </div>
      </div>
      <Consulta
        consulta={remisiones}
        cargando="Cargando las remisiones…"
        error="No fue posible cargar las remisiones."
        vacio={VISTAS.find((v) => v.valor === vista)!.vacio}
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <div className="scroll-x">
            <table className="tabla tabla-apilable bandeja-tabla remisiones-tabla">
              <thead>
                <tr>
                  <th>Remisión</th>
                  <th>Clínica</th>
                  <th>Cobertura</th>
                  <th>{vista === 'utilizada' ? 'Atendida' : 'Vence'}</th>
                  {vista === 'todas' && <th>Estado</th>}
                  {conAcciones && <th><span className="sr-only">Acciones</span></th>}
                </tr>
              </thead>
              <tbody>
                {d.map((r) => (
                  <tr key={r.id}>
                    <td className="principal" data-etiqueta="Remisión">
                      <Link to={`/panel/familias/${r.familia_id}`}>
                        {r.titular}
                        {r.mascota && ` · ${r.mascota}`}
                      </Link>
                      <div className="bandeja-detalle">
                        <span className="numero">{r.codigo}</span>
                        <span>{r.motivo}</span>
                      </div>
                    </td>
                    <td data-etiqueta="Clínica">{r.clinica}</td>
                    <td data-etiqueta="Cobertura">
                      {r.valor_cubierto ? (
                        <span className="numero sin-cortes">Cubrió {moneda(r.valor_cubierto)}</span>
                      ) : (
                        <span className="numero sin-cortes">{cobertura(r)}</span>
                      )}
                    </td>
                    <td data-etiqueta={vista === 'utilizada' ? 'Atendida' : 'Vence'}>
                      {r.estado === 'utilizada' && r.fecha_atencion ? (
                        <span className="numero sin-cortes">{fechaCompacta(r.fecha_atencion)}</span>
                      ) : r.vencida ? (
                        // Lo vencido se dice con icono y palabra, no solo en rojo.
                        <span className="bandeja-vencida">
                          <Icono nombre="alerta" size={14} />
                          <span>Venció el</span>
                          <span className="numero">{fechaCompacta(r.vence_en)}</span>
                        </span>
                      ) : (
                        <span className="numero sin-cortes">{fechaCompacta(r.vence_en)}</span>
                      )}
                    </td>
                    {vista === 'todas' && (
                      <td data-etiqueta="Estado">
                        <Distintivo dominio="remision" valor={r.estado} />
                      </td>
                    )}
                    {conAcciones && (
                      <td className="tabla-acciones">
                        {r.estado === 'emitida' && (
                          <button className="btn btn-plano btn-plano-peligro" type="button" onClick={() => setAnulando(r)} aria-label={`Anular la remisión ${r.codigo}`}>
                            Anular
                          </button>
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
  const activas = (familia?.mascotas ?? []).filter((m) => m.activa)

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
            {/* Como la clínica: dice qué falta en vez de quedarse en blanco, y no elige por nadie. */}
            <select className="input" name="mascota_id" required disabled={!familia} defaultValue="" key={familia?.id ?? 'sin-familia'}>
              <option value="" disabled>
                {!familia ? 'Elige primero la familia' : activas.length === 0 ? 'La familia no tiene mascotas activas' : 'Elige la mascota'}
              </option>
              {activas.map((m) => (
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
            <textarea className="input" name="motivo" rows={2} required minLength={5} />
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
  // Cerrar por cualquier camino olvida el intento: el error no pasa a la ventana de otra remisión.
  function cerrar() {
    anular.reset()
    onCerrar()
  }
  return (
    <Modal
      abierto={remision !== null}
      onCambio={(v) => !v && cerrar()}
      titulo={`Anular la remisión ${remision?.codigo ?? ''}`}
      descripcion="La clínica ya no la acepta y el cupo del beneficio vuelve a la familia. No se deshace."
      pie={
        <>
          <button className="btn btn-secundario" type="button" onClick={cerrar}>
            Mantenerla
          </button>
          <button className="btn btn-peligro" type="submit" form="anular-remision" disabled={anular.isPending}>
            {anular.isPending ? 'Anulando…' : 'Anular remisión'}
          </button>
        </>
      }
    >
      <form
        id="anular-remision"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const motivo = String(new FormData(e.currentTarget).get('motivo')).trim()
          if (remision) anular.mutate({ id: remision.id, motivo }, { onSuccess: cerrar })
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
