import { useId, useState } from 'react'

import { Icono } from '@/components/Icono'
import { Insignia } from '@/components/Distintivo'
import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'
import type { ClinicaRead, TipoAliada } from '@/types'

import { useActualizarClinica, useQuitarLogo, useSubirLogo } from './api'
import { TIPOS_ALIADA } from './portada'

// Lo que dice de una aliada la portada pública (R3-PUB-04): un bloque de su ficha con su propia
// ventana, decidido con el usuario, sin mezclarlo con lo interno (NIT, correo, convenios).

export function EnLaPortada({ clinica: c, editable }: { clinica: ClinicaRead; editable: boolean }) {
  const [editando, setEditando] = useState(false)
  return (
    <section className="bloque" aria-labelledby="clinica-portada">
      <h3 id="clinica-portada">En la portada</h3>
      {c.en_portada ? (
        <div className="aliada-portada">
          {c.logo_url && <img className="aliada-logo" src={c.logo_url} alt={`Logo de ${c.nombre}`} />}
          <dl className="ficha">
            <div>
              <dt>Es</dt>
              <dd>
                {c.tipo_nombre} {c.atiende_24h && <Insignia tono="ok">24 horas</Insignia>}
              </dd>
            </div>
            <div>
              <dt>Lugar en la red</dt>
              <dd className="numero">{c.orden_portada}</dd>
            </div>
            <div>
              <dt>Barrio</dt>
              <dd>{c.barrio ?? <span className="apagado">Sin escribir</span>}</dd>
            </div>
            <div>
              <dt>Horario</dt>
              <dd>{c.horario ?? <span className="apagado">Sin escribir</span>}</dd>
            </div>
            <div className="ancho">
              <dt>Presentación</dt>
              <dd>{c.presentacion ?? <span className="apagado">Sin escribir: la portada solo dice su nombre y dónde está.</span>}</dd>
            </div>
          </dl>
        </div>
      ) : (
        <p className="admin-nota">No sale en la portada: quien entra a timu.com.co no la ve en la red de aliadas.</p>
      )}
      {editable && (
        <div>
          <button className="btn btn-secundario" type="button" onClick={() => setEditando(true)}>
            Editar cómo sale en la portada
          </button>
        </div>
      )}
      {editando && <EditarEnPortada clinica={c} onCerrar={() => setEditando(false)} />}
    </section>
  )
}

function EditarEnPortada({ clinica: c, onCerrar }: { clinica: ClinicaRead; onCerrar: () => void }) {
  const id = useId()
  const actualizar = useActualizarClinica()
  const subirLogo = useSubirLogo()
  const quitarLogo = useQuitarLogo()
  const [logo, setLogo] = useState<File | null>(null)
  const error = actualizar.error ?? subirLogo.error ?? quitarLogo.error
  const guardando = actualizar.isPending || subirLogo.isPending || quitarLogo.isPending

  return (
    <Modal
      abierto
      onCambio={(v) => !v && onCerrar()}
      titulo={`${c.nombre} en la portada`}
      descripcion="Lo que ve quien entra a timu.com.co en la red de aliadas. Lo interno (NIT, correo, convenios) no sale."
      pie={
        <button className="btn btn-primario" type="submit" form="aliada-portada" disabled={guardando}>
          Guardar
        </button>
      }
    >
      <form
        id="aliada-portada"
        className="formulario"
        onSubmit={async (e) => {
          e.preventDefault()
          const d = new FormData(e.currentTarget)
          const texto = (n: string) => String(d.get(n) ?? '').trim() || null
          try {
            await actualizar.mutateAsync({
              id: c.id,
              en_portada: d.get('en_portada') === 'on',
              tipo: String(d.get('tipo')) as TipoAliada,
              atiende_24h: d.get('atiende_24h') === 'on',
              barrio: texto('barrio'),
              horario: texto('horario'),
              presentacion: texto('presentacion'),
              orden_portada: Number(d.get('orden_portada') || 0),
            })
            if (logo) await subirLogo.mutateAsync({ id: c.id, logo })
            onCerrar()
          } catch {
            // El error de cada paso lo muestra el aviso de abajo.
          }
        }}
      >
        <label className="acciones ancho">
          <input type="checkbox" name="en_portada" defaultChecked={c.en_portada} />
          <span>Mostrarla en la portada</span>
        </label>
        <div className="campo">
          <label htmlFor={`${id}-tipo`}>Qué es</label>
          <select id={`${id}-tipo`} className="input" name="tipo" defaultValue={c.tipo}>
            {TIPOS_ALIADA.map((t) => (
              <option key={t.valor} value={t.valor}>
                {t.nombre}
              </option>
            ))}
          </select>
        </div>
        <label className="acciones">
          <input type="checkbox" name="atiende_24h" defaultChecked={c.atiende_24h} />
          <span>Atiende las 24 horas</span>
        </label>
        <div className="campo">
          <label htmlFor={`${id}-barrio`}>Barrio</label>
          <input id={`${id}-barrio`} className="input" name="barrio" maxLength={120} defaultValue={c.barrio ?? ''} />
        </div>
        <div className="campo">
          <label htmlFor={`${id}-orden`}>Lugar en la red</label>
          <input
            id={`${id}-orden`}
            className="input"
            name="orden_portada"
            type="number"
            min={0}
            max={1000}
            aria-describedby={`${id}-orden-ayuda`}
            defaultValue={c.orden_portada}
          />
          <span className="campo-ayuda" id={`${id}-orden-ayuda`}>
            De menor a mayor, de norte a sur del valle.
          </span>
        </div>
        <div className="campo ancho">
          <label htmlFor={`${id}-horario`}>Horario</label>
          <input id={`${id}-horario`} className="input" name="horario" maxLength={255} defaultValue={c.horario ?? ''} />
        </div>
        <div className="campo ancho">
          <label htmlFor={`${id}-presentacion`}>Presentación</label>
          <textarea id={`${id}-presentacion`} className="input" name="presentacion" rows={3} maxLength={2000} defaultValue={c.presentacion ?? ''} />
        </div>
        <div className="campo ancho">
          {/* El control del navegador dice «Choose File» en su idioma: un botón propio con la palabra nuestra. */}
          <span className="registro-foto-etiqueta" id={`${id}-logo`}>
            Logo (JPG, PNG o WEBP de hasta 2 MB)
          </span>
          <div className="acciones">
            <label className="btn btn-secundario registro-foto">
              <Icono nombre="subir" size={16} /> {logo || c.logo_url ? 'Cambiar logo' : 'Elegir logo'}
              <input className="sr-only" type="file" accept="image/jpeg,image/png,image/webp" aria-labelledby={`${id}-logo`} onChange={(e) => setLogo(e.target.files?.[0] ?? null)} />
            </label>
            {c.logo_url && !logo && (
              <button className="btn btn-plano" type="button" disabled={quitarLogo.isPending} onClick={() => quitarLogo.mutate(c.id)}>
                Quitar logo
              </button>
            )}
          </div>
          {logo && <span className="campo-ayuda">{logo.name}: se sube al guardar.</span>}
        </div>
        {error && (
          <p className="error ancho" role="alert">
            {mensajeError(error, 'No fue posible guardar cómo sale en la portada.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
