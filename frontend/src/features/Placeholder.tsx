import { Icono } from '@/components/Icono'

/** Pantalla base de los módulos que aún no llegan en el backlog del backend. */
export function Placeholder({ titulo, detalle, ticket }: { titulo: string; detalle: string; ticket?: string }) {
  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>{titulo}</h3>
        {ticket && <span className="distintivo distintivo-neutro">{ticket}</span>}
      </div>
      <div className="fila">
        <span className="fila-icono"><Icono nombre="ayuda" size={18} /></span>
        <div className="fila-cuerpo">
          <strong>Módulo en construcción</strong>
          <span>{detalle}</span>
        </div>
      </div>
    </section>
  )
}
