import { useState } from 'react'

import { Modal } from '@/components/Modal'
import { useEspecies } from '@/features/catalogos'
import { mensajeError } from '@/lib/errores'
import { moneda } from '@/lib/formato'
import type { CotizacionRead, FamiliaRead, Periodicidad } from '@/types'

import {
  useAfiliarAsistida,
  useCotizacion,
  usePagoManualAfiliacion,
  type DatosAfiliacion,
  type InicioAfiliacion,
  type PeludoElegido,
} from './api'
import { ElegirPlan } from './ElegirPlan'

const PERIODOS: { valor: Periodicidad; etiqueta: string }[] = [
  { valor: 'mensual', etiqueta: 'Mensual' },
  { valor: 'trimestral', etiqueta: 'Trimestral' },
  { valor: 'semestral', etiqueta: 'Semestral' },
  { valor: 'anual', etiqueta: 'Anual' },
]

/**
 * Afiliación asistida (F1-AFI, 6.3): el comercial elige el plan de cada peludo y la forma de
 * pago, ve el precio que calcula el backend y deja registrada cómo aceptó la familia. Se
 * genera el enlace de pago; si la familia ya pagó por otro medio, se registra el pago manual.
 */
export function AfiliarModal({ familia, abierto, onCerrar }: { familia: FamiliaRead; abierto: boolean; onCerrar: () => void }) {
  const afiliar = useAfiliarAsistida(familia.id)
  const pagoManual = usePagoManualAfiliacion()
  const [inicio, setInicio] = useState<InicioAfiliacion | null>(null)

  function cerrar() {
    afiliar.reset()
    pagoManual.reset()
    setInicio(null)
    onCerrar()
  }

  return (
    <Modal abierto={abierto} onCambio={(v) => !v && cerrar()} titulo={`Afiliar a ${familia.titular_nombre}`}>
      {pagoManual.isSuccess ? (
        <p className="aviso-ok" role="status">
          Pago registrado: la afiliación quedó activa y la familia recibe su bienvenida por WhatsApp.
        </p>
      ) : inicio ? (
        <div className="pila">
          <p className="aviso-ok" role="status">
            Afiliación iniciada por {moneda(inicio.valor)}. Envía este enlace de pago a la familia:
          </p>
          <input className="input codigo" readOnly value={inicio.enlace_pago} aria-label="Enlace de pago" onFocus={(e) => e.target.select()} />
          <form
            className="formulario"
            onSubmit={(e) => {
              e.preventDefault()
              const d = new FormData(e.currentTarget)
              pagoManual.mutate({
                solicitudId: inicio.solicitud_id,
                medio: String(d.get('medio')),
                comprobante: String(d.get('comprobante')).trim(),
              })
            }}
          >
            <p className="subtitulo ancho">¿Ya pagó por otro medio?</p>
            <label className="campo">
              <span>Medio</span>
              <select className="input" name="medio" defaultValue="transferencia">
                <option value="transferencia">Transferencia</option>
                <option value="consignacion">Consignación</option>
                <option value="efectivo">Efectivo</option>
                <option value="datafono">Datáfono</option>
              </select>
            </label>
            <label className="campo">
              <span>Comprobante</span>
              <input className="input" name="comprobante" required minLength={3} />
            </label>
            {pagoManual.isError && (
              <p className="error ancho" role="alert">
                {mensajeError(pagoManual.error, 'No fue posible registrar el pago.')}
              </p>
            )}
            <button className="btn btn-suave ancho" type="submit" disabled={pagoManual.isPending}>
              Registrar pago recibido
            </button>
          </form>
        </div>
      ) : (
        <ElegirAfiliacion familia={familia} enviando={afiliar.isPending} error={afiliar.error} onAfiliar={(datos) => afiliar.mutate(datos, { onSuccess: setInicio })} />
      )}
    </Modal>
  )
}

function ElegirAfiliacion({
  familia,
  enviando,
  error,
  onAfiliar,
}: {
  familia: FamiliaRead
  enviando: boolean
  error: Error | null
  onAfiliar: (datos: DatosAfiliacion) => void
}) {
  const especies = useEspecies()
  const activas = (familia.mascotas ?? []).filter((m) => m.activa)
  const [planes, setPlanes] = useState<Record<string, string>>({})
  const [periodicidad, setPeriodicidad] = useState<Periodicidad>('mensual')
  const peludos: PeludoElegido[] = activas.map((m) => ({ mascota_id: m.id, especie: m.especie, plan_id: planes[m.id] ?? '' }))
  const cotizacion = useCotizacion(familia.ciudad, peludos)
  const opcion = cotizacion.data?.find((c) => c.periodicidad === periodicidad)
  const nombreEspecie = (codigo: string) => especies.data?.find((e) => e.codigo === codigo)?.nombre ?? codigo

  if (activas.length === 0) {
    return <p className="apagado">La familia no tiene mascotas activas: agrégalas antes de afiliar.</p>
  }

  return (
    <form
      className="formulario"
      onSubmit={(e) => {
        e.preventDefault()
        const d = new FormData(e.currentTarget)
        onAfiliar({
          peludos: peludos.map(({ mascota_id, plan_id }) => ({ mascota_id, plan_id })),
          periodicidad,
          medio_aceptacion: String(d.get('medio_aceptacion')),
          detalle_aceptacion: String(d.get('detalle') ?? '').trim() || undefined,
        })
      }}
    >
      <fieldset className="ancho formulario">
        <legend className="ancho">Plan de cada peludo</legend>
        {activas.map((m) => (
          <ElegirPlan
            key={m.id}
            etiqueta={`${m.nombre} · ${nombreEspecie(m.especie)}`}
            ciudad={familia.ciudad}
            especie={m.especie}
            valor={planes[m.id]}
            onCambio={(planId) => setPlanes((p) => ({ ...p, [m.id]: planId }))}
          />
        ))}
      </fieldset>
      <label className="campo">
        <span>Forma de pago</span>
        <select className="input" value={periodicidad} onChange={(e) => setPeriodicidad(e.target.value as Periodicidad)}>
          {PERIODOS.map((p) => (
            <option key={p.valor} value={p.valor}>
              {p.etiqueta}
            </option>
          ))}
        </select>
      </label>
      <Resumen cargando={cotizacion.isFetching} error={cotizacion.error} opcion={opcion} peludos={activas.length} />
      <label className="campo">
        <span>Cómo aceptó las condiciones</span>
        <select className="input" name="medio_aceptacion" defaultValue="whatsapp">
          <option value="whatsapp">Por WhatsApp</option>
          <option value="llamada">En llamada</option>
          <option value="presencial">En persona</option>
        </select>
      </label>
      <label className="campo">
        <span>Soporte (quién, cuándo)</span>
        <input className="input" name="detalle" />
      </label>
      {error && (
        <p className="error ancho" role="alert">
          {mensajeError(error, 'No fue posible iniciar la afiliación.')}
        </p>
      )}
      <button className="btn btn-primario ancho" type="submit" disabled={enviando || !opcion}>
        Iniciar afiliación
      </button>
    </form>
  )
}

function Resumen({
  cargando,
  error,
  opcion,
  peludos,
}: {
  cargando: boolean
  error: Error | null
  opcion: CotizacionRead | undefined
  peludos: number
}) {
  if (error) {
    return (
      <p className="error ancho" role="alert">
        {mensajeError(error, 'No fue posible calcular el precio.')}
      </p>
    )
  }
  if (!opcion) {
    return <p className="apagado ancho">{cargando ? 'Calculando el precio…' : 'Elige el plan de cada peludo para ver el precio.'}</p>
  }
  const cada = opcion.meses === 1 ? 'al mes' : `cada ${opcion.meses} meses`
  return (
    <div className="ancho" role="status" aria-label="Precio de la afiliación">
      <p>
        <strong className="numero">{moneda(opcion.valor_periodo)}</strong> {cada}
        {opcion.descuento && <span className="apagado"> · ahorra {moneda(opcion.ahorro)}</span>}
      </p>
      {peludos > 1 && (
        <p className="apagado">
          Con {peludos} peludos cada uno paga la tarifa de {opcion.tarifa_de}, aunque estén en planes distintos
          {opcion.meses > 1 ? '; el descuento por periodo es solo para un peludo' : ''}.
        </p>
      )}
    </div>
  )
}
