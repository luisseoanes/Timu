import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Icono } from '@/components/Icono'
import { mensajeError } from '@/lib/errores'

import { urlContrato, useActualizarMisDatos, useMiFamilia, useMiPlan } from './api'
import { DocumentosPortal } from './DocumentosPortal'

/**
 * R3-POR-02 Los datos de la familia: lo que puede cambiar (contacto y dirección de las visitas),
 * lo que no (el titular), su contrato y sus documentos.
 */
export function PortalDatos() {
  const familia = useMiFamilia()
  const actualizar = useActualizarMisDatos()
  // Sin contrato vigente no hay plan: el botón llevaría a un 404.
  const conContrato = Boolean(useMiPlan().data)
  const [errorContrato, setErrorContrato] = useState<string | null>(null)

  async function abrirContrato() {
    setErrorContrato(null)
    try {
      window.open(await urlContrato(), '_blank', 'noopener')
    } catch (e) {
      setErrorContrato(mensajeError(e, 'No pudimos abrir el contrato.'))
    }
  }

  return (
    <div className="pila">
      <header className="portal-cabecera">
        <h1>Tus datos</h1>
        {conContrato && (
          <button className="btn btn-secundario" type="button" onClick={() => void abrirContrato()}>
            <Icono nombre="descargar" size={16} /> Tu contrato
          </button>
        )}
      </header>
      {errorContrato && (
        <p className="error" role="alert">
          {errorContrato}
        </p>
      )}
      <section className="portal-panel" aria-labelledby="datos-titulo">
        <h2 id="datos-titulo" className="portal-panel-titulo">
          Contacto y visitas
        </h2>
        <Consulta consulta={familia} cargando="Cargando tus datos…" error="No pudimos cargar tus datos.">
          {(f) => (
            <form
              className="formulario"
              onSubmit={(e) => {
                e.preventDefault()
                const d = new FormData(e.currentTarget)
                const cambios: Record<string, string> = {}
                for (const campo of ['email', 'telefono', 'barrio', 'direccion', 'complemento'] as const) {
                  const v = String(d.get(campo) ?? '').trim()
                  if (v !== (f[campo] ?? '')) cambios[campo] = v
                }
                actualizar.mutate(cambios)
              }}
            >
              <dl className="ficha ancho">
                <div>
                  <dt>Titular</dt>
                  <dd>{f.titular_nombre}</dd>
                </div>
                <div>
                  <dt>Documento</dt>
                  <dd className="numero">
                    {f.tipo_documento} {f.documento}
                  </dd>
                </div>
              </dl>
              <p className="apagado ancho">Para cambiar el titular o el documento, escríbenos por WhatsApp.</p>
              <label className="campo">
                <span>Celular (WhatsApp)</span>
                <input className="input" name="telefono" defaultValue={f.telefono} inputMode="tel" autoComplete="tel" required />
              </label>
              <label className="campo">
                <span>Correo</span>
                <input className="input" name="email" type="email" defaultValue={f.email ?? ''} autoComplete="email" />
              </label>
              <label className="campo">
                <span>Barrio</span>
                <input className="input" name="barrio" defaultValue={f.barrio} required minLength={2} maxLength={120} />
              </label>
              <label className="campo">
                <span>Dirección de las visitas</span>
                <input className="input" name="direccion" defaultValue={f.direccion ?? ''} autoComplete="street-address" />
              </label>
              <label className="campo ancho">
                <span>Complemento</span>
                <input className="input" name="complemento" defaultValue={f.complemento ?? ''} maxLength={255} placeholder="Torre, apartamento, indicaciones" />
              </label>
              {actualizar.isError && (
                <p className="error ancho" role="alert">
                  {mensajeError(actualizar.error, 'No pudimos guardar tus datos.')}
                </p>
              )}
              {actualizar.isSuccess && (
                <p className="exito ancho" role="status">
                  Datos guardados.
                </p>
              )}
              <div className="acciones ancho">
                <button className="btn btn-primario" type="submit" disabled={actualizar.isPending}>
                  {actualizar.isPending ? 'Guardando…' : 'Guardar'}
                </button>
              </div>
            </form>
          )}
        </Consulta>
      </section>
      <DocumentosPortal />
    </div>
  )
}
