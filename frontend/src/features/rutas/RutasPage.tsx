import { Fragment, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo, Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { useAuth, useEquipo } from '@/features/auth'
import { useCiudades, useNombreTipoServicio } from '@/features/catalogos'
import { fechaCortaConDia, fechaLarga, hora, hoyISO } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { RutaRead } from '@/types'

import { usePorRutear, useRutas } from './api'
import { LineaRuta, LineaRutaMini } from './LineaRuta'
import { PlanearModal } from './PlanearModal'
import { RutaAbierta } from './RutaAbierta'
import { donde, enRuta, paradaActual, resumen } from './ruta'

/**
 * Rutas domiciliarias (6.7). Quien solo sale a campo abre en su ruta del día; quien coordina
 * ve todas las del día, las planea y las ajusta. El día, la ciudad y la ruta abierta viven en
 * la URL: volver atrás o recargar no los pierde.
 */
export function RutasPage() {
  const { usuario } = useAuth()
  const [params, setParams] = useSearchParams()
  const dia = /^\d{4}-\d{2}-\d{2}$/.test(params.get('dia') ?? '') ? params.get('dia')! : hoyISO()

  function cambiar(cambios: Record<string, string>) {
    const nuevos = new URLSearchParams(params)
    for (const [clave, valor] of Object.entries(cambios)) {
      if (valor) nuevos.set(clave, valor)
      else nuevos.delete(clave)
    }
    // La ruta abierta es de un día y una ciudad: al cambiarlos deja de estar a la vista.
    if (!('ruta' in cambios)) nuevos.delete('ruta')
    setParams(nuevos, { replace: true })
  }

  const elegirDia = (
    <SelectorDia dia={dia} onCambio={(valor) => cambiar({ dia: valor === hoyISO() ? '' : valor })} />
  )
  // Sin saber quién es no se sabe qué vista le toca: la de coordinación pediría todas las rutas.
  if (!usuario) return null
  if (puede(usuario, 'campo') && !puede(usuario, 'planearRutas')) return <MiRuta dia={dia} elegirDia={elegirDia} />
  return <RutasDelDia dia={dia} elegirDia={elegirDia} params={params} cambiar={cambiar} />
}

/**
 * El día de las rutas, compacto: dice «Hoy» o «sáb 14 nov». El campo de fecha del navegador va
 * encima, transparente: al tocarlo el celular abre su calendario, y el teclado y los lectores de
 * pantalla lo usan con su etiqueta. En escritorio el clic no abre el calendario solo, así que se
 * pide con `showPicker`.
 */
function SelectorDia({ dia, onCambio }: { dia: string; onCambio: (dia: string) => void }) {
  const hoy = dia === hoyISO()
  return (
    <div className="rutas-dia">
      {!hoy && (
        <button className="btn btn-plano" type="button" onClick={() => onCambio(hoyISO())}>
          Volver a hoy
        </button>
      )}
      <label className="btn btn-secundario rutas-dia-boton">
        <Icono nombre="calendario" size={16} />
        <span aria-hidden="true">{hoy ? 'Hoy' : fechaCortaConDia(dia)}</span>
        <input
          type="date"
          value={dia}
          aria-label="Día de las rutas"
          onClick={(e) => {
            try {
              e.currentTarget.showPicker?.()
            } catch {
              // Sin gesto válido o sin soporte: el campo sigue enfocado y se edita con el teclado.
            }
          }}
          onChange={(e) => onCambio(e.target.value || hoyISO())}
        />
      </label>
    </div>
  )
}

/** «hoy» o «el jueves, 12 de noviembre»: el día dicho como se habla. */
function nombrarDia(dia: string): string {
  return dia === hoyISO() ? 'hoy' : `el ${fechaLarga(dia)}`
}

/** La última llegada estimada de lo que falta: hasta cuándo va la jornada. */
function ultimaLlegada(ruta: RutaRead): string | null {
  const ultima = enRuta(ruta)
    .filter((p) => p.estado === 'pendiente' && p.llegada_estimada)
    .at(-1)
  return ultima ? hora(ultima.llegada_estimada) : null
}

/** La ruta de quien sale a campo: su línea del día, sin buscarla entre las de los demás. */
function MiRuta({ dia, elegirDia }: { dia: string; elegirDia: React.ReactNode }) {
  const { usuario } = useAuth()
  const rutas = useRutas(dia, { responsable: usuario?.id })
  const mias = rutas.data ?? []
  const unica = mias.length === 1 ? mias[0] : null
  const hasta = unica && ultimaLlegada(unica)

  return (
    <div className="pila rutas-propia">
      <div className="rutas-barra">
        {/* Sin la pastilla de estado de la ruta: la línea ya lo dice (iniciar, en sitio, todas
            hechas), y en el celular cada fila de más aleja las paradas del pulgar. */}
        <p className="rutas-resumen numero">
          {[...(mias.length > 0 ? resumen(mias).split(' · ') : []), ...(hasta ? [`hasta las ${hasta}`] : [])].map(
            (pieza, i) => (
              // Cada pieza se parte por separado; el punto va aparte, con el mismo aire a cada lado.
              // El espacio entre piezas no ocupa sitio en el flex, pero separa el texto que leen
              // los lectores de pantalla.
              <Fragment key={pieza}>
                {i > 0 && (
                  <>
                    {' '}
                    <span className="rutas-separador" aria-hidden="true">
                      ·
                    </span>{' '}
                  </>
                )}
                <span className={pieza.startsWith('hasta') ? 'apagado' : undefined}>{pieza}</span>
              </Fragment>
            ),
          )}
        </p>
        {elegirDia}
      </div>
      <Consulta consulta={rutas} cargando="Cargando tu ruta…" error="No fue posible cargar tu ruta.">
        {(datos) =>
          datos.length === 0 ? (
            <section className="ficha-abierta ficha-vacia" aria-label="Tu ruta">
              <p>
                No tienes ruta para {nombrarDia(dia)}. Operaciones la planea con los domicilios agendados; si esperabas
                una, avísale.
              </p>
            </section>
          ) : (
            datos.map((r, i) => (
              <section key={r.id} className="ficha-abierta" aria-labelledby={`ruta-${r.id}`}>
                <h2 id={`ruta-${r.id}`} className={unica ? 'sr-only' : 'ruta-titulo'}>
                  {unica ? `Tu ruta de ${nombrarDia(dia)}` : `Ruta ${i + 1} · ${resumen([r])}`}
                </h2>
                {!unica && <Distintivo dominio="ruta" valor={r.estado} />}
                <LineaRuta ruta={r} />
              </section>
            ))
          )
        }
      </Consulta>
    </div>
  )
}

/** Las rutas del día para quien coordina: el listado, lo que falta por rutear y la ruta abierta. */
function RutasDelDia({
  dia,
  elegirDia,
  params,
  cambiar,
}: {
  dia: string
  elegirDia: React.ReactNode
  params: URLSearchParams
  cambiar: (cambios: Record<string, string>) => void
}) {
  const { usuario } = useAuth()
  const ciudades = useCiudades()
  const equipo = useEquipo()
  const nombreTipo = useNombreTipoServicio()
  const [planeando, setPlaneando] = useState(false)
  const ciudad = params.get('ciudad') ?? ''
  const rutas = useRutas(dia, { ciudad })
  const porRutear = usePorRutear(dia, ciudad)
  const abierta = rutas.data?.find((r) => r.id === params.get('ruta'))
  const planea = puede(usuario, 'planearRutas')
  // Una sola acción verde por vista: si la ruta abierta es la propia y tiene parada que atender,
  // la principal es la de esa parada; si no, planear.
  const atiende = abierta?.responsable_id === usuario?.id && Boolean(abierta && paradaActual(abierta))
  const responsable = (r: RutaRead) => equipo.data?.find((m) => m.id === r.responsable_id)?.nombre ?? 'Sin responsable'
  const sinRuta = porRutear.data ?? []

  /** La misma vista con otra ruta abierta, o con ninguna. */
  function enlace(ruta?: string) {
    const nuevos = new URLSearchParams(params)
    if (ruta) nuevos.set('ruta', ruta)
    else nuevos.delete('ruta')
    return `/rutas${nuevos.toString() ? `?${nuevos}` : ''}`
  }

  return (
    <div className="con-ficha" data-abierta={abierta ? 'true' : undefined}>
      <section className="listado" aria-labelledby="rutas-titulo">
        <div className="listado-cabeza">
          <h2 id="rutas-titulo">
            Rutas del día <span className="apagado numero">{rutas.data?.length ?? 0}</span>
          </h2>
          {planea && (
            <button className={`btn ${atiende ? 'btn-suave' : 'btn-primario'}`} type="button" onClick={() => setPlaneando(true)}>
              <Icono nombre="rutas" size={16} />
              Planear rutas
            </button>
          )}
        </div>

        <div className="filtros">
          {elegirDia}
          <select className="input" value={ciudad} onChange={(e) => cambiar({ ciudad: e.target.value })} aria-label="Filtrar por ciudad">
            <option value="">Todas las ciudades</option>
            {ciudades.data?.map((c) => (
              <option key={c.codigo} value={c.nombre}>
                {c.nombre}
              </option>
            ))}
          </select>
        </div>

        <Consulta
          consulta={rutas}
          cargando="Cargando rutas…"
          error="No fue posible cargar las rutas."
          vacio={`No hay rutas para ${nombrarDia(dia)}${ciudad ? ` en ${ciudad}` : ''}. ${
            planea
              ? 'Créalas con «Planear rutas»: el optimizador reparte los domicilios del día.'
              : 'Operaciones las planea con los domicilios agendados.'
          }`}
          estaVacio={(d) => d.length === 0}
        >
          {(datos) => (
            <ul className="listado-filas">
              {datos.map((r) => (
                <li key={r.id} className="listado-fila" data-seleccionada={r.id === abierta?.id}>
                  <span className="listado-fila-cabeza">
                    {/* El enlace es solo el nombre; ::after lo extiende a toda la fila. */}
                    <Link className="listado-fila-enlace" to={enlace(r.id)} aria-current={r.id === abierta?.id ? 'page' : undefined}>
                      {responsable(r)}
                    </Link>
                    <Distintivo dominio="ruta" valor={r.estado} />
                  </span>
                  <span className="ruta-fila-datos numero">
                    {resumen([r])} · {r.ciudad}
                    {r.responsable_id === usuario?.id && ' · tu ruta'}
                  </span>
                  <LineaRutaMini ruta={r} />
                </li>
              ))}
            </ul>
          )}
        </Consulta>

        <section className="bloque" aria-labelledby="por-rutear-titulo">
          <h3 id="por-rutear-titulo" className="ruta-bloque-titulo">
            Por rutear
            {sinRuta.length > 0 && <Insignia tono="alerta">{sinRuta.length}</Insignia>}
          </h3>
          <Consulta
            consulta={porRutear}
            cargando="Buscando domicilios sin ruta…"
            error="No fue posible consultar lo que falta por rutear."
            vacio="Todos los domicilios agendados del día tienen ruta."
            estaVacio={(d) => d.length === 0}
          >
            {(datos) => (
              <ul className="listado-filas">
                {datos.map((s) => (
                  <li key={s.id} className="listado-fila">
                    <span className="listado-fila-cabeza">
                      <Link className="listado-fila-enlace" to={`/servicios/${s.id}`}>
                        {s.familia.titular_nombre}
                        {s.mascota && ` · ${s.mascota.nombre}`}
                      </Link>
                      <span className="apagado numero">{hora(s.programado_para)}</span>
                    </span>
                    <span className="ruta-fila-datos">
                      {nombreTipo(s.tipo_codigo)} · {donde(s.familia)}
                      {!ciudad && `, ${s.ciudad}`}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Consulta>
        </section>
      </section>

      {abierta ? (
        // La clave reinicia la ficha al cambiar de ruta: lo desplegado vuelve a plegarse.
        <RutaAbierta key={abierta.id} ruta={abierta} responsable={responsable(abierta)} volver={enlace()} porRutear={sinRuta} />
      ) : (
        <section className="ficha-abierta ficha-vacia" aria-label="Ruta abierta">
          <p>Elige una ruta para ver sus paradas en orden: cuáles van hechas, cuál sigue y a dónde.</p>
        </section>
      )}

      {planeando && (
        <PlanearModal dia={dia} ciudadSugerida={ciudad || sinRuta[0]?.ciudad || ''} onCerrar={() => setPlaneando(false)} />
      )}
    </div>
  )
}
