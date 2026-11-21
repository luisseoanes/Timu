import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

import frenteAlLogo1600 from '@/assets/portada/frente-al-logo-1600.webp'
import frenteAlLogo800 from '@/assets/portada/frente-al-logo-800.webp'
import gatitos1600 from '@/assets/portada/gatitos-1600.webp'
import gatitos800 from '@/assets/portada/gatitos-800.webp'
import medica1600 from '@/assets/portada/medica-bulldog-1600.webp'
import medica800 from '@/assets/portada/medica-bulldog-800.webp'
import parque1200 from '@/assets/portada/parque-1200.webp'
import parque700 from '@/assets/portada/parque-700.webp'
import recepcion1600 from '@/assets/portada/recepcion-1600.webp'
import recepcion800 from '@/assets/portada/recepcion-800.webp'
import { mensajeError } from '@/lib/errores'
import { moneda } from '@/lib/formato'
import type { PlanPublico } from '@/types'

import { ArmaTuPlan, type Manada } from './ArmaTuPlan'
import { Comparador } from './Comparador'
import { ContactoPortada } from './ContactoPortada'
import { MarcoPublico } from './MarcoPublico'
import { useAliadasPublicas, useDatosTimu, rutaDePlan } from './portada'
import { RedTimu } from './RedTimu'
import { tarifaCon, useCiudadesRegistro, usePlanesRegistro } from './registro'

/** Una foto del álbum: dos anchos para el celular y el escritorio, con su pie en pastilla. */
function Foto({
  chica,
  grande,
  anchoGrande,
  alt,
  pie,
  sizes,
  primera = false,
  className,
}: {
  chica: string
  grande: string
  anchoGrande: number
  alt: string
  pie?: string
  sizes: string
  primera?: boolean
  className?: string
}) {
  return (
    <figure className={`album-foto${className ? ` ${className}` : ''}`}>
      <img
        src={chica}
        srcSet={`${chica} ${Math.round(anchoGrande / 2)}w, ${grande} ${anchoGrande}w`}
        sizes={sizes}
        alt={alt}
        loading={primera ? 'eager' : 'lazy'}
        // React 18 no conoce `fetchPriority`: va como el atributo del DOM, en minúscula.
        {...(primera ? ({ fetchpriority: 'high' } as Record<string, string>) : {})}
        decoding="async"
      />
      {pie && <figcaption>{pie}</figcaption>}
    </figure>
  )
}

/** Los planes como pastillas en su color, con lo menos que paga un peludo al mes. */
function PastillasPlanes({ planes, peludos }: { planes: PlanPublico[]; peludos: number }) {
  return (
    <ul className="pastillas-planes" aria-label="Los planes">
      {planes.map((p) => (
        <li key={p.id}>
          <Link className="pastilla-plan" data-color={p.color} to={rutaDePlan(p)}>
            <span>{p.nombre}</span>
            <strong className="numero">{moneda(tarifaCon(p, peludos))}</strong>
          </Link>
        </li>
      ))}
    </ul>
  )
}

/** Lleva a la sección del ancla (`/#planes`), también al llegar desde otra página o de la web vieja. */
function useIrAlAncla() {
  const { hash } = useLocation()
  useEffect(() => {
    if (!hash) return
    document.getElementById(decodeURIComponent(hash.slice(1)))?.scrollIntoView()
  }, [hash])
}

/**
 * 6.1 La portada de timu.com.co (R3-PUB-04, «Álbum de la manada»): abre con la gente y los peludos
 * reales de TIMU y deja la oferta a un toque. Todo lo que dice de un plan sale del catálogo, de las
 * aliadas lo que decide Administración y de TIMU lo que escribe en «Datos de TIMU».
 */
export function PortadaPage() {
  useIrAlAncla()
  const ciudades = useCiudadesRegistro()
  const datos = useDatosTimu()
  const aliadas = useAliadasPublicas()
  const [manada, setManada] = useState<Manada>({ ciudad: '', perros: 1, gatos: 0 })
  // Hasta que la familia elija, la ciudad es la de la clínica de TIMU si se vende allí.
  const ciudad = manada.ciudad || (ciudades.data?.includes(datos.data?.clinica_ciudad ?? '') ? datos.data!.clinica_ciudad! : (ciudades.data?.[0] ?? ''))
  const planes = usePlanesRegistro(ciudad)
  const lista = planes.data ?? []
  const peludos = Math.max(manada.perros + manada.gatos, 1)

  useEffect(() => {
    document.title = 'TIMU · Medicina veterinaria prepagada para perros y gatos'
  }, [])

  return (
    <MarcoPublico>
      <section className="album" aria-labelledby="portada-titulo">
        <div className="album-mosaico">
          <Foto
            className="album-principal"
            chica={medica800}
            grande={medica1600}
            anchoGrande={1600}
            sizes="(min-width: 1100px) 40vw, 100vw"
            alt="Una médica veterinaria de TIMU abraza a un bulldog francés en la clínica"
            pie="Consulta en nuestra clínica"
            primera
          />
          <Foto
            chica={recepcion800}
            grande={recepcion1600}
            anchoGrande={1600}
            sizes="(min-width: 1100px) 25vw, 50vw"
            alt="Una persona del equipo de TIMU en la recepción de la clínica"
            pie="Te recibimos en la clínica"
          />
          <Foto
            className="album-logo"
            chica={frenteAlLogo800}
            grande={frenteAlLogo1600}
            anchoGrande={1600}
            sizes="(min-width: 1100px) 25vw, 50vw"
            alt="Una persona del equipo de TIMU señala el logo en la clínica"
            pie="El equipo de TIMU"
          />
        </div>
        <div className="album-panel">
          <h1 id="portada-titulo" className="album-titulo">
            Tu peludito, bien cuidado.
          </h1>
          <p className="album-frase">
            Medicina veterinaria prepagada para tu perro o tu gato: médicos veterinarios, nuestra clínica y una red de aliadas. Lo que cubre cada
            plan, dicho de frente.
          </p>
          {lista.length > 0 && <PastillasPlanes planes={lista} peludos={peludos} />}
          <ArmaTuPlan manada={{ ...manada, ciudad }} planes={lista} cargando={planes.isFetching && !planes.data} onCambio={setManada} />
        </div>
      </section>

      <section id="planes" className="seccion" aria-labelledby="planes-titulo">
        <div className="seccion-cabeza">
          <h2 id="planes-titulo" className="seccion-titulo">
            {lista.length > 1 ? `${lista.length === 3 ? 'Tres' : lista.length} planes` : 'Los planes'}
            {ciudad && ` en ${ciudad}`}, lado a lado
          </h2>
          <p>
            Lo que cubre cada uno, cuántas veces al año y desde cuándo. El precio es por peludo al mes y baja cuantos más se unen
            {peludos > 1 ? `: con ${peludos} peludos, cada uno paga lo que dice la tabla.` : '.'}
          </p>
        </div>
        {planes.isError ? (
          <p className="aviso-error" role="alert">
            {mensajeError(planes.error, 'No pudimos cargar los planes.')}
          </p>
        ) : planes.isPending ? (
          <div className="esqueleto" role="status">
            <span className="sr-only">Cargando los planes…</span>
            <span className="esqueleto-linea" aria-hidden="true" />
            <span className="esqueleto-linea" aria-hidden="true" />
          </div>
        ) : lista.length === 0 ? (
          <p className="apagado">Aún no vendemos planes en {ciudad}. Elige otra ciudad, o escríbenos y te avisamos cuando lleguemos.</p>
        ) : (
          <>
            <Comparador planes={lista} titulo={`Lo que cubre cada plan en ${ciudad}`} totalPeludos={peludos} />
            <ul className="planes-detalle" aria-label="Todo lo que cubre cada plan">
              {lista.map((p) => (
                <li key={p.id}>
                  <Link to={rutaDePlan(p)} className="planes-detalle-enlace" data-color={p.color}>
                    Todo lo que cubre {p.nombre}
                  </Link>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      <section id="aliadas" className="seccion seccion-red" aria-labelledby="aliadas-titulo">
        <div className="seccion-cabeza">
          <h2 id="aliadas-titulo" className="seccion-titulo">
            La red TIMU
          </h2>
          <p>Nuestra clínica y las clínicas, especialistas y servicios aliados que atienden a los peludos afiliados.</p>
        </div>
        {aliadas.isError ? (
          <p className="aviso-error" role="alert">
            {mensajeError(aliadas.error, 'No pudimos cargar la red de aliadas.')}
          </p>
        ) : aliadas.isPending ? (
          <div className="esqueleto" role="status">
            <span className="sr-only">Cargando la red…</span>
            <span className="esqueleto-linea" aria-hidden="true" />
          </div>
        ) : (
          <RedTimu
            aliadas={aliadas.data}
            datos={datos.data}
            aDomicilio={lista.filter((p) => p.beneficios.some((b) => b.tipo_servicio_codigo === 'consulta_domiciliaria')).map((p) => p.nombre)}
          />
        )}
      </section>

      <section id="nosotros" className="seccion seccion-nosotros" aria-labelledby="nosotros-titulo">
        <div className="nosotros-fotos">
          <Foto
            chica={parque700}
            grande={parque1200}
            anchoGrande={1200}
            sizes="(min-width: 900px) 30vw, 100vw"
            alt="Una mujer abraza a su perro en un parque"
          />
          <Foto chica={gatitos800} grande={gatitos1600} anchoGrande={1600} sizes="(min-width: 900px) 20vw, 50vw" alt="Cuatro gatitos corren por la hierba" />
        </div>
        <div className="nosotros-texto">
          <h2 id="nosotros-titulo" className="seccion-titulo">
            Quiénes somos
          </h2>
          {datos.data?.presentacion && <p className="nosotros-presentacion">{datos.data.presentacion}</p>}
          {(datos.data?.mision || datos.data?.vision) && (
            <dl className="nosotros-lista">
              {datos.data.mision && (
                <div>
                  <dt>Misión</dt>
                  <dd>{datos.data.mision}</dd>
                </div>
              )}
              {datos.data.vision && (
                <div>
                  <dt>Visión</dt>
                  <dd>{datos.data.vision}</dd>
                </div>
              )}
            </dl>
          )}
          {datos.data?.valores.length ? (
            <ul className="nosotros-valores" aria-label="Nuestros valores">
              {datos.data.valores.map((v) => (
                <li key={v}>{v}</li>
              ))}
            </ul>
          ) : null}
        </div>
      </section>

      <section id="contacto" className="seccion seccion-contacto" aria-labelledby="contacto-titulo">
        <div className="seccion-cabeza">
          <h2 id="contacto-titulo" className="seccion-titulo">
            Hablemos de tu peludo
          </h2>
        </div>
        <ContactoPortada datos={datos.data} />
      </section>
    </MarcoPublico>
  )
}
