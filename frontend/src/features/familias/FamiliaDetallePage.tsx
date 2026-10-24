import { Link, useParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Pestanas } from '@/components/Pestanas'
import { useAuth } from '@/features/auth/AuthContext'
import { useNombreTipoServicio } from '@/features/catalogos/api'
import { fecha, fechaHora } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { CambioHistorial, FamiliaRead } from '@/types'

import { useFamilia, useHistorial, useServiciosFamilia } from './api'
import { AccionesFamilia } from './AccionesFamilia'
import { CarteraFamilia } from './CarteraFamilia'
import { DatosFamilia } from './DatosFamilia'
import { MascotasFamilia } from './MascotasFamilia'

/** Ficha de una familia: sus datos, mascotas, cuenta, servicios e historial. */
export function FamiliaDetallePage() {
  const { id = '' } = useParams()
  const { usuario } = useAuth()
  const familia = useFamilia(id)

  return (
    <Consulta consulta={familia} cargando="Cargando la familia…" error="No fue posible cargar la familia.">
      {(f) => (
        <>
          <div className="detalle-cabeza">
            <Link to="/familias" className="btn btn-plano" aria-label="Volver a familias">
              <Icono nombre="volver" size={16} />
            </Link>
            <h1>{f.titular_nombre}</h1>
            <Distintivo dominio="afiliacion" valor={f.estado} />
            {f.usuario_portal_id && <span className="distintivo distintivo-info">Con portal</span>}
            {puede(usuario, 'gestionarAfiliacion') && <AccionesFamilia familia={f} />}
          </div>
          {f.dada_de_baja_en && (
            <p className="error" role="status">
              Dada de baja el {fecha(f.dada_de_baja_en.slice(0, 10))}: {f.motivo_baja}
            </p>
          )}
          <Pestanas
            etiqueta="Secciones de la familia"
            pestanas={[
              { valor: 'datos', titulo: 'Datos', contenido: <DatosFamilia familia={f} /> },
              { valor: 'mascotas', titulo: 'Mascotas', contenido: <MascotasFamilia familia={f} /> },
              { valor: 'cartera', titulo: 'Cartera', contenido: <CarteraFamilia familia={f} /> },
              { valor: 'servicios', titulo: 'Servicios', contenido: <ServiciosFamilia familia={f} /> },
              { valor: 'historial', titulo: 'Historial', contenido: <HistorialFamilia familiaId={f.id} /> },
            ]}
          />
        </>
      )}
    </Consulta>
  )
}

function ServiciosFamilia({ familia }: { familia: FamiliaRead }) {
  const servicios = useServiciosFamilia(familia.id)
  const nombreTipo = useNombreTipoServicio()
  return (
    <section className="tarjeta">
      <Consulta
        consulta={servicios}
        cargando="Cargando servicios…"
        error="No fue posible cargar los servicios."
        vacio="Esta familia todavía no tiene servicios programados."
        estaVacio={(d) => d.items.length === 0}
      >
        {(d) => (
          <div className="scroll-x">
            <table className="tabla">
              <thead>
                <tr>
                  <th>Servicio</th>
                  <th>Mascota</th>
                  <th>Programado</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {d.items.map((s) => (
                  <tr key={s.id}>
                    <td className="principal">{nombreTipo(s.tipo_codigo)}</td>
                    <td>{familia.mascotas?.find((m) => m.id === s.mascota_id)?.nombre ?? '—'}</td>
                    <td className="numero">{fechaHora(s.programado_para)}</td>
                    <td>
                      <Distintivo dominio="servicio" valor={s.estado} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Consulta>
    </section>
  )
}

const ACCIONES: Record<string, string> = {
  crear: 'Registro creado',
  editar: 'Datos editados',
  cambio_estado: 'Cambio de estado',
  eliminar: 'Registro eliminado',
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
      return `${campo.replace(/_/g, ' ')}: ${valor(antes)} → ${valor(despues)}`
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
          <ol className="pila" aria-label="Historial de cambios">
            {d.map((c, i) => (
              <li key={`${c.fecha}-${i}`}>
                <strong>{ACCIONES[c.accion] ?? c.accion}</strong>{' '}
                <span className="apagado numero">{fechaHora(c.fecha)}</span>
                {detalle(c) && <div className="apagado">{detalle(c)}</div>}
              </li>
            ))}
          </ol>
        )}
      </Consulta>
    </section>
  )
}
