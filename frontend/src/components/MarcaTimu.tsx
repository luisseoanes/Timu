/**
 * Marcador de la marca mientras TIMU entrega el logo en vector (docs/manual-de-marca.md,
 * sección 13). Es solo texto: no imita el logo ni lo recolorea. Cuando llegue el SVG, este
 * componente lo muestra tal cual, con su versión para fondo oscuro en `claro`.
 */
export function MarcaTimu({ claro = false }: { claro?: boolean }) {
  return (
    <span className={`marca${claro ? ' marca-clara' : ''}`}>
      <span className="marca-nombre">TIMU</span>
      <span className="marca-sub">Medicina veterinaria prepagada</span>
    </span>
  )
}
