import * as Menu from '@radix-ui/react-dropdown-menu'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useAuth } from '@/features/auth'
import { useCiudades, usePlanes } from '@/features/catalogos'
import { mensajeError } from '@/lib/errores'
import { fechaCompacta, hoyISO, moneda, telefono } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { ClinicaRead } from '@/types'

import { useActualizarClinica, useClinicas, useConvenios, useCrearClinica, useCrearConvenio, useRecuentosRemisiones, useRemisiones } from './api'
import { cobertura } from './remision'

/** Clínicas y convenios en listado con ficha (R2-PAN-10), como Familias: la clínica abierta vive en
 * la URL (`?clinica=`), con sus datos, sus convenios y las remisiones que tiene por usar. */
export function Clinicas() {
  const [params] = useSearchParams()
  const abierta = params.get('clinica')
  return (
    <div className="con-ficha" data-abierta={abierta ? 'true' : undefined}>
      <ClinicasLista seleccionada={abierta} />
      {abierta ? (
        <FichaClinica key={abierta} id={abierta} />
      ) : (
        <section className="ficha-abierta ficha-vacia" aria-label="Clínica abierta">
          <p>Abre una clínica para ver sus convenios y las remisiones que tiene por usar.</p>
        </section>
      )}
    </div>
  )
}

function ClinicasLista({ seleccionada }: { seleccionada: string | null }) {
  const { usuario } = useAuth()
  const [params] = useSearchParams()
  const esAdmin = puede(usuario, 'administrar')
  // Administración ve también las inactivas, para volver a activarlas.
  const clinicas = useClinicas(undefined, esAdmin)
  const [nueva, setNueva] = useState(false)
  const enlace = (id: string) => {
    const siguiente = new URLSearchParams(params)
    siguiente.set('clinica', id)
    return `?${siguiente}`
  }

  return (
    <section className="listado" aria-labelledby="clinicas-titulo">
      <div className="listado-cabeza">
        <h2 id="clinicas-titulo">
          Clínicas {clinicas.data && <span className="apagado numero">{clinicas.data.length}</span>}
        </h2>
        {esAdmin && (
          // Verde solo sin una clínica abierta: con la ficha a la vista, el verde es de ella.
          <button className={`btn ${seleccionada ? 'btn-suave' : 'btn-primario'}`} type="button" onClick={() => setNueva(true)}>
            <Icono nombre="mas" size={16} /> Nueva clínica
          </button>
        )}
      </div>
      <Consulta
        consulta={clinicas}
        cargando="Cargando las clínicas…"
        error="No fue posible cargar las clínicas."
        vacio={esAdmin ? 'Aún no hay clínicas aliadas. Registra la primera con «Nueva clínica».' : 'No hay clínicas aliadas activas.'}
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <ul className="listado-filas" aria-label="Clínicas aliadas">
            {d.map((c) => (
              <li key={c.id} className="listado-fila" data-seleccionada={c.id === seleccionada}>
                <span className="listado-fila-cabeza">
                  {/* El enlace es solo el nombre; ::after lo extiende a toda la fila. */}
                  <Link className="listado-fila-enlace" to={enlace(c.id)} aria-current={c.id === seleccionada ? 'page' : undefined}>
                    {c.nombre}
                  </Link>
                  {!c.activa && <Insignia tono="neutro">Inactiva</Insignia>}
                </span>
                <span className="servicio-fila-datos">
                  <span>{c.ciudad}</span>
                  {c.telefono && <span className="numero">{telefono(c.telefono)}</span>}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Consulta>
      <NuevaClinica abierto={nueva} onCerrar={() => setNueva(false)} />
    </section>
  )
}

function FichaClinica({ id }: { id: string }) {
  const { usuario } = useAuth()
  const clinicas = useClinicas(undefined, puede(usuario, 'administrar'))
  const c = clinicas.data?.find((x) => x.id === id)
  return (
    <section className="ficha-abierta" aria-label="Clínica abierta">
      <Consulta consulta={clinicas} cargando="Cargando la clínica…" error="No fue posible cargar la clínica.">
        {() => (c ? <Ficha clinica={c} /> : <p className="apagado">Esta clínica ya no existe o no la puedes ver.</p>)}
      </Consulta>
    </section>
  )
}

function Ficha({ clinica: c }: { clinica: ClinicaRead }) {
  const { usuario } = useAuth()
  const [params] = useSearchParams()
  const esAdmin = puede(usuario, 'administrar')
  const actualizar = useActualizarClinica()
  const convenios = useConvenios(c.id)
  const planes = usePlanes()
  const recuentos = useRecuentosRemisiones(c.id)
  const porUsar = useRemisiones({ clinica_id: c.id, estado: 'emitida' })
  const [nuevo, setNuevo] = useState(false)
  const volver = new URLSearchParams(params)
  volver.delete('clinica')
  const nombrePlan = (planId: string | null | undefined) => (planId ? (planes.data?.find((p) => p.id === planId)?.nombre ?? '…') : 'Todos los planes')

  return (
    <>
      <header className="ficha-cabeza">
        <Link to={`?${volver}`} className="btn btn-plano ficha-volver" aria-label="Volver a las clínicas">
          <Icono nombre="volver" size={16} />
        </Link>
        <h2 className="aliada-titulo">{c.nombre}</h2>
        <div className="ficha-datos aliada-quien">
          {!c.activa && <Insignia tono="neutro">Inactiva</Insignia>}
          <span>{c.ciudad}</span>
          {c.telefono && <span className="numero">{telefono(c.telefono)}</span>}
          {c.email && <span>{c.email}</span>}
        </div>
        {esAdmin && (
          <div className="ficha-acciones">
            <button className="btn btn-primario" type="button" onClick={() => setNuevo(true)} disabled={!c.activa}>
              <Icono nombre="mas" size={16} /> Nuevo convenio
            </button>
            <Menu.Root modal={false}>
              <Menu.Trigger className="btn btn-secundario btn-icono" aria-label={`Más acciones con ${c.nombre}`}>
                <Icono nombre="puntos" size={18} />
              </Menu.Trigger>
              <Menu.Portal>
                <Menu.Content className="menu" align="end" sideOffset={6}>
                  {/* Desactivar es reversible: la clínica deja de recibir remisiones, sus convenios se conservan. */}
                  <Menu.Item className="menu-item" onSelect={() => actualizar.mutate({ id: c.id, activa: !c.activa })}>
                    {c.activa ? 'Desactivar clínica' : 'Activar clínica'}
                  </Menu.Item>
                </Menu.Content>
              </Menu.Portal>
            </Menu.Root>
          </div>
        )}
        {!c.activa && <p className="aliada-nota">Inactiva: no recibe remisiones nuevas.</p>}
        {actualizar.isError && (
          <p className="error" role="alert">
            {mensajeError(actualizar.error, 'No fue posible actualizar la clínica.')}
          </p>
        )}
      </header>

      <dl className="ficha">
        <div>
          <dt>NIT</dt>
          <dd className="numero">{c.nit ?? '—'}</dd>
        </div>
        <div>
          <dt>Dirección</dt>
          <dd>{c.direccion ?? '—'}</dd>
        </div>
        <div className="ancho">
          <dt>Servicios que presta</dt>
          <dd>{c.servicios ?? '—'}</dd>
        </div>
      </dl>

      <section className="bloque" aria-labelledby="clinica-convenios">
        <h3 id="clinica-convenios">Convenios</h3>
        <Consulta
          consulta={convenios}
          cargando="Cargando los convenios…"
          error="No fue posible cargar los convenios."
          vacio={esAdmin ? 'Sin convenios: no se le puede remitir hasta registrar uno.' : 'Sin convenios: no se le puede remitir.'}
          estaVacio={(d) => d.length === 0}
        >
          {(d) => (
            <div className="scroll-x">
              <table className="tabla tabla-apilable bandeja-tabla">
                <thead>
                  <tr>
                    <th>Beneficio</th>
                    <th>Cubre</th>
                    <th>Tarifa</th>
                    <th>Vigencia</th>
                  </tr>
                </thead>
                <tbody>
                  {d.map((cv) => (
                    <tr key={cv.id}>
                      <td className="principal" data-etiqueta="Beneficio">
                        {cv.beneficio}
                        <div className="bandeja-detalle">
                          <span>{nombrePlan(cv.plan_id)}</span>
                          {!cv.activo && <span>Inactivo</span>}
                        </div>
                      </td>
                      <td data-etiqueta="Cubre">
                        <span className="numero sin-cortes">{cobertura(cv)}</span>
                      </td>
                      <td data-etiqueta="Tarifa">
                        <span className="numero sin-cortes">{moneda(cv.tarifa)}</span>
                      </td>
                      <td data-etiqueta="Vigencia">
                        <span className="numero sin-cortes">
                          {cv.vigente_hasta ? `${fechaCompacta(cv.vigente_desde)} a ${fechaCompacta(cv.vigente_hasta)}` : `Desde el ${fechaCompacta(cv.vigente_desde)}`}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Consulta>
      </section>

      <section className="bloque" aria-labelledby="clinica-remisiones">
        <h3 id="clinica-remisiones">Remisiones</h3>
        {recuentos.data && (
          <p className="aliada-nota">
            {/* Cada recuento lleva a sus remisiones en la bandeja, solo las de esta clínica. */}
            <Link to={`/panel/aliadas?pestana=remisiones&vista=emitida&remisiones_de=${c.id}`}>
              <span className="numero">{recuentos.data.emitida}</span> por usar
            </Link>{' '}
            ·{' '}
            <Link to={`/panel/aliadas?pestana=remisiones&vista=utilizada&remisiones_de=${c.id}`}>
              <span className="numero">{recuentos.data.utilizada}</span> {recuentos.data.utilizada === 1 ? 'atendida' : 'atendidas'}
            </Link>{' '}
            ·{' '}
            <Link to={`/panel/aliadas?pestana=remisiones&vista=anulada&remisiones_de=${c.id}`}>
              <span className="numero">{recuentos.data.anulada}</span> {recuentos.data.anulada === 1 ? 'anulada' : 'anuladas'}
            </Link>
          </p>
        )}
        <Consulta
          consulta={porUsar}
          cargando="Cargando las remisiones…"
          error="No fue posible cargar las remisiones."
          vacio="Ninguna remisión espera atención en esta clínica."
          estaVacio={(d) => d.length === 0}
        >
          {(d) => (
            <ul className="aliada-remisiones">
              {d.map((r) => (
                <li key={r.id}>
                  <Link to={`/panel/familias/${r.familia_id}`}>
                    {r.titular}
                    {r.mascota && ` · ${r.mascota}`}
                  </Link>
                  <span className="bandeja-detalle">
                    <span className="numero">{r.codigo}</span>
                    {r.vencida ? (
                      <span className="bandeja-vencida">
                        <Icono nombre="alerta" size={14} />
                        <span>Venció el</span>
                        <span className="numero">{fechaCompacta(r.vence_en)}</span>
                      </span>
                    ) : (
                      <span className="numero">Vence el {fechaCompacta(r.vence_en)}</span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Consulta>
      </section>
      <NuevoConvenio clinica={c} abierto={nuevo} onCerrar={() => setNuevo(false)} />
    </>
  )
}

function NuevoConvenio({ clinica, abierto, onCerrar }: { clinica: ClinicaRead; abierto: boolean; onCerrar: () => void }) {
  const crear = useCrearConvenio()
  const planes = usePlanes()
  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          crear.reset()
          onCerrar()
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
              plan_id: String(d.get('plan_id') ?? '') || undefined,
            },
            { onSuccess: onCerrar },
          )
        }}
      >
        <label className="campo ancho">
          <span>Beneficio</span>
          <input className="input" name="beneficio" required minLength={3} placeholder="Ej.: Radiografía, hospitalización" />
        </label>
        <label className="campo">
          <span>Plan</span>
          <select className="input" name="plan_id" defaultValue="">
            <option value="">Todos los planes</option>
            {planes.data?.map((p) => (
              <option key={p.id} value={p.id}>{p.nombre}</option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Cobertura (%)</span>
          <input className="input" name="cobertura_pct" type="number" min={0} max={100} defaultValue={100} required />
        </label>
        <label className="campo">
          <span>Tarifa acordada (COP)</span>
          <input className="input" name="tarifa" type="number" min={1} required />
        </label>
        <label className="campo">
          <span>Tope cubierto (COP, opcional)</span>
          <input className="input" name="tope_cubierto" type="number" min={1} />
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
  )
}

function NuevaClinica({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const crear = useCrearClinica()
  const ciudades = useCiudades()
  const [params, setParams] = useSearchParams()
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
            {
              // Se abre su ficha: lo siguiente es registrar sus convenios.
              onSuccess: (creada) => {
                const siguiente = new URLSearchParams(params)
                siguiente.set('clinica', creada.id)
                setParams(siguiente)
                onCerrar()
              },
            },
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
