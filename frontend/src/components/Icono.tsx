/**
 * Iconografía del sistema: trazo de 1.6, esquinas redondeadas, 20px por defecto.
 * Un solo componente para no mezclar librerías ni pesos de trazo distintos.
 */
export type NombreIcono =
  | 'panel' | 'familias' | 'cartera' | 'servicios' | 'preventivos'
  | 'clinica' | 'rutas' | 'campanas' | 'buscar' | 'campana' | 'ayuda'
  | 'salir' | 'usuario' | 'llave' | 'calendario' | 'pago' | 'mas'

const TRAZOS: Record<NombreIcono, string> = {
  panel: 'M4 13h6V4H4v9Zm0 7h6v-5H4v5Zm10 0h6v-9h-6v9Zm0-16v5h6V4h-6Z',
  familias: 'M17 20v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9.5 10a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Zm12.5 10v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8',
  cartera: 'M3 7h18v12H3zM3 7l2-3h14l2 3M7 12h5',
  servicios: 'M8 3v4M16 3v4M3 10h18M5 7h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2Z',
  preventivos: 'M12 21s-7-4.4-7-9.5A4.5 4.5 0 0 1 12 8a4.5 4.5 0 0 1 7 3.5C19 16.6 12 21 12 21Z',
  clinica: 'M12 7v10M7 12h10M6 3h12a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z',
  rutas: 'M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11Zm0-8.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z',
  campanas: 'M4 8h4l8-4v16l-8-4H4zM19 9a4 4 0 0 1 0 6',
  buscar: 'M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm10 2-4.3-4.3',
  campana: 'M18 9a6 6 0 1 0-12 0c0 6-3 7-3 7h18s-3-1-3-7M13.7 20a2 2 0 0 1-3.4 0',
  ayuda: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Zm-2.2-11a2.2 2.2 0 1 1 3 2.1c-.5.2-.8.7-.8 1.2v.4M12 17h.01',
  salir: 'M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9',
  usuario: 'M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z',
  llave: 'M14 8a5 5 0 1 1-4.6 7L3 21l2-2 2 2 2-2 1.4-1.4A5 5 0 0 1 14 8Zm2 3h.01',
  calendario: 'M8 3v4M16 3v4M3 10h18M5 7h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2Z',
  pago: 'M3 10h18M3 7h18v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Zm4 8h4',
  mas: 'M12 5v14M5 12h14',
}

export function Icono({ nombre, size = 20 }: { nombre: NombreIcono; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={TRAZOS[nombre]} />
    </svg>
  )
}
