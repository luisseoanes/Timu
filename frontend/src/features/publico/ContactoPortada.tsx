import { useState } from 'react'

import { Icono } from '@/components/Icono'
import { enlaceWhatsApp } from '@/lib/enlaces'
import { mensajeError } from '@/lib/errores'
import { telefono } from '@/lib/formato'
import type { DatosTimuRead } from '@/types'

import { useEnviarContacto, type MensajeContacto } from './portada'
import { useCiudadesRegistro } from './registro'

/** Lo que acepta quien escribe: el mismo texto que guarda el backend (`AUTORIZACION_CONTACTO`). */
const AUTORIZACION = 'Autorizo a TIMU a usar estos datos para responder mi mensaje y contarme de sus planes.'

/**
 * Contacto (R3-PUB-04): el formulario entra al embudo de Comercial como un interesado con su
 * mensaje y la autorización de datos (Ley 1581); al lado, cómo se llega a TIMU sin escribir.
 */
export function ContactoPortada({ datos }: { datos?: DatosTimuRead }) {
  const enviar = useEnviarContacto()
  const ciudades = useCiudadesRegistro()
  const [falta, setFalta] = useState(false)

  return (
    <div className="contacto">
      <div className="contacto-datos">
        {datos?.whatsapp && (
          <a className="contacto-whatsapp" href={enlaceWhatsApp(datos.whatsapp)} target="_blank" rel="noreferrer">
            <Icono nombre="mensaje" size={20} />
            <span>
              <strong>Escríbenos por WhatsApp</strong>
              <span className="numero">{telefono(datos.whatsapp)}</span>
            </span>
          </a>
        )}
        <dl className="contacto-lista">
          {datos?.telefonos.length ? (
            <div>
              <dt>Llámanos</dt>
              <dd>
                {datos.telefonos.map((t) => (
                  <a key={t} className="numero" href={`tel:${t}`}>
                    {telefono(t)}
                  </a>
                ))}
              </dd>
            </div>
          ) : null}
          {datos?.correo && (
            <div>
              <dt>Correo</dt>
              <dd>
                <a href={`mailto:${datos.correo}`}>{datos.correo}</a>
              </dd>
            </div>
          )}
          {datos?.clinica_direccion && (
            <div>
              <dt>{datos.clinica_nombre ?? 'Nuestra clínica'}</dt>
              <dd>
                {[datos.clinica_direccion, datos.clinica_barrio, datos.clinica_ciudad].filter(Boolean).join(', ')}
                {datos.clinica_horario && <span className="contacto-horario">{datos.clinica_horario}</span>}
              </dd>
            </div>
          )}
          {datos?.horario_atencion && (
            <div>
              <dt>Cuándo te atendemos</dt>
              <dd>{datos.horario_atencion}</dd>
            </div>
          )}
          {datos?.redes.length ? (
            <div>
              <dt>Redes</dt>
              <dd>
                {datos.redes.map((r) => (
                  <a key={r.url} href={r.url} target="_blank" rel="noreferrer">
                    {r.nombre}
                  </a>
                ))}
              </dd>
            </div>
          ) : null}
        </dl>
      </div>

      {enviar.isSuccess ? (
        <div className="contacto-form contacto-recibido" role="status">
          <Icono nombre="check" size={24} />
          <h3>Recibimos tu mensaje</h3>
          <p>Te respondemos pronto por WhatsApp o al correo que nos dejaste.</p>
        </div>
      ) : (
        <form
          className="contacto-form"
          aria-labelledby="contacto-form-titulo"
          onSubmit={(e) => {
            e.preventDefault()
            const f = new FormData(e.currentTarget)
            const texto = (n: string) => String(f.get(n) ?? '').trim() || undefined
            const datos: MensajeContacto = {
              nombre: String(f.get('nombre')).trim(),
              telefono: texto('telefono'),
              email: texto('email'),
              ciudad: texto('ciudad'),
              mascota: texto('mascota'),
              especie: (texto('especie') as MensajeContacto['especie']) ?? undefined,
              mensaje: String(f.get('mensaje')).trim(),
              acepta_datos: true,
              sitio_web: String(f.get('sitio_web') ?? ''),
            }
            // Para responder hace falta por dónde: el celular o el correo.
            if (!datos.telefono && !datos.email) return setFalta(true)
            setFalta(false)
            enviar.mutate(datos)
          }}
        >
          <h3 id="contacto-form-titulo">Déjanos un mensaje</h3>
          <div className="formulario">
            <div className="campo ancho">
              <label htmlFor="contacto-nombre">Tu nombre</label>
              <input id="contacto-nombre" className="input" name="nombre" required minLength={2} maxLength={160} autoComplete="name" />
            </div>
            <div className="campo">
              <label htmlFor="contacto-telefono">Celular</label>
              <input id="contacto-telefono" className="input" name="telefono" type="tel" inputMode="tel" maxLength={20} autoComplete="tel" />
            </div>
            <div className="campo">
              <label htmlFor="contacto-email">Correo</label>
              <input id="contacto-email" className="input" name="email" type="email" maxLength={254} autoComplete="email" />
            </div>
            {falta && (
              <p className="error ancho" role="alert">
                Escribe tu celular o tu correo para poder responderte.
              </p>
            )}
            <div className="campo">
              <label htmlFor="contacto-ciudad">Ciudad</label>
              <select id="contacto-ciudad" className="input" name="ciudad" defaultValue="">
                <option value="">Prefiero no decirlo</option>
                {ciudades.data?.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <div className="campo">
              <label htmlFor="contacto-especie">Tu peludo es</label>
              <select id="contacto-especie" className="input" name="especie" defaultValue="">
                <option value="">Prefiero no decirlo</option>
                <option value="canino">Perro</option>
                <option value="felino">Gato</option>
              </select>
            </div>
            <div className="campo ancho">
              <label htmlFor="contacto-mascota">Cómo se llama (opcional)</label>
              <input id="contacto-mascota" className="input" name="mascota" maxLength={80} />
            </div>
            <div className="campo ancho">
              <label htmlFor="contacto-mensaje">Tu mensaje</label>
              <textarea id="contacto-mensaje" className="input" name="mensaje" required minLength={2} maxLength={2000} rows={4} />
            </div>
            {/* Trampa para robots: una persona no la ve ni la llena. */}
            <div className="sr-only" aria-hidden="true">
              <label htmlFor="contacto-sitio">Sitio web</label>
              <input id="contacto-sitio" name="sitio_web" tabIndex={-1} autoComplete="off" />
            </div>
            <label className="acciones ancho contacto-autorizo">
              <input type="checkbox" name="acepta_datos" required />
              <span>
                {AUTORIZACION}{' '}
                {datos?.politica_datos_url && (
                  <a href={datos.politica_datos_url} target="_blank" rel="noreferrer">
                    Política de tratamiento de datos
                  </a>
                )}
              </span>
            </label>
          </div>
          {enviar.isError && (
            <p className="error" role="alert">
              {mensajeError(enviar.error, 'No pudimos enviar tu mensaje. Inténtalo de nuevo o escríbenos por WhatsApp.')}
            </p>
          )}
          <div>
            <button className="btn btn-secundario" type="submit" disabled={enviar.isPending}>
              {enviar.isPending ? 'Enviando…' : 'Enviar mensaje'}
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
