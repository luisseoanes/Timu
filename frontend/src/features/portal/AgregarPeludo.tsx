import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Icono } from '@/components/Icono'
import { mensajeError } from '@/lib/errores'
import { fecha, hoyISO, moneda } from '@/lib/formato'
import type { AltaPeludoRead, Periodicidad } from '@/types'

import { useAgregarPeludo, useAltasPeludo, useCotizacionAlta, usePlanesAlta } from './api'

/** Solo perros y gatos (decisión de TIMU), como en el registro en línea. */
const ESPECIES = [
  { codigo: 'canino', nombre: 'Perro' },
  { codigo: 'felino', nombre: 'Gato' },
] as const
const CADA: Record<Periodicidad, string> = {
  mensual: 'al mes',
  trimestral: 'cada trimestre',
  semestral: 'cada semestre',
  anual: 'al año',
}

/**
 * 6.1 Un peludo más con el contrato vigente: la familia paga lo que queda del periodo en curso
 * con la tarifa nueva y el peludo entra al contrato cuando la pasarela aprueba el pago.
 */
export function PortalAgregarPeludo() {
  const altas = useAltasPeludo()
  const ultima = altas.data?.find((a) => a.estado !== 'cancelada')
  const esperando = ultima?.estado === 'pendiente_pago' && ultima.estado_pago === 'pendiente'
  return (
    <div className="pila">
      <div className="detalle-cabeza">
        <Link to="/portal/mascotas" className="btn btn-plano" aria-label="Volver a mis mascotas">
          <Icono nombre="volver" size={16} />
        </Link>
        <h1>Agregar un peludo</h1>
      </div>
      {ultima && <EstadoAlta alta={ultima} />}
      {!esperando && <FormularioAlta />}
    </div>
  )
}

function EstadoAlta({ alta }: { alta: AltaPeludoRead }) {
  if (alta.estado === 'pendiente_pago' && alta.estado_pago === 'pendiente') {
    return (
      <p className="aviso-ok" role="status">
        Estamos esperando la confirmación del pago para afiliar a {alta.nombre}. Esta página se actualiza sola.
      </p>
    )
  }
  if (alta.estado === 'pendiente_pago') {
    return (
      <p className="aviso-error" role="alert">
        La pasarela no aprobó el pago para afiliar a {alta.nombre}. No se hizo ningún cobro: puedes intentarlo de
        nuevo.
      </p>
    )
  }
  if (alta.estado === 'completada') {
    return (
      <p className="aviso-ok" role="status">
        <Icono nombre="check" size={16} /> {alta.nombre} ya está afiliado. <Link to="/portal/mascotas">Ver mis mascotas</Link>
      </p>
    )
  }
  return (
    <p className="aviso-ok" role="status">
      Recibimos el pago para afiliar a {alta.nombre}. Un asesor termina su afiliación y te escribe pronto.
    </p>
  )
}

function FormularioAlta() {
  const [especie, setEspecie] = useState<string>('canino')
  const [planId, setPlanId] = useState('')
  const planes = usePlanesAlta()
  const cotizacion = useCotizacionAlta(especie, planId)
  const agregar = useAgregarPeludo()
  const cot = cotizacion.data
  const delaEspecie = (planes.data ?? []).filter((p) => p.especies.length === 0 || p.especies.includes(especie))

  function enviar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    const texto = (c: string) => String(d.get(c) ?? '').trim()
    agregar.mutate(
      {
        nombre: texto('nombre'),
        especie,
        raza: texto('raza') || undefined,
        sexo: (texto('sexo') || undefined) as 'macho' | 'hembra' | undefined,
        fecha_nacimiento: texto('fecha_nacimiento'),
        peso_kg: Number(texto('peso_kg')),
        plan_id: planId,
      },
      { onSuccess: (r) => window.location.assign(r.enlace_pago) },
    )
  }

  return (
    <section className="tarjeta">
      <form className="formulario" onSubmit={enviar}>
        <label className="campo">
          <span>Nombre</span>
          <input className="input" name="nombre" required maxLength={120} />
        </label>
        <label className="campo">
          <span>Especie</span>
          <select
            className="input"
            value={especie}
            onChange={(e) => {
              setEspecie(e.target.value)
              setPlanId('')
            }}
          >
            {ESPECIES.map((e) => (
              <option key={e.codigo} value={e.codigo}>
                {e.nombre}
              </option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Raza (opcional)</span>
          <input className="input" name="raza" maxLength={80} placeholder="Criollo, mestizo…" />
        </label>
        <label className="campo">
          <span>Sexo (opcional)</span>
          <select className="input" name="sexo" defaultValue="">
            <option value="">Sin dato</option>
            <option value="hembra">Hembra</option>
            <option value="macho">Macho</option>
          </select>
        </label>
        <label className="campo">
          <span>Fecha de nacimiento (aproximada)</span>
          <input className="input" name="fecha_nacimiento" type="date" required max={hoyISO()} />
        </label>
        <label className="campo">
          <span>Peso en kg</span>
          <input className="input" name="peso_kg" type="number" required min={0.1} max={149} step={0.1} inputMode="decimal" />
        </label>
        <label className="campo ancho">
          <span>Plan</span>
          <select className="input" value={planId} required onChange={(e) => setPlanId(e.target.value)}>
            <option value="" disabled>
              {planes.isPending ? 'Cargando planes…' : 'Elige el plan'}
            </option>
            {delaEspecie.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nombre}
              </option>
            ))}
          </select>
        </label>
        {planes.isError && (
          <p className="aviso-error ancho" role="alert">
            {mensajeError(planes.error, 'No pudimos cargar los planes.')}
          </p>
        )}
        {cotizacion.isError && (
          <p className="aviso-error ancho" role="alert">
            {mensajeError(cotizacion.error, 'No pudimos calcular el valor.')}
          </p>
        )}
        {cot && (
          <p className="ancho" role="status" aria-label="Valor del peludo nuevo">
            Desde el {fecha(cot.hasta)} tu afiliación pasa de {moneda(cot.valor_periodo_actual)} a{' '}
            <strong className="numero">{moneda(cot.valor_periodo_nuevo)}</strong> {CADA[cot.periodicidad]}. Hoy pagas{' '}
            <strong className="numero">{moneda(cot.valor_ajuste)}</strong> por los días que quedan del periodo
            {cot.cuotas_adelantadas > 0 && ' y la diferencia de la próxima cuota, que ya emitimos con el valor anterior'}.
          </p>
        )}
        {agregar.isError && (
          <p className="aviso-error ancho" role="alert">
            {mensajeError(agregar.error, 'No pudimos agregar a tu peludo.')}
          </p>
        )}
        <button
          className="btn btn-primario btn-grande ancho"
          type="submit"
          disabled={!cot || agregar.isPending || agregar.isSuccess}
        >
          <Icono nombre="pago" size={18} />{' '}
          {agregar.isPending ? 'Preparando el pago…' : cot ? `Pagar ${moneda(cot.valor_ajuste)}` : 'Pagar'}
        </button>
      </form>
    </section>
  )
}
