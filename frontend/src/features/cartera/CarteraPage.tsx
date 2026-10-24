import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Paginacion } from '@/components/Paginacion'
import { fecha, moneda } from '@/lib/formato'
import type { EstadoAfiliacion } from '@/types'

import { useContratos } from './api'

// El contrato comparte los estados de la afiliación (los deriva cartera).
const ESTADOS: { valor: EstadoAfiliacion; label: string }[] = [
  { valor: 'activa', label: 'Activa' },
  { valor: 'en_mora', label: 'En mora' },
  { valor: 'congelada', label: 'Congelada' },
  { valor: 'cancelada', label: 'Cancelada' },
]

const POR_PAGINA = 25

/** Contratos con su saldo vencido, los más atrasados primero (F1-CAR). */
export function CarteraPage() {
  const [q, setQ] = useState('')
  const [estado, setEstado] = useState<EstadoAfiliacion | ''>('')
  const [params] = useSearchParams()
  const [soloMora, setSoloMora] = useState(params.get('mora') === '1')
  const [offset, setOffset] = useState(0)
  const contratos = useContratos({
    q: q || undefined,
    estado: estado || undefined,
    solo_mora: soloMora || undefined,
    limit: POR_PAGINA,
    offset,
  })

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Cartera</h3>
        <span className="apagado numero">{contratos.data?.total ?? 0} contratos</span>
      </div>

      <div className="filtros" style={{ marginBottom: 'var(--e4)' }}>
        <label className="buscador">
          <Icono nombre="buscar" size={18} />
          <input
            type="search"
            placeholder="Titular, documento o contrato"
            value={q}
            onChange={(e) => {
              setQ(e.target.value)
              setOffset(0)
            }}
            aria-label="Buscar contratos"
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
        <label className="acciones">
          <input
            type="checkbox"
            checked={soloMora}
            onChange={(e) => {
              setSoloMora(e.target.checked)
              setOffset(0)
            }}
          />
          Sólo con saldo vencido
        </label>
      </div>

      <Consulta
        consulta={contratos}
        cargando="Cargando cartera…"
        error="No fue posible cargar la cartera."
        vacio="Ningún contrato coincide con el filtro."
        estaVacio={(d) => d.items.length === 0}
      >
        {(datos) => (
          <>
            <div className="scroll-x">
              <table className="tabla">
                <thead>
                  <tr>
                    <th>Contrato</th>
                    <th>Titular</th>
                    <th>Ciudad</th>
                    <th>Plan</th>
                    <th>Mensualidad</th>
                    <th>Saldo vencido</th>
                    <th>Días de mora</th>
                    <th>Renovación</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {datos.items.map((c) => (
                    <tr key={c.id}>
                      <td className="numero">{c.numero}</td>
                      <td className="principal">
                        <Link to={`/familias/${c.familia_id}`}>{c.titular}</Link>
                      </td>
                      <td>{c.ciudad}</td>
                      <td>{c.plan}</td>
                      <td className="numero">{moneda(c.valor_mensual)}</td>
                      <td className="numero">{Number(c.saldo_vencido) > 0 ? moneda(c.saldo_vencido) : '—'}</td>
                      <td className="numero">{c.dias_mora > 0 ? c.dias_mora : '—'}</td>
                      <td className="numero">{fecha(c.fecha_renovacion)}</td>
                      <td>
                        <Distintivo dominio="afiliacion" valor={c.estado} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Paginacion total={datos.total} limit={datos.limit} offset={datos.offset} onCambio={setOffset} />
          </>
        )}
      </Consulta>
    </section>
  )
}
