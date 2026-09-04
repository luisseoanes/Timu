import { useState } from 'react'

import { Icono } from '@/components/Icono'
import type { EstadoAfiliacion } from '@/types'

import { useFamilias } from './api'

const ESTADOS: { valor: EstadoAfiliacion; label: string }[] = [
  { valor: 'prospecto', label: 'Prospecto' },
  { valor: 'activa', label: 'Activa' },
  { valor: 'en_mora', label: 'En mora' },
  { valor: 'congelada', label: 'Congelada' },
  { valor: 'cancelada', label: 'Cancelada' },
]

// El color del distintivo comunica el estado antes que el texto.
const TONO: Record<EstadoAfiliacion, string> = {
  activa: 'ok',
  prospecto: 'info',
  en_mora: 'alerta',
  congelada: 'neutro',
  cancelada: 'peligro',
}

export function FamiliasPage() {
  const [q, setQ] = useState('')
  const [estado, setEstado] = useState<EstadoAfiliacion | ''>('')
  const { data, isLoading, error } = useFamilias({ q: q || undefined, estado: estado || undefined })

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Familias afiliadas</h3>
        <span className="apagado numero">{data?.total ?? 0} registros</span>
      </div>

      <div className="filtros" style={{ marginBottom: 'var(--e4)' }}>
        <label className="buscador">
          <Icono nombre="buscar" size={18} />
          <input
            type="search"
            placeholder="Nombre, documento o teléfono"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            aria-label="Buscar familias"
          />
        </label>
        <select
          className="input"
          style={{ width: 'auto' }}
          value={estado}
          onChange={(e) => setEstado(e.target.value as EstadoAfiliacion | '')}
          aria-label="Filtrar por estado"
        >
          <option value="">Todos los estados</option>
          {ESTADOS.map((e) => (
            <option key={e.valor} value={e.valor}>{e.label}</option>
          ))}
        </select>
        <button className="btn btn-primario" type="button" style={{ marginLeft: 'auto' }}>
          <Icono nombre="mas" size={16} />
          Nueva familia
        </button>
      </div>

      {isLoading && <p className="apagado">Cargando familias…</p>}
      {error && <p className="error">No fue posible cargar las familias. Reintenta en un momento.</p>}

      {data && (
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
              {data.items.map((f) => (
                <tr key={f.id}>
                  <td className="principal">{f.titular_nombre}</td>
                  <td className="numero">{f.documento}</td>
                  <td>{f.ciudad}</td>
                  <td className="numero">{f.telefono}</td>
                  <td>
                    <span className={`distintivo distintivo-${TONO[f.estado]}`}>
                      {ESTADOS.find((e) => e.valor === f.estado)?.label ?? f.estado}
                    </span>
                  </td>
                  <td className="numero">{f.mascotas.length}</td>
                </tr>
              ))}
              {data.items.length === 0 && (
                <tr>
                  <td colSpan={6} className="apagado">Ninguna familia coincide con el filtro.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
