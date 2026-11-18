import * as Menu from '@radix-ui/react-dropdown-menu'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { Icono } from '@/components/Icono'
import { MarcaTimu } from '@/components/MarcaTimu'
import { useAuth } from '@/features/auth'
import { enlaceWhatsApp } from '@/lib/enlaces'
import { inicioDeRol } from '@/lib/permisos'

import { useDatosTimu } from './portada'

/** Las secciones de la portada: la barra las enlaza desde la portada y desde cada plan. */
const SECCIONES = [
  { ancla: 'planes', nombre: 'Planes' },
  { ancla: 'aliadas', nombre: 'Aliadas' },
  { ancla: 'nosotros', nombre: 'Nosotros' },
  { ancla: 'contacto', nombre: 'Contacto' },
] as const

/**
 * El marco de la web pública (R3-PUB-04): la barra marina con el logo, las secciones, «Ingresar»
 * (cada perfil llega a su espacio desde el mismo ingreso) y la afiliación; abajo, el pie con los
 * datos de TIMU. El verde lleno no va aquí: es de «Arma tu plan» o de la afiliación de cada plan.
 */
export function MarcoPublico({ children }: { children: ReactNode }) {
  return (
    <div className="publica">
      <a className="saltar" href="#contenido">
        Saltar al contenido
      </a>
      <BarraPublica />
      <main id="contenido" className="publica-cuerpo">
        {children}
      </main>
      <PiePublico />
    </div>
  )
}

function Ingresar() {
  const { usuario } = useAuth()
  // Con la sesión abierta, lleva a su espacio: el panel, el portal o el de la clínica.
  return usuario ? (
    <Link className="publica-barra-enlace" to={inicioDeRol(usuario.rol)}>
      Ir a mi espacio
    </Link>
  ) : (
    <Link className="publica-barra-enlace" to="/login">
      Ingresar
    </Link>
  )
}

function BarraPublica() {
  return (
    <header className="publica-barra">
      {/* El logo completo, con su fila de animales; en el celular, el compacto. */}
      <Link to="/" className="publica-marca publica-marca-completa" aria-label="TIMU, ir al inicio">
        <MarcaTimu claro />
      </Link>
      <Link to="/" className="publica-marca publica-marca-compacta" aria-label="TIMU, ir al inicio">
        <MarcaTimu claro compacta />
      </Link>
      <nav className="publica-nav" aria-label="Secciones">
        {SECCIONES.map((s) => (
          <Link key={s.ancla} to={{ pathname: '/', hash: s.ancla }}>
            {s.nombre}
          </Link>
        ))}
      </nav>
      <div className="publica-barra-acciones">
        <Ingresar />
        <Link className="btn publica-btn-marca" to="/afiliacion">
          Afiliar a mi peludo
        </Link>
        {/* En el celular, las secciones van en un menú: la barra solo deja el logo y la afiliación. */}
        <Menu.Root modal={false}>
          <Menu.Trigger className="btn btn-icono publica-menu" aria-label="Menú">
            <Icono nombre="puntos" size={20} />
          </Menu.Trigger>
          <Menu.Portal>
            <Menu.Content className="menu" align="end" sideOffset={8}>
              {SECCIONES.map((s) => (
                <Menu.Item key={s.ancla} asChild>
                  <Link className="menu-item" to={{ pathname: '/', hash: s.ancla }}>
                    {s.nombre}
                  </Link>
                </Menu.Item>
              ))}
              <Menu.Separator className="menu-separador" />
              <Menu.Item asChild>
                <Link className="menu-item" to="/login">
                  <Icono nombre="usuario" size={18} /> Ingresar
                </Link>
              </Menu.Item>
            </Menu.Content>
          </Menu.Portal>
        </Menu.Root>
      </div>
    </header>
  )
}

function PiePublico() {
  const datos = useDatosTimu()
  const d = datos.data
  return (
    <footer className="publica-pie">
      <div className="publica-pie-cuerpo">
        <div className="publica-pie-marca">
          <MarcaTimu claro />
          {(d?.razon_social || d?.nit) && (
            <p>
              {d.razon_social}
              {d.nit && <span className="numero"> · NIT {d.nit}</span>}
            </p>
          )}
        </div>
        <nav className="publica-pie-grupo" aria-label="La web de TIMU">
          <h2 className="publica-pie-titulo">TIMU</h2>
          {SECCIONES.map((s) => (
            <Link key={s.ancla} to={{ pathname: '/', hash: s.ancla }}>
              {s.nombre}
            </Link>
          ))}
          <Link to="/afiliacion">Afiliar a mi peludo</Link>
        </nav>
        <nav className="publica-pie-grupo" aria-label="Ingresar">
          <h2 className="publica-pie-titulo">Ingresar</h2>
          {/* Un solo ingreso: cada perfil llega a su espacio. */}
          <Link to="/login">Familias afiliadas</Link>
          <Link to="/login">Clínicas aliadas</Link>
          <Link to="/login">Equipo TIMU</Link>
        </nav>
        {d && (d.whatsapp || d.correo || d.redes.length > 0 || d.politica_datos_url) && (
          <div className="publica-pie-grupo">
            <h2 className="publica-pie-titulo">Escríbenos</h2>
            {d.whatsapp && (
              <a href={enlaceWhatsApp(d.whatsapp)} target="_blank" rel="noreferrer">
                WhatsApp
              </a>
            )}
            {d.correo && (
              // Si no cabe, se parte tras la arroba y no en medio del dominio.
              <a href={`mailto:${d.correo}`}>
                {d.correo.split('@')[0]}@<wbr />
                {d.correo.split('@')[1]}
              </a>
            )}
            {d.redes.map((r) => (
              <a key={r.url} href={r.url} target="_blank" rel="noreferrer">
                {r.nombre}
              </a>
            ))}
            {d.politica_datos_url && (
              <a href={d.politica_datos_url} target="_blank" rel="noreferrer">
                Política de tratamiento de datos
              </a>
            )}
          </div>
        )}
      </div>
    </footer>
  )
}
