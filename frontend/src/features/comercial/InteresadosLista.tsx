import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Paginacion } from '@/components/Paginacion'
import { diaISO, fechaCompacta, hoyISO, porcentaje } from '@/lib/formato'
import type { InteresadoRead, RecuentosEmbudo } from '@/types'

import { ETAPAS, useEmbudo, useInteresados, useRecuentosEmbudo } from './api'
import { nombreDe, nombreOrigen } from './interesado'
import { NuevoInteresado } from './NuevoInteresado'

type Vista = 'abiertos' | 'afiliados' | 'perdidos'

const VISTAS: { valor: Vista; label: string; recuento: keyof RecuentosEmbudo; vacio: string }[] = [
  { valor: 'abiertos', label: 'Abiertos', recuento: 'abiertos', vacio: 'Nadie está en el embudo. Registra un interesado o espera a que escriba por WhatsApp.' },
  { valor: 'afiliados', label: 'Afiliados', recuento: 'afiliado', vacio: 'Ningún interesado se ha afiliado todavía.' },
  { valor: 'perdidos', label: 'Perdidos', recuento: 'perdido', vacio: 'Ningún interesado se ha perdido.' },
]

const POR_PAGINA = 30

/** Los interesados del embudo: abiertos agrupados por etapa, en su orden; afiliados o perdidos. */
export function InteresadosLista({ seleccionado }: { seleccionado: string | null }) {
  const [params, setParams] = useSearchParams()
  const vista: Vista = VISTAS.find((v) => v.valor === params.get('vista'))?.valor ?? 'abiertos'
  const q = params.get('q') ?? ''
  const offset = Number(params.get('desde') ?? 0)
  const [nuevo, setNuevo] = useState(false)
  const hoy = hoyISO()
  const embudo = useEmbudo(`${hoy.slice(0, 8)}01`, hoy)
  const recuentos = useRecuentosEmbudo(q || undefined)
  const interesados = useInteresados({
    q: q || undefined,
    abiertos: vista === 'abiertos' || undefined,
    etapa: vista === 'afiliados' ? 'afiliado' : vista === 'perdidos' ? 'perdido' : undefined,
    limit: POR_PAGINA,
    offset,
  })

  function cambiar(cambios: Record<string, string>) {
    const siguiente = new URLSearchParams(params)
    siguiente.delete('desde')
    for (const [clave, valor] of Object.entries(cambios)) {
      if (valor) siguiente.set(clave, valor)
      else siguiente.delete(clave)
    }
    setParams(siguiente, { replace: true })
  }
  const enlace = (id: string) => {
    const siguiente = new URLSearchParams(params)
    siguiente.set('interesado', id)
    return `?${siguiente}`
  }

  return (
    <section className="listado" aria-labelledby="interesados-titulo">
      <div className="listado-cabeza">
        <h2 id="interesados-titulo">
          Interesados {recuentos.data && <span className="apagado numero">{recuentos.data.abiertos}</span>}
        </h2>
        {/* Verde solo sin un interesado abierto: con la ficha a la vista, el verde es de ella. */}
        <button className={`btn ${seleccionado ? 'btn-suave' : 'btn-primario'}`} type="button" onClick={() => setNuevo(true)}>
          <Icono nombre="mas" size={16} /> Nuevo interesado
        </button>
      </div>
      {embudo.data && (
        <p className="comercial-mes">
          Este mes: <span className="numero">{embudo.data.total}</span> {embudo.data.total === 1 ? 'interesado' : 'interesados'} · conversión{' '}
          <span className="numero">{porcentaje(embudo.data.conversion)}</span>
        </p>
      )}
      <div className="filtros comercial-filtros">
        <div className="segmento comercial-vistas" role="group" aria-label="Vista de los interesados">
          {VISTAS.map((v) => (
            <button
              key={v.valor}
              type="button"
              className="segmento-opcion"
              data-state={vista === v.valor ? 'active' : 'inactive'}
              aria-pressed={vista === v.valor}
              onClick={() => cambiar({ vista: v.valor === 'abiertos' ? '' : v.valor })}
            >
              {v.label}
              {recuentos.data && (
                <>
                  {' '}
                  <span className="segmento-recuento numero">{recuentos.data[v.recuento]}</span>
                </>
              )}
            </button>
          ))}
        </div>
        <label className="buscador">
          <Icono nombre="buscar" size={18} />
          <input type="search" placeholder="Nombre o celular" value={q} onChange={(e) => cambiar({ q: e.target.value })} aria-label="Buscar interesados" />
        </label>
      </div>

      <Consulta
        consulta={interesados}
        cargando="Cargando los interesados…"
        error="No fue posible cargar los interesados."
        vacio={q ? 'Nadie de esta vista coincide con la búsqueda.' : VISTAS.find((v) => v.valor === vista)!.vacio}
        estaVacio={(d) => d.items.length === 0}
      >
        {(d) => (
          <>
            {vista === 'abiertos' ? (
              <ul className="listado-filas" aria-label="Interesados abiertos, por etapa">
                {porEtapa(d.items).map((g) => (
                  <li key={g.etapa} className="servicios-dia">
                    <span className="servicios-dia-rotulo">
                      {g.label} · <span className="numero">{recuentos.data?.[g.etapa as keyof RecuentosEmbudo] ?? g.interesados.length}</span>
                    </span>
                    <ul className="servicios-dia-filas">
                      {g.interesados.map((i) => (
                        <FilaInteresado key={i.id} interesado={i} seleccionado={seleccionado} enlace={enlace(i.id)} />
                      ))}
                    </ul>
                  </li>
                ))}
              </ul>
            ) : (
              <ul className="listado-filas" aria-label={`Interesados ${vista}`}>
                {d.items.map((i) => (
                  <FilaInteresado key={i.id} interesado={i} seleccionado={seleccionado} enlace={enlace(i.id)} conEtapa />
                ))}
              </ul>
            )}
            <Paginacion
              total={d.total}
              limit={d.limit}
              offset={d.offset}
              onCambio={(o) => {
                const siguiente = new URLSearchParams(params)
                if (o) siguiente.set('desde', String(o))
                else siguiente.delete('desde')
                setParams(siguiente, { replace: true })
              }}
            />
          </>
        )}
      </Consulta>
      <NuevoInteresado abierto={nuevo} onCerrar={() => setNuevo(false)} />
    </section>
  )
}

/** La página llega en el orden del embudo: se agrupa sin reordenar. */
function porEtapa(items: InteresadoRead[]): { etapa: string; label: string; interesados: InteresadoRead[] }[] {
  return ETAPAS.map((e) => ({ etapa: e.valor as string, label: e.label as string, interesados: items.filter((i) => i.etapa === e.valor) })).filter(
    (g) => g.interesados.length > 0,
  )
}

function FilaInteresado({
  interesado: i,
  seleccionado,
  enlace,
  conEtapa = false,
}: {
  interesado: InteresadoRead
  seleccionado: string | null
  enlace: string
  conEtapa?: boolean
}) {
  const cuando = i.ultimo_contacto ?? i.created_at
  return (
    <li className="listado-fila" data-seleccionada={i.id === seleccionado}>
      <span className="listado-fila-cabeza">
        {/* El enlace es solo el nombre; ::after lo extiende a toda la fila. */}
        <Link className="listado-fila-enlace" to={enlace} aria-current={i.id === seleccionado ? 'page' : undefined}>
          {nombreDe(i)}
        </Link>
        {conEtapa && <Distintivo dominio="etapa" valor={i.etapa} />}
      </span>
      <span className="servicio-fila-datos">
        <span>{nombreOrigen(i.origen)}</span>
        {i.ciudad && <span>{i.ciudad}</span>}
        <span className="numero">{fechaCompacta(diaISO(cuando))}</span>
      </span>
    </li>
  )
}
