import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useAuth } from '@/features/auth'
import { mensajeError } from '@/lib/errores'
import { puede } from '@/lib/permisos'
import type { RespuestaRead } from '@/types'

import { useAprobarRespuesta, useCrearRespuesta, useRespuestas } from './api'

export function Respuestas() {
  const { usuario } = useAuth()
  const respuestas = useRespuestas()
  const aprobar = useAprobarRespuesta()
  const [nueva, setNueva] = useState(false)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Respuestas aprobadas</h3>
        <button className="btn btn-suave" type="button" onClick={() => setNueva(true)}>
          <Icono nombre="mas" size={16} /> Nueva respuesta
        </button>
      </div>
      <p className="apagado" style={{ marginBottom: 'var(--e4)' }}>
        La orientación virtual sólo sale de estas respuestas. Las variables van numeradas en el texto: {'{{1}}'}, {'{{2}}'}…
      </p>
      {aprobar.isError && (
        <p className="error" role="alert">
          {mensajeError(aprobar.error, 'No fue posible aprobar.')}
        </p>
      )}
      <Consulta
        consulta={respuestas}
        cargando="Cargando respuestas…"
        error="No fue posible cargar las respuestas."
        vacio="Aún no hay respuestas. Crea la primera."
        estaVacio={(d) => d.length === 0}
      >
        {(d) =>
          d.map((r: RespuestaRead) => (
            <div key={r.codigo} className="fila">
              <div className="fila-cuerpo">
                <strong>{r.titulo}</strong>
                <span>{r.cuerpo}</span>
              </div>
              <Insignia tono={r.estado === 'aprobada' ? 'ok' : 'alerta'}>
                {r.estado === 'aprobada' ? 'Aprobada' : 'Por aprobar'}
              </Insignia>
              {r.estado !== 'aprobada' && puede(usuario, 'administrar') && (
                <button className="btn btn-plano" type="button" onClick={() => aprobar.mutate(r.codigo)}>
                  Aprobar
                </button>
              )}
            </div>
          ))
        }
      </Consulta>
      <NuevaRespuesta abierto={nueva} onCerrar={() => setNueva(false)} />
    </section>
  )
}

function NuevaRespuesta({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const crear = useCrearRespuesta()
  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          crear.reset()
          onCerrar()
        }
      }}
      titulo="Nueva respuesta"
      descripcion="Queda por aprobar hasta que la administración la revise."
      pie={
        <button className="btn btn-primario" type="submit" form="nueva-respuesta" disabled={crear.isPending}>
          Guardar
        </button>
      }
    >
      <form
        id="nueva-respuesta"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const d = new FormData(e.currentTarget)
          const cuerpo = String(d.get('cuerpo')).trim()
          const variables = String(d.get('variables') ?? '')
            .split(',')
            .map((v) => v.trim())
            .filter(Boolean)
          crear.mutate(
            { codigo: String(d.get('codigo')).trim(), titulo: String(d.get('titulo')).trim(), cuerpo, variables },
            { onSuccess: onCerrar },
          )
        }}
      >
        <label className="campo">
          <span>Código</span>
          <input className="input" name="codigo" required pattern="[a-z0-9_]+" title="minúsculas, números y guion bajo" />
        </label>
        <label className="campo">
          <span>Título</span>
          <input className="input" name="titulo" required />
        </label>
        <label className="campo ancho">
          <span>Texto (variables numeradas: {'{{1}}'}, {'{{2}}'}…)</span>
          <textarea className="input" name="cuerpo" rows={4} required placeholder="Hola, para {{1}} recomendamos…" />
        </label>
        <label className="campo ancho">
          <span>Nombre de cada variable, en orden y separados por coma</span>
          <input className="input" name="variables" placeholder="mascota, medicamento" />
        </label>
        {crear.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(crear.error, 'No fue posible guardar.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
