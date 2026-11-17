import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'
import { moneda } from '@/lib/formato'
import type { CotizacionRead, Periodicidad, PlanPublico } from '@/types'

import { FichaPeludo } from './FichaPeludo'
import { MarcoRegistro } from './MarcoRegistro'
import { PagoRegistro } from './PagoRegistro'
import { Contacto } from './Contacto'
import { useCiudadesRegistro, useCotizacionRegistro, usePlanesRegistro, type PeludoRegistro } from './registro'

const MAX_PELUDOS = 10
const PELUDO_NUEVO: PeludoRegistro = { nombre: '', especie: 'canino', plan_id: '' }

/**
 * 6.1 / 6.12 Registro en línea (R3-PUB-02, «Cada peludo, su plan»): la familia arma su manada,
 * una ficha por peludo con su plan, y ve el total de la familia mientras la arma; después elige
 * cómo pagar, paga en Wompi y completa sus datos. Todo precio y toda condición salen del backend.
 */
export function RegistroPage() {
  const [ciudad, setCiudad] = useState('')
  const [confirmando, setConfirmando] = useState<string | null>(null)
  const [pagando, setPagando] = useState(false)
  const [peludos, setPeludos] = useState<PeludoRegistro[]>([PELUDO_NUEVO])
  const [periodicidad, setPeriodicidad] = useState<Periodicidad>('mensual')
  const planes = usePlanesRegistro(ciudad)
  const cotizacion = useCotizacionRegistro(
    ciudad,
    peludos.map(({ especie, plan_id }) => ({ especie, plan_id })),
  )
  const opciones = cotizacion.data ?? []
  const mensual = opciones.find((o) => o.periodicidad === 'mensual')

  const nombres = peludos.map((p) => p.nombre.trim().toLowerCase())
  const repetido = (i: number) => Boolean(nombres[i]) && nombres.indexOf(nombres[i]!) !== i
  const lista = peludos.every((p, i) => p.nombre.trim() && p.plan_id && !repetido(i))

  return (
    <>
      <MarcoRegistro
        aparte={
          <Resumen
            ciudad={ciudad}
            peludos={peludos}
            planes={planes.data ?? []}
            mensual={mensual}
            pagando={pagando}
            lista={lista}
            calculando={cotizacion.isFetching}
            onPagar={() => setPagando(true)}
          />
        }
      >
        {pagando ? (
          <PagoRegistro
            ciudad={ciudad}
            peludos={peludos}
            planes={planes.data ?? []}
            opciones={opciones}
            cargando={cotizacion.isFetching}
            error={cotizacion.error}
            periodicidad={periodicidad}
            onPeriodicidad={setPeriodicidad}
            onVolver={() => setPagando(false)}
          />
        ) : (
          <div className="registro-manada">
            <div className="registro-titulo">
              <h1>¿Quiénes se unen a la manada?</h1>
              <p>
                Plan de salud prepagado para perros y gatos. Tres pasos: tu manada, el pago y los datos de la familia.
              </p>
            </div>
            <Ciudad
              ciudad={ciudad}
              onElegir={(c) => {
                if (!ciudad) return setConfirmando(c)
                // Cada ciudad vende sus planes: los ya elegidos pueden no estar en la nueva.
                setCiudad(c)
                setPeludos(peludos.map((p) => ({ ...p, plan_id: '' })))
              }}
            />
            {ciudad && planes.isError && (
              <p className="aviso-error" role="alert">
                <Icono nombre="alerta" size={16} /> {mensajeError(planes.error, 'No pudimos cargar los planes.')}
              </p>
            )}
            {ciudad && planes.isPending && (
              <div className="esqueleto" role="status">
                <span className="sr-only">Cargando los planes de {ciudad}…</span>
                <span className="esqueleto-linea" aria-hidden="true" />
                <span className="esqueleto-linea" aria-hidden="true" />
                <span className="esqueleto-linea" aria-hidden="true" />
              </div>
            )}
            {ciudad && planes.data && (
              <>
                {peludos.map((p, i) => (
                  <FichaPeludo
                    key={i}
                    indice={i}
                    peludo={p}
                    planes={planes.data}
                    totalPeludos={peludos.length}
                    nombreRepetido={repetido(i)}
                    onCambio={(cambio) => setPeludos(peludos.map((x, j) => (j === i ? { ...x, ...cambio } : x)))}
                    onQuitar={peludos.length > 1 ? () => setPeludos(peludos.filter((_, j) => j !== i)) : undefined}
                  />
                ))}
                {peludos.length < MAX_PELUDOS && (
                  <button className="registro-otro" type="button" onClick={() => setPeludos([...peludos, PELUDO_NUEVO])}>
                    <Icono nombre="mas" size={18} /> Otro peludo
                  </button>
                )}
              </>
            )}
            <p className="registro-nota">
              ¿Ya estás afiliado? Agrega tu peludo desde <Link to="/portal/mascotas/nueva">tu portal</Link>.
            </p>
            {/* En el celular el resumen es una barra: el contacto va aquí, al final de la manada. */}
            <div className="registro-solo-celular">
              <Contacto />
            </div>
          </div>
        )}
      </MarcoRegistro>

      <Modal
        abierto={confirmando !== null}
        onCambio={(v) => !v && setConfirmando(null)}
        titulo="Antes de seguir"
        descripcion="Por ahora afiliamos solo perros y gatos."
        pie={
          <button
            className="btn btn-primario"
            type="button"
            onClick={() => {
              setCiudad(confirmando ?? '')
              setConfirmando(null)
            }}
          >
            Confirmo que solo voy a afiliar perros o gatos
          </button>
        }
      >
        <p>Si tienes otra especie, escríbenos por WhatsApp y te contamos cuándo la incluimos.</p>
      </Modal>
    </>
  )
}

/** Dónde vive la familia: de la ciudad dependen los planes y sus precios. */
function Ciudad({ ciudad, onElegir }: { ciudad: string; onElegir: (ciudad: string) => void }) {
  const ciudades = useCiudadesRegistro()
  const [elegida, setElegida] = useState(ciudad)
  const sinCobertura = elegida === 'otra'
  return (
    <div className="registro-ciudad">
      <div className="campo">
        <label htmlFor="registro-ciudad">¿En qué ciudad vives?</label>
        <select
          id="registro-ciudad"
          className="input"
          value={elegida}
          disabled={ciudades.isPending}
          onChange={(e) => {
            setElegida(e.target.value)
            if (e.target.value && e.target.value !== 'otra') onElegir(e.target.value)
          }}
        >
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
      </div>
      {ciudades.isError && (
        <p className="aviso-error" role="alert">
          <Icono nombre="alerta" size={16} /> {mensajeError(ciudades.error, 'No pudimos cargar las ciudades.')}
        </p>
      )}
      {sinCobertura && (
        <p className="aviso-alerta" role="status">
          <Icono nombre="info" size={16} />{' '}
          {/* Las ciudades salen del catálogo: sin él, no se nombran de memoria. */}
          {ciudades.data?.length
            ? `Por ahora solo atendemos en ${ciudades.data.join(' y ')}. Pronto llegaremos a más ciudades.`
            : 'Por ahora no tenemos cobertura en otras ciudades. Pronto llegaremos a más.'}
        </p>
      )}
    </div>
  )
}

/**
 * El total de la familia, que se recalcula al sumar un peludo o cambiar un plan («2 peludos ·
 * tarifa de 2»). En el celular es una barra fija abajo; en escritorio, el resumen a la derecha.
 */
function Resumen({
  ciudad,
  peludos,
  planes,
  mensual,
  pagando,
  lista,
  calculando,
  onPagar,
}: {
  ciudad: string
  peludos: PeludoRegistro[]
  planes: PlanPublico[]
  mensual: CotizacionRead | undefined
  pagando: boolean
  lista: boolean
  calculando: boolean
  onPagar: () => void
}) {
  if (!ciudad) return null
  const cuantos = `${peludos.length} ${peludos.length === 1 ? 'peludo' : 'peludos'}`
  return (
    // Pagando, el verde es «Pagar»: en el celular la manada deja de ser barra fija y va al final.
    <aside className={pagando ? 'registro-resumen registro-resumen-quieto' : 'registro-resumen'} aria-label="Tu afiliación">
      <h2 className="registro-resumen-titulo">Tu manada en {ciudad}</h2>
      <ul className="registro-resumen-lista">
        {peludos.map((p, i) => {
          const plan = planes.find((x) => x.id === p.plan_id)
          return (
            <li key={i}>
              <span className="registro-resumen-quien">{p.nombre.trim() || `Peludo ${i + 1}`}</span>
              {plan ? (
                <span className="registro-resumen-plan">
                  <span className="marcador-plan" data-color={plan.color} aria-hidden="true" />
                  {plan.nombre}
                  {mensual?.peludos[i] && <span className="numero"> · {moneda(mensual.peludos[i]!.valor_mensual)}</span>}
                </span>
              ) : (
                <span className="registro-resumen-plan apagado">Sin plan todavía</span>
              )}
            </li>
          )
        })}
      </ul>
      <p className="registro-total" aria-live="polite">
        {mensual ? (
          <>
            <span>
              {cuantos}
              {peludos.length > 1 && ` · tarifa de ${mensual.tarifa_de}`}
            </span>
            <strong className="numero">{moneda(mensual.valor_mensual)} al mes</strong>
          </>
        ) : (
          <span>{calculando ? 'Calculando…' : 'Elige un plan para cada peludo y ves el total.'}</span>
        )}
      </p>
      {!pagando && (
        <button className="btn btn-primario btn-bloque btn-grande" type="button" disabled={!lista || !mensual} onClick={onPagar}>
          Elegir cómo pagar
        </button>
      )}
      <div className="registro-confianza">
        <p className="registro-nota">
          <Icono nombre="candado" size={14} /> El pago lo procesa Wompi.
        </p>
        <Contacto />
      </div>
    </aside>
  )
}
