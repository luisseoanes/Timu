import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useAuth } from '@/features/auth'
import { mensajeError } from '@/lib/errores'
import { puede } from '@/lib/permisos'

import { useCrearSegmento, useSegmentos, type FiltrosSegmento } from './api'
import { FormFiltros } from './FormFiltros'
import { resumenFiltros } from './segmento'

export function Segmentos() {
  const { usuario } = useAuth()
  const segmentos = useSegmentos()
  const crear = useCrearSegmento()
  const [nuevo, setNuevo] = useState(false)
  const [filtros, setFiltros] = useState<FiltrosSegmento>({})

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Segmentos guardados</h3>
        {puede(usuario, 'mercadeo') && (
          <button className="btn btn-suave" type="button" onClick={() => setNuevo(true)}>
            <Icono nombre="mas" size={16} /> Nuevo segmento
          </button>
        )}
      </div>
      <Consulta
        consulta={segmentos}
        cargando="Cargando segmentos…"
        error="No fue posible cargar los segmentos."
        vacio={
          puede(usuario, 'mercadeo')
            ? 'Un segmento guarda a quién le llega una campaña (ciudad, plan, estado de la afiliación) para usarlo otra vez. Crea el primero con «Nuevo segmento».'
            : 'Todavía no hay segmentos: los crea mercadeo para elegir a quién le llega una campaña.'
        }
        estaVacio={(s) => s.length === 0}
      >
        {(s) =>
          s.map((seg) => (
            <div key={seg.id} className="fila">
              <span className="fila-icono">
                <Icono nombre="familias" size={16} />
              </span>
              <div className="fila-cuerpo">
                <strong>{seg.nombre}</strong>
                <span>{seg.descripcion ?? resumenFiltros(seg.filtros as FiltrosSegmento)}</span>
              </div>
            </div>
          ))
        }
      </Consulta>
      <Modal
        abierto={nuevo}
        onCambio={(v) => {
          if (!v) {
            crear.reset()
            setNuevo(false)
          }
        }}
        titulo="Nuevo segmento"
        pie={
          <button className="btn btn-primario" type="submit" form="nuevo-segmento" disabled={crear.isPending}>
            Guardar segmento
          </button>
        }
      >
        <form
          id="nuevo-segmento"
          className="formulario"
          onSubmit={(e) => {
            e.preventDefault()
            const fd = new FormData(e.currentTarget)
            crear.mutate(
              { nombre: String(fd.get('nombre')).trim(), descripcion: String(fd.get('descripcion') ?? '').trim() || undefined, filtros },
              { onSuccess: () => { setNuevo(false); setFiltros({}) } },
            )
          }}
        >
          <label className="campo">
            <span>Nombre</span>
            <input className="input" name="nombre" required />
          </label>
          <label className="campo">
            <span>Descripción</span>
            <input className="input" name="descripcion" />
          </label>
          <div className="ancho">
            <FormFiltros valor={filtros} onCambio={setFiltros} />
          </div>
          {crear.isError && (
            <p className="error ancho" role="alert">
              {mensajeError(crear.error, 'No fue posible guardar el segmento.')}
            </p>
          )}
        </form>
      </Modal>
    </section>
  )
}
