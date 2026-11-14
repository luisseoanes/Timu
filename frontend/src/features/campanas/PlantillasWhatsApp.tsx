import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'

import {
  useCrearPlantillaWhatsApp,
  useEstadoPlantilla,
  usePlantillasWhatsApp,
} from './api'

export function PlantillasWhatsApp() {
  const plantillas = usePlantillasWhatsApp()
  const crear = useCrearPlantillaWhatsApp()
  const estado = useEstadoPlantilla()
  const [nueva, setNueva] = useState(false)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Plantillas de WhatsApp</h3>
        <button className="btn btn-suave" type="button" onClick={() => setNueva(true)}>
          <Icono nombre="mas" size={16} /> Nueva plantilla
        </button>
      </div>
      <p className="apagado" style={{ marginBottom: 'var(--e4)' }}>
        Meta aprueba cada plantilla antes de que se pueda usar. Registra aquí el estado que muestra el administrador de WhatsApp.
      </p>
      {estado.isError && (
        <p className="error" role="alert">
          {mensajeError(estado.error, 'No fue posible cambiar el estado.')}
        </p>
      )}
      <Consulta consulta={plantillas} cargando="Cargando…" error="No fue posible cargar las plantillas." vacio="No hay plantillas." estaVacio={(p) => p.length === 0}>
        {(p) => (
          <div className="scroll-x">
            <table className="tabla">
              <thead>
                <tr>
                  <th>Plantilla</th>
                  <th>Categoría</th>
                  <th>Texto</th>
                  <th>Aprobación</th>
                  <th>Activa</th>
                </tr>
              </thead>
              <tbody>
                {p.map((pl) => (
                  <tr key={pl.id}>
                    <td className="principal numero">
                      {pl.nombre} <span className="apagado">v{pl.version}</span>
                    </td>
                    <td>{pl.categoria}</td>
                    <td>{pl.cuerpo}</td>
                    <td>
                      <select
                        className="input"
                        value={pl.estado_aprobacion}
                        aria-label={`Aprobación de ${pl.nombre}`}
                        onChange={(e) => estado.mutate({ id: pl.id, estado_aprobacion: e.target.value })}
                      >
                        {['borrador', 'enviada', 'aprobada', 'rechazada', 'pausada'].map((s) => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                    </td>
                    <td>
                      <input
                        type="checkbox"
                        checked={pl.activa}
                        aria-label={`${pl.nombre} activa`}
                        onChange={(e) => estado.mutate({ id: pl.id, estado_aprobacion: pl.estado_aprobacion, activa: e.target.checked })}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Consulta>
      <Modal
        abierto={nueva}
        onCambio={(v) => {
          if (!v) {
            crear.reset()
            setNueva(false)
          }
        }}
        titulo="Nueva plantilla de WhatsApp"
        pie={
          <button className="btn btn-primario" type="submit" form="nueva-plantilla-wa" disabled={crear.isPending}>
            Guardar
          </button>
        }
      >
        <form
          id="nueva-plantilla-wa"
          className="formulario"
          onSubmit={(e) => {
            e.preventDefault()
            const fd = new FormData(e.currentTarget)
            const cuerpo = String(fd.get('cuerpo')).trim()
            const variables = [...cuerpo.matchAll(/\{\{(\d+)\}\}/g)].map((m) => m[1] ?? '')
            crear.mutate(
              { nombre: String(fd.get('nombre')).trim(), categoria: String(fd.get('categoria')), cuerpo, variables: [...new Set(variables)] },
              { onSuccess: () => setNueva(false) },
            )
          }}
        >
          <label className="campo">
            <span>Nombre (como en Meta)</span>
            <input className="input" name="nombre" required pattern="[a-z0-9_]+" />
          </label>
          <label className="campo">
            <span>Categoría</span>
            <select className="input" name="categoria" defaultValue="utility">
              <option value="utility">Utilidad</option>
              <option value="marketing">Marketing</option>
              <option value="authentication">Autenticación</option>
            </select>
          </label>
          <label className="campo ancho">
            <span>Texto (variables {'{{1}}'}, {'{{2}}'}…)</span>
            <textarea className="input" name="cuerpo" rows={4} required />
          </label>
          {crear.isError && (
            <p className="error ancho" role="alert">
              {mensajeError(crear.error, 'No fue posible guardar la plantilla.')}
            </p>
          )}
        </form>
      </Modal>
    </section>
  )
}
