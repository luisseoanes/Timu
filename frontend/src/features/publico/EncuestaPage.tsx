import { useState } from 'react'
import { useParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Icono } from '@/components/Icono'
import { MarcaTimu } from '@/features/auth/AccesoLayout'
import { mensajeError } from '@/lib/errores'
import { fecha } from '@/lib/formato'

import { useContextoEncuesta, useResponderEncuesta } from './api'

const ESCALA = [
  { valor: 1, texto: 'Muy mala' },
  { valor: 2, texto: 'Mala' },
  { valor: 3, texto: 'Regular' },
  { valor: 4, texto: 'Buena' },
  { valor: 5, texto: 'Excelente' },
]

/** Encuesta que llega por enlace tras una atención (F3-ENC-02). El token es el secreto. */
export function EncuestaPage() {
  const { token = '' } = useParams()
  const contexto = useContextoEncuesta(token)
  const responder = useResponderEncuesta(token)
  const [puntaje, setPuntaje] = useState<number | null>(null)
  const [comentario, setComentario] = useState('')

  return (
    <div className="publica">
      <MarcaTimu />
      <section className="publica-tarjeta">
        <Consulta consulta={contexto} cargando="Cargando la encuesta…" error="No encontramos esta encuesta.">
          {(c) =>
            c.respondida || responder.isSuccess ? (
              <div className="pila">
                <h1>¡Gracias!</h1>
                <p className="aviso-ok" role="status">
                  <Icono nombre="check" size={16} /> Tu respuesta nos ayuda a cuidar mejor a {c.mascota ?? 'tu mascota'}.
                </p>
              </div>
            ) : (
              <form
                className="pila"
                onSubmit={(e) => {
                  e.preventDefault()
                  if (puntaje) responder.mutate({ puntaje, comentario: comentario.trim() || undefined })
                }}
              >
                <div className="ingreso-titulo">
                  <h1>¿Cómo te fue?</h1>
                  <p>
                    {c.atencion ?? 'Tu atención'}
                    {c.mascota ? ` de ${c.mascota}` : ''}
                    {c.fecha ? ` el ${fecha(c.fecha)}` : ''}.
                  </p>
                </div>
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
                <label className="campo">
                  <span>¿Algo que quieras contarnos? (opcional)</span>
                  <textarea
                    className="input"
                    rows={4}
                    maxLength={2000}
                    value={comentario}
                    onChange={(e) => setComentario(e.target.value)}
                  />
                </label>
                {responder.isError && (
                  <p className="aviso-error" role="alert">
                    {mensajeError(responder.error, 'No pudimos guardar tu respuesta.')}
                  </p>
                )}
                <button className="btn btn-primario btn-grande" type="submit" disabled={!puntaje || responder.isPending}>
                  {responder.isPending ? 'Enviando…' : 'Enviar respuesta'}
                </button>
              </form>
            )
          }
        </Consulta>
      </section>
    </div>
  )
}
