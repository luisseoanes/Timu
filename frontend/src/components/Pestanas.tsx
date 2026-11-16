import * as Tabs from '@radix-ui/react-tabs'
import { useLayoutEffect, useRef, useState, type ReactNode } from 'react'

type Desborde = 'derecha' | 'izquierda' | 'ambos' | undefined

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
  const controlada = valor !== undefined ? { value: valor, onValueChange: onCambio } : {}
  const [ref, desborde] = useDesborde()
  return (
    <Tabs.Root defaultValue={inicial ?? pestanas[0]?.valor} {...controlada}>
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
