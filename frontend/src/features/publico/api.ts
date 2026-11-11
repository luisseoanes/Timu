import { useMutation, useQuery } from '@tanstack/react-query'

import { api } from '@/api/client'

/** Lo que ve quien abre el enlace de una encuesta (F3-ENC-02). */
export interface ContextoEncuesta {
  tipo: 'satisfaccion' | 'seguimiento' | string
  atencion: string | null
  fecha: string | null
  mascota: string | null
  respondida: boolean
}

/** Lo que muestra la verificación pública de un carnet (F2-PRE-06). */
export interface CarnetVerificado {
  codigo: string
  emitido_en: string
  sha256: string
  mascota: { nombre: string; especie: string; raza: string | null }
  aplicados: {
    nombre: string
    dosis: string | null
    fecha_aplicacion: string | null
    producto: string | null
    lote: string | null
    peso_kg?: number | null
    aplicado_por?: string | null
  }[]
}

export function useContextoEncuesta(token: string) {
  return useQuery({
    queryKey: ['encuesta-publica', token],
    queryFn: async () => (await api.get<ContextoEncuesta>(`/encuestas/respuesta/${token}`)).data,
    retry: false,
  })
}

export function useResponderEncuesta(token: string) {
  return useMutation({
    mutationFn: async (respuesta: { puntaje: number; comentario?: string }) =>
      (await api.post<{ detail: string }>(`/encuestas/respuesta/${token}`, respuesta)).data,
  })
}

export function useCarnetVerificado(codigo: string) {
  return useQuery({
    queryKey: ['carnet-verificado', codigo],
    queryFn: async () => (await api.get<CarnetVerificado>(`/verificacion/carnets/${codigo}`)).data,
    retry: false,
  })
}
