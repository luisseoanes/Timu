import * as Tabs from '@radix-ui/react-tabs'
import { useLayoutEffect, useRef, useState, type ReactNode } from 'react'

type Desborde = 'derecha' | 'izquierda' | 'ambos' | undefined

/** Desplaza la tira lo justo para que la pestaña activa se vea entera: abierta desde la URL o
 * elegida con el teclado, no puede quedar cortada en el borde. Solo mueve la tira, no la página. */
function mostrarActiva(lista: HTMLElement | null) {
  const activa = lista?.querySelector<HTMLElement>('[role="tab"][data-state="active"]')
  if (!lista || !activa) return
  const inicio = activa.offsetLeft - lista.offsetLeft
  const fin = inicio + activa.offsetWidth
  if (inicio < lista.scrollLeft) lista.scrollLeft = inicio
  else if (fin > lista.scrollLeft + lista.clientWidth) lista.scrollLeft = fin - lista.clientWidth
}

/** Por dónde sigue la tira cuando no cabe (en el celular se desplaza en su fila): el borde de
 * ese lado se desvanece para que se vea que hay más pestañas. */
function useDesborde() {
  const ref = useRef<HTMLDivElement>(null)
  const [desborde, setDesborde] = useState<Desborde>()
  useLayoutEffect(() => {
    const lista = ref.current
    if (!lista || typeof ResizeObserver === 'undefined') return
    const medir = () => {
      const izquierda = lista.scrollLeft > 1
      const derecha = lista.scrollLeft + lista.clientWidth < lista.scrollWidth - 1
      setDesborde(izquierda && derecha ? 'ambos' : derecha ? 'derecha' : izquierda ? 'izquierda' : undefined)
    }
    mostrarActiva(lista)
    medir()
    const observador = new ResizeObserver(medir)
    observador.observe(lista)
    lista.addEventListener('scroll', medir, { passive: true })
    return () => {
      observador.disconnect()
      lista.removeEventListener('scroll', medir)
    }
  }, [])
  return [ref, desborde] as const
}

/**
 * Pestañas sobre Radix Tabs: Radix pone el comportamiento (flechas, roles tab/tabpanel,
 * foco); el aspecto sale de `.pestanas-lista` y `.pestana` en componentes.css.
 */
export function Pestanas({
  pestanas,
  etiqueta,
  inicial,
  valor,
  onCambio,
}: {
  pestanas: { valor: string; titulo: string; contenido: ReactNode }[]
  /** Nombre accesible del grupo: `Secciones de la familia`. */
  etiqueta: string
  inicial?: string
  /** Pestaña abierta, cuando la decide quien usa el componente (con `onCambio`). */
  valor?: string
  onCambio?: (valor: string) => void
}) {
  const [ref, desborde] = useDesborde()
  // Tras cada cambio de pestaña, que la activa quede a la vista en la tira.
  const alCambiar = (v: string) => {
    onCambio?.(v)
    requestAnimationFrame(() => mostrarActiva(ref.current))
  }
  const controlada = valor !== undefined ? { value: valor } : {}
  return (
    <Tabs.Root defaultValue={inicial ?? pestanas[0]?.valor} {...controlada} onValueChange={alCambiar}>
      <Tabs.List ref={ref} className="pestanas-lista" aria-label={etiqueta} data-desborda={desborde}>
        {pestanas.map((p) => (
          <Tabs.Trigger key={p.valor} value={p.valor} className="pestana">
            {p.titulo}
          </Tabs.Trigger>
        ))}
      </Tabs.List>
      {pestanas.map((p) => (
        <Tabs.Content key={p.valor} value={p.valor}>
          {p.contenido}
        </Tabs.Content>
      ))}
    </Tabs.Root>
  )
}
