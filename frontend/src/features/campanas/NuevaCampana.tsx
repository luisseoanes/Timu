import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'

import { useCrearCampana, usePlantillasWhatsApp, useSegmentos, type FiltrosSegmento } from './api'
import { FormFiltros } from './FormFiltros'

/** Crear una campaña: su plantilla aprobada, cómo se llena cada variable y a quién le llega. Al
 * crearla, su ficha queda abierta para programar el envío. */
export function NuevaCampana({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const crear = useCrearCampana()
  const [params, setParams] = useSearchParams()
  const plantillas = usePlantillasWhatsApp()
  const segmentos = useSegmentos()
  const [plantilla, setPlantilla] = useState('')
  const [segmentoId, setSegmentoId] = useState('')
  const [filtros, setFiltros] = useState<FiltrosSegmento>({})
  const elegida = plantillas.data?.find((p) => p.nombre === plantilla)
  const aprobadas = plantillas.data?.filter((p) => p.estado_aprobacion === 'aprobada' && p.activa) ?? []

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          crear.reset()
          onCerrar()
        }
      }}
      titulo="Nueva campaña"
      descripcion="Sólo se envían plantillas aprobadas por Meta. Quien se dio de baja queda fuera."
      pie={
        <button className="btn btn-primario" type="submit" form="nueva-campana" disabled={!plantilla || crear.isPending}>
          {crear.isPending ? 'Creando…' : 'Crear campaña'}
        </button>
      }
    >
      <form
        id="nueva-campana"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const fd = new FormData(e.currentTarget)
          // Cada variable sale de un dato de la familia o de un texto fijo (campanas/service.py: _variables).
          const variables = (elegida?.variables ?? []).map((_, i) => {
            const fuente = String(fd.get(`fuente_${i}`) ?? 'titular_nombre')
            return fuente === 'texto' ? `texto:${String(fd.get(`texto_${i}`) ?? '')}` : fuente
          })
          crear.mutate(
            {
              nombre: String(fd.get('nombre')).trim(),
              plantilla,
              variables,
              segmento_id: segmentoId || undefined,
              segmento: segmentoId ? undefined : filtros,
            },
            {
              onSuccess: (creada) => {
                const siguiente = new URLSearchParams(params)
                siguiente.set('campana', creada.id)
                setParams(siguiente)
                crear.reset()
                onCerrar()
              },
            },
          )
        }}
      >
        <label className="campo ancho">
          <span>Nombre</span>
          <input className="input" name="nombre" required />
        </label>
        <label className="campo">
          <span>Plantilla</span>
          <select className="input" value={plantilla} onChange={(e) => setPlantilla(e.target.value)} required>
            <option value="" disabled>
              {aprobadas.length ? 'Elige la plantilla' : 'No hay plantillas aprobadas'}
            </option>
            {aprobadas.map((p) => (
              <option key={p.id} value={p.nombre}>{p.titulo ?? p.nombre}</option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Audiencia</span>
          <select className="input" value={segmentoId} onChange={(e) => setSegmentoId(e.target.value)}>
            <option value="">Filtros a la medida</option>
            {segmentos.data?.map((s) => (
              <option key={s.id} value={s.id}>{s.nombre}</option>
            ))}
          </select>
        </label>
        {elegida && <p className="aviso ancho">{elegida.cuerpo}</p>}
        {elegida?.variables.map((v, i) => (
          <fieldset key={v} className="formulario ancho">
            <legend className="ancho">Variable {`{{${v}}}`}</legend>
            <label className="campo">
              <span>Se llena con</span>
              <select className="input" name={`fuente_${i}`} defaultValue="titular_nombre">
                <option value="titular_nombre">Nombre del titular</option>
                <option value="mascota_nombre">Nombre de la mascota</option>
                <option value="ciudad">Ciudad</option>
                <option value="plan">Plan</option>
                <option value="texto">Texto fijo</option>
              </select>
            </label>
            <label className="campo">
              <span>Texto fijo (si aplica)</span>
              <input className="input" name={`texto_${i}`} />
            </label>
          </fieldset>
        ))}
        {!segmentoId && (
          <div className="ancho">
            <FormFiltros valor={filtros} onCambio={setFiltros} />
          </div>
        )}
        {crear.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(crear.error, 'No fue posible crear la campaña.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
