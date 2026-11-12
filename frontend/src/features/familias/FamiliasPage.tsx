import { FamiliasLista } from './FamiliasLista'

/** Familias sin ninguna abierta: el listado y, al lado, qué aparecerá al elegir una. */
export function FamiliasPage() {
  return (
    <div className="con-ficha">
      <FamiliasLista />
      <section className="ficha-abierta ficha-vacia" aria-label="Familia abierta">
        <p>
          Elige una familia para ver su línea: las cuotas, los preventivos y los servicios del año, con lo vencido y
          lo próximo a la vista.
        </p>
      </section>
    </div>
  )
}
