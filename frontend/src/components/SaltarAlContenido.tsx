import type { MouseEvent } from 'react'

/** El `id` del `<main>` de cada espacio, al que lleva el enlace. */
export const ID_CONTENIDO = 'contenido'

/**
 * El primer elemento enfocable de cada espacio con sesión (DEU-79): con el teclado, la barra con
 * la marca, los módulos y la cuenta son de 7 a 9 paradas de Tab antes del contenido. Solo se ve al
 * enfocarlo. Mueve el foco sin tocar la URL (el `#` lo usan las páginas públicas para sus secciones).
 */
export function SaltarAlContenido() {
  function saltar(e: MouseEvent<HTMLAnchorElement>) {
    e.preventDefault()
    document.getElementById(ID_CONTENIDO)?.focus()
  }
  return (
    <a className="saltar-contenido" href={`#${ID_CONTENIDO}`} onClick={saltar}>
      Saltar al contenido
    </a>
  )
}
