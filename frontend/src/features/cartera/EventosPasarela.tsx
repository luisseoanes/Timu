import { useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { mensajeError } from '@/lib/errores'
import { fechaHora } from '@/lib/formato'

import { useEventosPasarela, useRecuentosEventosPasarela, useReprocesarEvento } from './api'

// Lo que avisa cada proveedor, en palabras (cartera/pasarela.py procesa los cambios de un pago).
// Un tipo que no está aquí se muestra tal cual: es un aviso que TIMU no procesa.
const TIPOS_EVENTO: Record<string, string> = { 'transaction.updated': 'Cambio en un pago' }
const PROVEEDORES: Record<string, string> = { wompi: 'Wompi' }

// Los valores son los del backend (core/enums.py, EstadoEventoPasarela) y las claves de sus
// recuentos; «Todos» no filtra.
const VISTAS_EVENTOS = [
  { valor: 'error', label: 'Con error', vacio: 'Ningún evento de la pasarela ha fallado.' },
  { valor: 'procesado', label: 'Procesados', vacio: 'Aún no se ha procesado ningún evento.' },
  { valor: 'todos', label: 'Todos', vacio: 'La pasarela no ha enviado ningún evento todavía.' },
] as const
type VistaEventos = (typeof VISTAS_EVENTOS)[number]['valor']

/** Lo que avisa la pasarela de pagos: los que fallaron primero, para reprocesarlos. La vista vive
 * en la URL (`?eventos=`), como en las demás bandejas, y cada una dice cuántos tiene. */
export function EventosPasarela() {
  const [params, setParams] = useSearchParams()
  const estado: VistaEventos = VISTAS_EVENTOS.find((v) => v.valor === params.get('eventos'))?.valor ?? 'error'
  const eventos = useEventosPasarela(estado === 'todos' ? undefined : estado)
  const recuentos = useRecuentosEventosPasarela()
  const reprocesar = useReprocesarEvento()

  function setEstado(valor: VistaEventos) {
    const siguiente = new URLSearchParams(params)
    siguiente.set('eventos', valor)
    setParams(siguiente, { replace: true })
  }

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Eventos de la pasarela de pagos</h3>
      </div>
      <div className="filtros bandeja-filtros">
        <div className="segmento bandeja-vistas bandeja-vistas-tres" role="group" aria-label="Estado de los eventos">
          {VISTAS_EVENTOS.map((v) => (
            <button
              key={v.valor}
              type="button"
              className="segmento-opcion"
              data-state={estado === v.valor ? 'active' : 'inactive'}
              aria-pressed={estado === v.valor}
              onClick={() => setEstado(v.valor)}
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
      {reprocesar.isError && (
        <p className="error" role="alert">
          {mensajeError(reprocesar.error, 'No fue posible reprocesar el evento.')}
        </p>
      )}
      <Consulta
        consulta={eventos}
        cargando="Cargando los eventos…"
        error="No fue posible cargar los eventos."
        vacio={VISTAS_EVENTOS.find((v) => v.valor === estado)!.vacio}
        estaVacio={(d) => d.items.length === 0}
      >
        {(d) => (
          <div className="scroll-x">
            <table className="tabla tabla-apilable bandeja-tabla eventos-tabla">
              <thead>
                <tr>
                  <th>Evento</th>
                  <th>Recibido</th>
                  <th>Referencia</th>
                  <th>Estado</th>
                  <th><span className="sr-only">Acciones</span></th>
                </tr>
              </thead>
              <tbody>
                {d.items.map((ev) => (
                  <tr key={ev.id}>
                    <td className="principal" data-etiqueta="Evento">
                      {TIPOS_EVENTO[ev.tipo] ?? ev.tipo}
                      <div className="bandeja-detalle">
                        <span>{PROVEEDORES[ev.proveedor] ?? ev.proveedor}</span>
                      </div>
                      {ev.error && <div className="error">{ev.error}</div>}
                    </td>
                    <td data-etiqueta="Recibido">
                      <span className="numero sin-cortes">{fechaHora(ev.created_at)}</span>
                    </td>
                    <td data-etiqueta="Referencia">
                      <span className="numero">{ev.referencia ?? '—'}</span>
                    </td>
                    <td data-etiqueta="Estado">
                      <Distintivo dominio="evento_pasarela" valor={ev.estado} />
                    </td>
                    <td className="tabla-acciones">
                      {ev.estado !== 'procesado' && (
                        <button
                          className="btn btn-suave"
                          type="button"
                          disabled={reprocesar.isPending}
                          onClick={() => reprocesar.mutate(ev.id)}
                          aria-label={`Reprocesar el evento ${ev.referencia ?? TIPOS_EVENTO[ev.tipo] ?? ev.tipo}`}
                        >
                          Reprocesar
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
    </section>
  )
}
