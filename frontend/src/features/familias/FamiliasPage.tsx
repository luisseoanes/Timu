import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Paginacion } from '@/components/Paginacion'
import { useAuth } from '@/features/auth/AuthContext'
import { puede } from '@/lib/permisos'
import type { EstadoAfiliacion } from '@/types'

import { useFamilias } from './api'
import { NuevaFamiliaModal } from './NuevaFamiliaModal'

const ESTADOS: { valor: EstadoAfiliacion; label: string }[] = [
  { valor: 'prospecto', label: 'Prospecto' },
  { valor: 'activa', label: 'Activa' },
  { valor: 'en_mora', label: 'En mora' },
  { valor: 'congelada', label: 'Congelada' },
  { valor: 'cancelada', label: 'Cancelada' },
]

const POR_PAGINA = 25

export function FamiliasPage() {
  const { usuario } = useAuth()
  const [params] = useSearchParams()
  const qUrl = params.get('q') ?? ''
  const [q, setQ] = useState(qUrl)
  const [estado, setEstado] = useState<EstadoAfiliacion | ''>('')
  const [offset, setOffset] = useState(0)
  const [nueva, setNueva] = useState(false)
  // El buscador de la cabecera llega por ?q=: una búsqueda nueva reemplaza la escrita aquí.
  const [qPrevio, setQPrevio] = useState(qUrl)
  if (qUrl !== qPrevio) {
    setQPrevio(qUrl)
    setQ(qUrl)
    setOffset(0)
  }
  const familias = useFamilias({
    q: q || undefined,
    estado: estado || undefined,
    limit: POR_PAGINA,
    offset,
  })

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Familias afiliadas</h3>
        <span className="apagado numero">{familias.data?.total ?? 0} registros</span>
      </div>

      <div className="filtros" style={{ marginBottom: 'var(--e4)' }}>
        <label className="buscador">
          <Icono nombre="buscar" size={18} />
          <input
            type="search"
            placeholder="Nombre, documento o teléfono"
            value={q}
            onChange={(e) => {
              setQ(e.target.value)
              setOffset(0)
            }}
            aria-label="Buscar familias"
          />
        </label>
        <select
          className="input"
          style={{ width: 'auto' }}
          value={estado}
          onChange={(e) => {
            setEstado(e.target.value as EstadoAfiliacion | '')
            setOffset(0)
          }}
          aria-label="Filtrar por estado"
        >
          <option value="">Todos los estados</option>
          {ESTADOS.map((e) => (
            <option key={e.valor} value={e.valor}>{e.label}</option>
          ))}
        </select>
        {puede(usuario, 'gestionarAfiliacion') && (
          <button
            className="btn btn-primario"
            type="button"
            style={{ marginLeft: 'auto' }}
            onClick={() => setNueva(true)}
          >
            <Icono nombre="mas" size={16} />
            Nueva familia
          </button>
        )}
      </div>

      <Consulta
        consulta={familias}
        cargando="Cargando familias…"
        error="No fue posible cargar las familias."
        vacio="Ninguna familia coincide con el filtro."
        estaVacio={(d) => d.items.length === 0}
      >
        {(datos) => (
          <>
            <div className="scroll-x">
              <table className="tabla">
                <thead>
                  <tr>
                    <th>Titular</th>
                    <th>Documento</th>
                    <th>Ciudad</th>
                    <th>Teléfono</th>
                    <th>Estado</th>
                    <th>Mascotas</th>
                  </tr>
                </thead>
                <tbody>
                  {datos.items.map((f) => (
                    <tr key={f.id}>
                      <td className="principal">
                        <Link to={`/familias/${f.id}`}>{f.titular_nombre}</Link>
                      </td>
                      <td className="numero">{f.documento}</td>
                      <td>{f.ciudad}</td>
                      <td className="numero">{f.telefono}</td>
                      <td>
                        <Distintivo dominio="afiliacion" valor={f.estado} />
                      </td>
                      <td className="numero">{f.mascotas?.filter((m) => m.activa).length ?? 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Paginacion total={datos.total} limit={datos.limit} offset={datos.offset} onCambio={setOffset} />
          </>
        )}
      </Consulta>

      <NuevaFamiliaModal abierto={nueva} onCambio={setNueva} />
    </section>
  )
}
