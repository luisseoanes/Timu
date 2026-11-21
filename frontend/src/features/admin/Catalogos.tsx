import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Insignia } from '@/components/Distintivo'
import { Modal } from '@/components/Modal'
import { nombreModalidad, useEspecies, useTiposServicio } from '@/features/catalogos'
import { mensajeError } from '@/lib/errores'
import type { EsquemaPreventivoRead } from '@/types'

import { useActivarCatalogo, useCiudadesTodas, useEsquemas } from './api'

type Catalogo = 'ciudades' | 'tipos-servicio' | 'esquemas-preventivos'

// Lo que deja de pasar al apagar cada catálogo (catalogos, servicios y preventivos en el backend).
const AL_APAGAR: Record<Catalogo, string> = {
  ciudades: 'La ciudad deja de ofrecerse en afiliaciones y servicios nuevos. Lo que ya existe en ella sigue.',
  'tipos-servicio': 'Ya no se pueden agendar servicios nuevos de este tipo. Los que ya están agendados siguen.',
  'esquemas-preventivos': 'Deja de programarse a las mascotas que entran. Lo que ya está programado se conserva.',
}

interface Apagando {
  catalogo: Catalogo
  codigo: string
  nombre: string
}

/** Catálogos maestros: no se borran (hay registros que los referencian), se apagan. Apagar dice qué
 * deja de pasar y se confirma; encender es directo. */
export function Catalogos() {
  const ciudades = useCiudadesTodas()
  const tipos = useTiposServicio()
  const esquemas = useEsquemas()
  const especies = useEspecies()
  const activar = useActivarCatalogo()
  const [apagando, setApagando] = useState<Apagando | null>(null)
  const nombreEspecie = (codigo: string) => especies.data?.find((e) => e.codigo === codigo)?.nombre ?? codigo

  return (
    <div className="pila">
      {activar.isError && (
        <p className="error" role="alert">
          {mensajeError(activar.error, 'No fue posible actualizar el catálogo.')}
        </p>
      )}
      <div className="dos-columnas">
        <section className="tarjeta">
          <div className="tarjeta-cabeza">
            <h2>
              Ciudades con cobertura{' '}
              {ciudades.data && (
                <span className="apagado numero">
                  {ciudades.data.filter((c) => c.activa).length} de {ciudades.data.length}
                </span>
              )}
            </h2>
          </div>
          <p className="admin-nota">{AL_APAGAR.ciudades}</p>
          <Consulta consulta={ciudades} cargando="Cargando las ciudades…" error="No fue posible cargar las ciudades.">
            {(d) =>
              d.map((c) => (
                <div key={c.codigo} className="fila">
                  <span className="fila-cuerpo">
                    <strong>{c.nombre}</strong>
                    <span>{c.departamento}</span>
                  </span>
                  <Interruptor nombre={c.nombre} activo={c.activa} pendiente={activar.isPending} onApagar={() => setApagando({ catalogo: 'ciudades', codigo: c.codigo, nombre: c.nombre })} onEncender={() => activar.mutate({ catalogo: 'ciudades', codigo: c.codigo, activo: true })} />
                </div>
              ))
            }
          </Consulta>
        </section>
        <div className="pila">
          <section className="tarjeta">
            <div className="tarjeta-cabeza">
              <h2>Tipos de servicio</h2>
            </div>
            <p className="admin-nota">{AL_APAGAR['tipos-servicio']}</p>
            <Consulta consulta={tipos} cargando="Cargando los tipos…" error="No fue posible cargar los tipos.">
              {(d) =>
                d.map((t) => (
                  <div key={t.codigo} className="fila">
                    <span className="fila-cuerpo">
                      <strong>{t.nombre}</strong>
                      {/* Un solo texto: dentro de .fila-cuerpo cada span es un bloque y partía la línea. */}
                      <span>{`${nombreModalidad(t.modalidad)} · ${t.duracion_min} min${t.requiere_autorizacion ? ' · requiere autorización' : ''}`}</span>
                    </span>
                    <Interruptor nombre={t.nombre} activo={t.activo} pendiente={activar.isPending} onApagar={() => setApagando({ catalogo: 'tipos-servicio', codigo: t.codigo, nombre: t.nombre })} onEncender={() => activar.mutate({ catalogo: 'tipos-servicio', codigo: t.codigo, activo: true })} />
                  </div>
                ))
              }
            </Consulta>
          </section>
          <section className="tarjeta">
            <div className="tarjeta-cabeza">
              <h2>Esquemas preventivos</h2>
            </div>
            <p className="admin-nota">{AL_APAGAR['esquemas-preventivos']}</p>
            <Consulta consulta={esquemas} cargando="Cargando los esquemas…" error="No fue posible cargar los esquemas.">
              {(d) =>
                d.map((e) => (
                  <div key={e.codigo} className="fila">
                    <span className="fila-cuerpo">
                      <strong>{e.nombre}</strong>
                      <span>{`${nombreEspecie(e.especie_codigo)} · ${pauta(e)}`}</span>
                    </span>
                    <Interruptor nombre={e.nombre} activo={e.activo} pendiente={activar.isPending} onApagar={() => setApagando({ catalogo: 'esquemas-preventivos', codigo: e.codigo, nombre: e.nombre })} onEncender={() => activar.mutate({ catalogo: 'esquemas-preventivos', codigo: e.codigo, activo: true })} />
                  </div>
                ))
              }
            </Consulta>
          </section>
        </div>
      </div>
      {apagando && (
        <Modal
          abierto
          onCambio={(v) => !v && setApagando(null)}
          titulo={`Apagar ${apagando.nombre}`}
          descripcion={`${AL_APAGAR[apagando.catalogo]} Se puede volver a encender.`}
          pie={
            <>
              <button className="btn btn-secundario" type="button" onClick={() => setApagando(null)}>
                Dejarlo activo
              </button>
              <button
                className="btn btn-peligro"
                type="button"
                disabled={activar.isPending}
                onClick={() => activar.mutate({ catalogo: apagando.catalogo, codigo: apagando.codigo, activo: false }, { onSuccess: () => setApagando(null) })}
              >
                Apagar
              </button>
            </>
          }
        />
      )}
    </div>
  )
}

/** El estado escrito y lo que se puede hacer: apagar pide confirmación (quien lo llama abre la
 * ventana); encender es directo. */
function Interruptor({
  nombre,
  activo,
  pendiente,
  onApagar,
  onEncender,
}: {
  nombre: string
  activo: boolean
  pendiente: boolean
  onApagar: () => void
  onEncender: () => void
}) {
  return (
    <span className="catalogo-estado">
      {activo ? <Insignia tono="ok">Activo</Insignia> : <Insignia tono="neutro">Apagado</Insignia>}
      {activo ? (
        <button className="btn btn-plano" type="button" onClick={onApagar} aria-label={`Apagar ${nombre}`}>
          Apagar
        </button>
      ) : (
        <button className="btn btn-suave" type="button" disabled={pendiente} onClick={onEncender} aria-label={`Encender ${nombre}`}>
          Encender
        </button>
      )}
    </span>
  )
}

/** «3 dosis cada 21 días · refuerzo cada 365 días»; una sola dosis no tiene intervalo inicial. */
function pauta(e: EsquemaPreventivoRead): string {
  const iniciales = e.dosis_iniciales === 1 ? '1 dosis' : `${e.dosis_iniciales} dosis cada ${e.intervalo_inicial_dias} días`
  return e.intervalo_refuerzo_dias ? `${iniciales} · refuerzo cada ${e.intervalo_refuerzo_dias} días` : iniciales
}
