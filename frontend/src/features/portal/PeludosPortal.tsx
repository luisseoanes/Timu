import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Insignia } from '@/components/Distintivo'
import { FotoEditable } from '@/components/FotoEditable'
import { Icono } from '@/components/Icono'
import { Pestanas } from '@/components/Pestanas'
import { useEspecies, useNombreTipoServicio } from '@/features/catalogos'
import { mensajeError } from '@/lib/errores'
import { edad, fecha, fechaCorta, hoyISO, moneda, peso } from '@/lib/formato'
import type { MascotaRead } from '@/types'

import { AgendarModal } from './Agenda'
import {
  useCarnetPdfPortal,
  useCarnetPortal,
  useFotoMascotaPortal,
  useHistoriaPortal,
  useMiCuenta,
  useMiFamilia,
  useMiLinea,
  useMiPlan,
  useMisServicios,
  type BeneficioPortal,
} from './api'
import { AccesoPeludo } from './InicioPortal'
import { delPeludo, recorrido, vencidasDe } from './linea'
import { LineaPortal } from './LineaPortal'
import { cupo, finDeLinea, motivoSinAgendar } from './plan'

// --- Tus peludos ------------------------------------------------------------------------------

export function PortalMascotas() {
  const familia = useMiFamilia()
  const especies = useEspecies()
  const detalle = (m: MascotaRead) => {
    const especie = especies.data?.find((e) => e.codigo === m.especie)?.nombre ?? m.especie
    return [m.raza ? `${especie} · ${m.raza}` : especie, edad(m.fecha_nacimiento)].filter(Boolean).join(' · ')
  }
  const linea = useMiLinea()
  return (
    <div className="pila">
      <header className="portal-cabecera">
        <h1>Tus peludos</h1>
        <Link to="/portal/mascotas/nueva" className="btn btn-primario">
          <Icono nombre="mas" size={16} /> Agregar un peludo
        </Link>
      </header>
      <Consulta
        consulta={familia}
        cargando="Cargando tus peludos…"
        error="No pudimos cargar tus peludos."
        vacio="Aún no tienes peludos en tu plan. Agrega el primero."
        estaVacio={(f) => !(f.mascotas ?? []).some((m) => m.activa)}
      >
        {(f) => (
          <ul className="portal-peludos-lista portal-peludos-lista-completa">
            {(f.mascotas ?? [])
              .filter((m) => m.activa)
              .map((m) => (
                <li key={m.id}>
                  <AccesoPeludo
                    mascota={m}
                    detalle={detalle(m)}
                    vencidos={linea.data ? vencidasDe(linea.data.estaciones, m.id) : null}
                  />
                </li>
              ))}
          </ul>
        )}
      </Consulta>
    </div>
  )
}

// --- La ficha de un peludo --------------------------------------------------------------------

/**
 * La ficha de un peludo: quién es, su propia línea (sus preventivos y sus visitas) abierta en
 * «hoy», y su carnet, su historia y lo que le cubre el plan.
 */
export function PortalMascota() {
  const { mascotaId = '' } = useParams()
  const familia = useMiFamilia()
  const plan = useMiPlan()
  const cuenta = useMiCuenta()
  const linea = useMiLinea()
  const servicios = useMisServicios()
  const [agendando, setAgendando] = useState(false)
  const mascota = familia.data?.mascotas?.find((m) => m.id === mascotaId)
  const delPlan = plan.data?.mascotas.find((m) => m.mascota_id === mascotaId)
  const color = delPlan?.color ?? null
  const hoy = hoyISO()
  const sinAgendar = motivoSinAgendar(plan.data)

  return (
    <div className="pila">
      <section className="portal-panel portal-peludo-identidad" aria-label="Quién es">
        <header className="portal-peludo-cabeza">
          <Link to="/portal/mascotas" className="btn btn-plano btn-icono" aria-label="Volver a tus peludos">
            <Icono nombre="volver" size={18} />
          </Link>
          <div>
            <h1>{mascota?.nombre ?? '…'}</h1>
            {mascota && <DatosPeludo mascota={mascota} plan={delPlan?.plan} color={color} />}
          </div>
        </header>
        {mascota && <FotoPortal mascota={mascota} />}
      </section>

      <Consulta consulta={familia} cargando="Cargando…" error="No pudimos cargar a tu peludo.">
        {() =>
          mascota ? (
            <>
              <section className="portal-linea" aria-labelledby="peludo-linea-titulo">
                <h2 id="peludo-linea-titulo" className="sr-only">
                  Lo que le toca a {mascota.nombre}
                </h2>
                <Consulta
                  consulta={linea}
                  cargando="Cargando sus vacunas, desparasitaciones y visitas…"
                  error="No pudimos cargar sus vacunas, desparasitaciones y visitas."
                >
                  {(l) => (
                    <LineaPortal
                      elementos={recorrido(delPeludo(l.estaciones, mascota.id), hoy)}
                      hoy={hoy}
                      color={color}
                      cuenta={cuenta.data ?? null}
                      servicios={servicios.data ?? []}
                      sinAgendar={sinAgendar}
                      onAgendar={() => setAgendando(true)}
                      etiqueta={`La línea de ${mascota.nombre}`}
                      fin={finDeLinea(plan.data, mascota.nombre)}
                      dePeludo
                    />
                  )}
                </Consulta>
              </section>
              <div className="portal-panel">
              <Pestanas
                etiqueta={`Secciones de ${mascota.nombre}`}
                pestanas={[
                  { valor: 'carnet', titulo: 'Carnet', contenido: <CarnetPortal mascotaId={mascota.id} /> },
                  { valor: 'historia', titulo: 'Historia clínica', contenido: <HistoriaPortal mascotaId={mascota.id} /> },
                  {
                    valor: 'plan',
                    titulo: 'Su plan',
                    contenido: <PlanPeludo nombre={mascota.nombre} plan={delPlan} />,
                  },
                ]}
              />
              </div>
              <AgendarModal abierto={agendando} onCerrar={() => setAgendando(false)} mascotaId={mascota.id} />
            </>
          ) : (
            <p className="apagado">No encontramos a ese peludo entre los tuyos.</p>
          )
        }
      </Consulta>
    </div>
  )
}

function DatosPeludo({ mascota, plan, color }: { mascota: MascotaRead; plan?: string; color: string | null }) {
  const especies = useEspecies()
  const especie = especies.data?.find((e) => e.codigo === mascota.especie)?.nombre ?? mascota.especie
  const datos = [mascota.raza ? `${especie} · ${mascota.raza}` : especie, edad(mascota.fecha_nacimiento), mascota.peso_kg ? peso(mascota.peso_kg) : null]
  return (
    <p className="portal-peludo-datos">
      <span>{datos.filter(Boolean).join(' · ')}</span>
      {plan && (
        <span className="portal-plan-marca">
          <span className="marcador-plan" data-color={color ?? undefined} aria-hidden="true" />
          {plan}
        </span>
      )}
    </p>
  )
}

function FotoPortal({ mascota }: { mascota: MascotaRead }) {
  const { subir, quitar } = useFotoMascotaPortal(mascota.id)
  const fallo = subir.error ?? quitar.error
  return (
    <FotoEditable
      url={mascota.foto_url}
      alt={`Foto de ${mascota.nombre}`}
      marcador={<Icono nombre="huella" size={24} />}
      editable={mascota.activa}
      ocupada={subir.isPending || quitar.isPending}
      error={fallo ? mensajeError(fallo, 'No pudimos guardar la foto.') : null}
      onSubir={(foto) => {
        quitar.reset()
        subir.mutate(foto)
      }}
      onQuitar={() => {
        subir.reset()
        quitar.mutate()
      }}
    />
  )
}

function CarnetPortal({ mascotaId }: { mascotaId: string }) {
  const carnet = useCarnetPortal(mascotaId)
  const pdf = useCarnetPdfPortal()
  return (
    <section className="bloque" aria-labelledby="carnet-titulo">
      <div className="tarjeta-cabeza">
        <h3 id="carnet-titulo">Carnet de vacunación</h3>
        <button className="btn btn-secundario" type="button" disabled={pdf.isPending} onClick={() => pdf.mutate(mascotaId)}>
          <Icono nombre="descargar" size={16} /> {pdf.isPending ? 'Generando…' : 'Descargar PDF'}
        </button>
      </div>
      {pdf.isSuccess && (
        <p className="aviso-ok" role="status">
          Listo: <a href={pdf.data.url} target="_blank" rel="noreferrer">abrir el carnet</a>. Código de verificación{' '}
          <strong className="numero">{pdf.data.codigo}</strong>.
        </p>
      )}
      {pdf.isError && (
        <p className="error" role="alert">
          {mensajeError(pdf.error, 'No pudimos generar el PDF.')}
        </p>
      )}
      <Consulta
        consulta={carnet}
        cargando="Cargando el carnet…"
        error="No pudimos cargar el carnet."
        vacio="Aún no tiene vacunas ni desparasitaciones en su calendario."
        estaVacio={(c) => c.aplicados.length + c.vencidos.length + c.proximos.length === 0}
      >
        {(c) => (
          <ul className="carnet-lista">
            {c.vencidos.map((v) => (
              <li key={v.id}>
                <span>
                  <strong>{v.nombre}</strong>
                  <span className="apagado">
                    Dosis {v.dosis} · tocaba el {fechaCorta(v.fecha_programada)}
                  </span>
                </span>
                <Insignia tono="peligro">Vencida</Insignia>
              </li>
            ))}
            {c.proximos.map((p) => (
              <li key={p.id}>
                <span>
                  <strong>{p.nombre}</strong>
                  <span className="apagado">
                    Dosis {p.dosis} · el {fecha(p.fecha_programada)}
                  </span>
                </span>
                <Insignia tono="info">Programada</Insignia>
              </li>
            ))}
            {c.aplicados.map((a) => (
              <li key={a.id}>
                <span>
                  <strong>{a.nombre}</strong>
                  <span className="apagado">
                    Dosis {a.dosis} · aplicada el {fecha(a.fecha_aplicacion)}
                    {a.aplicado_por ? ` por ${a.aplicado_por}` : ''}
                    {a.peso_kg ? ` · pesaba ${peso(a.peso_kg)}` : ''}
                  </span>
                </span>
                <Insignia tono="ok">Aplicada</Insignia>
              </li>
            ))}
          </ul>
        )}
      </Consulta>
    </section>
  )
}

function HistoriaPortal({ mascotaId }: { mascotaId: string }) {
  const historia = useHistoriaPortal(mascotaId)
  return (
    <section className="bloque" aria-label="Historia clínica">
      <Consulta
        consulta={historia}
        cargando="Cargando la historia…"
        error="No pudimos cargar la historia."
        vacio="Aún no tiene consultas registradas."
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <ol className="historial">
            {d.map((e) => (
              <li key={e.id}>
                <span className="historial-fecha numero">{fecha(e.fecha)}</span>
                <div>
                  <strong>{e.motivo}</strong>
                  {e.diagnostico && <p>Diagnóstico: {e.diagnostico}</p>}
                  {e.tratamiento && <p className="apagado">Tratamiento: {e.tratamiento}</p>}
                </div>
              </li>
            ))}
          </ol>
        )}
      </Consulta>
    </section>
  )
}

/** Lo que le cubre el plan a este peludo, con su cupo dicho de frente (nada de «ilimitado»). */
function PlanPeludo({
  nombre,
  plan,
}: {
  nombre: string
  plan?: { plan: string; valor_mensual: string; beneficios: BeneficioPortal[] }
}) {
  const nombreTipo = useNombreTipoServicio()
  if (!plan) return <p className="apagado">{nombre} no está en un plan vigente.</p>
  return (
    <section className="bloque" aria-labelledby="plan-peludo-titulo">
      <h3 id="plan-peludo-titulo">
        {plan.plan} · <span className="numero">{moneda(plan.valor_mensual)}</span> al mes
      </h3>
      <ul className="beneficios">
        {plan.beneficios.map((b) => (
          <li key={b.tipo_servicio}>
            <Icono nombre="check" size={14} /> {nombreTipo(b.tipo_servicio)}: {cupo(b)}
            {b.cobertura_pct < 100 && ` · cubre el ${b.cobertura_pct} %`}
          </li>
        ))}
      </ul>
    </section>
  )
}
