import { useState, type ComponentType } from 'react'
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo, Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Pestanas } from '@/components/Pestanas'
import { useAuth } from '@/features/auth'
import { RegistrarPagoModal, useEstadoCuenta } from '@/features/cartera'
import { fecha, fechaHora } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { CambioHistorial, EstacionRead, FamiliaRead, LineaFamiliaRead } from '@/types'

import { useFamilia, useHistorial, useLinea } from './api'
import { AccionesFamilia } from './AccionesFamilia'
import { CarteraFamilia } from './CarteraFamilia'
import { ComunicacionesFamilia } from './ComunicacionesFamilia'
import { ContactosFamilia } from './ContactosFamilia'
import { DatosFamilia } from './DatosFamilia'
import { DocumentosFamilia } from './DocumentosFamilia'
import { FamiliasLista } from './FamiliasLista'
import { LineaFamilia } from './LineaFamilia'
import { estacionesDelPerfil, type Parada } from './linea'
import { MascotasFamilia } from './MascotasFamilia'
import { ResumenCartera, ResumenMascotas } from './ResumenFamilia'
import { ServiciosFamilia } from './ServiciosFamilia'

/** Dónde se atiende cada tipo de estación de la línea. */
const SECCION: Record<EstacionRead['tipo'], string> = {
  cuota: 'cartera',
  preventivo: 'mascotas',
  servicio: 'servicios',
}

/** Lo que recibe quien gestiona un preventivo desde su estación. */
export interface GestionarPreventivoProps {
  familiaId: string
  /** Los preventivos pendientes de la estación: una estación junta lo del mismo día. */
  eventoIds: string[]
  onCerrar: () => void
}

/** Una familia abierta: el listado a la izquierda y su ficha con la línea a la derecha.
 * `GestionarPreventivo` lo inyecta `App.tsx` (R2-PAN-08, decidido con el usuario): agendar un
 * preventivo desde su estación sin que `familias` importe `preventivos`. */
export function FamiliaDetallePage({ GestionarPreventivo }: { GestionarPreventivo?: ComponentType<GestionarPreventivoProps> }) {
  const { id = '' } = useParams()
  return (
    <div className="con-ficha" data-abierta="true">
      <FamiliasLista seleccionada={id} />
      {/* La clave reinicia la ficha al cambiar de familia: pestaña y línea plegada vuelven al principio. */}
      <FichaFamilia key={id} id={id} GestionarPreventivo={GestionarPreventivo} />
    </div>
  )
}

function FichaFamilia({ id, GestionarPreventivo }: { id: string; GestionarPreventivo?: ComponentType<GestionarPreventivoProps> }) {
  const familia = useFamilia(id)
  const linea = useLinea(id)
  return (
    <section className="ficha-abierta" aria-label="Familia abierta">
      <Consulta consulta={familia} cargando="Cargando la familia…" error="No fue posible cargar la familia.">
        {(f) => (
          <Ficha familia={f} linea={linea.data} lineaCargando={linea.isPending} lineaError={linea.isError} GestionarPreventivo={GestionarPreventivo} />
        )}
      </Consulta>
    </section>
  )
}

function Ficha({
  familia: f,
  linea,
  lineaCargando,
  lineaError,
  GestionarPreventivo,
}: {
  familia: FamiliaRead
  linea: LineaFamiliaRead | undefined
  lineaCargando: boolean
  lineaError: boolean
  GestionarPreventivo?: ComponentType<GestionarPreventivoProps>
}) {
  const { usuario } = useAuth()
  const [params] = useSearchParams()
  const navegar = useNavigate()
  // Un enlace puede abrir la ficha en una pestaña (la bandeja de Cartera, en «cartera»).
  const pedida = (useLocation().state as { seccion?: string } | null)?.seccion
  const [seccion, setSeccion] = useState(pedida ?? 'datos')
  const [pagando, setPagando] = useState<string | null>(null)
  const [preventivo, setPreventivo] = useState<Omit<GestionarPreventivoProps, 'onCerrar'> | null>(null)
  const cuenta = useEstadoCuenta(f.id, puede(usuario, 'verCartera'))
  const abiertas = cuenta.data?.cuotas.filter((q) => q.estado !== 'pagada' && q.estado !== 'anulada') ?? []
  const planes = linea?.planes ?? []
  // Cada perfil ve sus estaciones: Operaciones no ve las cuotas, Comercial no ve los servicios.
  const estaciones = linea ? estacionesDelPerfil(linea.estaciones, usuario) : []
  const proxima = estaciones.find((e) => e.estado === 'proxima')

  /** Cómo se atiende una estación: una cuota pendiente se paga ahí mismo (si el perfil puede), un
   * preventivo pendiente se agenda ahí mismo (o se autoriza antes, si le falta), un servicio se
   * abre en su ficha y el resto lleva a su sección de la familia. */
  const accion = (e: EstacionRead): 'pagar' | 'agendar' | 'abrir' | 'ver' =>
    e.tipo === 'servicio'
      ? 'abrir'
      : e.tipo === 'cuota' && puede(usuario, 'cartera') && abiertas.some((q) => q.id === e.referencia_id)
        ? 'pagar'
        : e.tipo === 'preventivo' && GestionarPreventivo && e.estado !== 'hecha'
          ? 'agendar'
          : 'ver'
  const atender = (parada: Pick<Parada, 'estaciones'>) => {
    const [primera] = parada.estaciones
    const a = accion(primera)
    if (a === 'abrir') navegar(`/panel/servicios/${primera.referencia_id}`)
    else if (a === 'pagar') setPagando(primera.referencia_id)
    else if (a === 'agendar')
      setPreventivo({ familiaId: f.id, eventoIds: parada.estaciones.filter((e) => accion(e) === 'agendar').map((e) => e.referencia_id) })
    else setSeccion(SECCION[primera.tipo])
  }
  const VERBO = { pagar: 'Registrar pago de', agendar: 'Agendar', abrir: 'Abrir', ver: 'Ver' }

  return (
    <>
      <header className="ficha-cabeza">
        <Link to={`/panel/familias${params.toString() ? `?${params}` : ''}`} className="btn btn-plano ficha-volver" aria-label="Volver a familias">
          <Icono nombre="volver" size={16} />
        </Link>
        <h2>{f.titular_nombre}</h2>
        <div className="ficha-datos">
          {planes.map((p) => (
            <span key={p.plan_id} className="familia-fila-marcador">
              <span className="marcador-plan" data-color={p.color} aria-hidden="true" />
              {p.nombre}
            </span>
          ))}
          <Distintivo dominio="afiliacion" valor={f.estado} />
          {f.usuario_portal_id && <Insignia tono="info">Con portal</Insignia>}
          <span className="apagado">
            {f.ciudad} · {f.barrio}
          </span>
        </div>
        <div className="ficha-acciones">
          {proxima && (
            <button className="btn btn-primario" type="button" onClick={() => atender({ estaciones: [proxima] })}>
              {VERBO[accion(proxima)]} {proxima.titulo.toLowerCase()}
              {proxima.mascota ? ` de ${proxima.mascota}` : ''}
            </button>
          )}
          {puede(usuario, 'cartera') && <AccionesFamilia familia={f} />}
        </div>
      </header>
      {f.dada_de_baja_en && (
        <p className="error" role="status">
          Dada de baja el {fecha(f.dada_de_baja_en.slice(0, 10))}: {f.motivo_baja}
        </p>
      )}

      <section className="ficha-linea" aria-label="Línea de la familia">
        {lineaCargando ? (
          <div className="esqueleto" role="status">
            <span className="sr-only">Cargando la línea…</span>
            <span className="esqueleto-linea" aria-hidden="true" />
          </div>
        ) : lineaError || !linea ? (
          <p className="error">No fue posible cargar la línea de la familia.</p>
        ) : (
          <LineaFamilia estaciones={estaciones} color={planes[0]?.color} onActivar={atender} />
        )}
      </section>

      <div className="ficha-resumen">
        <ResumenMascotas familia={f} planes={planes} />
        {puede(usuario, 'verCartera') && <ResumenCartera familiaId={f.id} />}
      </div>

      <RegistrarPagoModal
        familiaId={f.id}
        cuotas={abiertas}
        cuotaId={pagando ?? undefined}
        abierto={pagando !== null}
        onCerrar={() => setPagando(null)}
      />

      {preventivo && GestionarPreventivo && <GestionarPreventivo {...preventivo} onCerrar={() => setPreventivo(null)} />}

      <Pestanas
        etiqueta="Secciones de la familia"
        valor={seccion}
        onCambio={setSeccion}
        pestanas={[
          {
            valor: 'datos',
            titulo: 'Datos',
            contenido: (
              <>
                <DatosFamilia familia={f} />
                <ContactosFamilia familia={f} />
              </>
            ),
          },
          // Cada perfil, sus pestañas (Sección 12, docs/perfiles-y-permisos.md): Atención las ve todas,
          // Comercial lo que necesita para afiliar y renovar, y Operaciones lo de la visita.
          puede(usuario, 'verCartera') && { valor: 'mascotas', titulo: 'Mascotas', contenido: <MascotasFamilia familia={f} /> },
          puede(usuario, 'verCartera') && { valor: 'cartera', titulo: 'Cartera', contenido: <CarteraFamilia familia={f} /> },
          puede(usuario, 'servicios') && { valor: 'servicios', titulo: 'Servicios', contenido: <ServiciosFamilia familia={f} /> },
          puede(usuario, 'cartera') && { valor: 'documentos', titulo: 'Documentos', contenido: <DocumentosFamilia familia={f} /> },
          puede(usuario, 'verCartera') && {
            valor: 'comunicaciones',
            titulo: 'Comunicaciones',
            contenido: <ComunicacionesFamilia familiaId={f.id} />,
          },
          puede(usuario, 'verCartera') && { valor: 'historial', titulo: 'Historial', contenido: <HistorialFamilia familiaId={f.id} /> },
        ].filter((p) => p !== false)}
      />
    </>
  )
}

const ACCIONES: Record<string, string> = {
  crear: 'Registro creado',
  editar: 'Datos editados',
  cambio_estado: 'Cambio de estado',
  eliminar: 'Registro eliminado',
}

/** Nombre legible de cada campo de la familia; uno sin nombre se muestra tal cual. */
const CAMPOS: Record<string, string> = {
  titular_nombre: 'Titular',
  tipo_documento: 'Tipo de documento',
  documento: 'Documento',
  email: 'Correo',
  telefono: 'Celular',
  ciudad: 'Ciudad',
  barrio: 'Barrio',
  direccion: 'Dirección',
  complemento: 'Complemento',
  notas: 'Notas',
  estado: 'Estado',
  latitud: 'Latitud',
  longitud: 'Longitud',
  geo_precision: 'Precisión de la ubicación',
  origen: 'Origen',
  motivo_baja: 'Motivo de la baja',
  dada_de_baja_en: 'Fecha de baja',
}

function valor(v: unknown): string {
  if (v === null || v === undefined || v === '') return 'vacío'
  return typeof v === 'object' ? JSON.stringify(v) : String(v)
}

/** Qué cambió, campo por campo. En la creación sólo se dice que se creó. */
function detalle(c: CambioHistorial): string {
  if (c.accion === 'crear' || c.accion === 'eliminar') return ''
  return Object.entries(c.cambios)
    .map(([campo, par]) => {
      const [antes, despues] = Array.isArray(par) ? par : [undefined, par]
      return `${CAMPOS[campo] ?? campo.replace(/_/g, ' ')}: ${valor(antes)} → ${valor(despues)}`
    })
    .join(' · ')
}

function HistorialFamilia({ familiaId }: { familiaId: string }) {
  const historial = useHistorial(familiaId)
  return (
    <section className="tarjeta">
      <Consulta
        consulta={historial}
        cargando="Cargando historial…"
        error="No fue posible cargar el historial."
        vacio="Sin cambios registrados."
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          // Lo más reciente primero: es lo que se viene a mirar.
          <ol className="historial" aria-label="Historial de cambios">
            {[...d]
              .sort((a, b) => b.fecha.localeCompare(a.fecha))
              .map((c, i) => (
                <li key={`${c.fecha}-${i}`}>
                  <span className="historial-fecha numero">{fechaHora(c.fecha)}</span>
                  <div>
                    <strong>{ACCIONES[c.accion] ?? c.accion}</strong>
                    {detalle(c) && <p className="apagado">{detalle(c)}</p>}
                  </div>
                </li>
              ))}
          </ol>
        )}
      </Consulta>
    </section>
  )
}
