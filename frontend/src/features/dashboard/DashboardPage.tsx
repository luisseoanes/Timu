import { Icono, type NombreIcono } from '@/components/Icono'
import { AnilloProgreso } from '@/components/AnilloProgreso'
import { useAuth } from '@/features/auth/AuthContext'

/**
 * Panel de inicio. Los indicadores llegarán de `F4-DAS-02`; mientras tanto la
 * pantalla muestra datos de ejemplo, señalados como tales, para que el diseño
 * se pueda validar contra la referencia.
 */

const ACCESOS: { icono: NombreIcono; label: string }[] = [
  { icono: 'servicios', label: 'Agendar servicio' },
  { icono: 'clinica', label: 'Historia clínica' },
  { icono: 'pago', label: 'Registrar pago' },
  { icono: 'familias', label: 'Nueva familia' },
]

const PROXIMOS = [
  { icono: 'servicios' as NombreIcono, titulo: 'Vacunación · Kira', sub: 'Ana Ruiz · Bogotá', lado: 'Hoy, 10:30 a.m.' },
  { icono: 'rutas' as NombreIcono, titulo: 'Ruta norte · 6 paradas', sub: 'Téc. Carlos Peña', lado: 'Hoy, 8:00 a.m.' },
  { icono: 'clinica' as NombreIcono, titulo: 'Control · Nube', sub: 'Dr. Sara Martínez', lado: 'Mañana, 2:00 p.m.' },
]

const CARTERA = [
  { titulo: 'Cuotas al día', valor: '412 familias', estado: 'ok' as const, etiqueta: 'Al día' },
  { titulo: 'En mora', valor: '38 familias', estado: 'alerta' as const, etiqueta: 'Por gestionar' },
  { titulo: 'Renovaciones del mes', valor: '17 contratos', estado: 'info' as const, etiqueta: 'Programadas' },
]

export function DashboardPage() {
  const { usuario } = useAuth()
  const nombre = usuario?.nombre?.split(' ')[0] ?? ''

  return (
    <div className="con-rail">
      <div className="contenido">
        <section className="bienvenida">
          <h1>Hola {nombre}</h1>
          <p className="apagado">
            Esto es lo que la operación tiene entre manos hoy: servicios agendados, rutas en
            camino y la cartera que necesita gestión.
          </p>
          <div className="bienvenida-datos">
            <span className="distintivo distintivo-ok">14 servicios hoy</span>
            <span className="distintivo distintivo-info">3 rutas activas</span>
            <span className="distintivo distintivo-neutro">Datos de ejemplo</span>
          </div>
        </section>

        <div className="accesos">
          {ACCESOS.map((a) => (
            <button className="acceso" type="button" key={a.label}>
              <Icono nombre={a.icono} />
              {a.label}
            </button>
          ))}
        </div>

        <div className="dos-columnas">
          <section className="tarjeta">
            <div className="tarjeta-cabeza">
              <h3>Próximos servicios</h3>
              <a href="#servicios">Ver todos</a>
            </div>
            {PROXIMOS.map((p) => (
              <div className="fila" key={p.titulo}>
                <span className="fila-icono"><Icono nombre={p.icono} size={18} /></span>
                <div className="fila-cuerpo">
                  <strong>{p.titulo}</strong>
                  <span>{p.sub}</span>
                </div>
                <div className="fila-lado">{p.lado}</div>
              </div>
            ))}
          </section>

          <section className="tarjeta">
            <div className="tarjeta-cabeza">
              <h3>Estado de cartera</h3>
              <a href="#cartera">Ver detalle</a>
            </div>
            {CARTERA.map((c) => (
              <div className="fila" key={c.titulo}>
                <span className="fila-icono"><Icono nombre="cartera" size={18} /></span>
                <div className="fila-cuerpo">
                  <strong>{c.titulo}</strong>
                  <span>{c.valor}</span>
                </div>
                <span className={`distintivo distintivo-${c.estado}`}>{c.etiqueta}</span>
              </div>
            ))}
          </section>
        </div>
      </div>

      <aside className="rail">
        <section className="tarjeta">
          <div className="tarjeta-cabeza"><h3>Cumplimiento de hoy</h3></div>
          <AnilloProgreso valor={72} />
          <p className="apagado" style={{ textAlign: 'center', fontSize: 'var(--t-menor)' }}>
            10 de 14 servicios completados
          </p>
          <div className="metricas" style={{ marginTop: 'var(--e4)' }}>
            <div className="metrica"><b className="numero">10</b><span>Completados</span></div>
            <div className="metrica"><b className="numero">3</b><span>En ruta</span></div>
            <div className="metrica"><b className="numero">1</b><span>Reprogramado</span></div>
          </div>
        </section>

        <section className="tarjeta">
          <div className="tarjeta-cabeza"><h3>Requiere atención</h3></div>
          <div className="aviso">
            <b>38 familias en mora</b> superan los 10 días. El congelamiento automático se
            aplica a los 30 días y hoy hay 6 en ese límite.
          </div>
          <button className="btn btn-suave btn-bloque" type="button" style={{ marginTop: 'var(--e3)' }}>
            Gestionar cartera
          </button>
        </section>

        <section className="tarjeta">
          <div className="tarjeta-cabeza"><h3>Preventivos por vencer</h3></div>
          <div className="fila">
            <span className="fila-icono"><Icono nombre="preventivos" size={18} /></span>
            <div className="fila-cuerpo">
              <strong>Vacunación anual</strong>
              <span>22 mascotas este mes</span>
            </div>
            <span className="distintivo distintivo-alerta">En 20 días</span>
          </div>
          <div className="fila">
            <span className="fila-icono"><Icono nombre="preventivos" size={18} /></span>
            <div className="fila-cuerpo">
              <strong>Desparasitación</strong>
              <span>9 mascotas vencidas</span>
            </div>
            <span className="distintivo distintivo-peligro">Vencido</span>
          </div>
        </section>
      </aside>
    </div>
  )
}
