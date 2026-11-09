import { Icono } from '@/components/Icono'

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
