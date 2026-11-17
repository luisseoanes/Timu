import { isAxiosError } from 'axios'
import { useState } from 'react'
import { useParams } from 'react-router-dom'

import { AccesoLayout } from '@/components/AccesoLayout'
import { Icono } from '@/components/Icono'
import { esErrorPasajero, mensajeError } from '@/lib/errores'
import { fechaLarga } from '@/lib/formato'
import type { ContextoEncuestaRead } from '@/types'

import { type RespuestaEncuesta, useContextoEncuesta, useResponderEncuesta } from './api'

const ESCALA = [
  { valor: 1, texto: 'Muy mala' },
  { valor: 2, texto: 'Mala' },
  { valor: 3, texto: 'Regular' },
  { valor: 4, texto: 'Buena' },
  { valor: 5, texto: 'Excelente' },
]

type ComoSigue = 'bien' | 'duda' | 'novedad'

/** Las respuestas del seguimiento (6.21), cada una con lo que se le pide contar después. */
const COMO_SIGUE: { valor: ComoSigue; texto: string; icono: 'check' | 'ayuda' | 'alerta'; comentario: string }[] = [
  { valor: 'bien', texto: 'Sigue bien', icono: 'check', comentario: '¿Algo que quieras contarnos? (opcional)' },
  { valor: 'duda', texto: 'Tenemos una duda', icono: 'ayuda', comentario: '¿Cuál es tu duda? (opcional)' },
  { valor: 'novedad', texto: 'Algo no va bien', icono: 'alerta', comentario: '¿Qué notaste? (opcional)' },
]

/**
 * Encuesta que llega por WhatsApp tras una atención (F3-ENC-02). El token es el secreto. La de
 * satisfacción (6.20) se califica del 1 al 5; la de seguimiento (6.21) pregunta cómo sigue la
 * mascota. Hereda el acceso: es la otra página a la que la familia llega desde un enlace.
 */
export function EncuestaPage() {
  const { token = '' } = useParams()
  const contexto = useContextoEncuesta(token)
  const responder = useResponderEncuesta(token)

  let contenido
  if (contexto.isPending) {
    contenido = (
      <div className="esqueleto ingreso-esqueleto" role="status">
        <span className="sr-only">Abriendo la encuesta…</span>
        <span className="esqueleto-linea" aria-hidden="true" />
        <span className="esqueleto-linea" aria-hidden="true" />
        <span className="esqueleto-linea" aria-hidden="true" />
      </div>
    )
  } else if (contexto.isError && !esErrorPasajero(contexto.error)) {
    contenido = (
      <div className="ingreso-titulo">
        <h1>Esta encuesta no está disponible</h1>
        <p>Puede que el enlace esté incompleto. Ábrelo de nuevo desde el mensaje de WhatsApp en el que te llegó.</p>
      </div>
    )
  } else if (contexto.isError) {
    contenido = (
      <>
        <div className="ingreso-titulo">
          <h1>No pudimos abrir la encuesta</h1>
        </div>
        <p className="aviso-error" role="alert">
          <Icono nombre="alerta" size={16} />{' '}
          {mensajeError(contexto.error, 'El servidor no respondió. Intenta de nuevo en un momento.')}
        </p>
        <button className="btn btn-primario btn-bloque btn-grande" type="button" onClick={() => contexto.refetch()}>
          Reintentar
        </button>
      </>
    )
  } else if (responder.isSuccess) {
    contenido = <Gracias contexto={contexto.data} teContactamos={responder.data.te_contactamos} />
  } else if (contexto.data.respondida) {
    contenido = (
      <div className="ingreso-titulo">
        <h1>Ya nos respondiste</h1>
        <p>Esta encuesta ya tiene tu respuesta. Gracias por tomarte el tiempo.</p>
      </div>
    )
  } else {
    contenido = (
      <Formulario
        contexto={contexto.data}
        enviando={responder.isPending}
        error={responder.error}
        onEnviar={(respuesta) => responder.mutate(respuesta)}
      />
    )
  }

  return (
    <AccesoLayout frase={frase(contexto.data)} arriba>
      {contenido}
    </AccesoLayout>
  )
}

/** La frase del panel le habla a quien llega, sin repetir la pregunta. */
function frase(c: ContextoEncuestaRead | undefined): string | undefined {
  if (!c?.mascota) return undefined
  return c.tipo === 'seguimiento' ? `Seguimos pendientes de ${c.mascota}.` : `Tu opinión nos ayuda a cuidar mejor a ${c.mascota}.`
}

/** «Consulta domiciliaria del lunes, 27 de octubre»: de qué atención se pregunta. */
function deQueAtencion(c: ContextoEncuestaRead): string | null {
  if (!c.atencion) return null
  return c.fecha ? `${c.atencion} del ${fechaLarga(c.fecha)}` : c.atencion
}

function Formulario({
  contexto,
  enviando,
  error,
  onEnviar,
}: {
  contexto: ContextoEncuestaRead
  enviando: boolean
  error: Error | null
  onEnviar: (respuesta: RespuestaEncuesta) => void
}) {
  const [puntaje, setPuntaje] = useState<number | null>(null)
  const [comoSigue, setComoSigue] = useState<ComoSigue | null>(null)
  const [comentario, setComentario] = useState('')
  const seguimiento = contexto.tipo === 'seguimiento'
  const atencion = deQueAtencion(contexto)
  const elegida = COMO_SIGUE.find((o) => o.valor === comoSigue)
  const listo = seguimiento ? comoSigue !== null : puntaje !== null
  // Otra pestaña la respondió mientras esta seguía abierta: la API responde 422.
  const yaRespondida = isAxiosError(error) && error.response?.status === 422

  return (
    <>
      <div className="ingreso-titulo">
        {seguimiento ? (
          <h1>¿Cómo sigue {contexto.mascota ?? 'tu peludito'} después de la atención?</h1>
        ) : (
          <h1>¿Cómo te fue{contexto.mascota ? ` en la atención de ${contexto.mascota}` : ''}?</h1>
        )}
        {atencion && <p>{atencion}.</p>}
      </div>

      <form
        className="ingreso-form"
        onSubmit={(e) => {
          e.preventDefault()
          const texto = comentario.trim() || undefined
          if (seguimiento && comoSigue) onEnviar({ como_sigue: comoSigue, comentario: texto })
          else if (!seguimiento && puntaje) onEnviar({ puntaje, comentario: texto })
        }}
      >
        {seguimiento ? (
          <fieldset className="calificacion calificacion-seguimiento">
            <legend>Cuéntanos cómo está</legend>
            {COMO_SIGUE.map((o) => (
              <label key={o.valor} className="calificacion-opcion" data-valor={o.valor}>
                <input
                  type="radio"
                  name="como_sigue"
                  value={o.valor}
                  checked={comoSigue === o.valor}
                  onChange={() => setComoSigue(o.valor)}
                />
                <Icono nombre={o.icono} size={20} />
                <span>{o.texto}</span>
              </label>
            ))}
          </fieldset>
        ) : (
          <fieldset className="calificacion">
            <legend>Califica la atención</legend>
            {ESCALA.map((e) => (
              <label key={e.valor} className="calificacion-opcion">
                <input
                  type="radio"
                  name="puntaje"
                  value={e.valor}
                  checked={puntaje === e.valor}
                  onChange={() => setPuntaje(e.valor)}
                />
                <span className="calificacion-numero">{e.valor}</span>
                <span>{e.texto}</span>
              </label>
            ))}
          </fieldset>
        )}

        {comoSigue === 'novedad' && (
          <p className="aviso-alerta">
            <Icono nombre="mensaje" size={16} /> Si es una urgencia, no esperes: escríbenos ya por el chat de WhatsApp en el
            que te llegó este enlace.
          </p>
        )}

        <div className="campo">
          <label htmlFor="encuesta-comentario">{elegida?.comentario ?? '¿Algo que quieras contarnos? (opcional)'}</label>
          <textarea
            id="encuesta-comentario"
            className="input"
            rows={4}
            maxLength={2000}
            value={comentario}
            onChange={(e) => setComentario(e.target.value)}
          />
        </div>

        {error && (
          <p className="aviso-error" role="alert">
            <Icono nombre="alerta" size={16} />{' '}
            {yaRespondida
              ? 'Esta encuesta ya tenía una respuesta.'
              : esErrorPasajero(error)
                ? 'No pudimos guardar tu respuesta. Intenta de nuevo en un momento.'
                : 'No pudimos guardar tu respuesta. Abre otra vez el enlace desde el mensaje de WhatsApp.'}
          </p>
        )}
        <button className="btn btn-primario btn-bloque btn-grande" type="submit" disabled={!listo || enviando || yaRespondida}>
          {enviando ? 'Enviando…' : 'Enviar respuesta'}
        </button>
      </form>
    </>
  )
}

/** Dice qué pasa ahora: si la respuesta dejó una tarea, alguien del equipo contacta a la familia. */
function Gracias({ contexto, teContactamos }: { contexto: ContextoEncuestaRead; teContactamos: boolean }) {
  const mascota = contexto.mascota ?? 'tu peludito'
  return (
    <div className="ingreso-titulo">
      <h1>¡Gracias!</h1>
      <p role="status">
        {teContactamos
          ? `Alguien del equipo TIMU te va a contactar para saber más y ayudarte con ${mascota}.`
          : `Tu respuesta nos ayuda a cuidar mejor a ${mascota}.`}
      </p>
    </div>
  )
}
