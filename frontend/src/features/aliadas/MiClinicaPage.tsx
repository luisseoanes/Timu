import { useState } from 'react'

import { Icono } from '@/components/Icono'
import { MarcaTimu } from '@/features/auth/AccesoLayout'
import { useAuth } from '@/features/auth/AuthContext'
import { mensajeError } from '@/lib/errores'
import { fecha, hoyISO, moneda } from '@/lib/formato'

import { useRemisionAliada, useReportarAtencion, type RemisionAliada } from './api'

/**
 * Espacio de la clínica aliada (F2-ALI-03): valida el código de una remisión y reporta
 * la atención. Sólo ve lo necesario de la familia: titular, últimos dígitos del
 * documento y la mascota.
 */
export function MiClinicaPage() {
  const { usuario, logout } = useAuth()
  const [codigo, setCodigo] = useState('')
  const [buscado, setBuscado] = useState<string | null>(null)
  const remision = useRemisionAliada(buscado)

  return (
    <div className="publica">
      <div className="acciones" style={{ width: 'min(760px, 100%)', justifyContent: 'space-between' }}>
        <MarcaTimu />
        <div className="acciones">
          <span className="apagado">{usuario?.nombre}</span>
          <button className="btn btn-plano" type="button" onClick={logout}>
            <Icono nombre="salir" size={16} /> Salir
          </button>
        </div>
      </div>
      <section className="publica-tarjeta publica-ancha">
        <div className="ingreso-titulo">
          <h1>Validar remisión</h1>
          <p>Escribe el código que trae la familia para ver la cobertura y reportar la atención.</p>
        </div>
        <form
          className="acciones"
          onSubmit={(e) => {
            e.preventDefault()
            setBuscado(codigo.trim().toUpperCase())
          }}
        >
          <input
            className="input codigo-input"
            style={{ flex: 1 }}
            aria-label="Código de la remisión"
            value={codigo}
            onChange={(e) => setCodigo(e.target.value)}
            required
          />
          <button className="btn btn-primario btn-grande" type="submit">
            Validar
          </button>
        </form>
        {buscado && remision.isPending && <p className="apagado">Validando…</p>}
        {remision.isError && (
          <p className="aviso-error" role="alert">
            {mensajeError(remision.error, 'No encontramos esa remisión.')}
          </p>
        )}
        {remision.data && <DetalleRemision remision={remision.data} />}
      </section>
    </div>
  )
}

function DetalleRemision({ remision: r }: { remision: RemisionAliada }) {
  const reportar = useReportarAtencion(r.codigo)
  const usable = r.vigente && r.estado === 'emitida'

  return (
    <div className="pila">
      <p className={usable ? 'aviso-ok' : 'aviso-error'} role="status">
        {usable
          ? `Remisión vigente hasta el ${fecha(r.vence_en)}.`
          : r.estado === 'utilizada'
            ? 'Esta remisión ya fue utilizada.'
            : 'Esta remisión no está vigente.'}
      </p>
      <dl className="ficha">
        <div><dt>Titular</dt><dd>{r.titular}</dd></div>
        <div><dt>Documento</dt><dd className="numero">…{r.documento_ultimos}</dd></div>
        <div><dt>Mascota</dt><dd>{r.mascota.nombre} · {r.mascota.especie}</dd></div>
        <div><dt>Motivo</dt><dd>{r.motivo}</dd></div>
        <div><dt>Beneficio</dt><dd>{r.beneficio ?? '—'}</dd></div>
        <div>
          <dt>Cobertura</dt>
          <dd className="numero">
            {r.cobertura_pct}%{r.tope_cubierto ? ` hasta ${moneda(r.tope_cubierto)}` : ''}
          </dd>
        </div>
        {r.valor_cubierto && <div><dt>Cubierto</dt><dd className="numero">{moneda(r.valor_cubierto)}</dd></div>}
      </dl>
      {usable && (
        <form
          className="formulario"
          onSubmit={(e) => {
            e.preventDefault()
            const d = new FormData(e.currentTarget)
            reportar.mutate({ fecha: String(d.get('fecha')), valor_atencion: String(d.get('valor')), resumen: String(d.get('resumen')).trim() })
          }}
        >
          <label className="campo">
            <span>Fecha de la atención</span>
            <input className="input" name="fecha" type="date" max={hoyISO()} defaultValue={hoyISO()} required />
          </label>
          <label className="campo">
            <span>Valor de la atención (COP)</span>
            <input className="input" name="valor" type="number" min={0} required />
          </label>
          <label className="campo ancho">
            <span>Resumen clínico</span>
            <textarea className="input" name="resumen" rows={3} required minLength={5} />
          </label>
          {reportar.isError && (
            <p className="error ancho" role="alert">
              {mensajeError(reportar.error, 'No fue posible reportar la atención.')}
            </p>
          )}
          <button className="btn btn-primario ancho" type="submit" disabled={reportar.isPending}>
            Reportar atención
          </button>
        </form>
      )}
      {reportar.isSuccess && (
        <p className="aviso-ok" role="status">
          Atención reportada. TIMU cubre {moneda(reportar.data.valor_cubierto)}.
        </p>
      )}
    </div>
  )
}
