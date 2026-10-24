import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useAuth } from '@/features/auth/AuthContext'
import { useFamilia } from '@/features/familias/api'
import { useMascotas } from '@/features/preventivos/api'
import { mensajeError } from '@/lib/errores'
import { fecha, hoyISO } from '@/lib/formato'
import { puede } from '@/lib/permisos'

import { CAMPOS_CLINICOS, useCrearEntrada, useHistoria, usePlantillas, type DatosEntrada } from './api'

/** Historia clínica de una mascota: línea de tiempo de consultas, de la más reciente. */
export function HistoriaMascotaPage() {
  const { mascotaId = '' } = useParams()
  const { usuario } = useAuth()
  const mascota = useMascotas([mascotaId]).get(mascotaId)
  const familia = useFamilia(mascota?.familia_id)
  const [verCorregidas, setVerCorregidas] = useState(false)
  const historia = useHistoria(mascotaId, verCorregidas)
  const [nueva, setNueva] = useState(false)
  const completa = puede(usuario, 'clinico')

  return (
    <div className="pila">
      <div className="detalle-cabeza">
        <Link to="/clinica" className="btn btn-plano" aria-label="Volver a clínica">
          <Icono nombre="volver" size={16} />
        </Link>
        <h1>Historia de {mascota?.nombre ?? '…'}</h1>
        {familia.data && (
          <Link to={`/familias/${familia.data.id}`} className="distintivo distintivo-info">
            {familia.data.titular_nombre}
          </Link>
        )}
        {puede(usuario, 'medico') && (
          <button className="btn btn-primario" type="button" style={{ marginLeft: 'auto' }} onClick={() => setNueva(true)}>
            <Icono nombre="mas" size={16} /> Nueva consulta
          </button>
        )}
      </div>

      {mascota && (
        <section className="tarjeta">
          <dl className="ficha">
            <div><dt>Especie</dt><dd>{mascota.especie}</dd></div>
            <div><dt>Raza</dt><dd>{mascota.raza ?? '—'}</dd></div>
            <div><dt>Sexo</dt><dd>{mascota.sexo ?? '—'}</dd></div>
            <div><dt>Nacimiento</dt><dd className="numero">{fecha(mascota.fecha_nacimiento)}</dd></div>
            <div><dt>Peso</dt><dd className="numero">{mascota.peso_kg ? `${mascota.peso_kg} kg` : '—'}</dd></div>
            <div><dt>Esterilizada</dt><dd>{mascota.esterilizada === null || mascota.esterilizada === undefined ? '—' : mascota.esterilizada ? 'Sí' : 'No'}</dd></div>
          </dl>
        </section>
      )}

      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Consultas</h3>
          <label className="acciones">
            <input type="checkbox" checked={verCorregidas} onChange={(e) => setVerCorregidas(e.target.checked)} />
            Incluir versiones corregidas
          </label>
        </div>
        {!completa && (
          <p className="aviso" style={{ marginBottom: 'var(--e4)' }}>
            Tu perfil ve el resumen de cada consulta. El detalle clínico lo ven el equipo médico y la administración.
          </p>
        )}
        <Consulta
          consulta={historia}
          cargando="Cargando la historia…"
          error="No fue posible cargar la historia clínica."
          vacio="Esta mascota todavía no tiene consultas registradas."
          estaVacio={(d) => d.length === 0}
        >
          {(entradas) => (
            <ol className="linea-tiempo">
              {entradas.map((e) => (
                <li key={e.id} className={e.estado === 'firmada' ? 'hecho' : ''}>
                  <div className="acciones">
                    <strong className="numero">{fecha(e.fecha)}</strong>
                    <span className="apagado">{e.tipo === 'domiciliaria' ? 'Domiciliaria' : 'Presencial'}</span>
                    <Distintivo dominio="historia" valor={e.estado} />
                    {completa && <Link to={`/clinica/historias/${e.id}`}>Abrir</Link>}
                  </div>
                  <p>{e.motivo}</p>
                  {e.diagnostico && <p className="apagado">Diagnóstico: {e.diagnostico}</p>}
                </li>
              ))}
            </ol>
          )}
        </Consulta>
      </section>

      <NuevaEntradaModal mascotaId={mascotaId} abierto={nueva} onCerrar={() => setNueva(false)} />
    </div>
  )
}

function NuevaEntradaModal({ mascotaId, abierto, onCerrar }: { mascotaId: string; abierto: boolean; onCerrar: () => void }) {
  const navegar = useNavigate()
  const crear = useCrearEntrada()
  const plantillas = usePlantillas()
  const [plantilla, setPlantilla] = useState('')
  const prellenado = plantillas.data?.find((p) => p.codigo === plantilla)?.campos as Record<string, string> | undefined

  function guardar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    const datos: DatosEntrada = { fecha: String(d.get('fecha')) }
    for (const { campo } of CAMPOS_CLINICOS) {
      const v = String(d.get(campo) ?? '').trim()
      if (v) datos[campo] = v
    }
    crear.mutate(
      { ...datos, mascota_id: mascotaId, tipo: String(d.get('tipo')), plantilla_codigo: plantilla || undefined },
      { onSuccess: (entrada) => navegar(`/clinica/historias/${entrada.id}`) },
    )
  }

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          crear.reset()
          onCerrar()
        }
      }}
      titulo="Nueva consulta"
      descripcion="Queda como borrador hasta que la firmes; firmada ya no se edita, se corrige con una nueva versión."
      pie={
        <button className="btn btn-primario" type="submit" form="nueva-entrada" disabled={crear.isPending}>
          Guardar borrador
        </button>
      }
    >
      {/* La plantilla cambia los valores iniciales: el formulario se monta de nuevo con su key. */}
      <form key={plantilla} id="nueva-entrada" className="formulario" onSubmit={guardar}>
        <label className="campo">
          <span>Plantilla</span>
          <select className="input" value={plantilla} onChange={(e) => setPlantilla(e.target.value)}>
            <option value="">Sin plantilla</option>
            {plantillas.data
              ?.filter((p) => p.activa)
              .map((p) => (
                <option key={p.codigo} value={p.codigo}>{p.nombre}</option>
              ))}
          </select>
        </label>
        <label className="campo">
          <span>Modalidad</span>
          <select className="input" name="tipo" defaultValue="domiciliaria">
            <option value="domiciliaria">Domiciliaria</option>
            <option value="presencial">Presencial</option>
          </select>
        </label>
        <label className="campo">
          <span>Fecha</span>
          <input className="input" name="fecha" type="date" max={hoyISO()} defaultValue={hoyISO()} required />
        </label>
        {CAMPOS_CLINICOS.map(({ campo, label }) => (
          <label key={campo} className="campo ancho">
            <span>{label}</span>
            <textarea
              className="input"
              name={campo}
              rows={campo === 'motivo' ? 2 : 3}
              required={campo === 'motivo'}
              defaultValue={prellenado?.[campo] ?? ''}
            />
          </label>
        ))}
        {crear.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(crear.error, 'No fue posible guardar la consulta.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
