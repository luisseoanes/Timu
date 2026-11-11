import * as Tabs from '@radix-ui/react-tabs'
import type { ReactNode } from 'react'

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
  return (
    <Tabs.Root defaultValue={inicial ?? pestanas[0]?.valor} {...controlada}>
      <Tabs.List className="pestanas-lista" aria-label={etiqueta}>
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
