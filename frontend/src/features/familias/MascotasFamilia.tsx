import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Modal } from '@/components/Modal'
import { useEspecies } from '@/features/catalogos/api'
import { mensajeError } from '@/lib/errores'
import { fecha } from '@/lib/formato'
import type { FamiliaRead, MascotaRead } from '@/types'

import { useAgregarMascota, useBajaMascota, type NuevaMascota } from './api'

export function MascotasFamilia({ familia }: { familia: FamiliaRead }) {
  const [agregando, setAgregando] = useState(false)
  const [deBaja, setDeBaja] = useState<MascotaRead | null>(null)
  const especies = useEspecies()
  const mascotas = familia.mascotas ?? []
  const nombreEspecie = (codigo: string) => especies.data?.find((e) => e.codigo === codigo)?.nombre ?? codigo

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Mascotas</h3>
        {!familia.dada_de_baja_en && (
          <button className="btn btn-suave" type="button" onClick={() => setAgregando(true)}>
            Agregar mascota
          </button>
        )}
      </div>
      {mascotas.length === 0 ? (
        <p className="apagado">Esta familia no tiene mascotas registradas.</p>
      ) : (
        <div className="scroll-x">
          <table className="tabla">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Especie</th>
                <th>Raza</th>
                <th>Sexo</th>
                <th>Nacimiento</th>
                <th>Estado</th>
                <th><span className="sr-only">Acciones</span></th>
              </tr>
            </thead>
            <tbody>
              {mascotas.map((m) => (
                <tr key={m.id}>
                  <td className="principal">{m.nombre}</td>
                  <td>{nombreEspecie(m.especie)}</td>
                  <td>{m.raza ?? '—'}</td>
                  <td>{m.sexo ?? '—'}</td>
                  <td className="numero">{fecha(m.fecha_nacimiento)}</td>
                  <td>
                    {m.activa ? (
                      <span className="distintivo distintivo-ok">Activa</span>
                    ) : (
                      <span className="distintivo distintivo-neutro" title={m.motivo_baja ?? undefined}>
                        De baja
                      </span>
                    )}
                  </td>
                  <td>
                    <Link to={`/clinica/mascotas/${m.id}`} className="btn btn-plano">
                      Historia
                    </Link>
                    {m.activa && (
                      <button className="btn btn-plano" type="button" onClick={() => setDeBaja(m)}>
                        Dar de baja
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <AgregarMascotaModal familiaId={familia.id} abierto={agregando} onCerrar={() => setAgregando(false)} />
      <BajaMascotaModal mascota={deBaja} onCerrar={() => setDeBaja(null)} />
    </section>
  )
}

function AgregarMascotaModal({ familiaId, abierto, onCerrar }: { familiaId: string; abierto: boolean; onCerrar: () => void }) {
  const agregar = useAgregarMascota(familiaId)
  const especies = useEspecies()

  function guardar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    const opcional = (campo: string) => String(d.get(campo) ?? '').trim() || undefined
    const mascota: NuevaMascota = {
      nombre: String(d.get('nombre') ?? '').trim(),
      especie: String(d.get('especie') ?? ''),
      raza: opcional('raza'),
      sexo: opcional('sexo') as NuevaMascota['sexo'],
      fecha_nacimiento: opcional('fecha_nacimiento'),
    }
    agregar.mutate(mascota, { onSuccess: onCerrar })
  }

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          agregar.reset()
          onCerrar()
        }
      }}
      titulo="Agregar mascota"
      descripcion="Cada mascota adicional puede cambiar el valor mensual del contrato."
      pie={
        <button className="btn btn-primario" type="submit" form="agregar-mascota" disabled={agregar.isPending}>
          {agregar.isPending ? 'Guardando…' : 'Agregar'}
        </button>
      }
    >
      <form id="agregar-mascota" className="formulario" onSubmit={guardar}>
        <label className="campo">
          <span>Nombre</span>
          <input className="input" name="nombre" required />
        </label>
        <label className="campo">
          <span>Especie</span>
          <select className="input" name="especie" required defaultValue="">
            <option value="" disabled>Selecciona la especie</option>
            {especies.data
              ?.filter((e) => e.activa)
              .map((e) => (
                <option key={e.codigo} value={e.codigo}>{e.nombre}</option>
              ))}
          </select>
        </label>
        <label className="campo">
          <span>Raza (opcional)</span>
          <input className="input" name="raza" />
        </label>
        <label className="campo">
          <span>Sexo (opcional)</span>
          <select className="input" name="sexo" defaultValue="">
            <option value="">Sin dato</option>
            <option value="hembra">Hembra</option>
            <option value="macho">Macho</option>
          </select>
        </label>
        <label className="campo">
          <span>Fecha de nacimiento (opcional)</span>
          <input className="input" name="fecha_nacimiento" type="date" />
        </label>
        {agregar.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(agregar.error, 'No fue posible agregar la mascota.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

function BajaMascotaModal({ mascota, onCerrar }: { mascota: MascotaRead | null; onCerrar: () => void }) {
  const baja = useBajaMascota()

  function guardar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!mascota) return
    const motivo = String(new FormData(e.currentTarget).get('motivo') ?? '').trim()
    baja.mutate({ id: mascota.id, motivo }, { onSuccess: onCerrar })
  }

  return (
    <Modal
      abierto={mascota !== null}
      onCambio={(v) => {
        if (!v) {
          baja.reset()
          onCerrar()
        }
      }}
      titulo={`Dar de baja a ${mascota?.nombre ?? 'la mascota'}`}
      descripcion="La mascota deja de recibir servicios. Su historia clínica se conserva."
      pie={
        <button className="btn btn-primario" type="submit" form="baja-mascota" disabled={baja.isPending}>
          {baja.isPending ? 'Guardando…' : 'Confirmar baja'}
        </button>
      }
    >
      <form id="baja-mascota" className="formulario" onSubmit={guardar}>
        <label className="campo ancho">
          <span>Motivo</span>
          <textarea className="input" name="motivo" rows={3} required minLength={3} />
        </label>
        {baja.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(baja.error, 'No fue posible dar de baja a la mascota.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
