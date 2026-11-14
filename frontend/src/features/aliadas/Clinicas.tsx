import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useAuth } from '@/features/auth'
import { useCiudades } from '@/features/catalogos'
import { mensajeError } from '@/lib/errores'
import { hoyISO, moneda } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { ClinicaRead } from '@/types'

import {
  useActualizarClinica,
  useClinicas,
  useConvenios,
  useCrearClinica,
  useCrearConvenio,
} from './api'

export function Clinicas() {
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
                {!c.activa && <Insignia tono="neutro">Inactiva</Insignia>}
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
