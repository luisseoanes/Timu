import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Pestanas } from '@/components/Pestanas'
import { SelectorFamilia, useFamilia, useMascotas } from '@/features/familias'
import { mensajeError } from '@/lib/errores'
import type { Tono } from '@/lib/estados'
import { fechaCompacta, peso } from '@/lib/formato'
import type { FamiliaRead } from '@/types'

import { useCarnet, useEmitirCarnet, useGenerarCalendario, type FilaCarnet } from './api'
import { BandejaPreventivos } from './BandejaPreventivos'
import { dosis } from './preventivo'

export function PreventivosPage() {
  const [params] = useSearchParams()
  // Desde la ficha de una mascota se llega con ?mascota=<id>, directo a su carnet.
  const mascota = params.get('mascota')
  return (
    <Pestanas
      etiqueta="Secciones de preventivos"
      inicial={mascota ? 'carnet' : undefined}
      pestanas={[
        { valor: 'bandeja', titulo: 'Por hacer', contenido: <BandejaPreventivos /> },
        { valor: 'carnet', titulo: 'Carnet por mascota', contenido: <CarnetMascota mascotaInicial={mascota} /> },
      ]}
    />
  )
}

function CarnetMascota({ mascotaInicial }: { mascotaInicial: string | null }) {
  // undefined: aún no se eligió ninguna, y vale la de la mascota con que se llegó.
  const [elegida, setFamilia] = useState<FamiliaRead | null | undefined>(undefined)
  const [mascotaId, setMascotaId] = useState<string | null>(mascotaInicial)
  const inicial = useMascotas(mascotaInicial ? [mascotaInicial] : []).get(mascotaInicial ?? '')
  const deLaInicial = useFamilia(elegida === undefined ? inicial?.familia_id : undefined)
  const familia = elegida === undefined ? (deLaInicial.data ?? null) : elegida
  const carnet = useCarnet(mascotaId)
  const generar = useGenerarCalendario()
  const emitir = useEmitirCarnet()
  const mascotas = familia?.mascotas?.filter((m) => m.activa) ?? []

  return (
    <div className="pila">
      <section className="tarjeta">
        <div className="formulario">
          <div className="ancho">
            <SelectorFamilia
              valor={familia}
              onCambio={(f) => {
                setFamilia(f)
                setMascotaId(f?.mascotas?.find((m) => m.activa)?.id ?? null)
                generar.reset()
                emitir.reset()
              }}
            />
          </div>
          {familia && (
            <label className="campo">
              <span>Mascota</span>
              <select className="input" value={mascotaId ?? ''} onChange={(e) => setMascotaId(e.target.value || null)}>
                {mascotas.map((m) => (
                  <option key={m.id} value={m.id}>{m.nombre}</option>
                ))}
              </select>
            </label>
          )}
        </div>
      </section>

      {mascotaId && (
        <section className="tarjeta">
          <div className="tarjeta-cabeza">
            <h3>Carnet de {carnet.data?.mascota.nombre ?? '…'}</h3>
            <div className="acciones">
              <button className="btn btn-suave" type="button" disabled={generar.isPending} onClick={() => generar.mutate(mascotaId)}>
                Generar calendario
              </button>
              <button className="btn btn-primario" type="button" disabled={emitir.isPending} onClick={() => emitir.mutate(mascotaId)}>
                <Icono nombre="descargar" size={16} /> Emitir carnet PDF
              </button>
            </div>
          </div>
          {generar.isSuccess && (
            <p className="aviso-ok" role="status">
              Calendario actualizado: {generar.data.length} eventos nuevos.
            </p>
          )}
          {emitir.isSuccess && (
            <p className="aviso-ok" role="status">
              Carnet emitido con código <strong className="numero">{emitir.data.codigo}</strong>.{' '}
              <a href={emitir.data.url} target="_blank" rel="noreferrer">Abrir PDF</a> ·{' '}
              <Link to={`/verificar/${emitir.data.codigo}`}>Página de verificación</Link>
            </p>
          )}
          {(generar.isError || emitir.isError) && (
            <p className="error" role="alert">
              {mensajeError(generar.error ?? emitir.error, 'No fue posible completar la acción.')}
            </p>
          )}
          <Consulta consulta={carnet} cargando="Cargando el carnet…" error="No fue posible cargar el carnet.">
            {(c) => (
              <div className="tres-columnas">
                <ListaCarnet titulo="Aplicados" filas={c.aplicados} vacio="Aún no hay aplicaciones registradas." tono="ok" />
                <ListaCarnet titulo="Vencidos" filas={c.vencidos} vacio="Nada vencido." tono="peligro" pasado />
                <ListaCarnet titulo="Próximos" filas={c.proximos} vacio="Sin programación. Genera el calendario." tono="info" />
              </div>
            )}
          </Consulta>
        </section>
      )}
    </div>
  )
}

function ListaCarnet({ titulo, filas, vacio, tono, pasado = false }: { titulo: string; filas: FilaCarnet[]; vacio: string; tono: Tono; pasado?: boolean }) {
  return (
    <div>
      <h4 className="subtitulo">
        {titulo} <Insignia tono={tono}>{filas.length}</Insignia>
      </h4>
      {filas.length === 0 ? (
        <p className="apagado">{vacio}</p>
      ) : (
        <ul className="preventivos-carnet">
          {filas.map((f) => (
            <li key={f.id} className="fila">
              <span className="fila-icono" data-tono={pasado ? 'peligro' : undefined}>
                <Icono nombre="preventivos" size={16} />
              </span>
              <span className="fila-cuerpo">
                <strong>
                  {f.nombre} · {dosis(f.dosis, f.refuerzo)}
                </strong>
                <span>
                  {f.fecha_aplicacion ? (
                    `Aplicado el ${fechaCompacta(f.fecha_aplicacion)}`
                  ) : pasado ? (
                    // Lo vencido con icono y palabra, como en la bandeja.
                    <span className="bandeja-vencida">
                      <Icono nombre="alerta" size={14} />
                      <span>Tocaba el {fechaCompacta(f.fecha_programada)} ·</span>
                      <span>vencido</span>
                    </span>
                  ) : (
                    `Toca el ${fechaCompacta(f.fecha_programada)}`
                  )}
                  {f.producto ? ` · ${f.producto}` : ''}
                  {f.lote ? ` · lote ${f.lote}` : ''}
                  {f.peso_kg ? ` · ${peso(f.peso_kg)}` : ''}
                  {f.aplicado_por ? ` · aplicó ${f.aplicado_por}` : ''}
                </span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
