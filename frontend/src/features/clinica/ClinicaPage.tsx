import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Pestanas } from '@/components/Pestanas'
import { useAuth } from '@/features/auth'
import { useEspecies, useNombreTipoServicio } from '@/features/catalogos'
import { useMascotas } from '@/features/familias'
import { useRutas } from '@/features/rutas'
import { mensajeError } from '@/lib/errores'
import { fecha, hora, hoyISO } from '@/lib/formato'
import { puede } from '@/lib/permisos'

import { useBorradores, useBuscarMascotas } from './api'
import { AtencionVirtual } from './AtencionVirtual'
import { Plantillas } from './Plantillas'
import { Respuestas } from './Respuestas'

export function ClinicaPage() {
  const { usuario } = useAuth()
  const [params] = useSearchParams()
  const historia = (
    <div className="clinica-inicio" data-con-pendiente={puede(usuario, 'medico') || undefined}>
      {puede(usuario, 'medico') && <TrabajoPendiente />}
      <BuscarHistoria />
    </div>
  )
  const pestanas = [{ valor: 'historia', titulo: 'Historia clínica', contenido: historia }]
  if (puede(usuario, 'clinico')) {
    pestanas.push(
      { valor: 'virtual', titulo: 'Atención virtual', contenido: <AtencionVirtual /> },
      { valor: 'respuestas', titulo: 'Respuestas aprobadas', contenido: <Respuestas /> },
      { valor: 'plantillas', titulo: 'Plantillas de consulta', contenido: <Plantillas /> },
    )
  }
  // La página controla la pestaña: una plantilla que aparece en la URL (al recargar o desde un
  // enlace) lleva a la suya, y cerrar su ficha («Volver») no la cambia.
  const plantilla = params.get('plantilla')
  const [pestana, setPestana] = useState(plantilla ? 'plantillas' : 'historia')
  const [vista, setVista] = useState(plantilla)
  if (plantilla !== vista) {
    setVista(plantilla)
    if (plantilla) setPestana('plantillas')
  }
  // Mientras llega el perfil solo está la historia; quien no ve las plantillas se queda en ella.
  const valor = pestanas.some((p) => p.valor === pestana) ? pestana : 'historia'
  return <Pestanas etiqueta="Secciones de clínica" pestanas={pestanas} valor={valor} onCambio={setPestana} />
}

/**
 * Lo que el médico tiene entre manos al abrir Clínica: las mascotas de su ruta de hoy, que abren
 * la consulta de esa visita, y sus consultas sin firmar.
 */
function TrabajoPendiente() {
  const { usuario } = useAuth()
  const nombreTipo = useNombreTipoServicio()
  const rutas = useRutas(hoyISO(), { responsable: usuario?.id })
  const borradores = useBorradores()
  const mascotas = useMascotas(borradores.data?.map((e) => e.mascota_id) ?? [])
  const visitas = (rutas.data ?? [])
    .filter((r) => r.estado === 'planificada' || r.estado === 'en_curso')
    .flatMap((r) => r.paradas)
    .filter((p) => p.mascota && p.estado !== 'omitida')

  return (
    <section className="tarjeta" aria-labelledby="pendiente-titulo">
      <div className="tarjeta-cabeza">
        <h2 id="pendiente-titulo">Tu trabajo de hoy</h2>
      </div>
      <section className="bloque clinica-bloque" aria-labelledby="visitas-titulo">
        <h3 id="visitas-titulo">En tu ruta</h3>
        <Consulta
          consulta={rutas}
          cargando="Cargando tu ruta…"
          error="No fue posible cargar tu ruta."
          vacio="No tienes visitas en la ruta de hoy."
          estaVacio={() => visitas.length === 0}
        >
          {() => (
            <ul className="listado-filas">
              {visitas.map((p) => (
                <li key={p.id} className="listado-fila">
                  <span className="listado-fila-cabeza">
                    <Link className="listado-fila-enlace" to={`/panel/clinica/mascotas/${p.mascota!.id}?servicio=${p.servicio_id}`}>
                      {p.mascota!.nombre} · {p.familia.titular_nombre}
                    </Link>
                    <span className="apagado numero">{p.estado === 'completada' ? 'Atendida' : hora(p.llegada_estimada)}</span>
                  </span>
                  <span className="clinica-fila-detalle">{nombreTipo(p.tipo_codigo)}</span>
                </li>
              ))}
            </ul>
          )}
        </Consulta>
      </section>
      <section className="bloque clinica-bloque" aria-labelledby="borradores-titulo">
        <h3 id="borradores-titulo">Consultas sin firmar</h3>
        <Consulta
          consulta={borradores}
          cargando="Cargando tus borradores…"
          error="No fue posible cargar tus borradores."
          vacio="No tienes consultas sin firmar."
          estaVacio={(d) => d.length === 0}
        >
          {(d) => (
            <ul className="listado-filas">
              {d.map((e) => (
                <li key={e.id} className="listado-fila">
                  <span className="listado-fila-cabeza">
                    <Link className="listado-fila-enlace" to={`/panel/clinica/historias/${e.id}`}>
                      {mascotas.get(e.mascota_id)?.nombre ?? 'Mascota'} · {fecha(e.fecha)}
                    </Link>
                    <Distintivo dominio="historia" valor={e.estado} />
                  </span>
                  <span className="clinica-fila-detalle">{e.motivo}</span>
                </li>
              ))}
            </ul>
          )}
        </Consulta>
      </section>
    </section>
  )
}

/** El médico abre la historia de cualquier mascota, sin pasar por Familias (Sección 12). */
function BuscarHistoria() {
  const [q, setQ] = useState('')
  const resultados = useBuscarMascotas(q)
  const especies = useEspecies()
  const especie = (codigo: string) => especies.data?.find((e) => e.codigo === codigo)?.nombre ?? codigo
  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h2>Abrir una historia clínica</h2>
      </div>
      <label className="campo">
        <span>Mascota o titular</span>
        <span className="buscador">
          <Icono nombre="buscar" size={18} />
          <input type="search" placeholder="Nombre de la mascota, del titular o documento" value={q} onChange={(e) => setQ(e.target.value)} />
        </span>
      </label>
      {q.trim().length > 1 &&
        (resultados.isError ? (
          // Un fallo se dice: antes, el 403 de /familias dejaba la lista vacía sin decir nada.
          <p className="aviso-error" role="alert">
            {mensajeError(resultados.error, 'No fue posible buscar la mascota.')}
          </p>
        ) : (
          <ul className="opciones" aria-label="Mascotas encontradas">
            {resultados.isPending && <li className="apagado">Buscando…</li>}
            {resultados.data?.items.length === 0 && <li className="apagado">Ninguna mascota coincide.</li>}
            {resultados.data?.items.map((m) => (
              <li key={m.id}>
                <Link className="opcion" to={`/panel/clinica/mascotas/${m.id}`}>
                  <strong>{m.nombre}</strong>
                  <span>
                    {especie(m.especie)} · {m.titular_nombre}
                    {!m.activa && ' · De baja'}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        ))}
    </section>
  )
}
