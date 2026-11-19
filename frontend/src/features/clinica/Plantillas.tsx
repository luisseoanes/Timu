import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'

import { useCrearPlantilla, usePlantillas, CAMPOS_CLINICOS } from './api'

export function Plantillas() {
  const plantillas = usePlantillas()
  const crear = useCrearPlantilla()
  const [nueva, setNueva] = useState(false)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Plantillas de consulta</h3>
        <button className="btn btn-suave" type="button" onClick={() => setNueva(true)}>
          <Icono nombre="mas" size={16} /> Nueva plantilla
        </button>
      </div>
      <Consulta
        consulta={plantillas}
        cargando="Cargando plantillas…"
        error="No fue posible cargar las plantillas."
        vacio="No hay plantillas. Agilizan el registro de consultas frecuentes."
        estaVacio={(d) => d.length === 0}
      >
        {(d) =>
          d.map((p) => (
            <div key={p.codigo} className="fila">
              <div className="fila-cuerpo">
                <strong>{p.nombre}</strong>
                <span>{Object.keys(p.campos).join(', ') || 'Sin campos prellenados'}</span>
              </div>
            </div>
          ))
        }
      </Consulta>
      <Modal
        abierto={nueva}
        onCambio={(v) => {
          if (!v) {
            crear.reset()
            setNueva(false)
          }
        }}
        titulo="Nueva plantilla"
        descripcion="Los campos que llenes aquí aparecen prellenados al registrar una consulta."
        pie={
          <button className="btn btn-primario" type="submit" form="nueva-plantilla" disabled={crear.isPending}>
            Guardar plantilla
          </button>
        }
      >
        <form
          id="nueva-plantilla"
          className="formulario"
          onSubmit={(e) => {
            e.preventDefault()
            const d = new FormData(e.currentTarget)
            const campos: Record<string, string> = {}
            for (const { campo } of CAMPOS_CLINICOS) {
              const v = String(d.get(campo) ?? '').trim()
              if (v) campos[campo] = v
            }
            crear.mutate(
              { codigo: String(d.get('codigo')).trim(), nombre: String(d.get('nombre')).trim(), campos },
              { onSuccess: () => setNueva(false) },
            )
          }}
        >
          <label className="campo">
            <span>Código</span>
            <input className="input" name="codigo" required pattern="[a-z0-9_]+" />
          </label>
          <label className="campo">
            <span>Nombre</span>
            <input className="input" name="nombre" required />
          </label>
          {CAMPOS_CLINICOS.filter((c) => c.campo !== 'notas_internas').map(({ campo, label }) => (
            <label key={campo} className="campo ancho">
              <span>{label}</span>
              <textarea className="input" name={campo} rows={2} />
            </label>
          ))}
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
