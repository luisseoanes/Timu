import * as Menu from '@radix-ui/react-dropdown-menu'
import type { UseQueryResult } from '@tanstack/react-query'
import { useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { useAuth, useEquipo } from '@/features/auth'
import { useCiudades, useNombreTipoServicio } from '@/features/catalogos'
import { useRutas } from '@/features/rutas'
import { descargar } from '@/lib/descargas'
import { mensajeError } from '@/lib/errores'
import { diaISO, fecha, fechaCorta, fechaCortaConDia, hora, hoyISO } from '@/lib/formato'
import { NOMBRE_ROL, puede } from '@/lib/permisos'
import type { Rol } from '@/types'

import {
  useEvolucion,
  useIndicadores,
  useMisPendientes,
  useComercialHoy,
  useProximosServicios,
  useVencidos,
  type FiltrosIndicadores,
  type GruposVencidos,
  type ValoresIndicadores,
} from './api'
import { CIFRAS, codigosDe, contraQue, ordenCifras, type CodigoCifra } from './cifras'
import { FranjaCifras } from './FranjaCifras'
import { GraficoSerie } from './GraficoSerie'
import { InicioAdmin } from './InicioAdmin'
import { LineaDelDia, type Estacion } from './LineaDelDia'
import { ReportesProgramados } from './ReportesProgramados'
import { Saludo } from './Saludo'

type Periodo = 'mes' | '30' | 'trimestre' | 'anio'

const PERIODOS: { valor: Periodo; label: string }[] = [
  { valor: 'mes', label: 'Este mes' },
  { valor: '30', label: 'Últimos 30 días' },
  { valor: 'trimestre', label: 'Últimos 90 días' },
  { valor: 'anio', label: 'Este año' },
]

function restarDias(iso: string, dias: number): string {
  const d = new Date(`${iso}T12:00:00Z`)
  d.setUTCDate(d.getUTCDate() - dias)
  return d.toISOString().slice(0, 10)
}

function rango(periodo: Periodo): { desde: string; hasta: string } {
  const hoy = hoyISO()
  if (periodo === 'mes') return { desde: `${hoy.slice(0, 8)}01`, hasta: hoy }
  if (periodo === 'anio') return { desde: `${hoy.slice(0, 4)}-01-01`, hasta: hoy }
  return { desde: restarDias(hoy, periodo === '30' ? 29 : 89), hasta: hoy }
}

function plural(n: number, uno: string, varios: string): string {
  return `${n} ${n === 1 ? uno : varios}`
}

/** Espera a varias consultas a la vez: la línea se arma con todas o avisa del fallo. */
function Todas({ consultas, cargando, error, children }: { consultas: UseQueryResult[]; cargando: string; error: string; children: () => ReactNode }) {
  const fallida = consultas.find((c) => c.isError)
  if (fallida) {
    return (
      <Consulta consulta={fallida} cargando={cargando} error={error}>
        {() => null}
      </Consulta>
    )
  }
  const pendiente = consultas.find((c) => c.isPending)
  if (pendiente) {
    return (
      <Consulta consulta={pendiente} cargando={cargando} error={error}>
        {() => null}
      </Consulta>
    )
  }
  return <>{children()}</>
}


/** Un Inicio por perfil (Sección 12, docs/perfiles-y-permisos.md): Gerencia, el tablero de la
 * Sección 8; el administrador, lo que falta configurar; el médico, su jornada; y Comercial,
 * Atención al cliente y Operaciones, la línea de hoy con solo su trabajo. */
export function DashboardPage() {
  const { usuario } = useAuth()
  // Sin saber aún quién es, no se pide nada: las cifras dependen del perfil.
  if (!usuario) return null
  if (usuario.rol === 'admin') return <InicioAdmin />
  if (usuario.rol === 'medico') return <InicioMedico />
  if (puede(usuario, 'verIndicadores')) return <InicioEquipo rol={usuario.rol} />
  return <InicioPerfil rol={usuario.rol} />
}

// --- Equipo: cifras del período y el día de la operación ---------------------------------------

function InicioEquipo({ rol }: { rol: Rol | undefined }) {
  const [periodo, setPeriodo] = useState<Periodo>('mes')
  const [ciudad, setCiudad] = useState('')
  const [abierta, setAbierta] = useState<CodigoCifra | null>(null)
  const ciudades = useCiudades()
  const filtros: FiltrosIndicadores = { ...rango(periodo), ciudad: ciudad || undefined }
  const indicadores = useIndicadores(filtros)
  // El reparto por tipo no tiene serie en el tablero: va aparte, en su propio panel.
  const evolucion = useEvolucion(filtros, codigosDe(ordenCifras(rol)))
  const [errorDescarga, setErrorDescarga] = useState<string | null>(null)

  async function exportar(formato: 'csv' | 'xlsx') {
    setErrorDescarga(null)
    try {
      await descargar('/dashboard/indicadores', { ...filtros, formato }, `indicadores.${formato}`)
    } catch (e) {
      setErrorDescarga(mensajeError(e, 'No fue posible generar el archivo.'))
    }
  }

  return (
    <div className="inicio">
      <Saludo
        resumen={`cifras del ${fechaCorta(filtros.desde)} al ${fechaCorta(filtros.hasta)}${contraQue(evolucion.data) ? `, ${contraQue(evolucion.data)}` : ''}`}
      >
        <div className="inicio-filtros">
          <select className="input" value={periodo} onChange={(e) => setPeriodo(e.target.value as Periodo)} aria-label="Período">
            {PERIODOS.map((p) => (
              <option key={p.valor} value={p.valor}>
                {p.label}
              </option>
            ))}
          </select>
          <select className="input" value={ciudad} onChange={(e) => setCiudad(e.target.value)} aria-label="Ciudad">
            <option value="">Todas las ciudades</option>
            {ciudades.data?.map((c) => (
              <option key={c.codigo} value={c.nombre}>
                {c.nombre}
              </option>
            ))}
          </select>
          <Menu.Root>
            <Menu.Trigger className="btn btn-suave">
              <Icono nombre="descargar" size={16} /> Descargar
              <Icono nombre="abajo" size={16} />
            </Menu.Trigger>
            <Menu.Portal>
              <Menu.Content className="menu" align="end" sideOffset={6}>
                <Menu.Item className="menu-item" onSelect={() => void exportar('xlsx')}>
                  Excel (.xlsx)
                </Menu.Item>
                <Menu.Item className="menu-item" onSelect={() => void exportar('csv')}>
                  CSV (.csv)
                </Menu.Item>
              </Menu.Content>
            </Menu.Portal>
          </Menu.Root>
        </div>
      </Saludo>
      {errorDescarga && (
        <p className="error" role="alert">
          {errorDescarga}
        </p>
      )}

      <div className="inicio-cifras-marco" data-cargando={indicadores.isPlaceholderData || undefined}>
        <Consulta consulta={indicadores} cargando="Calculando las cifras del período…" error="No fue posible calcular las cifras.">
          {(d) => (
            <FranjaCifras
              orden={ordenCifras(rol)}
              indicadores={d.indicadores}
              evolucion={evolucion}
              abierta={abierta}
              onAbrir={setAbierta}
            />
          )}
        </Consulta>
      </div>

      <div className="inicio-cuerpo">
        {/* Gerencia mide y no opera: en lugar del día, los reportes que recibe por correo. */}
        <ReportesProgramados />
        <div className="inicio-columna">
          {/* Sale de la misma consulta que la franja: si falla, el aviso ya está arriba. */}
          {!indicadores.isError && (
            <section className="inicio-panel" aria-labelledby="inicio-tipos-titulo">
              <h2 id="inicio-tipos-titulo" className="inicio-panel-titulo">
                Servicios completados por tipo
              </h2>
              <Consulta consulta={indicadores} cargando="Contando los servicios…" error="No fue posible contar los servicios.">
                {(d) => <ServiciosPorTipo valores={d.indicadores} />}
              </Consulta>
            </section>
          )}
          {/* Con la serie de Recaudo abierta arriba, este gráfico sería el mismo dos veces. */}
          {abierta !== 'recaudo' && (
          <section className="inicio-panel" aria-labelledby="inicio-recaudo-titulo">
            <h2 id="inicio-recaudo-titulo" className="inicio-panel-titulo">
              Recaudo contra lo facturado
            </h2>
            <Consulta consulta={evolucion} cargando="Calculando la serie…" error="No fue posible calcular la serie.">
              {(d) => (
                <GraficoSerie titulo="Recaudo contra lo facturado" meses={d.meses} series={CIFRAS.recaudo.series} escala="moneda" compacto />
              )}
            </Consulta>
          </section>
          )}
        </div>
      </div>
    </div>
  )
}

type Vencido = 'mora' | 'preventivos' | 'tareas'

/** Lo vencido que pide cada perfil: solo lo que es suyo y puede leer. */
function gruposDe(rol: Rol | undefined): GruposVencidos {
  const atencion = rol === 'atencion_cliente'
  return { mora: atencion, preventivos: atencion, tareas: rol === 'comercial' || atencion || rol === 'operaciones' }
}

const TITULO_PERFIL: Partial<Record<Rol, string>> = {
  comercial: 'Lo comercial de hoy',
  atencion_cliente: 'Hoy con las familias',
  operaciones: 'Hoy en la operación',
}

// --- Comercial, Atención al cliente y Operaciones: la línea de hoy de cada uno -------------------

function InicioPerfil({ rol }: { rol: Rol | undefined }) {
  const [abierta, setAbierta] = useState<CodigoCifra | null>(null)
  const orden = ordenCifras(rol)
  // Las cifras del mes en curso, sin filtros: quien opera mira su mes; los cortes, Gerencia.
  const filtros: FiltrosIndicadores = rango('mes')
  const indicadores = useIndicadores(filtros)
  const evolucion = useEvolucion(filtros, codigosDe(orden))
  return (
    <div className="inicio">
      <Saludo resumen={`${rol ? NOMBRE_ROL[rol] : ''} · cifras del ${fechaCorta(filtros.desde)} al ${fechaCorta(filtros.hasta)}`} />
      <div className="inicio-cifras-marco">
        <Consulta consulta={indicadores} cargando="Calculando tus cifras del mes…" error="No fue posible calcular tus cifras.">
          {(d) => (
            <FranjaCifras orden={orden} indicadores={d.indicadores} evolucion={evolucion} abierta={abierta} onAbrir={setAbierta} />
          )}
        </Consulta>
      </div>
      <section className="inicio-panel" aria-labelledby="inicio-dia-titulo">
        <h2 id="inicio-dia-titulo" className="inicio-panel-titulo">
          {(rol && TITULO_PERFIL[rol]) ?? 'Hoy'}
        </h2>
        <LineaEquipo rol={rol} />
      </section>
    </div>
  )
}

/** Cada perfil ve primero lo vencido de su área. */
function ordenVencidos(rol: Rol | undefined): Vencido[] {
  return rol === 'operaciones' ? ['preventivos', 'tareas', 'mora'] : ['mora', 'tareas', 'preventivos']
}

function LineaEquipo({ rol }: { rol: Rol | undefined }) {
  const hoy = hoyISO()
  const vencidos = useVencidos(gruposDe(rol))
  // La agenda es de Operaciones (docs/perfiles-y-permisos.md): Atención no la ve en su Inicio.
  const conServicios = rol === 'operaciones'
  const servicios = useProximosServicios(hoy, conServicios)
  const comercial = useComercialHoy(rol === 'comercial')
  const nombreTipo = useNombreTipoServicio()
  const equipo = useEquipo('medico')
  const medico = (id: string | null) => (id && equipo.data?.find((m) => m.id === id)?.nombre) || 'sin médico asignado'

  return (
    <Todas
      consultas={[vencidos, ...(conServicios ? [servicios] : []), ...(rol === 'comercial' ? [comercial] : [])]}
      cargando="Revisando el día…"
      error="No fue posible revisar el día."
    >
      {() => {
        const { mora, preventivos, tareas } = vencidos.data!
        const antes: Estacion[] = []
        const despues: Estacion[] = []
        if (comercial.data) {
          const { conversaciones, renovaciones } = comercial.data
          if (conversaciones.length > 0) {
            antes.push({
              clave: 'conversaciones',
              estado: 'vencida',
              titulo: plural(conversaciones.length, 'conversación espera a un asesor', 'conversaciones esperan a un asesor'),
              detalle: conversaciones[0].interesado_nombre ?? undefined,
              accion: { texto: 'Contestar', to: '/panel/comercial?pestana=conversaciones' },
            })
          }
          if (renovaciones.total > 0) {
            despues.push({
              clave: 'renovaciones',
              estado: 'proxima',
              titulo: plural(renovaciones.total, 'contrato por renovar', 'contratos por renovar'),
              detalle: renovaciones.primero && `El primero, ${renovaciones.primero.titular}`,
              accion: { texto: 'Ver las renovaciones', to: '/panel/cartera?vista=por_renovar' },
            })
          }
        }
        for (const clave of ordenVencidos(rol)) {
          if (clave === 'mora' && mora.total > 0) {
            antes.push({
              clave,
              estado: 'vencida',
              titulo: plural(mora.total, 'contrato en mora', 'contratos en mora'),
              detalle: mora.primero && `El más atrasado: ${mora.primero.titular}, ${plural(mora.primero.dias_mora, 'día', 'días')}`,
              accion: { texto: 'Ver la mora', to: '/panel/cartera?mora=1' },
            })
          }
          if (clave === 'tareas' && tareas.total > 0) {
            antes.push({
              clave,
              estado: 'vencida',
              titulo: plural(tareas.total, 'tarea vencida', 'tareas vencidas'),
              detalle: tareas.primero && `${tareas.primero.titulo}${tareas.primero.vence_el ? ` · venció el ${fechaCorta(tareas.primero.vence_el)}` : ''}`,
              accion: { texto: 'Ver las tareas', to: '/panel/tareas?vencidas=1' },
            })
          }
          if (clave === 'preventivos' && preventivos.total > 0) {
            // Por autorizar no es vencido mientras su fecha no haya pasado: entonces va después de hoy.
            const atrasado = Boolean(preventivos.primero && preventivos.primero.fecha_programada < hoy)
            ;(atrasado ? antes : despues).push({
              clave,
              estado: atrasado ? 'vencida' : 'proxima',
              titulo: plural(preventivos.total, 'preventivo por autorizar', 'preventivos por autorizar'),
              detalle: preventivos.primero && `El primero, programado para el ${fechaCorta(preventivos.primero.fecha_programada)}`,
              accion: { texto: 'Autorizar', to: '/panel/preventivos?autorizacion=1' },
            })
          }
        }
        const { items, total } = servicios.data ?? { items: [], total: 0 }
        const ahora = new Date().toISOString()
        const deHoy = items.filter((s) => s.programado_para && diaISO(s.programado_para) === hoy)
        // Lo agendado para hoy cuya hora ya pasó no es «lo siguiente»: va antes de Hoy, sin atender.
        const sinAtender = deHoy.filter((s) => s.programado_para! < ahora)
        if (sinAtender.length > 0) {
          antes.push({
            clave: 'sin-atender',
            estado: 'vencida',
            titulo: plural(sinAtender.length, 'servicio de hoy sin atender', 'servicios de hoy sin atender'),
            detalle: `El primero estaba para las ${hora(sinAtender[0].programado_para)}`,
            accion: { texto: 'Ver los servicios', to: '/panel/servicios' },
          })
        }
        for (const s of deHoy.filter((s) => s.programado_para! >= ahora)) {
          despues.push({
            clave: s.id,
            estado: despues.length === 0 ? 'proxima' : 'futura',
            hora: hora(s.programado_para),
            titulo: s.mascota ? `${nombreTipo(s.tipo_codigo)} · ${s.mascota.nombre}` : nombreTipo(s.tipo_codigo),
            detalle: `${s.familia.titular_nombre} · ${s.ciudad} · ${medico(s.profesional_id)}`,
            accion: { texto: 'Ver', to: `/panel/servicios/${s.id}`, secundaria: true },
          })
        }
        // Los días siguientes, uno por estación: cuántos servicios y de qué.
        const porDia = new Map<string, typeof items>()
        for (const s of items) {
          const dia = s.programado_para ? diaISO(s.programado_para) : null
          if (dia && dia > hoy) porDia.set(dia, [...(porDia.get(dia) ?? []), s])
        }
        for (const [dia, delDia] of porDia) {
          const tipos = [...new Set(delDia.map((s) => nombreTipo(s.tipo_codigo)))]
          despues.push({
            clave: dia,
            estado: despues.length === 0 ? 'proxima' : 'futura',
            hora: fechaCortaConDia(dia),
            titulo: plural(delDia.length, 'servicio agendado', 'servicios agendados'),
            detalle: tipos.join(' · '),
            accion: { texto: 'Ver la agenda', to: '/panel/servicios', secundaria: true },
          })
        }
        if (total > items.length) {
          despues.push({
            clave: 'mas-servicios',
            estado: 'futura',
            titulo: `Y ${plural(total - items.length, 'servicio agendado más', 'servicios agendados más')}`,
            accion: { texto: 'Ver la agenda', to: '/panel/servicios', secundaria: true },
          })
        }
        return (
          <LineaDelDia
            etiqueta="El día de la operación"
            hoy={hoy}
            antes={antes}
            despues={despues}
            cierre={
              !conServicios
                ? 'No hay nada más por ahora. Lo nuevo de tu área aparecerá aquí.'
                : sinAtender.length > 0
                  ? 'No hay más servicios agendados. Los que se agenden aparecerán aquí.'
                  : 'No hay servicios agendados desde hoy. Los que se agenden aparecerán aquí.'
            }
          />
        )
      }}
    </Todas>
  )
}

function ServiciosPorTipo({ valores }: { valores: ValoresIndicadores }) {
  const nombreTipo = useNombreTipoServicio()
  const tipos = Object.entries(valores.servicios_por_tipo).sort((a, b) => b[1] - a[1])
  const maximo = Math.max(1, ...tipos.map(([, n]) => n))
  if (tipos.length === 0) return <p className="apagado">Ningún servicio se completó en el período.</p>
  return (
    <ul className="inicio-barras">
      {tipos.map(([tipo, n]) => (
        <li key={tipo}>
          <span className="inicio-barra-nombre">{nombreTipo(tipo)}</span>
          <span className="inicio-barra-pista" aria-hidden="true">
            <span className="inicio-barra-valor" style={{ width: `${(n / maximo) * 100}%` }} />
          </span>
          <span className="inicio-barra-cifra numero">{n}</span>
        </li>
      ))}
    </ul>
  )
}

// --- Médico: su jornada ------------------------------------------------------------------------

function InicioMedico() {
  return (
    <div className="inicio">
      <Saludo resumen="tu jornada" />
      <div className="inicio-cuerpo">
        <section className="inicio-panel" aria-labelledby="inicio-dia-titulo">
          <h2 id="inicio-dia-titulo" className="inicio-panel-titulo">
            Tu jornada
          </h2>
          <LineaMedico />
        </section>
        <MisTareas />
      </div>
    </div>
  )
}

function LineaMedico() {
  const { usuario } = useAuth()
  const hoy = hoyISO()
  const pendientes = useMisPendientes()
  const rutas = useRutas(hoy, { responsable: usuario?.id })
  const nombreTipo = useNombreTipoServicio()

  return (
    <Todas consultas={[pendientes, rutas]} cargando="Revisando tu jornada…" error="No fue posible revisar tu jornada.">
      {() => {
        const { borradores, vencidas } = pendientes.data!
        const antes: Estacion[] = []
        if (borradores.length > 0) {
          const antigua = borradores.map((b) => b.fecha).sort()[0]
          antes.push({
            clave: 'borradores',
            estado: 'vencida',
            titulo: plural(borradores.length, 'consulta sin firmar', 'consultas sin firmar'),
            detalle: `La más antigua es del ${fechaCorta(antigua)}`,
            accion: { texto: 'Firmar las consultas', to: '/panel/clinica' },
          })
        }
        if (vencidas.total > 0) {
          antes.push({
            clave: 'tareas',
            estado: 'vencida',
            titulo: plural(vencidas.total, 'tarea vencida', 'tareas vencidas'),
            detalle: vencidas.primero?.titulo,
            accion: { texto: 'Ver las tareas', to: '/panel/tareas?vencidas=1' },
          })
        }
        const paradas = (rutas.data ?? [])
          .filter((r) => r.estado !== 'cancelada')
          .flatMap((r) => r.paradas)
          .sort((a, b) => a.orden - b.orden)
        const faltan = paradas.filter((p) => p.estado !== 'completada' && p.estado !== 'omitida')
        const despues: Estacion[] = faltan.map((p, i) => ({
          clave: p.id,
          estado: i === 0 ? 'proxima' : 'futura',
          hora: p.llegada_estimada ? hora(p.llegada_estimada) : undefined,
          titulo: p.mascota ? `${nombreTipo(p.tipo_codigo)} · ${p.mascota.nombre}` : nombreTipo(p.tipo_codigo),
          detalle: [p.familia.titular_nombre, p.familia.barrio ?? p.familia.direccion].filter(Boolean).join(' · '),
          accion: i === 0 ? { texto: 'Abrir mi ruta', to: '/panel/rutas' } : undefined,
        }))
        const hechas = paradas.length - faltan.length
        return (
          <LineaDelDia
            etiqueta="Tu jornada"
            hoy={hoy}
            antes={antes}
            despues={despues}
            cierre={
              paradas.length === 0
                ? 'No tienes ruta para hoy. Si te asignan una, sus paradas aparecerán aquí.'
                : `Terminaste tu ruta de hoy: ${plural(hechas, 'parada atendida', 'paradas atendidas')}.`
            }
          />
        )
      }}
    </Todas>
  )
}

function MisTareas() {
  const pendientes = useMisPendientes()
  return (
    <section className="inicio-panel" aria-labelledby="inicio-tareas-titulo">
      <div className="inicio-panel-cabeza">
        <h2 id="inicio-tareas-titulo" className="inicio-panel-titulo">
          Tus tareas abiertas
        </h2>
        <Link to="/panel/tareas">Ver todas</Link>
      </div>
      <Consulta
        consulta={pendientes}
        cargando="Cargando tus tareas…"
        error="No fue posible cargar tus tareas."
        vacio="No tienes tareas abiertas. Las que te asignen aparecerán aquí."
        estaVacio={(d) => d.abiertas.items.length === 0}
      >
        {(d) => (
          <ul className="inicio-tareas">
            {d.abiertas.items.map((t) => (
              <li key={t.id}>
                <div>
                  <strong>{t.titulo}</strong>
                  <span>{t.vence_el ? `Vence el ${fecha(t.vence_el)}` : 'Sin fecha límite'}</span>
                </div>
                <Distintivo dominio="prioridad" valor={t.prioridad} />
              </li>
            ))}
          </ul>
        )}
      </Consulta>
    </section>
  )
}
