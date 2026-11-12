import { useId, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { Icono } from '@/components/Icono'
import { mensajeError } from '@/lib/errores'
import { fecha } from '@/lib/formato'
import type { MascotaRead } from '@/types'

import { useCrearEntrada, useFirmarConsulta, useGuardarConsulta, usePlantillas, type EntradaHistoria } from './api'
import {
  ESTACIONES,
  cambios,
  estacionInicial,
  faltanParaFirmar,
  siguienteDe,
  tituloDe,
  valoresDe,
  type CampoGuiado,
  type Valores,
} from './consulta'
import { Adjuntos } from './LecturaConsulta'

/**
 * La consulta como una línea de cinco estaciones (contrato de la superficie): un apartado por
 * pantalla, con la estación en la que se va marcada y cualquiera a un toque. El borrador se
 * guarda al cambiar de apartado; la consulta nace al dejar el motivo, que la historia exige.
 * Firmar dice qué falta antes de intentarlo.
 */
export function ConsultaGuiada({
  mascota,
  entrada,
  servicioId,
  anterior,
  volver,
  identidad,
  estacion: estacionPedida,
  onCreada,
  onFirmada,
}: {
  mascota: MascotaRead
  /** El borrador que se continúa; sin él, la consulta empieza aquí. */
  entrada?: EntradaHistoria
  /** El servicio de la visita: su consulta firmada registra los pasos del servicio. */
  servicioId?: string
  /** La última consulta firmada, como referencia de lo que se anotó la vez anterior. */
  anterior?: EntradaHistoria
  /** A dónde vuelve el celular, que muestra la historia o la consulta, no las dos. */
  volver: string
  /** Quién se atiende; en el celular, donde la historia no está al lado. */
  identidad?: ReactNode
  /** El apartado en el que se abre; si no, el primero vacío. */
  estacion?: number
  /** Al nacer la consulta, con el apartado al que se iba: para darle su propia dirección. */
  onCreada?: (id: string, estacion: number) => void
  onFirmada: (firmada: EntradaHistoria) => void
}) {
  const plantillas = usePlantillas()
  const crear = useCrearEntrada()
  const guardar = useGuardarConsulta()
  const firmar = useFirmarConsulta()
  const [id, setId] = useState(entrada?.id)
  const [valores, setValores] = useState<Valores>(() => valoresDe(entrada))
  const [guardados, setGuardados] = useState<Valores>(() => valoresDe(entrada))
  const [actual, setActual] = useState(() => estacionPedida ?? (entrada ? estacionInicial(valoresDe(entrada)) : 0))
  const [tipo, setTipo] = useState(servicioId ? 'domiciliaria' : 'presencial')
  const [plantilla, setPlantilla] = useState('')
  const [faltan, setFaltan] = useState<CampoGuiado[]>([])
  const [sinMotivo, setSinMotivo] = useState(false)
  const idTitulo = useId()
  const idAyuda = useId()
  const estacion = ESTACIONES[actual]
  const ultima = actual === ESTACIONES.length - 1
  const ocupada = crear.isPending || guardar.isPending || firmar.isPending
  const activas = (plantillas.data ?? []).filter((p) => p.activa)
  const referencia = anterior?.[estacion.campo]
  const error = crear.error ?? guardar.error ?? firmar.error

  function escribir(campo: keyof Valores, texto: string) {
    setValores((v) => ({ ...v, [campo]: texto }))
    if (campo === 'motivo') setSinMotivo(false)
    setFaltan((f) => f.filter((c) => c !== campo || !texto.trim()))
  }

  /** Guarda lo escrito: crea la consulta si aún no existe. Devuelve su id, o nada si falta el motivo. */
  async function guardarBorrador(): Promise<string | undefined> {
    if (!id) {
      if (!valores.motivo.trim()) return undefined
      const datos = Object.fromEntries(
        Object.entries(valores)
          .filter(([, texto]) => texto.trim())
          .map(([campo, texto]) => [campo, texto.trim()]),
      )
      const nueva = await crear.mutateAsync({
        ...datos,
        mascota_id: mascota.id,
        tipo,
        servicio_id: servicioId,
        plantilla_codigo: plantilla || undefined,
      })
      setId(nueva.id)
      setGuardados(valoresDe(nueva))
      return nueva.id
    }
    const distintos = cambios(valores, guardados)
    if (Object.keys(distintos).length > 0) setGuardados(valoresDe(await guardar.mutateAsync({ id, datos: distintos })))
    return id
  }

  async function ir(destino: number) {
    if (destino === actual) return
    if (!id && !valores.motivo.trim()) {
      setSinMotivo(true)
      setActual(0)
      return
    }
    try {
      const nacida = !id
      const guardada = await guardarBorrador()
      if (nacida && guardada && onCreada) {
        onCreada(guardada, destino)
        return
      }
      setActual(destino)
    } catch {
      // El error del servidor se muestra; el médico sigue en el apartado con lo que escribió.
    }
  }

  async function firmarConsulta() {
    const pendientes = faltanParaFirmar(valores, Boolean(servicioId))
    if (pendientes.length > 0) {
      setFaltan(pendientes)
      setActual(ESTACIONES.findIndex((e) => e.campo === pendientes[0]))
      return
    }
    try {
      const listo = await guardarBorrador()
      if (listo) onFirmada(await firmar.mutateAsync(listo))
    } catch {
      // Se muestra la causa que da el servidor.
    }
  }

  return (
    <section className="ficha-abierta consulta" aria-label={`Consulta de ${mascota.nombre}`}>
      <header className="consulta-cabeza">
        <Link to={volver} className="btn btn-plano ficha-volver" aria-label="Volver a la historia">
          <Icono nombre="volver" size={16} />
        </Link>
        <div className="consulta-cabeza-textos">
          {identidad}
          <p className="consulta-quien">
            <strong>{entrada ? `Consulta del ${fecha(entrada.fecha)}` : 'Consulta nueva'}</strong>
            <span>{servicioId ? 'De la visita de hoy' : id ? 'Borrador guardado' : 'Sin guardar aún'}</span>
          </p>
        </div>
      </header>

      <ol className="consulta-guia" aria-label="Apartados de la consulta" style={{ ['--avance' as string]: actual / (ESTACIONES.length - 1) }}>
        {ESTACIONES.map((e, i) => {
          const escrito = Boolean(valores[e.campo].trim())
          const estado = i === actual ? 'actual' : escrito ? 'hecha' : 'pendiente'
          return (
            <li key={e.campo} data-estado={estado} data-falta={faltan.includes(e.campo) || undefined}>
              <button
                type="button"
                aria-current={i === actual ? 'step' : undefined}
                aria-label={`${e.titulo}, ${escrito ? 'escrito' : 'sin escribir'}`}
                disabled={ocupada}
                onClick={() => void ir(i)}
              >
                <span className="consulta-estacion" aria-hidden="true" />
                <span className="consulta-estacion-nombre" aria-hidden="true">
                  {e.corto}
                </span>
              </button>
            </li>
          )
        })}
      </ol>

      <div className="consulta-apartado">
        <h2 id={idTitulo} className="consulta-titulo">
          {estacion.titulo}
        </h2>
        {actual === 0 && !id && (
          <div className="formulario">
            {activas.length > 0 && (
              <label className="campo">
                <span>Plantilla</span>
                <select
                  className="input"
                  value={plantilla}
                  onChange={(ev) => {
                    setPlantilla(ev.target.value)
                    const campos = activas.find((p) => p.codigo === ev.target.value)?.campos ?? {}
                    // La plantilla es el punto de partida: llena lo vacío, no pisa lo escrito.
                    setValores((v) =>
                      Object.fromEntries(
                        Object.entries(v).map(([campo, texto]) => [campo, texto.trim() ? texto : (campos[campo] ?? '')]),
                      ) as Valores,
                    )
                  }}
                >
                  <option value="">Sin plantilla</option>
                  {activas.map((p) => (
                    <option key={p.codigo} value={p.codigo}>
                      {p.nombre}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <label className="campo">
              <span>Modalidad</span>
              <select className="input" value={tipo} onChange={(ev) => setTipo(ev.target.value)}>
                <option value="domiciliaria">Domiciliaria</option>
                <option value="presencial">Presencial</option>
              </select>
            </label>
          </div>
        )}
        <p id={idAyuda} className="consulta-ayuda">
          {estacion.ayuda(mascota.nombre)}
        </p>
        <textarea
          key={estacion.campo}
          className="input consulta-campo"
          aria-labelledby={idTitulo}
          aria-describedby={idAyuda}
          aria-invalid={(estacion.campo === 'motivo' && sinMotivo) || faltan.includes(estacion.campo) || undefined}
          rows={6}
          value={valores[estacion.campo]}
          onChange={(ev) => escribir(estacion.campo, ev.target.value)}
        />
        {sinMotivo && actual === 0 && (
          <p className="error" role="alert">
            Escribe el motivo para seguir: la consulta se guarda a partir de él.
          </p>
        )}
        {ultima && (
          <label className="campo">
            <span>Notas internas (no las ve la familia)</span>
            <textarea
              className="input"
              rows={2}
              value={valores.notas_internas}
              onChange={(ev) => escribir('notas_internas', ev.target.value)}
            />
          </label>
        )}
        {referencia && (
          <p className="consulta-antes">
            <span className="etiqueta">En la última consulta · {fecha(anterior!.fecha)}</span>
            {referencia}
          </p>
        )}
        {faltan.length > 0 && (
          <p className="error" role="alert">
            Para firmar falta: {faltan.map(tituloDe).join(', ')}
            {faltan.includes('tratamiento') && servicioId ? '. Sin tratamiento, la visita no se puede terminar.' : '.'}
          </p>
        )}
        {error && (
          <p className="error" role="alert">
            {mensajeError(error, 'No fue posible guardar la consulta.')}
          </p>
        )}
      </div>

      <div className="consulta-pie">
        {actual > 0 && (
          <button className="btn btn-secundario" type="button" disabled={ocupada} onClick={() => void ir(actual - 1)}>
            Anterior
          </button>
        )}
        {ultima ? (
          <button className="btn btn-primario" type="button" disabled={ocupada} onClick={() => void firmarConsulta()}>
            {firmar.isPending ? 'Firmando…' : 'Firmar consulta'}
          </button>
        ) : (
          <button className="btn btn-primario" type="button" disabled={ocupada} onClick={() => void ir(actual + 1)}>
            {ocupada ? 'Guardando…' : `Siguiente: ${siguienteDe(actual)}`}
          </button>
        )}
      </div>

      {id && (
        <div className="consulta-adjuntos">
          <Adjuntos historiaId={id} puedeAdjuntar />
        </div>
      )}
    </section>
  )
}
