import { Insignia } from '@/components/Distintivo'
import { telefono } from '@/lib/formato'
import type { AliadaPublica, DatosTimuRead } from '@/types'

import { redTimu } from './portada'

/** Un horario corto («24 horas», «12 horas») va en pastilla a la derecha; uno largo, con los datos. */
const HORARIO_CORTO = 14

/** Datos que se leen seguidos, con el «·» pegado al que va delante (el teléfono, con espacios duros, no se parte). */
function Datos({ className, datos }: { className: string; datos: (string | null | undefined)[] }) {
  // «6:00 p. m.» no se parte; el «·» lo pega el CSS con un espacio duro.
  const presentes = datos.filter((d): d is string => Boolean(d)).map((d) => d.replace(/(\d) ([ap])\. m\./g, '$1\u00a0$2.\u00a0m.'))
  if (presentes.length === 0) return null
  return (
    <span className={`red-datos ${className}`}>
      {presentes.map((d) => (
        <span key={d}>{d}</span>
      ))}
    </span>
  )
}

/** Una aliada: su nombre y lo que es, cómo llegar y su horario; a la derecha, la pastilla de su horario corto. */
function Aliada({ aliada: a }: { aliada: AliadaPublica }) {
  const corto = a.atiende_24h ? '24 horas' : a.horario && a.horario.length <= HORARIO_CORTO ? a.horario : null
  return (
    <li className="red-aliada">
      {a.logo_url && <img className="red-aliada-logo" src={a.logo_url} alt="" loading="lazy" />}
      <div className="red-aliada-texto">
        <Datos className="red-aliada-nombre" datos={[a.nombre, a.tipo_nombre]} />
        <Datos className="red-aliada-dato" datos={[corto ? null : a.horario, a.direccion, a.telefono ? telefono(a.telefono).replace(/ /g, '\u00a0') : null]} />
        {a.presentacion && (
          <details className="red-aliada-mas">
            <summary>Más de {a.nombre}</summary>
            <p>{a.presentacion}</p>
          </details>
        )}
      </div>
      {corto && (
        <span className="red-aliada-horario">
          <Insignia tono={a.atiende_24h ? 'ok' : 'neutro'}>{corto}</Insignia>
        </span>
      )}
    </li>
  )
}

/**
 * «La red TIMU» (R3-PUB-04): las aliadas como el plano de una línea de metro, en el orden que fija
 * Administración. Cada barrio es una estación; la de la clínica de TIMU es la de intercambio, y de
 * ella sale el ramal a la casa de la familia si algún plan trae consulta domiciliaria. Lo que no
 * tiene sede abierta (especialistas, farmacia, funeraria) va aparte.
 */
export function RedTimu({ aliadas, datos, aDomicilio }: { aliadas: AliadaPublica[]; datos?: DatosTimuRead; aDomicilio: string[] }) {
  const { estaciones, servicios } = redTimu(aliadas, datos)
  if (estaciones.length === 0 && servicios.length === 0) return null
  return (
    <div className="red">
      {estaciones.length > 0 && (
        <ol className="red-linea" aria-label="Estaciones de la red TIMU">
          {estaciones.map((e) => (
            <li key={e.clave} className="red-estacion" data-intercambio={e.clinicaTimu || undefined}>
              <span className="red-punto" aria-hidden="true" />
              <h3 className="red-estacion-nombre">
                {e.nombre}
                {e.ciudad && <span className="red-estacion-ciudad">{e.ciudad}</span>}
              </h3>
              <ul className="red-aliadas">
                {e.clinicaTimu && datos?.clinica_nombre && (
                  <li className="red-aliada red-aliada-timu">
                    <div className="red-aliada-texto">
                      <Datos className="red-aliada-nombre" datos={[datos.clinica_nombre, 'Nuestra clínica']} />
                      <Datos className="red-aliada-dato" datos={[datos.clinica_horario, datos.clinica_direccion]} />
                    </div>
                  </li>
                )}
                {e.aliadas.map((a) => (
                  <Aliada key={a.id} aliada={a} />
                ))}
              </ul>
              {e.clinicaTimu && aDomicilio.length > 0 && (
                <p className="red-ramal">
                  <span className="red-ramal-punto" aria-hidden="true" />
                  <span>
                    <strong>Tu casa</strong> · Consulta domiciliaria{' '}
                    {aDomicilio.length > 1 ? `en los ${aDomicilio.length} planes` : `en ${aDomicilio[0]}`}
                  </span>
                </p>
              )}
            </li>
          ))}
        </ol>
      )}
      {servicios.length > 0 && (
        <div className="red-servicios">
          <h3 className="red-servicios-titulo">Especialistas y servicios de la red</h3>
          <ul className="red-aliadas">
            {servicios.map((a) => (
              <Aliada key={a.id} aliada={a} />
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
