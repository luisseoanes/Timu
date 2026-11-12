import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Paginacion } from '@/components/Paginacion'
import { useAuth } from '@/features/auth'
import { puede } from '@/lib/permisos'
import type { EstadoAfiliacion, LineaFamiliaRead } from '@/types'

import { useFamilias, useLineas } from './api'
import { LineaMini } from './LineaFamilia'
import { NuevaFamiliaModal } from './NuevaFamiliaModal'

const ESTADOS: { valor: EstadoAfiliacion; label: string }[] = [
  { valor: 'prospecto', label: 'Prospecto' },
  { valor: 'activa', label: 'Activa' },
  { valor: 'en_mora', label: 'En mora' },
  { valor: 'congelada', label: 'Congelada' },
  { valor: 'cancelada', label: 'Cancelada' },
]

const POR_PAGINA = 25

/**
 * El listado de familias, a la izquierda del panel de Familias. La búsqueda, el filtro y la
 * página viven en la URL: abrir una familia y volver no los pierde, y el buscador de la
 * cabecera llega por `?q=`.
 */
export function FamiliasLista({ seleccionada }: { seleccionada?: string }) {
  const { usuario } = useAuth()
  const [params, setParams] = useSearchParams()
  const [nueva, setNueva] = useState(false)
  const q = params.get('q') ?? ''
  const estado = (params.get('estado') ?? '') as EstadoAfiliacion | ''
  const offset = Number(params.get('desde') ?? 0)
  const familias = useFamilias({ q: q || undefined, estado: estado || undefined, limit: POR_PAGINA, offset })
  const lineas = useLineas(familias.data?.items.map((f) => f.id) ?? [])
  const porFamilia = new Map<string, LineaFamiliaRead>(lineas.data?.map((l) => [l.familia_id, l]))
  const sufijo = params.toString() ? `?${params}` : ''

  function cambiar(clave: string, valor: string) {
    const nuevos = new URLSearchParams(params)
    if (valor) nuevos.set(clave, valor)
    else nuevos.delete(clave)
    if (clave !== 'desde') nuevos.delete('desde')
    setParams(nuevos, { replace: true })
  }

  return (
    <section className="listado" aria-labelledby="familias-titulo">
      <div className="listado-cabeza">
        <h2 id="familias-titulo">
          Familias <span className="apagado numero">{familias.data?.total ?? 0}</span>
        </h2>
        {puede(usuario, 'gestionarAfiliacion') && (
          // Una sola acción verde llena por vista (manual, sección 11): con una familia abierta,
          // la principal es la de su próxima estación.
          <button className={`btn ${seleccionada ? 'btn-suave' : 'btn-primario'}`} type="button" onClick={() => setNueva(true)}>
            <Icono nombre="mas" size={16} />
            Nueva familia
          </button>
        )}
      </div>

      <div className="filtros">
        <label className="buscador">
          <Icono nombre="buscar" size={18} />
          <input
            type="search"
            placeholder="Buscar familia"
            value={q}
            onChange={(e) => cambiar('q', e.target.value)}
            aria-label="Buscar familias"
          />
        </label>
        <select
          className="input"
          value={estado}
          onChange={(e) => cambiar('estado', e.target.value)}
          aria-label="Filtrar por estado"
        >
          <option value="">Todos los estados</option>
          {ESTADOS.map((e) => (
            <option key={e.valor} value={e.valor}>
              {e.label}
            </option>
          ))}
        </select>
      </div>

      <Consulta
        consulta={familias}
        cargando="Cargando familias…"
        error="No fue posible cargar las familias."
        vacio={q || estado ? 'Ninguna familia coincide con el filtro. Prueba con otro nombre o quita el filtro de estado.' : 'Todavía no hay familias. Da de alta la primera con «Nueva familia».'}
        estaVacio={(d) => d.items.length === 0}
      >
        {(datos) => (
          <>
            <ul className="listado-filas">
              {datos.items.map((f) => {
                const linea = porFamilia.get(f.id)
                const planes = linea?.planes ?? []
                const activas = f.mascotas?.filter((m) => m.activa).map((m) => m.nombre) ?? []
                const vencidas = linea?.estaciones.filter((e) => e.estado === 'vencida').length ?? 0
                return (
                  <li key={f.id} className="listado-fila" data-seleccionada={f.id === seleccionada}>
                    <span className="listado-fila-cabeza">
                      {/* El enlace es solo el nombre; ::after lo extiende a toda la fila. */}
                      <Link
                        className="listado-fila-enlace"
                        to={`/familias/${f.id}${sufijo}`}
                        aria-current={f.id === seleccionada ? 'page' : undefined}
                      >
                        {f.titular_nombre}
                      </Link>
                      <Distintivo dominio="afiliacion" valor={f.estado} />
                    </span>
                    <span className="familia-fila-plan">
                      {planes.length > 0 ? (
                        planes.map((p) => (
                          <span key={p.plan_id} className="familia-fila-marcador">
                            <span className="marcador-plan" data-color={p.color} aria-hidden="true" />
                            {p.nombre}
                          </span>
                        ))
                      ) : (
                        <span>Sin plan</span>
                      )}
                      {activas.length > 0 && <span className="apagado">· {activas.join(', ')}</span>}
                    </span>
                    {/* Lo vencido se dice en texto, no solo con el punto rojo de la miniatura. */}
                    {vencidas > 0 && (
                      <span className="familia-fila-vencidas">
                        <Icono nombre="alerta" size={14} />
                        {vencidas} {vencidas === 1 ? 'vencida' : 'vencidas'}
                      </span>
                    )}
                    {linea && <LineaMini estaciones={linea.estaciones} color={planes[0]?.color} />}
                  </li>
                )
              })}
            </ul>
            <Paginacion
              total={datos.total}
              limit={datos.limit}
              offset={datos.offset}
              onCambio={(n) => cambiar('desde', n ? String(n) : '')}
            />
          </>
        )}
      </Consulta>

      <NuevaFamiliaModal abierto={nueva} onCambio={setNueva} />
    </section>
  )
}
