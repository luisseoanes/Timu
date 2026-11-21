import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'
import type { PlantillaWhatsAppRead } from '@/types'

import { useCrearPlantillaWhatsApp, useEstadoPlantilla, usePlantillasWhatsApp } from './api'

// Los valores son los del backend (core/enums.py): CategoriaPlantilla y EstadoAprobacionPlantilla.
const CATEGORIAS: Record<string, string> = { utility: 'Servicio', marketing: 'Promoción', authentication: 'Verificación' }
const APROBACION: Record<string, string> = {
  borrador: 'Borrador',
  enviada: 'Enviada a Meta',
  aprobada: 'Aprobada',
  rechazada: 'Rechazada',
  pausada: 'Pausada',
}

export function PlantillasWhatsApp() {
  const plantillas = usePlantillasWhatsApp()
  const crear = useCrearPlantillaWhatsApp()
  const estado = useEstadoPlantilla()
  const [nueva, setNueva] = useState(false)
  // El Inicio del administrador pide registrar una plantilla que citan las reglas
  // (`?nueva=<código>&titulo=<nombre>`): la ventana se abre con esos dos campos ya puestos.
  const [params, setParams] = useSearchParams()
  const pedida = params.get('nueva')
  // Editar el texto es registrar la versión siguiente: Meta vuelve a revisarla.
  const [editando, setEditando] = useState<PlantillaWhatsAppRead | null>(null)
  const abierta = nueva || pedida !== null || editando !== null

  function cerrar() {
    crear.reset()
    setNueva(false)
    setEditando(null)
    if (pedida !== null) {
      const sin = new URLSearchParams(params)
      sin.delete('nueva')
      sin.delete('titulo')
      setParams(sin, { replace: true })
    }
  }

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h2>Plantillas de WhatsApp</h2>
        <button className="btn btn-suave" type="button" onClick={() => setNueva(true)}>
          <Icono nombre="mas" size={16} /> Nueva plantilla
        </button>
      </div>
      <p className="campana-nota campana-intro">
        Meta aprueba cada plantilla antes de que se pueda usar. Registra aquí el estado que muestra el administrador de WhatsApp:
        al marcar como aprobada la versión más reciente, pasa a ser la que se envía.
      </p>
      {estado.isError && (
        <p className="error" role="alert">
          {mensajeError(estado.error, 'No fue posible cambiar el estado.')}
        </p>
      )}
      <Consulta consulta={plantillas} cargando="Cargando…" error="No fue posible cargar las plantillas." vacio="No hay plantillas." estaVacio={(p) => p.length === 0}>
        {(p) => (
          <div className="scroll-x">
            <table className="tabla tabla-apilable bandeja-tabla">
              <thead>
                <tr>
                  <th>Plantilla</th>
                  <th>Texto</th>
                  <th>Aprobación de Meta</th>
                  <th>Activa</th>
                  <th>
                    <span className="sr-only">Acciones</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {p.map((pl, i) => (
                  <tr key={pl.id}>
                    <td className="principal" data-etiqueta="Plantilla">
                      {pl.titulo ?? <span className="campana-plantilla">{pl.nombre}</span>}
                      <div className="bandeja-detalle">
                        {pl.titulo && <span className="campana-plantilla">{pl.nombre}</span>}
                        <span>{CATEGORIAS[pl.categoria] ?? pl.categoria}</span>
                        <span className="numero">versión {pl.version}</span>
                      </div>
                    </td>
                    <td data-etiqueta="Texto">
                      <span className="plantilla-cuerpo">{pl.cuerpo}</span>
                    </td>
                    <td data-etiqueta="Aprobación de Meta">
                      <select
                        className="input"
                        value={pl.estado_aprobacion}
                        aria-label={`Aprobación de ${pl.nombre}`}
                        onChange={(e) => estado.mutate({ id: pl.id, estado_aprobacion: e.target.value })}
                      >
                        {Object.entries(APROBACION).map(([valor, label]) => (
                          <option key={valor} value={valor}>{label}</option>
                        ))}
                      </select>
                    </td>
                    <td data-etiqueta="Activa">
                      <input
                        type="checkbox"
                        checked={pl.activa}
                        aria-label={`${pl.nombre} activa`}
                        onChange={(e) => estado.mutate({ id: pl.id, estado_aprobacion: pl.estado_aprobacion, activa: e.target.checked })}
                      />
                    </td>
                    <td className="tabla-acciones">
                      {/* El texto se cambia sobre la versión más reciente (la lista viene de la más nueva a la más vieja). */}
                      {p.findIndex((otra) => otra.nombre === pl.nombre && otra.idioma === pl.idioma) === i && (
                        <button className="btn btn-plano btn-accion" type="button" onClick={() => setEditando(pl)} aria-label={`Editar texto de ${pl.titulo ?? pl.nombre}`}>
                          Editar texto
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
      <Modal
        abierto={abierta}
        onCambio={(v) => {
          if (!v) cerrar()
        }}
        titulo={editando ? `Editar «${editando.titulo ?? editando.nombre}»` : 'Nueva plantilla de WhatsApp'}
        descripcion={
          editando
            ? `El texto nuevo queda como versión ${editando.version + 1}, en borrador. Hasta que Meta lo apruebe y lo marques como aprobado, se sigue enviando el que está en uso.`
            : undefined
        }
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
              {
                nombre: String(fd.get('nombre')).trim(),
                titulo: String(fd.get('titulo')).trim() || undefined,
                categoria: String(fd.get('categoria')),
                cuerpo,
                variables: [...new Set(variables)],
              },
              { onSuccess: cerrar },
            )
          }}
        >
          <label className="campo">
            <span>Nombre para el equipo</span>
            <input className="input" name="titulo" minLength={3} maxLength={120} placeholder="Aviso de mora" defaultValue={editando?.titulo ?? params.get('titulo') ?? ''} />
          </label>
          <label className="campo">
            <span>Código en Meta</span>
            {/* Al editar, el código es el de la plantilla: cambiarlo sería otra plantilla. */}
            <input className="input" name="nombre" required pattern="[a-z0-9_]+" defaultValue={editando?.nombre ?? pedida ?? ''} readOnly={editando !== null} />
          </label>
          <label className="campo">
            <span>Categoría</span>
            <select className="input" name="categoria" defaultValue={editando?.categoria ?? 'utility'}>
              {Object.entries(CATEGORIAS).map(([valor, label]) => (
                <option key={valor} value={valor}>{label}</option>
              ))}
            </select>
          </label>
          <label className="campo ancho">
            <span>Texto (variables {'{{1}}'}, {'{{2}}'}…)</span>
            <textarea className="input" name="cuerpo" rows={4} required defaultValue={editando?.cuerpo ?? ''} />
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
