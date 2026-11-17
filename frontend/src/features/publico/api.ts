import { useMutation, useQuery } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { CarnetVerificadoRead } from '@/types'

/** Lo que ve quien abre el enlace de una encuesta (F3-ENC-02). */
export interface ContextoEncuesta {
  tipo: 'satisfaccion' | 'seguimiento' | string
  atencion: string | null
  fecha: string | null
  mascota: string | null
  respondida: boolean
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

/** Lo que decía el carnet al emitirse (F2-PRE-06): sus secciones y lo pendiente. */
export function useCarnetVerificado(codigo: string) {
  return useQuery({
    queryKey: ['carnet-verificado', codigo],
    queryFn: async () => (await api.get<CarnetVerificadoRead>(`/verificacion/carnets/${codigo}`)).data,
    retry: false,
  })
}
