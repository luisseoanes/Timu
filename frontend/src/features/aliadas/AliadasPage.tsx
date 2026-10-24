import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { Pestanas } from '@/components/Pestanas'
import { useAuth } from '@/features/auth/AuthContext'
import { useCiudades } from '@/features/catalogos/api'
import { SelectorFamilia } from '@/features/familias/SelectorFamilia'
import { descargar } from '@/lib/descargas'
import { mensajeError } from '@/lib/errores'
import { fecha, hoyISO, moneda } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { ClinicaRead, FamiliaRead, RemisionRead } from '@/types'

import {
  useActualizarClinica,
  useAnularRemision,
  useClinicas,
  useConvenios,
  useCrearClinica,
  useCrearConvenio,
  useEmitirRemision,
  useLiquidacion,
  useRemisiones,
} from './api'

export function AliadasPage() {
  const { usuario } = useAuth()
  const pestanas = [
    { valor: 'remisiones', titulo: 'Remisiones', contenido: <Remisiones /> },
    { valor: 'clinicas', titulo: 'Clínicas y convenios', contenido: <Clinicas /> },
  ]
  if (puede(usuario, 'administrar')) pestanas.push({ valor: 'liquidacion', titulo: 'Liquidación', contenido: <Liquidacion /> })
  return <Pestanas etiqueta="Secciones de aliadas" pestanas={pestanas} />
}

function Remisiones() {
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

function Clinicas() {
  const { usuario } = useAuth()
  const esAdmin = puede(usuario, 'administrar')
  const clinicas = useClinicas(undefined, esAdmin)
  const actualizar = useActualizarClinica()
  const [abierta, setAbierta] = useState<ClinicaRead | null>(null)
  const [nueva, setNueva] = useState(false)

  return (
    <div className="con-rail">
      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Clínicas aliadas</h3>
          {esAdmin && (
            <button className="btn btn-suave" type="button" onClick={() => setNueva(true)}>
              <Icono nombre="mas" size={16} /> Nueva clínica
            </button>
          )}
        </div>
        <Consulta
          consulta={clinicas}
          cargando="Cargando clínicas…"
          error="No fue posible cargar las clínicas."
          vacio="No hay clínicas aliadas registradas."
          estaVacio={(d) => d.length === 0}
        >
          {(d) =>
            d.map((c) => (
              <button key={c.id} type="button" className="fila opcion" aria-pressed={abierta?.id === c.id} onClick={() => setAbierta(c)}>
                <span className="fila-icono">
                  <Icono nombre="aliadas" size={16} />
                </span>
                <span className="fila-cuerpo">
                  <strong>{c.nombre}</strong>
                  <span>
                    {c.ciudad}
                    {c.telefono ? ` · ${c.telefono}` : ''}
                  </span>
                </span>
                {!c.activa && <span className="distintivo distintivo-neutro">Inactiva</span>}
              </button>
            ))
          }
        </Consulta>
      </section>
      <aside className="rail">
        {abierta ? (
          <ConveniosClinica
            clinica={abierta}
            esAdmin={esAdmin}
            onAlternar={() => actualizar.mutate({ id: abierta.id, activa: !abierta.activa }, { onSuccess: (c) => setAbierta(c) })}
          />
        ) : (
          <section className="tarjeta">
            <p className="apagado">Elige una clínica para ver sus convenios.</p>
          </section>
        )}
      </aside>
      <NuevaClinica abierto={nueva} onCerrar={() => setNueva(false)} />
    </div>
  )
}

function ConveniosClinica({ clinica, esAdmin, onAlternar }: { clinica: ClinicaRead; esAdmin: boolean; onAlternar: () => void }) {
  const convenios = useConvenios(clinica.id)
  const crear = useCrearConvenio()
  const [nuevo, setNuevo] = useState(false)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>{clinica.nombre}</h3>
      </div>
      {clinica.servicios && <p className="apagado">{clinica.servicios}</p>}
      <h4 className="subtitulo" style={{ marginTop: 'var(--e4)' }}>
        Convenios
      </h4>
      <Consulta consulta={convenios} cargando="Cargando…" error="No fue posible cargar los convenios." vacio="Sin convenios." estaVacio={(d) => d.length === 0}>
        {(d) =>
          d.map((cv) => (
            <div key={cv.id} className="fila">
              <div className="fila-cuerpo">
                <strong>{cv.beneficio}</strong>
                <span>
                  {cv.cobertura_pct}% · tarifa {moneda(cv.tarifa)}
                  {cv.tope_cubierto ? ` · tope ${moneda(cv.tope_cubierto)}` : ''}
                </span>
              </div>
            </div>
          ))
        }
      </Consulta>
      {esAdmin && (
        <div className="acciones" style={{ marginTop: 'var(--e3)' }}>
          <button className="btn btn-suave" type="button" onClick={() => setNuevo(true)}>
            Nuevo convenio
          </button>
          <button className="btn btn-plano" type="button" onClick={onAlternar}>
            {clinica.activa ? 'Desactivar clínica' : 'Activar clínica'}
          </button>
        </div>
      )}
      <Modal
        abierto={nuevo}
        onCambio={(v) => {
          if (!v) {
            crear.reset()
            setNuevo(false)
          }
        }}
        titulo={`Convenio con ${clinica.nombre}`}
        pie={
          <button className="btn btn-primario" type="submit" form="nuevo-convenio" disabled={crear.isPending}>
            Guardar convenio
          </button>
        }
      >
        <form
          id="nuevo-convenio"
          className="formulario"
          onSubmit={(e) => {
            e.preventDefault()
            const d = new FormData(e.currentTarget)
            crear.mutate(
              {
                clinicaId: clinica.id,
                beneficio: String(d.get('beneficio')).trim(),
                cobertura_pct: Number(d.get('cobertura_pct')),
                tarifa: String(d.get('tarifa')),
                tope_cubierto: String(d.get('tope_cubierto') ?? '') || undefined,
                vigente_desde: String(d.get('vigente_desde')),
              },
              { onSuccess: () => setNuevo(false) },
            )
          }}
        >
          <label className="campo ancho">
            <span>Beneficio</span>
            <input className="input" name="beneficio" required placeholder="Ej.: Radiografía, hospitalización" />
          </label>
          <label className="campo">
            <span>Cobertura (%)</span>
            <input className="input" name="cobertura_pct" type="number" min={0} max={100} defaultValue={100} required />
          </label>
          <label className="campo">
            <span>Tarifa acordada (COP)</span>
            <input className="input" name="tarifa" type="number" min={0} required />
          </label>
          <label className="campo">
            <span>Tope cubierto (COP, opcional)</span>
            <input className="input" name="tope_cubierto" type="number" min={0} />
          </label>
          <label className="campo">
            <span>Vigente desde</span>
            <input className="input" name="vigente_desde" type="date" defaultValue={hoyISO()} required />
          </label>
          {crear.isError && (
            <p className="error ancho" role="alert">
              {mensajeError(crear.error, 'No fue posible guardar el convenio.')}
            </p>
          )}
        </form>
      </Modal>
    </section>
  )
}

function NuevaClinica({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const crear = useCrearClinica()
  const ciudades = useCiudades()
  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          crear.reset()
          onCerrar()
        }
      }}
      titulo="Nueva clínica aliada"
      pie={
        <button className="btn btn-primario" type="submit" form="nueva-clinica" disabled={crear.isPending}>
          Guardar
        </button>
      }
    >
      <form
        id="nueva-clinica"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const d = new FormData(e.currentTarget)
          const t = (c: string) => String(d.get(c) ?? '').trim() || null
          crear.mutate(
            { nombre: t('nombre') ?? '', nit: t('nit'), ciudad: t('ciudad') ?? '', direccion: t('direccion'), telefono: t('telefono'), email: t('email'), servicios: t('servicios') },
            { onSuccess: onCerrar },
          )
        }}
      >
        <label className="campo">
          <span>Nombre</span>
          <input className="input" name="nombre" required />
        </label>
        <label className="campo">
          <span>NIT</span>
          <input className="input" name="nit" />
        </label>
        <label className="campo">
          <span>Ciudad</span>
          <select className="input" name="ciudad" required defaultValue="">
            <option value="" disabled>Selecciona</option>
            {ciudades.data?.map((c) => (
              <option key={c.codigo} value={c.nombre}>{c.nombre}</option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Dirección</span>
          <input className="input" name="direccion" />
        </label>
        <label className="campo">
          <span>Teléfono</span>
          <input className="input" name="telefono" />
        </label>
        <label className="campo">
          <span>Correo</span>
          <input className="input" name="email" type="email" />
        </label>
        <label className="campo ancho">
          <span>Servicios que presta</span>
          <textarea className="input" name="servicios" rows={2} />
        </label>
        {crear.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(crear.error, 'No fue posible guardar la clínica.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

function Liquidacion() {
  const hoy = hoyISO()
  const [desde, setDesde] = useState(`${hoy.slice(0, 8)}01`)
  const [hasta, setHasta] = useState(hoy)
  const liquidacion = useLiquidacion(desde, hasta, true)
  const [errorCsv, setErrorCsv] = useState<string | null>(null)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Liquidación a aliadas</h3>
        <button
          className="btn btn-suave"
          type="button"
          onClick={() =>
            descargar('/aliadas/liquidacion', { desde, hasta, formato: 'csv' }, `liquidacion-${desde}-${hasta}.csv`).catch((e) =>
              setErrorCsv(mensajeError(e, 'No fue posible descargar.')),
            )
          }
        >
          <Icono nombre="descargar" size={16} /> CSV
        </button>
      </div>
      <div className="filtros" style={{ marginBottom: 'var(--e4)' }}>
        <label className="acciones">
          Desde
          <input className="input" style={{ width: 'auto' }} type="date" value={desde} onChange={(e) => setDesde(e.target.value)} />
        </label>
        <label className="acciones">
          Hasta
          <input className="input" style={{ width: 'auto' }} type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} />
        </label>
      </div>
      {errorCsv && (
        <p className="error" role="alert">
          {errorCsv}
        </p>
      )}
      <Consulta
        consulta={liquidacion}
        cargando="Calculando…"
        error="No fue posible calcular la liquidación."
        vacio="No hubo atenciones en aliadas en el período."
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <div className="scroll-x">
            <table className="tabla">
              <thead>
                <tr>
                  <th>Clínica</th>
                  <th>Atenciones</th>
                  <th>Valor atenciones</th>
                  <th>A cargo de TIMU</th>
                  <th>A cargo de familias</th>
                </tr>
              </thead>
              <tbody>
                {d.map((f) => (
                  <tr key={f.clinica_id}>
                    <td className="principal">
                      {f.clinica}
                      {f.nit && <div className="apagado numero">NIT {f.nit}</div>}
                    </td>
                    <td className="numero">{f.atenciones}</td>
                    <td className="numero">{moneda(f.valor_atenciones)}</td>
                    <td className="numero">{moneda(f.valor_cubierto)}</td>
                    <td className="numero">{moneda(f.valor_familias)}</td>
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
