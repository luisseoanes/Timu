import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { Paginacion } from '@/components/Paginacion'
import { Pestanas } from '@/components/Pestanas'
import { useAuth } from '@/features/auth'
import { useCiudades } from '@/features/catalogos'
import { mensajeError } from '@/lib/errores'
import { fechaCompacta, moneda } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { ContratoListado, RecuentosCartera } from '@/types'

import { useContratos, useEstadoCuenta, useRecuentosCartera, useRenovarContrato } from './api'
import { EventosPasarela } from './EventosPasarela'
import { porPagar } from './cuotas'
import { RegistrarPagoModal } from './RegistrarPagoModal'

type Vista = keyof RecuentosCartera

const VISTAS: { valor: Vista; label: string; vacio: string }[] = [
  { valor: 'en_mora', label: 'En mora', vacio: 'Nadie debe cuotas vencidas. Cuando una cuota pase su fecha sin pagarse, la familia aparece aquí.' },
  { valor: 'por_renovar', label: 'Por renovar', vacio: 'Ningún contrato vence en los próximos 90 días.' },
  { valor: 'todos', label: 'Todos', vacio: 'Ningún contrato coincide con la búsqueda.' },
]

const PERIODICIDAD: Record<string, string> = {
  mensual: 'al mes',
  trimestral: 'al trimestre',
  semestral: 'al semestre',
  anual: 'al año',
}

const POR_PAGINA = 25

/** Cartera (6.2): Atención al cliente cobra y revisa la pasarela de pagos; Comercial ve los contratos
 * para renovarlos (6.4). Docs/perfiles-y-permisos.md. */
export function CarteraPage() {
  const { usuario } = useAuth()
  const [params] = useSearchParams()
  if (!puede(usuario, 'cartera')) return <BandejaCartera />
  return (
    <Pestanas
      etiqueta="Secciones de cartera"
      // Una vista de la pasarela en la URL (`?eventos=`) abre su pestaña.
      inicial={params.has('eventos') ? 'pasarela' : 'contratos'}
      pestanas={[
        { valor: 'contratos', titulo: 'Contratos', contenido: <BandejaCartera /> },
        { valor: 'pasarela', titulo: 'Pasarela de pagos', contenido: <EventosPasarela /> },
      ]}
    />
  )
}

/** Cartera como bandeja (F1-CAR, R2-PAN-08): a quién cobrar, qué renovar y todos los contratos,
 * cada fila con la acción que toca. El estado de cuenta completo es la pestaña Cartera de la familia. */
function BandejaCartera() {
  const { usuario } = useAuth()
  const [params, setParams] = useSearchParams()
  // Sin vista, «En mora» para quien cobra: es lo que se cobra hoy, y adonde lleva «Ver la mora» del
  // Inicio (`?mora=1`); «Por renovar» para Comercial, que es lo suyo (6.4).
  const porDefecto: Vista = usuario?.rol === 'comercial' ? 'por_renovar' : 'en_mora'
  const vista: Vista = VISTAS.find((v) => v.valor === params.get('vista'))?.valor ?? porDefecto
  const q = params.get('q') ?? ''
  const ciudad = params.get('ciudad') ?? ''
  const offset = Number(params.get('desde') ?? 0)
  const [pagando, setPagando] = useState<ContratoListado | null>(null)
  const [renovando, setRenovando] = useState<ContratoListado | null>(null)
  const ciudades = useCiudades()
  // Atención cobra y Comercial renueva (Sección 12, docs/perfiles-y-permisos.md).
  const cobra = puede(usuario, 'cartera')
  const renueva = puede(usuario, 'renovar')

  const filtros = { q: q || undefined, ciudad: ciudad || undefined }
  const recuentos = useRecuentosCartera(filtros)
  const contratos = useContratos({
    ...filtros,
    solo_mora: vista === 'en_mora' || undefined,
    por_renovar: vista === 'por_renovar' || undefined,
    limit: POR_PAGINA,
    offset,
  })

  /** Cambia un filtro en la URL y vuelve a la primera página. */
  function cambiar(cambios: Record<string, string>) {
    const siguiente = new URLSearchParams(params)
    siguiente.delete('mora')
    siguiente.delete('desde')
    for (const [clave, valor] of Object.entries(cambios)) {
      if (valor) siguiente.set(clave, valor)
      else siguiente.delete(clave)
    }
    setParams(siguiente, { replace: true })
  }

  return (
    <section className="tarjeta">
      <div className="filtros bandeja-filtros">
        <div className="segmento bandeja-vistas bandeja-vistas-tres" role="group" aria-label="Vista de la cartera">
          {VISTAS.map((v) => (
            <button
              key={v.valor}
              type="button"
              className="segmento-opcion"
              data-state={vista === v.valor ? 'active' : 'inactive'}
              aria-pressed={vista === v.valor}
              onClick={() => cambiar({ vista: v.valor })}
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
        <label className="buscador bandeja-filtro">
          <Icono nombre="buscar" size={18} />
          <input
            type="search"
            placeholder="Titular, documento o contrato"
            value={q}
            onChange={(e) => cambiar({ q: e.target.value })}
            aria-label="Buscar contratos"
          />
        </label>
        <select className="input bandeja-filtro" value={ciudad} onChange={(e) => cambiar({ ciudad: e.target.value })} aria-label="Ciudad">
          <option value="">Todas las ciudades</option>
          {ciudades.data?.map((c) => (
            <option key={c.nombre} value={c.nombre}>{c.nombre}</option>
          ))}
        </select>
      </div>

      <Consulta
        consulta={contratos}
        cargando="Cargando la cartera…"
        error="No fue posible cargar la cartera."
        vacio={q || ciudad ? 'Ningún contrato de esta vista coincide con la búsqueda.' : VISTAS.find((v) => v.valor === vista)!.vacio}
        estaVacio={(d) => d.items.length === 0}
      >
        {(d) => (
          <>
            <div className="scroll-x">
              <table className="tabla tabla-apilable bandeja-tabla cartera-tabla">
                <thead>
                  <tr>
                    <th>Familia</th>
                    <th>Debe</th>
                    <th>Cuota</th>
                    <th>Renueva</th>
                    <th>Estado</th>
                    <th><span className="sr-only">Acciones</span></th>
                  </tr>
                </thead>
                <tbody>
                  {d.items.map((c) => {
                    const debe = Number(c.saldo_vencido) > 0
                    return (
                      <tr key={c.id}>
                        <td className="principal" data-etiqueta="Familia">
                          {/* El titular lleva al estado de cuenta completo: la pestaña Cartera de su familia. */}
                          <Link to={`/panel/familias/${c.familia_id}`} state={{ seccion: 'cartera' }}>{c.titular}</Link>
                          <div className="bandeja-detalle">
                            {c.planes.map((p) => (
                              <span key={p.nombre} className="familia-fila-marcador">
                                <span className="marcador-plan" data-color={p.color} aria-hidden="true" />
                                {p.nombre}
                              </span>
                            ))}
                            <span className="numero">{c.numero}</span>
                            <span>{c.ciudad}</span>
                          </div>
                        </td>
                        <td data-etiqueta="Debe">
                          {/* Lo vencido se dice con icono y palabra, no solo en rojo. */}
                          {debe ? (
                            <span className="bandeja-vencida">
                              <Icono nombre="alerta" size={14} />
                              {/* El separador cierra la primera pieza: si bajan de línea, ninguna empieza con él. */}
                              <span className="numero">{moneda(c.saldo_vencido)} ·</span>
                              <span>hace {c.dias_mora} {c.dias_mora === 1 ? 'día' : 'días'}</span>
                            </span>
                          ) : (
                            <span className="apagado">Al día</span>
                          )}
                        </td>
                        <td data-etiqueta="Cuota">
                          {/* Una sola pieza: apilada, la celda reparte sus hijos a los extremos. */}
                          <span className="numero sin-cortes">
                            {moneda(c.valor_periodo)} <span className="apagado">{PERIODICIDAD[c.periodicidad] ?? c.periodicidad}</span>
                          </span>
                        </td>
                        <td data-etiqueta="Renueva">
                          <span>
                            <span className="numero sin-cortes">{fechaCompacta(c.fecha_renovacion)}</span>
                            {c.renovable && <span className="cartera-renovable"> · ya se puede renovar</span>}
                          </span>
                        </td>
                        <td data-etiqueta="Estado">
                          <Distintivo dominio="afiliacion" valor={c.estado} />
                        </td>
                        <td className="tabla-acciones">
                          {cobra && debe && (
                            <button className="btn btn-suave" type="button" onClick={() => setPagando(c)} aria-label={`Registrar pago de ${c.titular}`}>
                              Registrar pago
                            </button>
                          )}
                          {renueva && c.renovable && (
                            <button
                              className={`btn ${debe ? 'btn-plano btn-accion' : 'btn-suave'}`}
                              type="button"
                              onClick={() => setRenovando(c)}
                              aria-label={`Renovar el contrato de ${c.titular}`}
                            >
                              Renovar
                            </button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            <Paginacion
              total={d.total}
              limit={d.limit}
              offset={d.offset}
              onCambio={(o) => {
                const siguiente = new URLSearchParams(params)
                if (o) siguiente.set('desde', String(o))
                else siguiente.delete('desde')
                setParams(siguiente, { replace: true })
              }}
            />
          </>
        )}
      </Consulta>
      {pagando && <PagoDeContrato contrato={pagando} onCerrar={() => setPagando(null)} />}
      <RenovarModal contrato={renovando} onCerrar={() => setRenovando(null)} />
    </section>
  )
}

/** El pago se aplica a una cuota de la familia: sus cuotas abiertas llegan con su estado de cuenta, y
 * la ventana abre con la más antigua y su saldo puestos, que es a la que se aplicaría. */
function PagoDeContrato({ contrato, onCerrar }: { contrato: ContratoListado; onCerrar: () => void }) {
  const cuenta = useEstadoCuenta(contrato.familia_id)
  // Los valores puestos se fijan al abrir: la ventana espera a las cuotas (si fallan, abre sin ellas).
  if (cuenta.isPending) return null
  const abiertas = porPagar(cuenta.data?.cuotas ?? [])
  return (
    <RegistrarPagoModal abierto familiaId={contrato.familia_id} titular={contrato.titular} cuotas={abiertas} cuotaId={abiertas[0]?.id} onCerrar={onCerrar} />
  )
}

function RenovarModal({ contrato, onCerrar }: { contrato: ContratoListado | null; onCerrar: () => void }) {
  const renovar = useRenovarContrato()
  function cerrar() {
    renovar.reset()
    onCerrar()
  }
  if (!contrato) return null
  return (
    <Modal
      abierto
      onCambio={(v) => !v && cerrar()}
      titulo={`Renovar el contrato de ${contrato.titular}`}
      descripcion={`${contrato.numero} vence el ${fechaCompacta(contrato.fecha_renovacion)}. Al renovarlo, su vigencia se extiende un año con el mismo plan y la misma cuota.`}
      pie={
        <>
          <button className="btn btn-secundario" type="button" onClick={cerrar}>
            Ahora no
          </button>
          <button className="btn btn-primario" type="button" disabled={renovar.isPending} onClick={() => renovar.mutate(contrato.id, { onSuccess: cerrar })}>
            {renovar.isPending ? 'Renovando…' : 'Renovar un año'}
          </button>
        </>
      }
    >
      {renovar.isError && (
        <p className="error" role="alert">
          {mensajeError(renovar.error, 'No fue posible renovar el contrato.')}
        </p>
      )}
    </Modal>
  )
}
