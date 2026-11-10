import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { useNombreTipoServicio } from '@/features/catalogos'
import { fechaHora, mesEnCurso } from '@/lib/formato'
import type { FamiliaRead, PendienteRead, ServicioRead } from '@/types'

import { useResumenServicios, type FiltrosResumen } from './api'

/**
 * 6.1 Servicios de la familia en un rango libre (por defecto, el mes en curso): lo utilizado
 * y lo pendiente por separado, lo abierto de una atención y el cupo consumido del plan.
 */
export function ServiciosFamilia({ familia }: { familia: FamiliaRead }) {
  const [filtros, setFiltros] = useState<FiltrosResumen>(() => mesEnCurso())
  const resumen = useResumenServicios(familia.id, filtros)
  const nombreTipo = useNombreTipoServicio()
  const mascotas = familia.mascotas ?? []
  const nombreMascota = (id: string | null | undefined) => mascotas.find((m) => m.id === id)?.nombre ?? '—'
  const rangoCompleto = Boolean(filtros.desde && filtros.hasta)
  const rangoInvertido = rangoCompleto && filtros.hasta < filtros.desde

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Servicios</h3>
      </div>
      <form className="formulario" onSubmit={(e) => e.preventDefault()} aria-label="Filtrar servicios">
        <label className="campo">
          <span>Desde</span>
          <input
            className="input"
            type="date"
            value={filtros.desde}
            onChange={(e) => setFiltros({ ...filtros, desde: e.target.value })}
            required
          />
        </label>
        <label className="campo">
          <span>Hasta</span>
          <input
            className="input"
            type="date"
            value={filtros.hasta}
            onChange={(e) => setFiltros({ ...filtros, hasta: e.target.value })}
            required
          />
        </label>
        <label className="campo">
          <span>Mascota</span>
          <select
            className="input"
            value={filtros.mascota_id ?? ''}
            onChange={(e) => setFiltros({ ...filtros, mascota_id: e.target.value || undefined })}
          >
            <option value="">Todas</option>
            {mascotas.map((m) => (
              <option key={m.id} value={m.id}>
                {m.nombre}
              </option>
            ))}
          </select>
        </label>
        <label className="acciones">
          <input
            type="checkbox"
            checked={filtros.incluir_cancelados ?? false}
            onChange={(e) => setFiltros({ ...filtros, incluir_cancelados: e.target.checked || undefined })}
          />
          <span>Ver cancelados</span>
        </label>
      </form>

      {!rangoCompleto ? (
        <p className="apagado">Elige la fecha inicial y la final del rango.</p>
      ) : rangoInvertido ? (
        <p className="error" role="alert">
          La fecha final es anterior a la inicial.
        </p>
      ) : (
        <Consulta consulta={resumen} cargando="Cargando servicios…" error="No fue posible cargar los servicios.">
          {(d) => (
            <>
              {d.cupos.length > 0 && (
                <>
                  <h4>Cupo del plan</h4>
                  <div className="scroll-x">
                    <table className="tabla">
                      <thead>
                        <tr>
                          <th>Beneficio</th>
                          <th>Usados</th>
                          <th>Periodo</th>
                        </tr>
                      </thead>
                      <tbody>
                        {d.cupos.map((c) => (
                          <tr key={c.tipo_codigo}>
                            <td className="principal">{nombreTipo(c.tipo_codigo)}</td>
                            <td className="numero">{c.cupo === null || c.cupo === undefined ? `${c.usados} (sin límite)` : `${c.usados} de ${c.cupo}`}</td>
                            <td>{c.periodo === 'mensual' ? 'Este mes' : 'Este año'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
              <TablaServicios
                titulo="Pendientes"
                vacio="No hay servicios pendientes en este rango."
                servicios={d.pendientes}
                nombreTipo={nombreTipo}
                nombreMascota={nombreMascota}
              />
              {d.pendientes_atencion.length > 0 && (
                <TablaPendientesAtencion pendientes={d.pendientes_atencion} />
              )}
              <TablaServicios
                titulo="Utilizados"
                vacio="No hay servicios utilizados en este rango."
                servicios={d.utilizados}
                nombreTipo={nombreTipo}
                nombreMascota={nombreMascota}
              />
              {filtros.incluir_cancelados && (
                <TablaServicios
                  titulo="Cancelados"
                  vacio="No hay servicios cancelados en este rango."
                  servicios={d.cancelados}
                  nombreTipo={nombreTipo}
                  nombreMascota={nombreMascota}
                />
              )}
            </>
          )}
        </Consulta>
      )}
    </section>
  )
}

function TablaServicios({
  titulo,
  vacio,
  servicios,
  nombreTipo,
  nombreMascota,
}: {
  titulo: string
  vacio: string
  servicios: ServicioRead[]
  nombreTipo: (codigo: string) => string
  nombreMascota: (id: string | null | undefined) => string
}) {
  return (
    <>
      <h4>{titulo}</h4>
      {servicios.length === 0 ? (
        <p className="apagado">{vacio}</p>
      ) : (
        <div className="scroll-x">
          <table className="tabla" aria-label={titulo}>
            <thead>
              <tr>
                <th>Servicio</th>
                <th>Mascota</th>
                <th>Fecha</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {servicios.map((s) => (
                <tr key={s.id}>
                  <td className="principal">{nombreTipo(s.tipo_codigo)}</td>
                  <td>{nombreMascota(s.mascota_id)}</td>
                  <td className="numero">{s.programado_para ? fechaHora(s.programado_para) : 'Sin programar'}</td>
                  <td>
                    <Distintivo dominio="servicio" valor={s.estado} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}

function TablaPendientesAtencion({ pendientes }: { pendientes: PendienteRead[] }) {
  return (
    <>
      <h4>Pendientes de una atención</h4>
      <div className="scroll-x">
        <table className="tabla" aria-label="Pendientes de una atención">
          <thead>
            <tr>
              <th>Qué quedó pendiente</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {pendientes.map((p) => (
              <tr key={p.id}>
                <td className="principal">{p.descripcion}</td>
                <td>
                  <Distintivo dominio="pendiente" valor={p.estado} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
