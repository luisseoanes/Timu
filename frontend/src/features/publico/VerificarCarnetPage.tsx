import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { MarcaTimu } from '@/components/MarcaTimu'
import { esErrorPasajero, mensajeError } from '@/lib/errores'
import { diaISO, fecha, fechaHora, peso } from '@/lib/formato'
import type { CarnetVerificadoRead, SeccionVerificada } from '@/types'

import { useCarnetVerificado } from './api'

/**
 * Verificación pública del carnet preventivo (6.15): un tercero —clínica, guardería,
 * aerolínea— confirma con el código impreso que el carnet es auténtico. Dice lo mismo que el
 * PDF el día que se emitió, sección por sección, sin datos de la familia.
 */
export function VerificarCarnetPage() {
  const { codigo = '' } = useParams()
  const carnet = useCarnetVerificado(codigo)

  let contenido
  if (carnet.isPending) {
    contenido = (
      <div className="esqueleto" role="status">
        <span className="sr-only">Verificando el carnet…</span>
        <span className="esqueleto-linea" aria-hidden="true" />
        <span className="esqueleto-linea" aria-hidden="true" />
        <span className="esqueleto-linea" aria-hidden="true" />
      </div>
    )
  } else if (carnet.isError && esErrorPasajero(carnet.error)) {
    contenido = (
      <section className="verificacion-veredicto">
        <h1>No pudimos verificar el carnet</h1>
        <p className="aviso-error" role="alert">
          <Icono nombre="alerta" size={16} />{' '}
          {mensajeError(carnet.error, 'El servidor no respondió. Intenta de nuevo en un momento.')}
        </p>
        <button className="btn btn-primario" type="button" onClick={() => carnet.refetch()}>
          Reintentar
        </button>
      </section>
    )
  } else if (carnet.isError) {
    contenido = <NoEncontrado codigo={codigo} />
  } else {
    contenido = <Carnet carnet={carnet.data} />
  }

  return (
    <div className="verificacion">
      <main className="verificacion-columna">
        <span className="verificacion-marca">
          <MarcaTimu compacta />
        </span>
        {contenido}
      </main>
    </div>
  )
}

function Carnet({ carnet: c }: { carnet: CarnetVerificadoRead }) {
  const emitido = fecha(diaISO(c.emitido_en))
  // Lo próximo solo dice su fecha: el estado se gana su columna cuando algo ya debía aplicarse.
  const hayVencido = c.pendientes?.some((p) => p.vencido) ?? false
  return (
    <>
      <section className="verificacion-veredicto">
        <h1 className="verificacion-autentico">
          <Icono nombre="escudo" size={32} /> Carnet auténtico
        </h1>
        <p>Carnet preventivo emitido por TIMU.</p>
        <dl className="verificacion-datos">
          <div>
            <dt>Mascota</dt>
            <dd>{[c.mascota.nombre, c.mascota.especie, c.mascota.raza].filter(Boolean).join(' · ')}</dd>
          </div>
          <div>
            <dt>Código</dt>
            <dd className="numero">{c.codigo}</dd>
          </div>
          <div>
            <dt>Emitido</dt>
            <dd className="numero">{fechaHora(c.emitido_en)}</dd>
          </div>
        </dl>
      </section>

      {c.secciones.map((s) => (
        <Seccion key={s.tipo} seccion={s} />
      ))}

      <section className="verificacion-seccion" aria-labelledby="carnet-pendiente">
        <h2 id="carnet-pendiente">Pendiente al emitirse</h2>
        {c.pendientes === null ? (
          <p>Este carnet se emitió antes de que la verificación guardara lo pendiente.</p>
        ) : c.pendientes.length === 0 ? (
          <p>No había nada pendiente.</p>
        ) : (
          <div className="scroll-x">
            <table className="tabla tabla-apilable">
              <thead>
                <tr>
                  <th>Preventivo</th>
                  <th>Programado para</th>
                  {hayVencido && <th>Estado</th>}
                </tr>
              </thead>
              <tbody>
                {c.pendientes.map((p, i) => (
                  <tr key={`${p.nombre}-${i}`}>
                    <td className="principal" data-etiqueta="Preventivo">
                      {p.nombre}
                      {p.dosis ? `, ${p.dosis.toLowerCase()}` : ''}
                    </td>
                    <td className="numero" data-etiqueta="Programado para">
                      {fecha(p.fecha_programada)}
                    </td>
                    {hayVencido && (
                      <td data-etiqueta="Estado">{p.vencido && <Insignia tono="alerta">Vencido</Insignia>}</td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <footer className="verificacion-pie">
        <p>
          Certifica que TIMU emitió este carnet el {emitido} y que lo de arriba es lo que decía ese día. Lo aplicado después no
          aparece: pide a la familia un carnet nuevo.
        </p>
        <p>
          Huella SHA-256 del PDF, para compararla con el documento: <span className="verificacion-huella">{c.sha256}</span>
        </p>
      </footer>
    </>
  )
}

/** Una sección del carnet impreso: las vacunas dicen la dosis; las desparasitaciones, el peso. */
function Seccion({ seccion: s }: { seccion: SeccionVerificada }) {
  const vacuna = s.tipo === 'vacuna'
  const id = `carnet-${s.tipo}`
  return (
    <section className="verificacion-seccion" aria-labelledby={id}>
      <h2 id={id}>{s.titulo}</h2>
      {s.aplicados.length === 0 ? (
        <p>Sin aplicaciones registradas.</p>
      ) : (
        <div className="scroll-x">
          <table className="tabla tabla-apilable">
            <thead>
              <tr>
                {vacuna ? (
                  <>
                    <th>Vacuna</th>
                    <th>Dosis</th>
                    <th>Aplicada</th>
                  </>
                ) : (
                  <>
                    <th>Aplicada</th>
                    <th>Peso</th>
                  </>
                )}
                <th>Producto</th>
                <th>Lote</th>
                <th>Próxima</th>
                <th>Aplicó</th>
              </tr>
            </thead>
            <tbody>
              {s.aplicados.map((a, i) => (
                <tr key={`${a.nombre}-${i}`}>
                  {vacuna ? (
                    <>
                      <td className="principal" data-etiqueta="Vacuna">
                        {a.nombre}
                      </td>
                      <td data-etiqueta="Dosis">{a.dosis ?? '—'}</td>
                      <td className="numero" data-etiqueta="Aplicada">
                        {fecha(a.fecha_aplicacion)}
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="numero principal" data-etiqueta="Aplicada">
                        {fecha(a.fecha_aplicacion)}
                      </td>
                      <td className="numero" data-etiqueta="Peso">
                        {peso(a.peso_kg)}
                      </td>
                    </>
                  )}
                  <td data-etiqueta="Producto">{a.producto ?? '—'}</td>
                  <td className="numero" data-etiqueta="Lote">
                    {a.lote ?? '—'}
                  </td>
                  <td className="numero" data-etiqueta="Próxima">
                    {fecha(a.proxima_fecha)}
                  </td>
                  <td data-etiqueta="Aplicó">{a.aplicado_por ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

/** El código no existe o se transcribió mal: se puede corregir aquí mismo. */
function NoEncontrado({ codigo }: { codigo: string }) {
  const navigate = useNavigate()
  const [nuevo, setNuevo] = useState(codigo)
  return (
    <section className="verificacion-veredicto">
      <h1>No encontramos este carnet</h1>
      <p>
        No hay ningún carnet emitido por TIMU con el código <strong className="numero">{codigo}</strong>. Revisa el código
        impreso al pie del carnet: son diez letras y números.
      </p>
      <form
        className="verificacion-buscar"
        onSubmit={(e) => {
          e.preventDefault()
          const limpio = nuevo.trim().toUpperCase()
          if (limpio) navigate(`/verificar/${encodeURIComponent(limpio)}`)
        }}
      >
        <div className="campo">
          <label htmlFor="codigo-carnet">Código del carnet</label>
          <input
            id="codigo-carnet"
            className="input numero"
            value={nuevo}
            onChange={(e) => setNuevo(e.target.value)}
            autoCapitalize="characters"
            autoComplete="off"
            spellCheck={false}
          />
        </div>
        <button className="btn btn-primario" type="submit">
          Verificar
        </button>
      </form>
    </section>
  )
}
