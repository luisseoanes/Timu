/**
 * Lo que falló por el mismo motivo, dicho una vez (DEU-73): el aviso de los casos de la IA repetía
 * la misma frase en cada caso, hasta un renglón de unos 184 caracteres. Conserva el orden en que
 * aparece cada motivo por primera vez.
 */
export function agruparPorMotivo<T>(
  elementos: T[],
  motivo: (e: T) => string | null | undefined,
  nombre: (e: T) => string,
): { motivo: string; nombres: string[] }[] {
  const grupos = new Map<string, string[]>()
  for (const e of elementos) {
    const m = motivo(e)
    if (!m) continue
    grupos.set(m, [...(grupos.get(m) ?? []), nombre(e)])
  }
  return [...grupos].map(([m, nombres]) => ({ motivo: m, nombres }))
}
