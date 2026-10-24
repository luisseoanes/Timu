import { Link, useSearchParams } from 'react-router-dom'

import { Icono } from '@/components/Icono'
import { MarcaTimu } from '@/features/auth/AccesoLayout'
import { mensajeError } from '@/lib/errores'
import { moneda } from '@/lib/formato'

import { useAfiliarse, type SolicitudAfiliacionPublica } from './api'

const PLANES: Record<string, string> = { individual: 'Plan Individual', familiar: 'Plan Familiar' }

/**
 * Afiliación en línea (F1-AFI): datos del titular, la mascota y la aceptación expresa
 * de condiciones y tratamiento de datos. Al enviar, se continúa en la pasarela de pago.
 */
export function AfiliacionPage() {
  const [params] = useSearchParams()
  const plan = params.get('plan') ?? 'individual'
  const afiliarse = useAfiliarse()

  function enviar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    const texto = (c: string) => String(d.get(c) ?? '').trim() || undefined
    const solicitud: SolicitudAfiliacionPublica = {
      titular_nombre: texto('titular_nombre') ?? '',
      tipo_documento: texto('tipo_documento') ?? 'CC',
      documento: texto('documento') ?? '',
      telefono: texto('telefono') ?? '',
      email: texto('email'),
      ciudad: texto('ciudad') ?? '',
      direccion: texto('direccion'),
      mascotas: [
        {
          nombre: texto('mascota_nombre') ?? '',
          especie: texto('mascota_especie') ?? 'canino',
          sexo: texto('mascota_sexo') as 'macho' | 'hembra' | undefined,
        },
      ],
      plan_codigo: plan,
      acepta_condiciones: d.get('acepta_condiciones') === 'on',
      acepta_tratamiento_datos: d.get('acepta_datos') === 'on',
      origen: params.get('origen') ?? 'web',
      sitio_web: texto('sitio_web'),
    }
    afiliarse.mutate(solicitud, {
      onSuccess: (r) => window.location.assign(r.enlace_pago),
    })
  }

  return (
    <div className="publica">
      <MarcaTimu />
      <section className="publica-tarjeta publica-ancha">
        <div className="ingreso-titulo">
          <h1>Afilia a tu familia</h1>
          <p>
            {PLANES[plan] ?? plan}: consultas a domicilio, preventivos y orientación virtual. Al terminar
            pagas el primer mes en línea.
          </p>
        </div>
        <form className="formulario" onSubmit={enviar}>
          <label className="campo ancho">
            <span>Nombre completo del titular</span>
            <input className="input" name="titular_nombre" required minLength={2} autoComplete="name" />
          </label>
          <label className="campo">
            <span>Tipo de documento</span>
            <select className="input" name="tipo_documento" defaultValue="CC">
              <option value="CC">Cédula de ciudadanía</option>
              <option value="CE">Cédula de extranjería</option>
              <option value="PA">Pasaporte</option>
              <option value="PPT">Permiso de protección temporal</option>
            </select>
          </label>
          <label className="campo">
            <span>Número de documento</span>
            <input className="input" name="documento" required inputMode="numeric" />
          </label>
          <label className="campo">
            <span>Celular (WhatsApp)</span>
            <input className="input" name="telefono" required inputMode="tel" autoComplete="tel" />
          </label>
          <label className="campo">
            <span>Correo (opcional)</span>
            <input className="input" name="email" type="email" autoComplete="email" />
          </label>
          <label className="campo">
            <span>Ciudad</span>
            <input className="input" name="ciudad" required autoComplete="address-level2" />
          </label>
          <label className="campo">
            <span>Dirección</span>
            <input className="input" name="direccion" autoComplete="street-address" />
          </label>
          <fieldset className="ancho formulario">
            <legend className="ancho">Tu mascota</legend>
            <label className="campo">
              <span>Nombre</span>
              <input className="input" name="mascota_nombre" required />
            </label>
            <label className="campo">
              <span>Especie</span>
              <select className="input" name="mascota_especie" defaultValue="canino">
                <option value="canino">Perro</option>
                <option value="felino">Gato</option>
              </select>
            </label>
            <label className="campo">
              <span>Sexo (opcional)</span>
              <select className="input" name="mascota_sexo" defaultValue="">
                <option value="">Sin dato</option>
                <option value="hembra">Hembra</option>
                <option value="macho">Macho</option>
              </select>
            </label>
          </fieldset>
          {/* Trampa para bots: invisible y fuera del orden de tabulación. */}
          <input name="sitio_web" tabIndex={-1} autoComplete="off" className="sr-only" aria-hidden="true" />
          <label className="ancho acciones">
            <input type="checkbox" name="acepta_condiciones" required />
            Acepto las condiciones del plan y del contrato de afiliación.
          </label>
          <label className="ancho acciones">
            <input type="checkbox" name="acepta_datos" required />
            Autorizo el tratamiento de mis datos personales según la Ley 1581 de 2012.
          </label>
          {afiliarse.isError && (
            <p className="aviso-error ancho" role="alert">
              {mensajeError(afiliarse.error, 'No pudimos registrar la afiliación.')}
            </p>
          )}
          {afiliarse.isSuccess && (
            <p className="aviso-ok ancho" role="status">
              Te llevamos a la pasarela para pagar {moneda(afiliarse.data.valor)}…
            </p>
          )}
          <button className="btn btn-primario btn-grande ancho" type="submit" disabled={afiliarse.isPending}>
            <Icono nombre="pago" size={18} /> {afiliarse.isPending ? 'Registrando…' : 'Continuar al pago'}
          </button>
        </form>
      </section>
    </div>
  )
}

/** Regreso desde la pasarela. El resultado real llega por webhook; aquí sólo se informa. */
export function AfiliacionResultadoPage() {
  return (
    <div className="publica">
      <MarcaTimu />
      <section className="publica-tarjeta">
        <h1>Estamos confirmando tu pago</h1>
        <p className="aviso-ok" role="status">
          <Icono nombre="check" size={16} /> Cuando la pasarela confirme el pago te escribiremos por WhatsApp con
          los datos de tu afiliación y el acceso al portal.
        </p>
        <Link to="/login" className="btn btn-suave">
          Ir al ingreso
        </Link>
      </section>
    </div>
  )
}
