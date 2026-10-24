import { Consulta } from '@/components/Consulta'
import { useTiposServicio } from '@/features/catalogos/api'
import { mensajeError } from '@/lib/errores'

import { useActivarCatalogo, useCiudadesTodas, useEsquemas } from './api'

/** Catálogos maestros: no se borran (hay registros que los referencian), se desactivan. */
export function Catalogos() {
  const ciudades = useCiudadesTodas()
  const tipos = useTiposServicio()
  const esquemas = useEsquemas()
  const activar = useActivarCatalogo()

  return (
    <div className="pila">
      {activar.isError && (
        <p className="error" role="alert">
          {mensajeError(activar.error, 'No fue posible actualizar el catálogo.')}
        </p>
      )}
      <div className="dos-columnas">
        <section className="tarjeta">
          <div className="tarjeta-cabeza">
            <h3>Ciudades con cobertura</h3>
          </div>
          <Consulta consulta={ciudades} cargando="Cargando…" error="No fue posible cargar las ciudades.">
            {(d) =>
              d.map((c) => (
                <label key={c.codigo} className="fila">
                  <span className="fila-cuerpo">
                    <strong>{c.nombre}</strong>
                    <span>{c.departamento}</span>
                  </span>
                  <input
                    type="checkbox"
                    checked={c.activa}
                    aria-label={`${c.nombre} con cobertura`}
                    onChange={(e) => activar.mutate({ catalogo: 'ciudades', codigo: c.codigo, activo: e.target.checked })}
                  />
                </label>
              ))
            }
          </Consulta>
        </section>
        <div className="pila">
          <section className="tarjeta">
            <div className="tarjeta-cabeza">
              <h3>Tipos de servicio</h3>
            </div>
            <Consulta consulta={tipos} cargando="Cargando…" error="No fue posible cargar los tipos.">
              {(d) =>
                d.map((t) => (
                  <label key={t.codigo} className="fila">
                    <span className="fila-cuerpo">
                      <strong>{t.nombre}</strong>
                      <span>
                        {t.modalidad} · {t.duracion_min} min{t.requiere_autorizacion ? ' · requiere autorización' : ''}
                      </span>
                    </span>
                    <input
                      type="checkbox"
                      checked={t.activo}
                      aria-label={`${t.nombre} activo`}
                      onChange={(e) => activar.mutate({ catalogo: 'tipos-servicio', codigo: t.codigo, activo: e.target.checked })}
                    />
                  </label>
                ))
              }
            </Consulta>
          </section>
          <section className="tarjeta">
            <div className="tarjeta-cabeza">
              <h3>Esquemas preventivos</h3>
            </div>
            <Consulta consulta={esquemas} cargando="Cargando…" error="No fue posible cargar los esquemas.">
              {(d) =>
                d.map((e) => (
                  <label key={e.codigo} className="fila">
                    <span className="fila-cuerpo">
                      <strong>{e.nombre}</strong>
                      <span>
                        {e.especie_codigo} · {e.dosis_iniciales} dosis cada {e.intervalo_inicial_dias} días
                        {e.intervalo_refuerzo_dias ? ` · refuerzo cada ${e.intervalo_refuerzo_dias} días` : ''}
                      </span>
                    </span>
                    <input
                      type="checkbox"
                      checked={e.activo}
                      aria-label={`${e.nombre} activo`}
                      onChange={(ev) => activar.mutate({ catalogo: 'esquemas-preventivos', codigo: e.codigo, activo: ev.target.checked })}
                    />
                  </label>
                ))
              }
            </Consulta>
          </section>
        </div>
      </div>
    </div>
  )
}
