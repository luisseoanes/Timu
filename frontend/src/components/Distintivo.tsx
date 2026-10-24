import { estado, type Dominio } from '@/lib/estados'

/** Distintivo de estado: el tono y el texto salen del mapeo único de `lib/estados.ts`. */
export function Distintivo({ dominio, valor }: { dominio: Dominio; valor: string }) {
  const { label, tono } = estado(dominio, valor)
  return <span className={`distintivo distintivo-${tono}`}>{label}</span>
}
