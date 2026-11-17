import { isAxiosError } from 'axios'
import { useEffect, useRef, useState } from 'react'

import { Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { esErrorPasajero, mensajeError } from '@/lib/errores'
import { fechaCompacta, moneda } from '@/lib/formato'
import type { RemisionVistaAliada } from '@/types'

import { useCoberturaAliada, useRemisionAliada, useReportarAtencion } from './api'
import { cobertura } from './remision'

const MILES = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 })

/** El valor tras una pausa al escribir: la vista previa de la cobertura no pide una cifra por tecla. */
function useRetrasado(valor: string, ms: number): string {
  const [retrasado, setRetrasado] = useState(valor)
  useEffect(() => {
    const t = setTimeout(() => setRetrasado(valor), ms)
    return () => clearTimeout(t)
  }, [valor, ms])
  return retrasado
}

/** El mostrador: el código que trae la familia y, debajo, la remisión que abre. */
export function ValidarRemision() {
  const [codigo, setCodigo] = useState('')
  const [buscado, setBuscado] = useState<string | null>(null)
  const campo = useRef<HTMLInputElement>(null)
  const remision = useRemisionAliada(buscado)
  // Con una remisión que se puede usar, el verde es reportar la atención.
  const usable = remision.data?.vigente === true

  return (
    <section className="aliada-panel aliada-validar" aria-labelledby="aliada-validar-titulo">
      <h1 id="aliada-validar-titulo">Validar una remisión</h1>
      <form
        className="aliada-codigo"
        onSubmit={(e) => {
          e.preventDefault()
          setBuscado(codigo.trim().toUpperCase())
        }}
      >
        <label className="campo">
          <span>Código de la remisión</span>
          <input
            ref={campo}
            className="input codigo-input"
            value={codigo}
            onChange={(e) => setCodigo(e.target.value)}
            aria-describedby="aliada-codigo-ayuda"
            autoComplete="off"
            autoCapitalize="characters"
            spellCheck={false}
            maxLength={12}
            required
          />
        </label>
        <button className={`btn ${usable ? 'btn-secundario' : 'btn-primario'}`} type="submit">
          Validar
        </button>
        <span id="aliada-codigo-ayuda" className="campo-ayuda">
          El que trae la familia. Da igual en mayúsculas o en minúsculas.
        </span>
      </form>

      {buscado && remision.isPending && (
        <div className="esqueleto" role="status">
          <span className="sr-only">Validando la remisión…</span>
          <span className="esqueleto-linea" aria-hidden="true" />
          <span className="esqueleto-linea" aria-hidden="true" />
          <span className="esqueleto-linea" aria-hidden="true" />
        </div>
      )}
      {remision.isError && <ErrorRemision error={remision.error} codigo={buscado ?? ''} reintentar={() => void remision.refetch()} />}
      {remision.data && (
        <FichaRemision
          key={remision.data.codigo}
          r={remision.data}
          // Reportada, el mostrador queda listo para la siguiente familia.
          alReportar={() => {
            setCodigo('')
            campo.current?.focus()
          }}
        />
      )}
    </section>
  )
}

function ErrorRemision({ error, codigo, reintentar }: { error: unknown; codigo: string; reintentar: () => void }) {
  if (isAxiosError(error) && error.response?.status === 404) {
    return (
      <div className="aviso-error" role="alert">
        <Icono nombre="alerta" size={16} />
        <p>
          No encontramos la remisión <strong className="numero">{codigo}</strong> en esta clínica. Revisa el código con la
          familia: si está bien escrito, la remisión es de otra clínica o TIMU no la ha emitido.
        </p>
      </div>
    )
  }
  return (
    <div className="aviso-error consulta-error" role="alert">
      <p>No pudimos validar la remisión. {mensajeError(error, 'Intenta de nuevo en un momento.')}</p>
      {esErrorPasajero(error) && (
        <button className="btn btn-secundario" type="button" onClick={reintentar}>
          Reintentar
        </button>
      )}
    </div>
  )
}

/** Si la remisión sirve, en palabras: con qué estado y qué significa para quien atiende. */
function EstadoRemision({ r }: { r: RemisionVistaAliada }) {
  if (r.vigente) {
    return (
      <>
        <Insignia tono="ok">Por usar</Insignia>
        <span>Se puede atender hasta el {fechaCompacta(r.vence_en)}.</span>
      </>
    )
  }
  if (r.vencida) {
    return (
      <>
        <Insignia tono="peligro" icono="alerta">
          Vencida
        </Insignia>
        <span>Venció el {fechaCompacta(r.vence_en)} y ya no se puede usar. La familia puede pedirle una nueva a TIMU.</span>
      </>
    )
  }
  if (r.estado === 'utilizada' && r.fecha_atencion) {
    return (
      <>
        <Insignia tono="neutro" icono="check">
          Atendida
        </Insignia>
        <span>Ya se reportó: la atención fue el {fechaCompacta(r.fecha_atencion)}.</span>
      </>
    )
  }
  return (
    <>
      <Insignia tono="neutro">Anulada</Insignia>
      <span>TIMU la anuló y ya no se puede usar.</span>
    </>
  )
}

function FichaRemision({ r, alReportar }: { r: RemisionVistaAliada; alReportar: () => void }) {
  const mascota = [r.mascota.especie_nombre, r.mascota.raza].filter(Boolean).join(', ')
  // Vencida y sin usar, una atención hecha dentro de su vigencia se reporta después; el formulario
  // no queda abierto invitando a reportar: se abre a propósito.
  const [tarde, setTarde] = useState(false)
  return (
    <article className="aliada-remision" aria-labelledby="aliada-remision-mascota">
      <p className="aliada-remision-estado" role="status">
        <EstadoRemision r={r} />
      </p>
      <div className="aliada-remision-quien">
        <h2 id="aliada-remision-mascota">
          {r.mascota.nombre} <span>· {mascota}</span>
        </h2>
        <p>
          {r.titular}, <span className="sin-cortes">documento terminado en <span className="numero">{r.documento_ultimos}</span></span>
        </p>
      </div>
      <dl className="ficha">
        <div className="ancho">
          <dt>Motivo</dt>
          <dd>{r.motivo}</dd>
        </div>
        <div>
          <dt>Beneficio</dt>
          <dd>{r.beneficio ?? '—'}</dd>
        </div>
        <div>
          <dt>Cobertura</dt>
          <dd className="numero">{cobertura(r)}</dd>
        </div>
        <div>
          <dt>Código</dt>
          <dd className="numero">{r.codigo}</dd>
        </div>
      </dl>
      {r.estado === 'utilizada' && r.valor_atencion && r.valor_cubierto && r.valor_familia && (
        <section className="aliada-cubre aliada-reportado" aria-labelledby="aliada-reportado-titulo">
          <h3 id="aliada-reportado-titulo">Lo que se reportó</h3>
          <Reparto atencion={r.valor_atencion} cubierto={r.valor_cubierto} familia={r.valor_familia} hecho />
        </section>
      )}
      {r.vencida && r.atencion_hasta && !tarde && (
        <div className="aliada-tarde">
          <button className="btn btn-plano btn-accion" type="button" onClick={() => setTarde(true)}>
            Reportar una atención hecha hasta el {fechaCompacta(r.atencion_hasta)}
          </button>
        </div>
      )}
      {(r.vigente || (tarde && r.atencion_hasta)) && <ReportarAtencion r={r} alReportar={alReportar} principal={r.vigente} />}
    </article>
  )
}

/** Cómo se reparte una atención: lo que cubre TIMU y lo que paga la familia (en pasado si ya se
 * reportó). */
function Reparto({
  atencion,
  cubierto,
  familia,
  hecho = false,
}: {
  atencion?: string
  cubierto: string
  familia: string
  hecho?: boolean
}) {
  return (
    <dl className="aliada-cifras">
      {atencion && (
        <div>
          <dt>Valor de la atención</dt>
          <dd className="numero">{moneda(atencion)}</dd>
        </div>
      )}
      <div>
        <dt>{hecho ? 'TIMU cubrió' : 'TIMU cubre'}</dt>
        <dd className="numero">{moneda(cubierto)}</dd>
      </div>
      <div>
        <dt>{hecho ? 'Pagó la familia' : 'Paga la familia'}</dt>
        <dd className="numero">{moneda(familia)}</dd>
      </div>
    </dl>
  )
}

function ReportarAtencion({
  r,
  alReportar,
  principal,
}: {
  r: RemisionVistaAliada
  alReportar: () => void
  /** Con la remisión vigente, reportar es el verde de la vista; con una vencida, «Validar» lo sigue siendo. */
  principal: boolean
}) {
  const [valor, setValor] = useState('')
  const consultado = useRetrasado(valor, 300)
  const cubre = useCoberturaAliada(r.codigo, Number(consultado) > 0 ? consultado : null)
  const reportar = useReportarAtencion(r.codigo, alReportar)
  const vista = valor && cubre.data && cubre.data.valor_atencion.split('.')[0] === valor ? cubre.data : null

  return (
    <form
      className="formulario aliada-reporte"
      aria-labelledby="aliada-reporte-titulo"
      onSubmit={(e) => {
        e.preventDefault()
        const d = new FormData(e.currentTarget)
        reportar.mutate({ fecha: String(d.get('fecha')), valor_atencion: valor, resumen: String(d.get('resumen')).trim() })
      }}
    >
      <h3 id="aliada-reporte-titulo" className="ancho">
        Reportar la atención
      </h3>
      <label className="campo">
        <span>Fecha de la atención</span>
        <input
          className="input"
          name="fecha"
          type="date"
          min={r.atencion_desde ?? undefined}
          max={r.atencion_hasta ?? undefined}
          defaultValue={r.atencion_hasta ?? undefined}
          autoFocus={!principal}
          required
        />
      </label>
      <div className="campo">
        <label htmlFor="aliada-valor">Valor de la atención</label>
        <input
          id="aliada-valor"
          className="input numero"
          inputMode="numeric"
          autoComplete="off"
          placeholder="$ 0"
          value={valor ? `$ ${MILES.format(Number(valor))}` : ''}
          onChange={(e) => setValor(e.target.value.replace(/\D/g, '').replace(/^0+/, '').slice(0, 10))}
          aria-describedby="aliada-valor-ayuda"
          required
        />
        <span id="aliada-valor-ayuda" className="campo-ayuda">
          Lo que la clínica factura por esta atención, en pesos.
        </span>
      </div>
      <div className="ancho aliada-cubre" aria-live="polite">
        {vista ? (
          <>
            <Reparto cubierto={vista.valor_cubierto} familia={vista.valor_familia} />
            {vista.con_tope && r.tope_cubierto && (
              <p className="aliada-nota">Llega al tope de {moneda(r.tope_cubierto)} de esta remisión: el resto lo paga la familia.</p>
            )}
          </>
        ) : cubre.isError && valor ? (
          <p className="aliada-nota">No pudimos calcular la cobertura. {mensajeError(cubre.error, 'Intenta de nuevo en un momento.')}</p>
        ) : (
          <p className="aliada-nota">
            {valor ? 'Calculando cuánto cubre TIMU…' : 'Escribe el valor para ver cuánto cubre TIMU y cuánto le cobras a la familia.'}
          </p>
        )}
      </div>
      <div className="campo ancho">
        <label htmlFor="aliada-resumen">Resumen clínico</label>
        <textarea id="aliada-resumen" className="input" name="resumen" rows={3} required minLength={5} maxLength={4000} aria-describedby="aliada-resumen-ayuda" />
        <span id="aliada-resumen-ayuda" className="campo-ayuda">
          Qué se le hizo a {r.mascota.nombre} y qué se encontró. Lo lee el equipo de TIMU.
        </span>
      </div>
      {reportar.isError && (
        <p className="error ancho" role="alert">
          {mensajeError(reportar.error, 'No fue posible reportar la atención.')}
        </p>
      )}
      <div className="ancho aliada-reporte-pie">
        <button className={`btn ${principal ? 'btn-primario' : 'btn-secundario'}`} type="submit" disabled={reportar.isPending}>
          {reportar.isPending ? 'Reportando…' : 'Reportar atención'}
        </button>
      </div>
    </form>
  )
}
