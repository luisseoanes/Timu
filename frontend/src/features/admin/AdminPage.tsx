import { useEffect, useId, type ReactNode } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { ConfiguracionEncuestas, PlantillasWhatsApp } from '@/features/campanas'
import { GuionBot } from '@/features/comercial'

import { Catalogos } from './Catalogos'
import { DatosTimu } from './DatosTimu'
import { InteligenciaArtificial } from './InteligenciaArtificial'
import { Planes } from './Planes'
import { Reglas } from './Reglas'
import { Supresion } from './Supresion'
import { Usuarios } from './Usuarios'

interface Seccion {
  valor: string
  titulo: string
  contenido: ReactNode
}

/**
 * Las secciones de Administración en cuatro apartados, por lo que configuran (DEU-76, decidido con
 * el usuario el 2026-11-23): en diez pestañas, a 1280 px una caía sola a otra fila y a 390 px seis
 * quedaban fuera de la vista.
 */
const APARTADOS: { titulo: string; secciones: Seccion[] }[] = [
  { titulo: 'Equipo', secciones: [{ valor: 'usuarios', titulo: 'Usuarios', contenido: <Usuarios /> }] },
  {
    titulo: 'Planes y catálogos',
    secciones: [
      { valor: 'planes', titulo: 'Planes', contenido: <Planes /> },
      { valor: 'catalogos', titulo: 'Catálogos', contenido: <Catalogos /> },
    ],
  },
  {
    titulo: 'Automatizaciones',
    secciones: [
      { valor: 'reglas', titulo: 'Reglas', contenido: <Reglas /> },
      { valor: 'plantillas', titulo: 'Plantillas de WhatsApp', contenido: <PlantillasWhatsApp /> },
      { valor: 'guion', titulo: 'Guion del asistente', contenido: <GuionBot /> },
      { valor: 'encuestas', titulo: 'Encuestas', contenido: <ConfiguracionEncuestas /> },
      { valor: 'ia', titulo: 'Inteligencia artificial', contenido: <InteligenciaArtificial /> },
    ],
  },
  {
    titulo: 'TIMU y privacidad',
    secciones: [
      { valor: 'timu', titulo: 'Datos de TIMU', contenido: <DatosTimu /> },
      { valor: 'supresion', titulo: 'Supresión de datos', contenido: <Supresion /> },
    ],
  },
]

const SECCIONES = APARTADOS.flatMap((a) => a.secciones)

/** Lo que la URL abre dentro de cada sección: la ficha de un plan o una regla. */
const SECCION_DE: Record<string, string> = { plan: 'planes', regla: 'reglas' }

/** La dirección de una sección: solo `?pestana=`, para que lo abierto en otra no vuelva a abrirse. */
const enlace = (valor: string) => `?pestana=${valor}`

/** Administración de la plataforma: sólo el perfil admin llega aquí (App.tsx). Configura y nada más
 * (Sección 12, docs/perfiles-y-permisos.md): los reportes son de Gerencia y la pasarela de Cartera.
 * Un índice a la izquierda con los cuatro apartados y la sección abierta a la derecha; en el celular,
 * el índice es un selector encima. Cada sección tiene su dirección (`?pestana=`, `?plan=`, `?regla=`). */
export function AdminPage() {
  const [params, setParams] = useSearchParams()
  const navegar = useNavigate()
  const idIndice = useId()
  const pedida = Object.keys(SECCION_DE).find((p) => params.has(p))
  const valor = pedida ? SECCION_DE[pedida]! : (params.get('pestana') ?? 'usuarios')
  const abierta = SECCIONES.find((s) => s.valor === valor) ?? SECCIONES[0]!
  // Una ficha pedida por enlace (`?plan=p1`) lleva también su sección: así «Volver» de la ficha,
  // que solo quita `plan`, se queda en Planes en vez de caer en Usuarios.
  useEffect(() => {
    if (pedida && params.get('pestana') !== valor) {
      const completa = new URLSearchParams(params)
      completa.set('pestana', valor)
      setParams(completa, { replace: true })
    }
  }, [pedida, params, setParams, valor])

  return (
    <div className="admin">
      <nav className="admin-indice" aria-label="Secciones de administración">
        {APARTADOS.map((a, i) => (
          <div key={a.titulo} className="admin-indice-apartado">
            <p className="admin-indice-titulo" id={`${idIndice}-${i}`}>
              {a.titulo}
            </p>
            <ul aria-labelledby={`${idIndice}-${i}`}>
              {a.secciones.map((s) => (
                <li key={s.valor}>
                  <Link to={enlace(s.valor)} aria-current={s.valor === abierta.valor ? 'page' : undefined}>
                    {s.titulo}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>
      <label className="admin-indice-movil campo">
        <span>Sección</span>
        <select className="input" value={abierta.valor} onChange={(e) => navegar(enlace(e.target.value))}>
          {APARTADOS.map((a) => (
            <optgroup key={a.titulo} label={a.titulo}>
              {a.secciones.map((s) => (
                <option key={s.valor} value={s.valor}>
                  {s.titulo}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </label>
      <div className="admin-seccion">{abierta.contenido}</div>
    </div>
  )
}
