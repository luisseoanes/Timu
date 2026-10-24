import type { ReactNode } from 'react'

import { Icono, type NombreIcono } from '@/components/Icono'

const PILARES: { icono: NombreIcono; titulo: string; texto: string }[] = [
  { icono: 'clinica', titulo: 'Historia clínica', texto: 'Cada consulta, fórmula y adjunto, firmado y en un solo lugar.' },
  { icono: 'rutas', titulo: 'Visitas a domicilio', texto: 'Rutas del día optimizadas para el equipo médico.' },
  { icono: 'preventivos', titulo: 'Preventivos al día', texto: 'Vacunas y desparasitaciones con carnet digital verificable.' },
]

/** Marca de TIMU: huella dentro de un sello con la cruz clínica. */
export function MarcaTimu({ claro = false }: { claro?: boolean }) {
  return (
    <span className={`marca${claro ? ' marca-clara' : ''}`}>
      <span className="marca-sello" aria-hidden="true">
        <Icono nombre="huella" size={22} />
      </span>
      <span className="marca-nombre">TIMU</span>
      <span className="marca-sub">Veterinaria a domicilio</span>
    </span>
  )
}

/**
 * Pantallas de acceso (ingreso, recuperación, activación): panel de marca a la
 * izquierda y el formulario a la derecha. Bajo 900 px el panel se reduce a la marca.
 */
export function AccesoLayout({ children }: { children: ReactNode }) {
  return (
    <div className="ingreso">
      <aside className="ingreso-marca">
        <MarcaTimu claro />

        <div className="ingreso-mensaje">
          <p className="ingreso-kicker">
            <Icono nombre="pulso" size={16} /> Plataforma clínica y operativa
          </p>
          <h2>El cuidado de cada mascota, coordinado de la casa a la consulta.</h2>
          <ul className="ingreso-pilares">
            {PILARES.map((p) => (
              <li key={p.titulo}>
                <span className="ingreso-pilar-icono" aria-hidden="true">
                  <Icono nombre={p.icono} size={18} />
                </span>
                <span>
                  <strong>{p.titulo}</strong>
                  <span>{p.texto}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>

        <VistaPreviaVisita />

        <p className="ingreso-legal">
          <Icono nombre="escudo" size={16} /> Datos clínicos protegidos · Ley 1581 de 2012
        </p>
      </aside>

      <main className="ingreso-contenido">{children}</main>
    </div>
  )
}

/** Tarjeta ilustrativa: así se ve una visita en la plataforma. Decorativa. */
function VistaPreviaVisita() {
  return (
    <div className="ingreso-vista" aria-hidden="true">
      <div className="ingreso-vista-cabeza">
        <span className="ingreso-avatar">
          <Icono nombre="huella" size={18} />
        </span>
        <span>
          <strong>Luna · Canino</strong>
          <span>Vacuna polivalente · 10:30 a. m.</span>
        </span>
        <span className="ingreso-chip">
          <Icono nombre="check" size={14} /> Aplicada
        </span>
      </div>
      <svg className="ingreso-pulso" viewBox="0 0 320 48" preserveAspectRatio="none">
        <path d="M0 30h70l10-18 14 32 12-24 8 10h52l9-14 11 20 8-8h126" />
      </svg>
      <div className="ingreso-vista-pie">
        <span><Icono nombre="rutas" size={14} /> Ruta norte · parada 3 de 8</span>
        <span><Icono nombre="clinica" size={14} /> Historia firmada</span>
      </div>
    </div>
  )
}
