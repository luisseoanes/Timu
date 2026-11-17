import * as Menu from '@radix-ui/react-dropdown-menu'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { useEspecies, useTiposServicio } from '@/features/catalogos'
import { mensajeError } from '@/lib/errores'
import { moneda } from '@/lib/formato'
import type { PlanRead } from '@/types'

import { useActualizarPlan, usePlanesAdmin } from './api'
import { EditarPlan, NuevoPlan } from './PlanFormularios'
import { COLORES, ETIQUETA_PELUDOS, PERIODOS, tarifa } from './planes'

/** Planes en listado con ficha (R2-PAN-10): el plan abierto vive en la URL (`?plan=`), con lo que
 * paga cada peludo, el descuento por pagar un periodo largo, sus beneficios y dónde se vende. */
export function Planes() {
  const [params] = useSearchParams()
  const abierto = params.get('plan')
  return (
    <div className="con-ficha" data-abierta={abierto ? 'true' : undefined}>
      <PlanesLista seleccionado={abierto} />
      {abierto ? (
        <FichaPlan key={abierto} id={abierto} />
      ) : (
        <section className="ficha-abierta ficha-vacia" aria-label="Plan abierto">
          <p>Abre un plan para ver lo que paga cada peludo, sus beneficios y dónde se vende.</p>
        </section>
      )}
    </div>
  )
}

function PlanesLista({ seleccionado }: { seleccionado: string | null }) {
  const [params] = useSearchParams()
  const planes = usePlanesAdmin()
  const [nuevo, setNuevo] = useState(false)
  const enlace = (id: string) => {
    const siguiente = new URLSearchParams(params)
    siguiente.set('plan', id)
    return `?${siguiente}`
  }
  return (
    <section className="listado" aria-labelledby="planes-titulo">
      <div className="listado-cabeza">
        <h2 id="planes-titulo">
          Planes {planes.data && <span className="apagado numero">{planes.data.length}</span>}
        </h2>
        {/* Verde solo sin un plan abierto: con la ficha a la vista, el verde es de ella. */}
        <button className={`btn ${seleccionado ? 'btn-suave' : 'btn-primario'}`} type="button" onClick={() => setNuevo(true)}>
          <Icono nombre="mas" size={16} /> Nuevo plan
        </button>
      </div>
      <Consulta
        consulta={planes}
        cargando="Cargando los planes…"
        error="No fue posible cargar los planes."
        vacio="Aún no hay planes. Crea el primero con «Nuevo plan»."
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <ul className="listado-filas" aria-label="Planes de afiliación">
            {d.map((p) => (
              <li key={p.id} className="listado-fila" data-seleccionada={p.id === seleccionado}>
                <span className="listado-fila-cabeza">
                  <span className="familia-fila-marcador">
                    <span className="marcador-plan" data-color={p.color} aria-hidden="true" />
                    {/* El enlace es solo el nombre; ::after lo extiende a toda la fila. */}
                    <Link className="listado-fila-enlace" to={enlace(p.id)} aria-current={p.id === seleccionado ? 'page' : undefined}>
                      {p.nombre}
                    </Link>
                  </span>
                  {!p.activo && <Insignia tono="neutro">Inactivo</Insignia>}
                </span>
                <span className="servicio-fila-datos">
                  <span className="numero">{moneda(tarifa(p, 1))} por peludo al mes</span>
                  <span>
                    {p.ciudades.length} {p.ciudades.length === 1 ? 'ciudad' : 'ciudades'}
                  </span>
                </span>
              </li>
            ))}
          </ul>
        )}
      </Consulta>
      <NuevoPlan abierto={nuevo} onCerrar={() => setNuevo(false)} />
    </section>
  )
}

function FichaPlan({ id }: { id: string }) {
  const planes = usePlanesAdmin()
  const p = planes.data?.find((x) => x.id === id)
  return (
    <section className="ficha-abierta" aria-label="Plan abierto">
      <Consulta consulta={planes} cargando="Cargando el plan…" error="No fue posible cargar el plan.">
        {() => (p ? <Ficha plan={p} /> : <p className="apagado">Este plan ya no existe.</p>)}
      </Consulta>
    </section>
  )
}

function Ficha({ plan: p }: { plan: PlanRead }) {
  const [params] = useSearchParams()
  const actualizar = useActualizarPlan()
  const tipos = useTiposServicio()
  const especies = useEspecies()
  const [editando, setEditando] = useState(false)
  const volver = new URLSearchParams(params)
  volver.delete('plan')
  const nombreEspecie = (codigo: string) => especies.data?.find((e) => e.codigo === codigo)?.nombre ?? codigo

  return (
    <>
      <header className="ficha-cabeza">
        <Link to={`?${volver}`} className="btn btn-plano ficha-volver" aria-label="Volver a los planes">
          <Icono nombre="volver" size={16} />
        </Link>
        <h2>{p.nombre}</h2>
        <div className="ficha-datos admin-quien">
          <span className="familia-fila-marcador">
            <span className="marcador-plan" data-color={p.color} aria-hidden="true" />
            {COLORES[p.color]}
          </span>
          {!p.activo && <Insignia tono="neutro">Inactivo</Insignia>}
        </div>
        <div className="ficha-acciones">
          <button className="btn btn-primario" type="button" onClick={() => setEditando(true)}>
            Editar plan
          </button>
          <Menu.Root modal={false}>
            <Menu.Trigger className="btn btn-secundario btn-icono" aria-label={`Más acciones con ${p.nombre}`}>
              <Icono nombre="puntos" size={18} />
            </Menu.Trigger>
            <Menu.Portal>
              <Menu.Content className="menu" align="end" sideOffset={6}>
                {/* Desactivar es reversible: deja de venderse y los contratos que lo tienen siguen. */}
                <Menu.Item className="menu-item" onSelect={() => actualizar.mutate({ id: p.id, activo: !p.activo })}>
                  {p.activo ? 'Desactivar plan' : 'Activar plan'}
                </Menu.Item>
              </Menu.Content>
            </Menu.Portal>
          </Menu.Root>
        </div>
        {!p.activo && <p className="admin-nota">Inactivo: no se ofrece en afiliaciones nuevas.</p>}
        {actualizar.isError && (
          <p className="error" role="alert">
            {mensajeError(actualizar.error, 'No fue posible actualizar el plan.')}
          </p>
        )}
      </header>

      <dl className="ficha">
        {p.descripcion && (
          <div className="ancho">
            <dt>Descripción</dt>
            <dd>{p.descripcion}</dd>
          </div>
        )}
        <div className="ancho">
          <dt>Especies</dt>
          <dd>{p.especies.length ? p.especies.map(nombreEspecie).join(', ') : 'Todas'}</dd>
        </div>
      </dl>

      <section className="bloque" aria-labelledby="plan-tarifas">
        <h3 id="plan-tarifas">Valor mensual por peludo</h3>
        <p className="admin-nota">Cada peludo paga según cuántos peludos tiene la afiliación, aunque estén en planes distintos.</p>
        {/* Iguales, una frase; si cambian con el número de peludos, en 2×2 (techo 62). */}
        {p.tarifas.length > 0 && p.tarifas.every((t) => Number(t.valor) === Number(p.tarifas[0]!.valor)) ? (
          <p className="admin-tarifa-unica">
            <span className="numero">{moneda(p.tarifas[0]!.valor)}</span> por peludo, tenga la afiliación los peludos que tenga.
          </p>
        ) : (
          <dl className="ficha plan-tarifas" aria-label={`Tarifas de ${p.nombre}`}>
            {p.tarifas.map((t) => (
              <div key={t.peludos}>
                <dt>{ETIQUETA_PELUDOS[t.peludos - 1]}</dt>
                <dd className="numero">{moneda(t.valor)}</dd>
              </div>
            ))}
          </dl>
        )}
      </section>

      <section className="bloque" aria-labelledby="plan-periodos">
        <h3 id="plan-periodos">Pago por periodo con un solo peludo</h3>
        {p.tarifas_periodicidad.length ? (
          <dl className="ficha">
            {p.tarifas_periodicidad.map((t) => (
              <div key={t.periodicidad}>
                <dt>{PERIODOS[t.periodicidad]}</dt>
                <dd className="numero">{moneda(t.valor)}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="admin-nota">Sin descuento por pagar un periodo largo: se cobra el valor mensual.</p>
        )}
      </section>

      <section className="bloque" aria-labelledby="plan-beneficios">
        <h3 id="plan-beneficios">Beneficios</h3>
        {p.beneficios.length ? (
          <div className="scroll-x">
            {/* Dos columnas cortas: caben en fila también en el celular (techo 63). */}
            <table className="tabla bandeja-tabla plan-beneficios">
              <thead>
                <tr>
                  <th>Servicio</th>
                  <th>Cupo</th>
                </tr>
              </thead>
              <tbody>
                {p.beneficios.map((b) => (
                  <tr key={b.id}>
                    <td className="principal" data-etiqueta="Servicio">
                      {tipos.data?.find((t) => t.codigo === b.tipo_servicio_codigo)?.nombre ?? b.tipo_servicio_codigo.replace(/_/g, ' ')}
                    </td>
                    <td data-etiqueta="Cupo">
                      <span className="numero sin-cortes">{b.cupo ? `${b.cupo} al ${b.periodo_cupo === 'anual' ? 'año' : 'mes'}` : `Sin tope al ${b.periodo_cupo === 'anual' ? 'año' : 'mes'}`}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="admin-nota">Sin beneficios: agrégalos con «Editar plan».</p>
        )}
      </section>

      <section className="bloque" aria-labelledby="plan-condiciones">
        <h3 id="plan-condiciones">Condiciones que ve quien se afilia</h3>
        <dl className="ficha">
          <div className="ancho">
            <dt>Carencia</dt>
            <dd>{p.carencia ?? <span className="apagado">Sin escribir: el registro no la muestra.</span>}</dd>
          </div>
          <div className="ancho">
            <dt>Exclusiones</dt>
            <dd>{p.exclusiones ?? <span className="apagado">Sin escribir: el registro no las muestra.</span>}</dd>
          </div>
          <div className="ancho">
            <dt>Términos y condiciones</dt>
            <dd>
              {p.terminos_url ? (
                <a href={p.terminos_url} target="_blank" rel="noreferrer">
                  {p.terminos_url}
                </a>
              ) : (
                <span className="apagado">Sin enlace: el registro no enlaza ningún documento.</span>
              )}
            </dd>
          </div>
        </dl>
      </section>

      <section className="bloque" aria-labelledby="plan-ciudades">
        <h3 id="plan-ciudades">
          Se vende en <span className="apagado numero">{p.ciudades.length}</span> {p.ciudades.length === 1 ? 'ciudad' : 'ciudades'}
        </h3>
        <p className="admin-ciudades">{p.ciudades.join(' · ') || 'Ninguna: no se puede vender hasta elegir una.'}</p>
      </section>
      {editando && <EditarPlan plan={p} onCerrar={() => setEditando(false)} />}
    </>
  )
}
