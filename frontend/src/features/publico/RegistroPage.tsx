import { useState } from 'react'

import { Icono } from '@/components/Icono'
import { MarcaTimu } from '@/components/MarcaTimu'
import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'
import { moneda } from '@/lib/formato'
import type { CotizacionRead, Periodicidad, PlanPublico } from '@/types'

import {
  ESPECIES_REGISTRO,
  guardarToken,
  useCiudadesRegistro,
  useCotizacionRegistro,
  useIniciarRegistro,
  usePlanesRegistro,
  type PeludoRegistro,
} from './registro'

const MAX_PELUDOS = 10
const PERIODOS: Record<Periodicidad, string> = {
  mensual: 'Mensual',
  trimestral: 'Trimestral',
  semestral: 'Semestral',
  anual: 'Anual',
}
const nombreEspecie = (codigo: string) => ESPECIES_REGISTRO.find((e) => e.codigo === codigo)?.nombre ?? codigo

type Paso = 'ciudad' | 'peludos' | 'planes' | 'pago'

/**
 * 6.1 Registro en línea: ciudad, peludos, un plan para cada uno, forma de pago y pago. Los
 * datos de la familia se piden después del pago. Todo precio sale del backend.
 */
export function RegistroPage() {
  const [paso, setPaso] = useState<Paso>('ciudad')
  const [ciudad, setCiudad] = useState('')
  const [confirmando, setConfirmando] = useState(false)
  const [peludos, setPeludos] = useState<PeludoRegistro[]>([{ nombre: '', especie: 'canino', plan_id: '' }])
  const [periodicidad, setPeriodicidad] = useState<Periodicidad>('mensual')
  const cotizacion = useCotizacionRegistro(
    ciudad,
    peludos.map(({ especie, plan_id }) => ({ especie, plan_id })),
  )
  const opciones = cotizacion.data ?? []
  const elegida = opciones.find((o) => o.periodicidad === periodicidad)

  return (
    <div className="publica">
      <MarcaTimu />
      <section className="publica-tarjeta publica-ancha">
        <div className="ingreso-titulo">
          <h1>Afilia a tus peludos</h1>
          <p>Consultas a domicilio, preventivos y orientación virtual. Al final pagas en línea y completas tus datos.</p>
        </div>
        {paso === 'ciudad' && (
          <PasoCiudad
            ciudad={ciudad}
            onElegir={(c) => {
              setCiudad(c)
              setConfirmando(true)
            }}
          />
        )}
        {paso === 'peludos' && (
          <PasoPeludos
            peludos={peludos}
            onCambio={setPeludos}
            onAtras={() => setPaso('ciudad')}
            onSeguir={() => setPaso('planes')}
          />
        )}
        {paso === 'planes' && (
          <PasoPlanes
            ciudad={ciudad}
            peludos={peludos}
            cotizacion={opciones.find((o) => o.periodicidad === 'mensual')}
            onCambio={setPeludos}
            onAtras={() => setPaso('peludos')}
            onSeguir={() => setPaso('pago')}
          />
        )}
        {paso === 'pago' && (
          <PasoPago
            ciudad={ciudad}
            peludos={peludos}
            opciones={opciones}
            cargando={cotizacion.isFetching}
            error={cotizacion.error}
            periodicidad={periodicidad}
            elegida={elegida}
            onPeriodicidad={setPeriodicidad}
            onAtras={() => setPaso('planes')}
          />
        )}
      </section>
      <Modal
        abierto={confirmando}
        onCambio={(v) => !v && setConfirmando(false)}
        titulo="Antes de seguir"
        descripcion="Por ahora afiliamos solo perros y gatos."
        pie={
          <button
            className="btn btn-primario"
            type="button"
            onClick={() => {
              setConfirmando(false)
              setPaso('peludos')
            }}
          >
            Confirmo que solo voy a afiliar perros o gatos
          </button>
        }
      >
        <p>Si tienes otra especie, escríbenos por WhatsApp y te contamos cuándo la incluimos.</p>
      </Modal>
    </div>
  )
}

function PasoCiudad({ ciudad, onElegir }: { ciudad: string; onElegir: (ciudad: string) => void }) {
  const ciudades = useCiudadesRegistro()
  const [elegida, setElegida] = useState(ciudad)
  const sinCobertura = elegida === 'otra'
  return (
    <form
      className="formulario"
      onSubmit={(e) => {
        e.preventDefault()
        if (elegida && !sinCobertura) onElegir(elegida)
      }}
    >
      <label className="campo ancho">
        <span>¿En qué ciudad vives?</span>
        <select className="input" value={elegida} onChange={(e) => setElegida(e.target.value)} required disabled={ciudades.isPending}>
          <option value="" disabled>
            {ciudades.isPending ? 'Cargando ciudades…' : 'Elige tu ciudad'}
          </option>
          {ciudades.data?.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
          <option value="otra">Otra ciudad</option>
        </select>
      </label>
      {ciudades.isError && (
        <p className="aviso-error ancho" role="alert">
          {mensajeError(ciudades.error, 'No pudimos cargar las ciudades.')}
        </p>
      )}
      {sinCobertura && (
        <p className="aviso-error ancho" role="status">
          Por ahora solo atendemos en {ciudades.data?.join(' y ') || 'Medellín y Bogotá'}. Pronto llegaremos a más ciudades.
        </p>
      )}
      <button className="btn btn-primario btn-grande ancho" type="submit" disabled={!elegida || sinCobertura}>
        Continuar
      </button>
    </form>
  )
}

function PasoPeludos({
  peludos,
  onCambio,
  onAtras,
  onSeguir,
}: {
  peludos: PeludoRegistro[]
  onCambio: (peludos: PeludoRegistro[]) => void
  onAtras: () => void
  onSeguir: () => void
}) {
  const cambiar = (i: number, cambio: Partial<PeludoRegistro>) =>
    onCambio(peludos.map((p, j) => (j === i ? { ...p, ...cambio, plan_id: cambio.especie ? '' : p.plan_id } : p)))
  const nombres = peludos.map((p) => p.nombre.trim().toLowerCase())
  const repetido = nombres.some((n, i) => n && nombres.indexOf(n) !== i)
  return (
    <form
      className="formulario"
      onSubmit={(e) => {
        e.preventDefault()
        if (!repetido) onSeguir()
      }}
    >
      <p className="ancho">¿A quiénes vas a afiliar? El nombre nos ayuda a saber qué plan es de quién.</p>
      {peludos.map((p, i) => (
        <fieldset key={i} className="ancho formulario">
          <legend className="ancho">Peludo {i + 1}</legend>
          <label className="campo">
            <span>Nombre</span>
            <input className="input" value={p.nombre} onChange={(e) => cambiar(i, { nombre: e.target.value })} required maxLength={120} />
          </label>
          <label className="campo">
            <span>Especie</span>
            <select className="input" value={p.especie} onChange={(e) => cambiar(i, { especie: e.target.value })}>
              {ESPECIES_REGISTRO.map((e) => (
                <option key={e.codigo} value={e.codigo}>
                  {e.nombre}
                </option>
              ))}
            </select>
          </label>
          {peludos.length > 1 && (
            <button className="btn btn-plano" type="button" onClick={() => onCambio(peludos.filter((_, j) => j !== i))}>
              Quitar
            </button>
          )}
        </fieldset>
      ))}
      {repetido && (
        <p className="aviso-error ancho" role="alert">
          Cada peludo necesita un nombre distinto.
        </p>
      )}
      <div className="acciones ancho">
        <button className="btn btn-plano" type="button" onClick={onAtras}>
          Atrás
        </button>
        {peludos.length < MAX_PELUDOS && (
          <button
            className="btn btn-suave"
            type="button"
            onClick={() => onCambio([...peludos, { nombre: '', especie: 'canino', plan_id: '' }])}
          >
            <Icono nombre="mas" size={16} /> Otro peludo
          </button>
        )}
        <button className="btn btn-primario" type="submit">
          Elegir planes
        </button>
      </div>
    </form>
  )
}

function PasoPlanes({
  ciudad,
  peludos,
  cotizacion,
  onCambio,
  onAtras,
  onSeguir,
}: {
  ciudad: string
  peludos: PeludoRegistro[]
  cotizacion: CotizacionRead | undefined
  onCambio: (peludos: PeludoRegistro[]) => void
  onAtras: () => void
  onSeguir: () => void
}) {
  const planes = usePlanesRegistro(ciudad)
  const paraEspecie = (especie: string): PlanPublico[] =>
    (planes.data ?? []).filter((p) => p.especies.length === 0 || p.especies.includes(especie))
  const completos = peludos.every((p) => p.plan_id)
  return (
    <form
      className="formulario"
      onSubmit={(e) => {
        e.preventDefault()
        if (completos) onSeguir()
      }}
    >
      {planes.isError && (
        <p className="aviso-error ancho" role="alert">
          {mensajeError(planes.error, 'No pudimos cargar los planes.')}
        </p>
      )}
      {peludos.map((p, i) => (
        <label key={i} className="campo ancho">
          <span>
            {p.nombre} · {nombreEspecie(p.especie)}
            {cotizacion?.peludos[i] && ` · ${moneda(cotizacion.peludos[i]!.valor_mensual)} al mes`}
          </span>
          <select
            className="input"
            value={p.plan_id}
            required
            onChange={(e) => onCambio(peludos.map((x, j) => (j === i ? { ...x, plan_id: e.target.value } : x)))}
          >
            <option value="" disabled>
              {planes.isPending ? 'Cargando planes…' : 'Elige el plan'}
            </option>
            {paraEspecie(p.especie).map((plan) => (
              <option key={plan.id} value={plan.id}>
                {plan.nombre} · desde {moneda(plan.tarifas.find((t) => t.peludos === 1)?.valor)} al mes
              </option>
            ))}
          </select>
        </label>
      ))}
      {peludos.length > 1 && cotizacion && (
        <p className="apagado ancho">
          Con {peludos.length} peludos cada uno paga la tarifa de {cotizacion.tarifa_de}, aunque estén en planes
          distintos.
        </p>
      )}
      <div className="acciones ancho">
        <button className="btn btn-plano" type="button" onClick={onAtras}>
          Atrás
        </button>
        <button className="btn btn-primario" type="submit" disabled={!completos}>
          Elegir forma de pago
        </button>
      </div>
    </form>
  )
}

function PasoPago({
  ciudad,
  peludos,
  opciones,
  cargando,
  error,
  periodicidad,
  elegida,
  onPeriodicidad,
  onAtras,
}: {
  ciudad: string
  peludos: PeludoRegistro[]
  opciones: CotizacionRead[]
  cargando: boolean
  error: Error | null
  periodicidad: Periodicidad
  elegida: CotizacionRead | undefined
  onPeriodicidad: (periodicidad: Periodicidad) => void
  onAtras: () => void
}) {
  const iniciar = useIniciarRegistro()

  function enviar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    const texto = (c: string) => String(d.get(c) ?? '').trim()
    iniciar.mutate(
      {
        ciudad,
        peludos: peludos.map((p) => ({ ...p, nombre: p.nombre.trim() })),
        periodicidad,
        contacto: {
          nombre: texto('contacto_nombre'),
          telefono: texto('contacto_telefono'),
          email: texto('contacto_email'),
        },
        acepta_condiciones: d.get('acepta_condiciones') === 'on',
        acepta_tratamiento_datos: d.get('acepta_datos') === 'on',
        sitio_web: texto('sitio_web') || undefined,
      },
      {
        onSuccess: (r) => {
          guardarToken(r.token)
          window.location.assign(r.enlace_pago)
        },
      },
    )
  }

  return (
    <form className="formulario" onSubmit={enviar}>
      {error && (
        <p className="aviso-error ancho" role="alert">
          {mensajeError(error, 'No pudimos calcular el precio.')}
        </p>
      )}
      {!error && opciones.length === 0 && (
        <p className="apagado ancho">{cargando ? 'Calculando el precio…' : 'Elige el plan de cada peludo.'}</p>
      )}
      {opciones.length > 0 && (
        <fieldset className="ancho formulario">
          <legend className="ancho">¿Cada cuánto quieres pagar?</legend>
          {opciones.map((o) => (
            <label key={o.periodicidad} className="ancho acciones">
              <input
                type="radio"
                name="periodicidad"
                value={o.periodicidad}
                checked={periodicidad === o.periodicidad}
                onChange={() => onPeriodicidad(o.periodicidad)}
              />
              {PERIODOS[o.periodicidad]}: <strong className="numero">{moneda(o.valor_periodo)}</strong>
              {o.meses === 1 ? ' al mes' : ` cada ${o.meses} meses`}
              {o.descuento && <span className="apagado"> · ahorras {moneda(o.ahorro)}</span>}
            </label>
          ))}
        </fieldset>
      )}
      {elegida && (
        <ul className="ancho" aria-label="Resumen de la afiliación">
          {peludos.map((p, i) => (
            <li key={i}>
              {p.nombre.trim()} · {elegida.peludos[i]?.plan_nombre} · {moneda(elegida.peludos[i]?.valor_mensual)} al
              mes
            </li>
          ))}
        </ul>
      )}
      <fieldset className="ancho formulario">
        <legend className="ancho">¿A quién le enviamos el comprobante?</legend>
        <label className="campo ancho">
          <span>Tu nombre</span>
          <input className="input" name="contacto_nombre" required minLength={2} maxLength={160} autoComplete="name" />
        </label>
        <label className="campo">
          <span>Celular (WhatsApp)</span>
          <input className="input" name="contacto_telefono" required inputMode="tel" autoComplete="tel" />
        </label>
        <label className="campo">
          <span>Correo</span>
          <input className="input" name="contacto_email" type="email" required autoComplete="email" />
        </label>
        <p className="apagado ancho">
          Después del pago te pedimos los datos de la familia. Si cierras el navegador, te enviamos el enlace por
          correo y WhatsApp.
        </p>
      </fieldset>
      {/* Trampa para bots: invisible y fuera del orden de tabulación. */}
      <input name="sitio_web" tabIndex={-1} autoComplete="off" className="sr-only" aria-hidden="true" />
      <label className="ancho acciones">
        <input type="checkbox" name="acepta_condiciones" required />
        Acepto las condiciones de los planes y del contrato de afiliación.
      </label>
      <label className="ancho acciones">
        <input type="checkbox" name="acepta_datos" required />
        Autorizo el tratamiento de mis datos personales según la Ley 1581 de 2012.
      </label>
      {iniciar.isError && (
        <p className="aviso-error ancho" role="alert">
          {mensajeError(iniciar.error, 'No pudimos iniciar la afiliación.')}
        </p>
      )}
      {iniciar.isSuccess && (
        <p className="aviso-ok ancho" role="status">
          Te llevamos a la pasarela para pagar {moneda(iniciar.data.valor)}…
        </p>
      )}
      <div className="acciones ancho">
        <button className="btn btn-plano" type="button" onClick={onAtras}>
          Atrás
        </button>
        <button
          className="btn btn-primario btn-grande"
          type="submit"
          disabled={!elegida || iniciar.isPending || iniciar.isSuccess}
        >
          <Icono nombre="pago" size={18} />{' '}
          {iniciar.isPending ? 'Registrando…' : elegida ? `Pagar ${moneda(elegida.valor_periodo)}` : 'Pagar'}
        </button>
      </div>
    </form>
  )
}
