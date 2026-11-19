import { useMutation, useQuery } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { CarnetVerificadoRead, ContextoEncuestaRead, RespuestaEncuestaRead } from '@/types'

/** Lo que responde la familia: la satisfacción con un puntaje y el seguimiento (6.21) con cómo sigue. */
export type RespuestaEncuesta =
  | { puntaje: number; comentario?: string }
  | { como_sigue: 'bien' | 'duda' | 'novedad'; comentario?: string }

/** Lo que ve quien abre el enlace de una encuesta (6.20). */
export function useContextoEncuesta(token: string) {
  return useQuery({
    queryKey: ['encuesta-publica', token],
    queryFn: async () => (await api.get<ContextoEncuestaRead>(`/encuestas/respuesta/${token}`)).data,
    retry: false,
  })
}

export function useResponderEncuesta(token: string) {
  return useMutation({
    mutationFn: async (respuesta: RespuestaEncuesta) =>
      (await api.post<RespuestaEncuestaRead>(`/encuestas/respuesta/${token}`, respuesta)).data,
  })
}

/** Lo que decía el carnet al emitirse (6.15): sus secciones y lo pendiente. */
export function useCarnetVerificado(codigo: string) {
  return useQuery({
    queryKey: ['carnet-verificado', codigo],
    queryFn: async () => (await api.get<CarnetVerificadoRead>(`/verificacion/carnets/${codigo}`)).data,
    retry: false,
  })
}
