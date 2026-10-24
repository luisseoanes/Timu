import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono, type NombreIcono } from '@/components/Icono'
import { useAuth } from '@/features/auth/AuthContext'
import { useCiudades } from '@/features/catalogos/api'
import { descargar } from '@/lib/descargas'
import { mensajeError } from '@/lib/errores'
import { fecha, fechaHora, hoyISO, moneda, porcentaje } from '@/lib/formato'
import { puede } from '@/lib/permisos'

import {
  useAlertas,
  useDefiniciones,
  useIndicadores,
  useMisTareas,
  useProximosServicios,
  type FiltrosIndicadores,
  type Indicadores,
} from './api'

const ACCESOS: { icono: NombreIcono; label: string; to: string }[] = [
  { icono: 'servicios', label: 'Agendar servicio', to: '/servicios?nuevo=1' },
  { icono: 'clinica', label: 'Historia clínica', to: '/clinica' },
  { icono: 'rutas', label: 'Rutas del día', to: '/rutas' },
  { icono: 'familias', label: 'Familias', to: '/familias' },
]

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

export function DashboardPage() {
  const { usuario } = useAuth()
  const nombre = usuario?.nombre?.split(' ')[0] ?? ''
  const gerencial = puede(usuario, 'verIndicadores')

  return (
    <div className="con-rail">
      <div className="pila">
        <section className="bienvenida">
          <h1>Hola {nombre}</h1>
          <p className="apagado">
            {gerencial
              ? 'Así va la operación: afiliaciones, recaudo, rutas y satisfacción del período.'
              : 'Tu jornada: próximas visitas y las tareas que tienes asignadas.'}
          </p>
        </section>

        <nav className="accesos" aria-label="Accesos rápidos">
          {ACCESOS.map((a) => (
            <Link className="acceso" to={a.to} key={a.label}>
              <Icono nombre={a.icono} />
              {a.label}
            </Link>
          ))}
        </nav>

        {gerencial ? <PanelGerencial /> : <MisTareas />}
      </div>

      <aside className="rail">
        <ProximosServicios />
        {gerencial && <RequiereAtencion />}
      </aside>
    </div>
  )
}

function PanelGerencial() {
  const [periodo, setPeriodo] = useState<Periodo>('mes')
  const [ciudad, setCiudad] = useState('')
  const ciudades = useCiudades()
  const filtros: FiltrosIndicadores = { ...rango(periodo), ciudad: ciudad || undefined }
  const indicadores = useIndicadores(filtros)
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
    <section className="tarjeta" aria-labelledby="titulo-indicadores">
      <div className="tarjeta-cabeza">
        <h3 id="titulo-indicadores">Indicadores</h3>
        <span className="apagado numero">
          {fecha(filtros.desde)} – {fecha(filtros.hasta)}
        </span>
      </div>
      <div className="filtros" style={{ marginBottom: 'var(--e4)' }}>
        <select
          className="input"
          style={{ width: 'auto' }}
          value={periodo}
          onChange={(e) => setPeriodo(e.target.value as Periodo)}
          aria-label="Período"
        >
          {PERIODOS.map((p) => (
            <option key={p.valor} value={p.valor}>{p.label}</option>
          ))}
        </select>
        <select
          className="input"
          style={{ width: 'auto' }}
          value={ciudad}
          onChange={(e) => setCiudad(e.target.value)}
          aria-label="Ciudad"
        >
          <option value="">Todas las ciudades</option>
          {ciudades.data?.map((c) => (
            <option key={c.codigo} value={c.nombre}>{c.nombre}</option>
          ))}
        </select>
        <div className="acciones" style={{ marginLeft: 'auto' }}>
          <button className="btn btn-suave" type="button" onClick={() => exportar('xlsx')}>
            <Icono nombre="descargar" size={16} /> Excel
          </button>
          <button className="btn btn-plano" type="button" onClick={() => exportar('csv')}>
            CSV
          </button>
        </div>
      </div>
      {errorDescarga && (
        <p className="error" role="alert">
          {errorDescarga}
        </p>
      )}
      <Consulta consulta={indicadores} cargando="Calculando indicadores…" error="No fue posible calcular los indicadores.">
        {(d) => <TableroIndicadores datos={d} />}
      </Consulta>
    </section>
  )
}

function TableroIndicadores({ datos }: { datos: Indicadores }) {
  const i = datos.indicadores
  const definiciones = useDefiniciones()
  const formula = (codigo: string) => definiciones.data?.find((d) => d.codigo === codigo)?.formula

  const tiles: { codigo: string; titulo: string; valor: string; detalle?: string }[] = [
    { codigo: 'afiliaciones', titulo: 'Afiliaciones', valor: String(i.afiliaciones), detalle: `${i.retiros} retiros` },
    { codigo: 'vigentes', titulo: 'Afiliados vigentes', valor: String(i.vigentes) },
    {
      codigo: 'recaudo',
      titulo: 'Recaudo',
      valor: moneda(i.recaudo),
      detalle: `${porcentaje(i.recaudo_del_facturado)} de ${moneda(i.facturado)} facturado`,
    },
    {
      codigo: 'mora',
      titulo: 'En mora',
      valor: String(i.mora.contratos_en_mora),
      detalle: `${porcentaje(i.mora.porcentaje)} · ${moneda(i.mora.saldo_vencido)} vencido`,
    },
    {
      codigo: 'cumplimiento_rutas',
      titulo: 'Cumplimiento de rutas',
      valor: porcentaje(i.cumplimiento_rutas.cumplimiento),
      detalle: `${i.cumplimiento_rutas.paradas_completadas} de ${i.cumplimiento_rutas.paradas_planeadas} paradas · puntualidad ${porcentaje(i.cumplimiento_rutas.puntualidad)}`,
    },
    {
      codigo: 'satisfaccion',
      titulo: 'Satisfacción',
      valor: i.satisfaccion.promedio === null ? '—' : `${i.satisfaccion.promedio.toFixed(1)} / 5`,
      detalle: `${i.satisfaccion.respondidas} de ${i.satisfaccion.enviadas} encuestas · respuesta ${porcentaje(i.satisfaccion.tasa_respuesta)}`,
    },
  ]

  const tipos = Object.entries(i.servicios_por_tipo).sort((a, b) => b[1] - a[1])
  const maximo = Math.max(1, ...tipos.map(([, n]) => n))

  return (
    <div className="pila">
      <div className="indicadores">
        {tiles.map((t) => (
          <div className="indicador" key={t.codigo} title={formula(t.codigo)}>
            <span className="indicador-titulo">{t.titulo}</span>
            <strong className="indicador-valor numero">{t.valor}</strong>
            {t.detalle && <span className="indicador-detalle">{t.detalle}</span>}
          </div>
        ))}
      </div>

      <div>
        <h4 className="subtitulo">Servicios completados por tipo</h4>
        {tipos.length === 0 ? (
          <p className="apagado">No hay servicios completados en el período.</p>
        ) : (
          <ul className="barras" aria-label="Servicios completados por tipo">
            {tipos.map(([tipo, n]) => (
              <li key={tipo} className="barra" title={`${tipo}: ${n} servicios`}>
                <span className="barra-etiqueta">{tipo}</span>
                <span className="barra-pista">
                  <span className="barra-valor" style={{ width: `${(n / maximo) * 100}%` }} />
                </span>
                <span className="barra-cifra numero">{n}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function ProximosServicios() {
  const servicios = useProximosServicios(hoyISO())
  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Próximos servicios</h3>
        <Link to="/servicios">Ver todos</Link>
      </div>
      <Consulta
        consulta={servicios}
        cargando="Cargando servicios…"
        error="No fue posible cargar los servicios."
        vacio="No hay servicios agendados desde hoy."
        estaVacio={(d) => d.items.length === 0}
      >
        {(d) =>
          d.items.map((s) => (
            <Link className="fila" key={s.id} to={`/servicios/${s.id}`}>
              <span className="fila-icono">
                <Icono nombre="servicios" size={18} />
              </span>
              <div className="fila-cuerpo">
                <strong>{s.tipo}</strong>
                <span>{s.ciudad}</span>
              </div>
              <div className="fila-lado">{fechaHora(s.programado_para)}</div>
            </Link>
          ))
        }
      </Consulta>
    </section>
  )
}

function RequiereAtencion() {
  const alertas = useAlertas()
  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Requiere atención</h3>
      </div>
      <Consulta consulta={alertas} cargando="Revisando pendientes…" error="No fue posible revisar los pendientes.">
        {(a) => (
          <>
            <Alerta to="/cartera?mora=1" icono="cartera" titulo="Contratos en mora" cantidad={a.enMora} />
            <Alerta to="/preventivos?autorizacion=1" icono="preventivos" titulo="Preventivos por autorizar" cantidad={a.preventivosPorAutorizar} />
            <Alerta to="/tareas?vencidas=1" icono="tareas" titulo="Tareas vencidas" cantidad={a.tareasVencidas} />
          </>
        )}
      </Consulta>
    </section>
  )
}

function Alerta({ to, icono, titulo, cantidad }: { to: string; icono: NombreIcono; titulo: string; cantidad: number }) {
  return (
    <Link className="fila" to={to}>
      <span className="fila-icono">
        <Icono nombre={icono} size={18} />
      </span>
      <div className="fila-cuerpo">
        <strong>{titulo}</strong>
      </div>
      <span className={`distintivo distintivo-${cantidad > 0 ? 'alerta' : 'ok'}`}>
        {cantidad > 0 ? cantidad : 'Al día'}
      </span>
    </Link>
  )
}

function MisTareas() {
  const tareas = useMisTareas()
  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Mis tareas abiertas</h3>
        <Link to="/tareas">Ver todas</Link>
      </div>
      <Consulta
        consulta={tareas}
        cargando="Cargando tareas…"
        error="No fue posible cargar tus tareas."
        vacio="No tienes tareas abiertas."
        estaVacio={(d) => d.items.length === 0}
      >
        {(d) =>
          d.items.map((t) => (
            <div className="fila" key={t.id}>
              <span className="fila-icono">
                <Icono nombre="tareas" size={18} />
              </span>
              <div className="fila-cuerpo">
                <strong>{t.titulo}</strong>
                <span>{t.vence_el ? `Vence ${fecha(t.vence_el)}` : 'Sin fecha límite'}</span>
              </div>
              <Distintivo dominio="prioridad" valor={t.prioridad} />
            </div>
          ))
        }
      </Consulta>
    </section>
  )
}

