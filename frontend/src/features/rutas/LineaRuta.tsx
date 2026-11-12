import { useId, useState } from 'react'
import { Link } from 'react-router-dom'

import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { useEspecies, useNombreTipoServicio } from '@/features/catalogos'
import { edad, hora, peso, rangoHoras } from '@/lib/formato'
import type { MascotaDeParada, ParadaRead, RutaRead } from '@/types'

import { AccionesParada } from './AccionesParada'
import { aQuien, descripcion, donde, enRuta, estadoEstacion, paradaActual, partirDireccion, type EstadoEstacion } from './ruta'

/**
 * La ruta como una línea vertical de metro (contrato de la superficie): las paradas hechas se
 * pliegan arriba, la que toca se abre con a dónde ir, a quién se atiende y su acción, y las que
 * faltan se leen debajo y se abren al activarlas. Una parada omitida ya no es de la ruta: va
 * aparte, con su motivo.
 */
export function LineaRuta({ ruta }: { ruta: RutaRead }) {
  const nombreTipo = useNombreTipoServicio()
  const [desplegado, setDesplegado] = useState(false)
  const idHechas = useId()
  const actual = paradaActual(ruta)
  const paradas = enRuta(ruta)
  const hechas = paradas.filter((p) => p.estado === 'completada')
  const faltan = paradas.filter((p) => p.estado !== 'completada')
  const omitidas = ruta.paradas.filter((p) => p.estado === 'omitida')
  // Con paradas por hacer, las hechas estorban: se pliegan tras una pastilla que las vuelve a
  // mostrar y a plegar, y que no desaparece (el foco se queda en ella). Si ya no falta ninguna,
  // las hechas son la ruta y van a la vista.
  const plegables = hechas.length > 0 && faltan.length > 0

  return (
    <>
      {paradas.length > 0 && (
        <ol className="linea-ruta" aria-label="Paradas de la ruta">
          {plegables && (
            <li className="linea-ruta-tramo">
              <button
                className="linea-tramo-boton"
                type="button"
                aria-expanded={desplegado}
                aria-controls={idHechas}
                onClick={() => setDesplegado(!desplegado)}
              >
                <Icono nombre="check" size={12} />
                {hechas.length} {hechas.length === 1 ? 'hecha' : 'hechas'}
                <span className="linea-tramo-flecha">
                  <Icono nombre="abajo" size={12} />
                </span>
              </button>
            </li>
          )}
          {(!plegables || desplegado) &&
            hechas.map((p, i) => (
              <Estacion key={p.id} id={i === 0 ? idHechas : undefined} ruta={ruta} parada={p} estado="hecha" />
            ))}
          {faltan.map((p) => (
            <Estacion key={p.id} ruta={ruta} parada={p} estado={estadoEstacion(p, actual)} />
          ))}
        </ol>
      )}
      {omitidas.length > 0 && (
        <section className="bloque" aria-labelledby={`omitidas-${ruta.id}`}>
          <h3 id={`omitidas-${ruta.id}`}>Omitidas</h3>
          <ul className="ruta-omitidas">
            {omitidas.map((p) => (
              <li key={p.id}>
                <span>
                  <strong>{aQuien(p)}</strong>
                  <span className="apagado">
                    {nombreTipo(p.tipo_codigo)} · {p.motivo_omision}
                  </span>
                </span>
                <Distintivo dominio="ruta" valor="omitida" />
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  )
}

function Estacion({
  ruta,
  parada,
  estado,
  id: idEstacion,
}: {
  ruta: RutaRead
  parada: ParadaRead
  estado: EstadoEstacion
  /** La primera parada hecha lleva el id que controla la pastilla de las hechas. */
  id?: string
}) {
  const nombreTipo = useNombreTipoServicio()
  const [abierta, setAbierta] = useState(false)
  const id = useId()
  const { familia } = parada
  const franja = rangoHoras(parada.ventana_desde, parada.ventana_hasta)
  const lugar = [familia.complemento, familia.barrio].filter(Boolean).join(' · ')
  const que = (
    <>
      {nombreTipo(parada.tipo_codigo)} · <Direccion texto={donde(familia)} />
    </>
  )

  if (estado === 'hecha') {
    return (
      <li id={idEstacion} className="estacion" data-estado="hecha">
        <span className="estacion-punto" aria-hidden="true" />
        <div className="estacion-cuerpo">
          <p className="estacion-hora">
            <span className="numero">{rangoHoras(parada.llegada_en, parada.salida_en) ?? hora(parada.salida_en)}</span>
            <Distintivo dominio="ruta" valor="completada" />
          </p>
          <p className="estacion-quien">{aQuien(parada)}</p>
          <p className="estacion-que">{que}</p>
          {parada.nota && <p className="estacion-que">Nota: {parada.nota}</p>}
        </div>
      </li>
    )
  }

  const cuando = (
    <>
      <span className="estacion-eta numero">
        {parada.estado === 'en_sitio' ? `Llegó ${hora(parada.llegada_en)}` : hora(parada.llegada_estimada)}
      </span>
      {franja && <span className="estacion-franja numero">franja {franja}</span>}
    </>
  )
  const visible = estado === 'actual' || abierta
  return (
    <li className="estacion" data-estado={estado}>
      <span className="estacion-punto" aria-hidden="true" />
      <div className="estacion-cuerpo">
        {estado === 'actual' ? (
          <p className="estacion-hora">
            {cuando}
            {/* La que toca sin haber salido aún no tiene estado propio en la API: es «próxima». */}
            <Distintivo dominio="ruta" valor={parada.estado === 'pendiente' ? 'proxima' : parada.estado} />
          </p>
        ) : (
          <button className="estacion-resumen" type="button" aria-expanded={abierta} aria-controls={id} onClick={() => setAbierta(!abierta)}>
            <span className="estacion-hora">{cuando}</span>
            {!abierta && (
              <>
                <span className="estacion-quien">{aQuien(parada)}</span>
                <span className="estacion-que">{que}</span>
              </>
            )}
            <span className="estacion-flecha">
              <Icono nombre="abajo" size={16} />
            </span>
          </button>
        )}
        {visible && (
          <div className="estacion-detalle" id={id}>
            <h3 className="estacion-direccion">
              <Direccion texto={familia.direccion ?? 'Sin dirección registrada'} />
            </h3>
            {lugar && <p className="estacion-lugar">{lugar}</p>}
            <p className="estacion-quien">
              <Link to={`/familias/${familia.id}`}>{familia.titular_nombre}</Link>
              {parada.mascota && <Mascota mascota={parada.mascota} />}
            </p>
            <p className="estacion-que">
              {nombreTipo(parada.tipo_codigo)}
              {parada.observaciones && ` · ${parada.observaciones}`}
            </p>
            <AccionesParada ruta={ruta} parada={parada} actual={estado === 'actual'} />
          </div>
        )}
      </div>
    </li>
  )
}

/** Una dirección cuyo número de casa no se parte entre dos líneas: leído a pleno sol, «100-»
 * arriba y «12» abajo parecen dos cifras. */
function Direccion({ texto }: { texto: string }) {
  const [antes, numero, despues] = partirDireccion(texto)
  return (
    <>
      {antes}
      {numero && <span className="sin-cortes">{numero}</span>}
      {despues}
    </>
  )
}

/** «· Max, canino de 6 años, 24 kg»: lo que el médico quiere saber antes de tocar la puerta. */
function Mascota({ mascota }: { mascota: MascotaDeParada }) {
  const especies = useEspecies()
  const especie = especies.data?.find((e) => e.codigo === mascota.especie)?.nombre ?? mascota.especie
  const anios = edad(mascota.fecha_nacimiento)
  const datos = [anios ? `${especie.toLowerCase()} de ${anios}` : especie.toLowerCase()]
  if (mascota.peso_kg !== null) datos.push(peso(mascota.peso_kg))
  return (
    <>
      {' '}
      · {mascota.nombre}, {datos.join(', ')}
    </>
  )
}

/** La ruta en miniatura para una fila del listado: dibujo para quien ve, resumen para quien no. */
export function LineaRutaMini({ ruta }: { ruta: RutaRead }) {
  const actual = paradaActual(ruta)
  return (
    <span className="linea-ruta-mini" role="img" aria-label={descripcion(ruta)}>
      {enRuta(ruta).map((p) => (
        <span key={p.id} className="linea-ruta-mini-punto" data-estado={estadoEstacion(p, actual)} />
      ))}
    </span>
  )
}
