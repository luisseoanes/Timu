import { useLayoutEffect, useRef, useState } from 'react'

/** El ancho real de una caja, para dibujar en píxeles y no deformar trazos ni puntos. Sin
 * ResizeObserver (pruebas en jsdom) se queda en el de partida. */
export function useAncho<T extends HTMLElement>(inicial: number, minimo = 0) {
  const ref = useRef<T>(null)
  const [ancho, setAncho] = useState(inicial)
  useLayoutEffect(() => {
    const caja = ref.current
    if (!caja || typeof ResizeObserver === 'undefined') return
    const medir = () => setAncho(Math.max(minimo, caja.clientWidth))
    medir()
    const observador = new ResizeObserver(medir)
    observador.observe(caja)
    return () => observador.disconnect()
  }, [minimo])
  return [ref, ancho] as const
}
