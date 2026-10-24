import { useParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Icono } from '@/components/Icono'
import { MarcaTimu } from '@/features/auth/AccesoLayout'
import { fecha, fechaHora } from '@/lib/formato'

import { useCarnetVerificado } from './api'

/**
 * Verificación pública del carnet de vacunación (F2-PRE-06): un tercero —clínica,
 * guardería, aerolínea— confirma con el código impreso que el carnet es auténtico.
 * Sólo muestra lo que el carnet ya mostraba, sin datos de la familia.
 */
export function VerificarCarnetPage() {
  const { codigo = '' } = useParams()
  const carnet = useCarnetVerificado(codigo)

  return (
    <div className="publica">
      <MarcaTimu />
      <section className="publica-tarjeta publica-ancha">
        <Consulta
          consulta={carnet}
          cargando="Verificando el carnet…"
          error="No encontramos un carnet con ese código. Revisa que esté bien escrito."
        >
          {(c) => (
            <div className="pila">
              <p className="aviso-ok" role="status">
                <Icono nombre="escudo" size={16} /> Carnet auténtico emitido por TIMU el {fechaHora(c.emitido_en)}.
              </p>
              <dl className="ficha">
                <div><dt>Mascota</dt><dd>{c.mascota.nombre}</dd></div>
                <div><dt>Especie</dt><dd>{c.mascota.especie}</dd></div>
                <div><dt>Raza</dt><dd>{c.mascota.raza ?? '—'}</dd></div>
                <div><dt>Código</dt><dd className="numero">{c.codigo}</dd></div>
              </dl>
              {c.aplicados.length === 0 ? (
                <p className="apagado">El carnet no registra aplicaciones.</p>
              ) : (
                <div className="scroll-x">
                  <table className="tabla">
                    <thead>
                      <tr>
                        <th>Aplicación</th>
                        <th>Fecha</th>
                        <th>Producto</th>
                        <th>Lote</th>
                      </tr>
                    </thead>
                    <tbody>
                      {c.aplicados.map((a, i) => (
                        <tr key={`${a.nombre}-${i}`}>
                          <td className="principal">
                            {a.nombre}
                            {a.dosis ? ` · ${a.dosis}` : ''}
                          </td>
                          <td className="numero">{fecha(a.fecha_aplicacion)}</td>
                          <td>{a.producto ?? '—'}</td>
                          <td className="numero">{a.lote ?? '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <p className="apagado numero" title="Huella del documento emitido">
                Huella SHA-256: {c.sha256.slice(0, 16)}…
              </p>
            </div>
          )}
        </Consulta>
      </section>
    </div>
  )
}
