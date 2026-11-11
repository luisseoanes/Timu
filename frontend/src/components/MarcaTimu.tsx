import blanco from '@/assets/marca/timu-blanco.svg'
import color from '@/assets/marca/timu-color.svg'
import compactoBlanco from '@/assets/marca/timu-compacto-blanco.svg'
import compactoColor from '@/assets/marca/timu-compacto-color.svg'

/**
 * El logo de TIMU (docs/manual-de-marca.md, sección 3), sacado del vector que entregó TIMU
 * (Marca TIMU.ai). No se recolorea: a color sobre fondo claro y en blanco (`claro`) sobre la
 * superficie de marca. `compacta` es el logotipo sin el lema ni las siluetas, que el manual
 * permite; va donde el lema no se leería (por debajo de unos 60 px de alto).
 *
 * Los SVG llevan los colores de la paleta escritos dentro: son el activo de la marca, no
 * colores de la interfaz, y la guarda de tokens no revisa los .svg.
 */
export function MarcaTimu({ claro = false, compacta = false }: { claro?: boolean; compacta?: boolean }) {
  const src = compacta ? (claro ? compactoBlanco : compactoColor) : claro ? blanco : color
  return (
    <img
      className={`marca${compacta ? ' marca-compacta' : ''}`}
      src={src}
      alt={compacta ? 'TIMU' : 'TIMU · Medicina veterinaria prepagada'}
    />
  )
}
