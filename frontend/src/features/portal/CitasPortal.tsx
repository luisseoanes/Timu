import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { Pestanas } from '@/components/Pestanas'
import { useNombreTipoServicio } from '@/features/catalogos'
import { mensajeError } from '@/lib/errores'
import { diaISO, fechaCortaConDia, hora } from '@/lib/formato'
import type { ServicioPortalRead } from '@/types'

import { AgendarModal, SelectorCupo } from './Agenda'
import { useCancelarPortal, useMiFamilia, useMiPlan, useMisServicios, useReprogramarPortal } from './api'
import { estadoDeCita, pasadas, puedeCambiar, puedeCancelar } from './citas'
import { motivoSinAgendar } from './plan'

/**
 * R3-POR-02 Las citas de la familia: las próximas con lo que se puede hacer con cada una y las
 * pasadas. Agendar es la acción verde de la vista, solo si el plan lo permite.
 */
export function PortalCitas() {
  const plan = useMiPlan()
  const sinAgendar = motivoSinAgendar(plan.data)
  const [agendando, setAgendando] = useState(false)

  return (
    <div className="pila">
      <header className="portal-cabecera">
        <h1>Tus citas</h1>
        {sinAgendar === null && (
          <button className="btn btn-primario" type="button" onClick={() => setAgendando(true)}>
            <Icono nombre="calendario" size={18} /> Agendar una visita
          </button>
        )}
      </header>
      {plan.data !== undefined && sinAgendar !== null && (
        <p className="portal-aviso">
          {sinAgendar} {(plan.data?.estado === 'congelada' || plan.data?.estado === 'en_mora') && <Link to="/portal/pagos">Ir a tus pagos</Link>}
        </p>
      )}
      <div className="portal-panel">
        <Pestanas
          etiqueta="Tus citas"
          pestanas={[
            { valor: 'proximas', titulo: 'Próximas', contenido: <Proximas /> },
            { valor: 'pasadas', titulo: 'Pasadas', contenido: <Pasadas /> },
          ]}
        />
      </div>
      <AgendarModal abierto={agendando} onCerrar={() => setAgendando(false)} />
    </div>
  )
}

function Proximas() {
  const citas = useMisServicios()
  const [reprogramando, setReprogramando] = useState<ServicioPortalRead | null>(null)
  const [cancelando, setCancelando] = useState<ServicioPortalRead | null>(null)
  return (
    <>
      <Consulta
        consulta={citas}
        cargando="Cargando tus citas…"
        error="No pudimos cargar tus citas."
        vacio="No tienes citas próximas."
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <ul className="citas" aria-label="Citas próximas">
            {d.map((s) => (
              <Cita key={s.id} cita={s}>
                {(puedeCambiar(s) || puedeCancelar(s)) && (
                  <div className="cita-acciones">
                    {puedeCambiar(s) && (
                      <button className="btn btn-secundario" type="button" onClick={() => setReprogramando(s)}>
                        Cambiar la fecha
                      </button>
                    )}
                    {puedeCancelar(s) && (
                      <button className="btn btn-plano btn-plano-peligro" type="button" onClick={() => setCancelando(s)}>
                        Cancelar
                      </button>
                    )}
                  </div>
                )}
              </Cita>
            ))}
          </ul>
        )}
      </Consulta>
      {reprogramando && <ReprogramarModal cita={reprogramando} onCerrar={() => setReprogramando(null)} />}
      <CancelarCitaModal cita={cancelando} onCerrar={() => setCancelando(null)} />
    </>
  )
}

function Pasadas() {
  const todas = useMisServicios(true)
  return (
    <Consulta
      consulta={todas}
      cargando="Cargando tus citas…"
      error="No pudimos cargar tus citas."
      vacio="Aún no tienes citas pasadas."
      estaVacio={(d) => pasadas(d).length === 0}
    >
      {(d) => (
        <ul className="citas" aria-label="Citas pasadas">
          {pasadas(d).map((s) => (
            <Cita key={s.id} cita={s} />
          ))}
        </ul>
      )}
    </Consulta>
  )
}

/** Una cita: cuándo, qué y para quién, y su estado dicho a la familia. */
function Cita({ cita, children }: { cita: ServicioPortalRead; children?: React.ReactNode }) {
  const nombreTipo = useNombreTipoServicio()
  const familia = useMiFamilia()
  const peludo = familia.data?.mascotas?.find((m) => m.id === cita.mascota_id)?.nombre
  const estado = estadoDeCita(cita.estado)
  return (
    <li className="cita">
      <p className="cita-cuando">
        {cita.programado_para ? (
          <>
            <strong>{fechaCortaConDia(diaISO(cita.programado_para))}</strong>
            <span className="numero">{hora(cita.programado_para)}</span>
          </>
        ) : (
          <strong>Por confirmar</strong>
        )}
      </p>
      <div className="cita-que">
        <h3>
          {nombreTipo(cita.tipo_codigo)}
          {peludo && <span className="apagado"> · {peludo}</span>}
        </h3>
        <Insignia tono={estado.tono}>{estado.label}</Insignia>
        {estado.explicacion && <p>{estado.explicacion}</p>}
      </div>
      {children}
    </li>
  )
}

function ReprogramarModal({ cita, onCerrar }: { cita: ServicioPortalRead; onCerrar: () => void }) {
  const reprogramar = useReprogramarPortal()
  const [inicio, setInicio] = useState('')
  return (
    <Modal
      abierto
      onCambio={(v) => !v && onCerrar()}
      titulo="Cambiar la fecha"
      descripcion="Elige otro día y otra hora. Los cambios se hacen con unas horas de anticipación."
      pie={
        <button className="btn btn-primario" type="submit" form="reprogramar-portal" disabled={!inicio || reprogramar.isPending}>
          Cambiar la fecha
        </button>
      }
    >
      <form
        id="reprogramar-portal"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const motivo = String(new FormData(e.currentTarget).get('motivo')).trim()
          reprogramar.mutate({ id: cita.id, inicio, motivo }, { onSuccess: onCerrar })
        }}
      >
        <SelectorCupo tipo={cita.tipo_codigo} valor={inicio} onCambio={setInicio} />
        <label className="campo ancho">
          <span>¿Por qué la cambias?</span>
          <input className="input" name="motivo" required minLength={3} />
        </label>
        {reprogramar.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(reprogramar.error, 'No pudimos cambiar la fecha.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

function CancelarCitaModal({ cita, onCerrar }: { cita: ServicioPortalRead | null; onCerrar: () => void }) {
  const cancelar = useCancelarPortal()
  return (
    <Modal
      abierto={cita !== null}
      onCambio={(v) => {
        if (!v) {
          cancelar.reset()
          onCerrar()
        }
      }}
      titulo="Cancelar la cita"
      descripcion="La cita se cancela y su horario queda libre. Si la necesitas otra vez, agéndala de nuevo."
      pie={
        <button className="btn btn-peligro" type="submit" form="cancelar-portal" disabled={cancelar.isPending}>
          Cancelar la cita
        </button>
      }
    >
      <form
        id="cancelar-portal"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const motivo = String(new FormData(e.currentTarget).get('motivo')).trim()
          if (cita) cancelar.mutate({ id: cita.id, motivo }, { onSuccess: onCerrar })
        }}
      >
        <label className="campo ancho">
          <span>¿Por qué la cancelas?</span>
          <input className="input" name="motivo" required minLength={3} />
        </label>
        {cancelar.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(cancelar.error, 'No pudimos cancelar la cita.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
