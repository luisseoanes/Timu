import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo, Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { descargar } from '@/lib/descargas'
import { mensajeError } from '@/lib/errores'
import { estadoCuota } from '@/lib/estados'
import { diaISO, fechaCortaConDia, moneda } from '@/lib/formato'

import { useMiCuenta, useMiPlan, useMisPagos, usePagarPortal } from './api'
import { alPagar } from './plan'
import { avisoDelPago, nombreCuota, porPagar, saldoDe } from './pagos'

/**
 * R3-POR-02 Los pagos de la familia: cuánto debe y el único verde para pagarlo todo, cada cuota
 * por pagar con su propio pago, y lo ya pagado con su comprobante. Al volver de la pasarela
 * (`/portal/pagos/:pagoId`), un aviso dice qué pasó con ese pago.
 */
export function PortalPagos() {
  const { pagoId } = useParams()
  const cuenta = useMiCuenta()
  const plan = useMiPlan()
  const pagos = useMisPagos(pagoId)
  const pagar = usePagarPortal()
  const qc = useQueryClient()
  const aviso = avisoDelPago(pagos.data?.find((p) => p.id === pagoId))
  const aprobado = aviso?.tono === 'ok'

  // Al aprobarse, el plan y la línea cambian (una cuenta al día deja de estar en pausa).
  useEffect(() => {
    if (aprobado) void qc.invalidateQueries({ queryKey: ['portal'], predicate: (q) => q.queryKey[1] !== 'pagos' })
  }, [aprobado, qc])

  function iniciarPago(cuotaId?: string) {
    pagar.mutate(cuotaId, { onSuccess: (r) => window.location.assign(r.enlace_pago) })
  }

  return (
    <div className="pila">
      <header className="portal-cabecera">
        <h1>Tus pagos</h1>
      </header>
      {aviso && (
        <p className={`portal-aviso portal-aviso-${aviso.tono}`} role="status">
          {aviso.texto}
        </p>
      )}

      <section className="portal-panel" aria-labelledby="cuenta-titulo">
        <h2 id="cuenta-titulo" className="sr-only">
          Tu cuenta
        </h2>
        <Consulta consulta={cuenta} cargando="Cargando tu cuenta…" error="No pudimos cargar tu cuenta.">
          {(c) => {
            const todoVencido = c !== null && Number(c.saldo_vencido) > 0 && Number(c.saldo_vencido) === Number(c.saldo_pendiente)
            return c === null ? (
              <p className="apagado">Aún no tienes un plan con cuotas. Escríbenos por WhatsApp para afiliarte.</p>
            ) : (
              <div className="pila">
                <div className="portal-saldo">
                  {Number(c.saldo_pendiente) > 0 ? (
                    <>
                      <p>
                        <span className="portal-saldo-cifra numero">{moneda(c.saldo_pendiente)}</span> por pagar
                        {Number(c.saldo_vencido) > 0 && (
                          <span className="portal-saldo-vencido">
                            , {todoVencido ? 'todo' : moneda(c.saldo_vencido)} vencido
                          </span>
                        )}
                      </p>
                      {alPagar(plan.data) && <p>{alPagar(plan.data)}</p>}
                      <button className="btn btn-primario" type="button" disabled={pagar.isPending} onClick={() => iniciarPago()}>
                        Pagar {moneda(c.saldo_pendiente)}
                      </button>
                    </>
                  ) : (
                    <p>
                      <Insignia tono="ok">Al día</Insignia> No tienes nada por pagar.
                    </p>
                  )}
                  {c.proximo_cobro && (
                    <p className="apagado">
                      Próximo cobro: <span className="numero">{moneda(c.proximo_cobro.valor)}</span> el {fechaCortaConDia(c.proximo_cobro.fecha)}
                    </p>
                  )}
                </div>
                {pagar.isError && (
                  <p className="error" role="alert">
                    {mensajeError(pagar.error, 'No pudimos iniciar el pago.')}
                  </p>
                )}
                {porPagar(c.cuotas).length > 0 && (
                  <section className="bloque" aria-labelledby="cuotas-titulo">
                    <h3 id="cuotas-titulo">Cuotas por pagar</h3>
                    <ul className="portal-lista">
                      {porPagar(c.cuotas).map((q) => (
                        <li key={q.id}>
                          <span>
                            <strong>{nombreCuota(q)}</strong>
                            <span className="apagado">
                              <span className="numero">{moneda(saldoDe(q))}</span> · vence el {fechaCortaConDia(q.fecha_vencimiento)}
                            </span>
                          </span>
                          {/* Si todo está vencido, ya lo dice el saldo: la pastilla en cada fila sobra. */}
                          {!todoVencido && <Distintivo dominio="cuota" valor={estadoCuota(q)} />}
                          {/* Con una sola, pagar esta es lo mismo que el verde de arriba. */}
                          {porPagar(c.cuotas).length > 1 && (
                            <button className="btn btn-plano btn-accion" type="button" disabled={pagar.isPending} onClick={() => iniciarPago(q.id)}>
                              Pagar esta
                            </button>
                          )}
                        </li>
                      ))}
                    </ul>
                  </section>
                )}
              </div>
            )
          }}
        </Consulta>
      </section>

      <HistorialPagos />
    </div>
  )
}

function HistorialPagos() {
  const pagos = useMisPagos()
  const [errorComprobante, setErrorComprobante] = useState<string | null>(null)
  return (
    <section className="portal-panel" aria-labelledby="pagos-titulo">
      <h2 id="pagos-titulo" className="portal-panel-titulo">
        Tu historial de pagos
      </h2>
      {errorComprobante && (
        <p className="error" role="alert">
          {errorComprobante}
        </p>
      )}
      <Consulta consulta={pagos} cargando="Cargando tus pagos…" error="No pudimos cargar tus pagos." vacio="Aún no tienes pagos." estaVacio={(d) => d.length === 0}>
        {(d) => (
          <ul className="portal-lista">
            {d.map((p) => (
              <li key={p.id}>
                <span>
                  <strong className="numero">{moneda(p.valor)}</strong>
                  <span className="apagado">
                    {fechaCortaConDia(diaISO(p.fecha_pago ?? p.created_at))}
                    {(p.estado === 'rechazado' || p.estado === 'anulado') && ' · No se cobró'}
                  </span>
                </span>
                <Distintivo dominio="pago" valor={p.estado} />
                {p.estado === 'aprobado' && (
                  <button
                    className="btn btn-plano btn-accion"
                    type="button"
                    onClick={() =>
                      descargar(`/portal/pagos/${p.id}/comprobante`, {}, `comprobante-${p.referencia_externa}.pdf`).catch((e) =>
                        setErrorComprobante(mensajeError(e, 'No pudimos descargar el comprobante.')),
                      )
                    }
                  >
                    <Icono nombre="descargar" size={16} /> Comprobante
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </Consulta>
    </section>
  )
}
