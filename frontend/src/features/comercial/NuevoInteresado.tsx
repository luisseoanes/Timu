import { useSearchParams } from 'react-router-dom'

import { Modal } from '@/components/Modal'
import { useCiudades } from '@/features/catalogos'
import { mensajeError } from '@/lib/errores'

import { ORIGENES, useCrearInteresado } from './api'

/** Registrar a alguien que llegó por fuera de WhatsApp: al guardarlo, su ficha queda abierta. */
export function NuevoInteresado({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const crear = useCrearInteresado()
  const ciudades = useCiudades()
  const [params, setParams] = useSearchParams()

  function cerrar() {
    crear.reset()
    onCerrar()
  }

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => !v && cerrar()}
      titulo="Nuevo interesado"
      descripcion="Con el celular o el correo basta. Si ya escribió por WhatsApp, se une a su conversación."
      pie={
        <button className="btn btn-primario" type="submit" form="nuevo-interesado" disabled={crear.isPending}>
          {crear.isPending ? 'Guardando…' : 'Guardar interesado'}
        </button>
      }
    >
      <form
        id="nuevo-interesado"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const d = new FormData(e.currentTarget)
          const t = (c: string) => String(d.get(c) ?? '').trim() || undefined
          crear.mutate(
            { nombre: t('nombre'), telefono: t('telefono'), email: t('email'), ciudad: t('ciudad'), origen: String(d.get('origen')) },
            {
              onSuccess: (creado) => {
                const siguiente = new URLSearchParams(params)
                siguiente.set('interesado', creado.id)
                setParams(siguiente)
                cerrar()
              },
            },
          )
        }}
      >
        <label className="campo">
          <span>Nombre</span>
          <input className="input" name="nombre" autoComplete="off" />
        </label>
        <label className="campo">
          <span>Celular</span>
          <input className="input" name="telefono" inputMode="tel" autoComplete="off" />
        </label>
        <label className="campo">
          <span>Correo</span>
          <input className="input" name="email" type="email" autoComplete="off" />
        </label>
        <label className="campo">
          <span>Ciudad</span>
          <select className="input" name="ciudad" defaultValue="">
            <option value="">Sin ciudad</option>
            {ciudades.data?.map((c) => (
              <option key={c.nombre} value={c.nombre}>{c.nombre}</option>
            ))}
          </select>
        </label>
        <label className="campo ancho">
          <span>Cómo llegó</span>
          <select className="input" name="origen" defaultValue="panel">
            {ORIGENES.map((o) => (
              <option key={o.valor} value={o.valor}>{o.label}</option>
            ))}
          </select>
        </label>
        {crear.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(crear.error, 'No fue posible guardar el interesado.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
