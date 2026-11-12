import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { useAuth } from '@/features/auth'
import { useEspecies } from '@/features/catalogos'
import { useFamilia, useMascotas } from '@/features/familias'
import { edad, fecha, peso } from '@/lib/formato'
import { puede } from '@/lib/permisos'

import { useHistoria, type EntradaHistoria } from './api'
import { anteriorFirmada } from './consulta'
import { ConsultaGuiada } from './ConsultaGuiada'
import { LecturaConsulta } from './LecturaConsulta'

/**
 * La historia clínica de una mascota en la plantilla de listado con ficha: la mascota y sus
 * consultas a la izquierda, la abierta a la derecha. En el celular se ve una u otra.
 *
 * Qué se abre: una consulta concreta (`entrada`), una nueva (`nueva`) o la de una visita
 * (`servicioId`), que continúa su borrador, enseña la ya firmada o empieza una.
 */
export function HistoriaClinica({
  mascotaId,
  entrada,
  nueva = false,
  servicioId,
}: {
  mascotaId: string
  entrada?: EntradaHistoria
  nueva?: boolean
  servicioId?: string
}) {
  const { usuario } = useAuth()
  const navegar = useNavigate()
  const { state } = useLocation() as { state: { estacion?: number } | null }
  const especies = useEspecies()
  const mascota = useMascotas([mascotaId]).get(mascotaId)
  const familia = useFamilia(mascota?.familia_id)
  const [verCorregidas, setVerCorregidas] = useState(false)
  const historia = useHistoria(mascotaId, verCorregidas)
  const completa = puede(usuario, 'clinico')
  const esMedico = puede(usuario, 'medico')
  const volver = `/clinica/mascotas/${mascotaId}`
  const entradas = historia.data ?? []
  const deLaVisita = servicioId ? entradas.find((e) => e.servicio_id === servicioId && e.estado !== 'corregida') : undefined
  const abierta = entrada ?? deLaVisita
  const abriendo = Boolean(entrada || nueva || servicioId)
  const especie = mascota && (especies.data?.find((e) => e.codigo === mascota.especie)?.nombre ?? mascota.especie)
  const anios = edad(mascota?.fecha_nacimiento)

  // Quién se atiende, para la consulta abierta: en el celular, la historia de la izquierda no está.
  const identidad = mascota && (
    <p className="consulta-identidad">
      <strong>
        {mascota.nombre}
        {familia.data && ` · ${familia.data.titular_nombre}`}
      </strong>
      <span className="numero">{[especie?.toLowerCase(), mascota.peso_kg != null && peso(mascota.peso_kg)].filter(Boolean).join(' · ')}</span>
    </p>
  )

  function contenido() {
    if (!abriendo) {
      return (
        <section className="ficha-abierta ficha-vacia" aria-label="Consulta abierta">
          <p>Elige una consulta para leerla{esMedico ? ', o empieza una nueva' : ''}.</p>
        </section>
      )
    }
    // La consulta de una visita se resuelve con la historia: hasta tenerla, no se sabe si ya existe.
    if (!mascota || (servicioId && !entrada && historia.isPending)) {
      return (
        <section className="ficha-abierta" aria-label="Consulta abierta">
          <div className="esqueleto" role="status">
            <span className="sr-only">Abriendo la consulta…</span>
            <span className="esqueleto-linea" aria-hidden="true" />
            <span className="esqueleto-linea" aria-hidden="true" />
          </div>
        </section>
      )
    }
    const propia = abierta?.estado === 'borrador' && esMedico && abierta.profesional_id === usuario?.id
    if (abierta && !propia) return <LecturaConsulta key={abierta.id} entrada={abierta} volver={volver} identidad={identidad} />
    if (!esMedico) {
      return (
        <section className="ficha-abierta ficha-vacia" aria-label="Consulta abierta">
          <p>Las consultas las escribe el equipo médico.</p>
        </section>
      )
    }
    return (
      <ConsultaGuiada
        // La de una visita conserva su estado al nacer su borrador; la nueva cambia de dirección.
        key={servicioId ? `visita-${servicioId}` : (abierta?.id ?? 'nueva')}
        mascota={mascota}
        entrada={abierta}
        servicioId={abierta ? (abierta.servicio_id ?? undefined) : servicioId}
        anterior={anteriorFirmada(entradas, abierta?.id)}
        volver={volver}
        identidad={identidad}
        estacion={state?.estacion}
        onCreada={servicioId ? undefined : (id, estacion) => navegar(`/clinica/historias/${id}`, { replace: true, state: { estacion } })}
        onFirmada={(firmada) => navegar(`/clinica/historias/${firmada.id}`, { state: { recienFirmada: true } })}
      />
    )
  }

  return (
    <div className="con-ficha" data-abierta={abriendo ? 'true' : undefined}>
      <section className="listado" aria-labelledby="historia-titulo">
        <header className="historia-mascota">
          <h2 id="historia-titulo">{mascota?.nombre ?? '…'}</h2>
          <p className="historia-mascota-datos">
            {familia.data && <Link to={`/familias/${familia.data.id}`}>{familia.data.titular_nombre}</Link>}
            {especie && (
              <span>
                {especie.toLowerCase()}
                {mascota?.sexo ? ` ${mascota.sexo}` : ''}
                {mascota?.raza ? `, ${mascota.raza.toLowerCase()}` : ''}
              </span>
            )}
          </p>
          {mascota && (
            <dl className="historia-mascota-ficha">
              <div>
                <dt>Edad</dt>
                <dd className="numero">{anios ?? '—'}</dd>
              </div>
              <div>
                <dt>Peso</dt>
                <dd className="numero">{peso(mascota.peso_kg)}</dd>
              </div>
              <div>
                <dt>Esterilizado</dt>
                <dd>{mascota.esterilizada === null || mascota.esterilizada === undefined ? '—' : mascota.esterilizada ? 'Sí' : 'No'}</dd>
              </div>
            </dl>
          )}
        </header>

        <div className="listado-cabeza">
          <h3>Consultas</h3>
          {esMedico && (
            // Una sola acción verde por vista: con una consulta abierta, la principal es la suya.
            <Link className={`btn ${abriendo ? 'btn-suave' : 'btn-primario'}`} to={`${volver}?nueva=1`}>
              <Icono nombre="mas" size={16} />
              Nueva consulta
            </Link>
          )}
        </div>
        <label className="acciones historia-corregidas">
          <input type="checkbox" checked={verCorregidas} onChange={(ev) => setVerCorregidas(ev.target.checked)} />
          Incluir versiones corregidas
        </label>
        {!completa && <p className="aviso">Tu perfil ve el resumen de cada consulta. El detalle clínico lo ven el equipo médico y la administración.</p>}
        <Consulta
          consulta={historia}
          cargando="Cargando la historia…"
          error="No fue posible cargar la historia clínica."
          vacio="Esta mascota todavía no tiene consultas registradas."
          estaVacio={(d) => d.length === 0}
        >
          {(lista) => (
            <ul className="listado-filas">
              {lista.map((e) => (
                <li key={e.id} className="listado-fila" data-seleccionada={e.id === abierta?.id}>
                  <span className="listado-fila-cabeza">
                    {completa ? (
                      // El enlace es la fecha; ::after lo extiende a toda la fila.
                      <Link className="listado-fila-enlace numero" to={`/clinica/historias/${e.id}`} aria-current={e.id === abierta?.id ? 'page' : undefined}>
                        {fecha(e.fecha)}
                      </Link>
                    ) : (
                      <strong className="numero">{fecha(e.fecha)}</strong>
                    )}
                    <Distintivo dominio="historia" valor={e.estado} />
                  </span>
                  <span className="historia-fila-motivo">
                    {e.motivo}
                    <span className="apagado"> · {e.tipo === 'domiciliaria' ? 'domiciliaria' : 'presencial'}</span>
                  </span>
                  {e.diagnostico && <span className="historia-fila-diagnostico">Diagnóstico: {e.diagnostico}</span>}
                </li>
              ))}
            </ul>
          )}
        </Consulta>
      </section>

      {contenido()}
    </div>
  )
}
