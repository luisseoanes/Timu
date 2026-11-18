import type { TipoAliada } from '@/types'

/** Lo que es cada aliada, como lo nombra la portada (`aliadas/service.py: NOMBRES_TIPO`). */
export const TIPOS_ALIADA: { valor: TipoAliada; nombre: string }[] = [
  { valor: 'clinica', nombre: 'Clínica veterinaria' },
  { valor: 'especialista', nombre: 'Especialista' },
  { valor: 'peluqueria', nombre: 'Peluquería y spa' },
  { valor: 'farmacia', nombre: 'Farmacia veterinaria' },
  { valor: 'hospedaje', nombre: 'Hotel y guardería' },
  { valor: 'funeraria', nombre: 'Transporte y funeraria' },
  { valor: 'otro', nombre: 'Aliada' },
]
