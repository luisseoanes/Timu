import { Link } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Icono } from '@/components/Icono'
import type { DatosTimuRead } from '@/types'

import { useLoQueFalta } from './api'
import { Saludo } from './Saludo'

/** Lo que la portada y los documentos necesitan de los Datos de TIMU, en palabras. */
const DATOS_NECESARIOS: [keyof DatosTimuRead, string][] = [
  ['presentacion', 'la presentación'],
  ['mision', 'la misión'],
  ['whatsapp', 'el WhatsApp'],
  ['correo', 'el correo'],
  ['clinica_direccion', 'la dirección de la clínica'],
  ['horario_atencion', 'el horario de atención'],
  ['politica_datos_url', 'la política de datos'],
]

interface Pendiente {
  clave: string
  bloquea: boolean
  titulo: string
  detalle?: string
  accion: { texto: string; pestana: string }
}

function lista(cosas: string[]): string {
  return cosas.length > 1 ? `${cosas.slice(0, -1).join(', ')} y ${cosas.at(-1)}` : (cosas[0] ?? '')
}

/** El Inicio del administrador: lo que falta configurar, lo que impide que algo funcione primero
 * (decidido con el usuario el 2026-11-19, docs/perfiles-y-permisos.md). Configura y no opera. */
export function InicioAdmin() {
  const falta = useLoQueFalta()
  return (
    <div className="inicio">
      <Saludo resumen="lo que falta configurar" />
      <section className="inicio-panel" aria-labelledby="inicio-config-titulo">
        <h2 id="inicio-config-titulo" className="inicio-panel-titulo">
          Lo que falta configurar
        </h2>
        <Consulta consulta={falta} cargando="Revisando la configuración…" error="No fue posible revisar la configuración.">
          {({ plantillas, datos, usuarios }) => {
            const pendientes: Pendiente[] = plantillas.map((p) => ({
              clave: p.codigo,
              bloquea: true,
              titulo: `La plantilla «${p.titulo}» no está aprobada en el catálogo`,
              detalle: `Sus avisos no se envían. La usa: ${lista(p.reglas)}.`,
              accion: { texto: 'Ver las plantillas', pestana: 'plantillas' },
            }))
            const vacios = DATOS_NECESARIOS.filter(([campo]) => !datos[campo]).map(([, nombre]) => nombre)
            if (vacios.length > 0) {
              pendientes.push({
                clave: 'datos',
                bloquea: true,
                titulo: `Datos de TIMU: falta ${lista(vacios)}`,
                detalle: 'La portada y los documentos los dicen tal como estén aquí.',
                accion: { texto: 'Completar los datos', pestana: 'timu' },
              })
            }
            if (usuarios.inactivos > 0) {
              pendientes.push({
                clave: 'inactivos',
                bloquea: false,
                titulo: usuarios.inactivos === 1 ? '1 usuario inactivo' : `${usuarios.inactivos} usuarios inactivos`,
                detalle: 'No pueden entrar. Se vuelven a activar desde Usuarios.',
                accion: { texto: 'Ver los usuarios', pestana: 'usuarios' },
              })
            }
            if (pendientes.length === 0) return <p className="apagado">Todo está configurado.</p>
            // Una sola acción verde: la de lo primero que impide que algo funcione.
            const principal = pendientes.findIndex((p) => p.bloquea)
            return (
              <ul className="inicio-config">
                {pendientes.map((p, i) => (
                  <li key={p.clave} className="fila">
                    <span className="fila-icono" data-bloquea={p.bloquea || undefined}>
                      <Icono nombre={p.bloquea ? 'alerta' : 'usuario'} size={16} />
                    </span>
                    <div className="fila-cuerpo">
                      <strong>{p.titulo}</strong>
                      {p.detalle && <span>{p.detalle}</span>}
                    </div>
                    <Link className={`btn ${i === principal ? 'btn-primario' : 'btn-suave'}`} to={`/panel/admin?pestana=${p.accion.pestana}`}>
                      {p.accion.texto}
                    </Link>
                  </li>
                ))}
              </ul>
            )
          }}
        </Consulta>
      </section>
    </div>
  )
}
