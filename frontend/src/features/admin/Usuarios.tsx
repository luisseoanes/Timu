import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { Paginacion } from '@/components/Paginacion'
import { useAuth } from '@/features/auth'
import { useClinicas } from '@/features/aliadas'
import { mensajeError } from '@/lib/errores'
import { telefono } from '@/lib/formato'
import { NOMBRE_ROL, PERFILES_EQUIPO } from '@/lib/permisos'
import type { RecuentosUsuarios, Rol, UsuarioRead } from '@/types'

import { useActualizarUsuario, useCrearUsuario, useRecuentosUsuarios, useUsuarios } from './api'

// El administrador gestiona a todo el equipo (Sección 12). En la fila solo se pasa entre perfiles
// del equipo: una cuenta de clínica aliada necesita su clínica (auth/service.py la exige), y eso
// se elige al crearla.
const ROLES_INTERNOS: readonly Rol[] = PERFILES_EQUIPO
const ROLES_EQUIPO: readonly Rol[] = [...PERFILES_EQUIPO, 'aliada']

type Vista = keyof RecuentosUsuarios

// Los grupos los define el backend (auth/router.py): el equipo, la clínica aliada, la familia al
// portal, y quien ya no entra, de cualquier perfil.
const VISTAS: { valor: Vista; label: string; vacio: string }[] = [
  { valor: 'equipo', label: 'Equipo', vacio: 'No hay nadie activo en el equipo.' },
  { valor: 'aliadas', label: 'Clínicas aliadas', vacio: 'Ninguna clínica aliada tiene acceso todavía. Créalo con «Nuevo usuario».' },
  { valor: 'familias', label: 'Familias', vacio: 'Ninguna familia tiene acceso al portal todavía.' },
  { valor: 'inactivos', label: 'Inactivos', vacio: 'No se ha desactivado a nadie.' },
]

const POR_PAGINA = 25

/** Usuarios como bandeja (R2-PAN-10): el equipo, las clínicas aliadas, las familias del portal y
 * quien ya no entra, con su recuento; cada fila con su perfil y lo que se puede hacer. */
export function Usuarios() {
  const { usuario: yo } = useAuth()
  const [vista, setVista] = useState<Vista>('equipo')
  const [q, setQ] = useState('')
  const [offset, setOffset] = useState(0)
  const recuentos = useRecuentosUsuarios(q || undefined)
  const usuarios = useUsuarios({ grupo: vista, q: q || undefined, limit: POR_PAGINA, offset })
  const actualizar = useActualizarUsuario()
  const [nuevo, setNuevo] = useState(false)
  const [desactivando, setDesactivando] = useState<UsuarioRead | null>(null)
  const [cambiando, setCambiando] = useState<{ usuario: UsuarioRead; rol: Rol } | null>(null)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Usuarios</h3>
        <button className="btn btn-primario" type="button" onClick={() => setNuevo(true)}>
          <Icono nombre="mas" size={16} /> Nuevo usuario
        </button>
      </div>
      <p className="admin-nota">Cambiar el perfil o desactivar a alguien cierra todas sus sesiones al instante.</p>
      <div className="filtros bandeja-filtros">
        <div className="segmento bandeja-vistas" role="group" aria-label="Vista de los usuarios">
          {VISTAS.map((v) => (
            <button
              key={v.valor}
              type="button"
              className="segmento-opcion"
              data-state={vista === v.valor ? 'active' : 'inactive'}
              aria-pressed={vista === v.valor}
              onClick={() => {
                setVista(v.valor)
                setOffset(0)
              }}
            >
              {v.label}
              {recuentos.data && (
                <>
                  {' '}
                  <span className="segmento-recuento numero">{recuentos.data[v.valor]}</span>
                </>
              )}
            </button>
          ))}
        </div>
        <label className="buscador bandeja-filtro">
          <Icono nombre="buscar" size={18} />
          <input
            type="search"
            placeholder="Nombre, correo o celular"
            value={q}
            onChange={(e) => {
              setQ(e.target.value)
              setOffset(0)
            }}
            aria-label="Buscar usuarios"
          />
        </label>
      </div>
      {actualizar.isError && (
        <p className="error" role="alert">
          {mensajeError(actualizar.error, 'No fue posible actualizar el usuario.')}
        </p>
      )}
      <Consulta
        consulta={usuarios}
        cargando="Cargando los usuarios…"
        error="No fue posible cargar los usuarios."
        vacio={q ? 'Nadie de esta vista coincide con la búsqueda.' : VISTAS.find((v) => v.valor === vista)!.vacio}
        estaVacio={(d) => d.items.length === 0}
      >
        {(d) => (
          <>
            <div className="scroll-x">
              <table className="tabla tabla-apilable bandeja-tabla usuarios-tabla">
                <thead>
                  <tr>
                    <th>Nombre</th>
                    <th>Perfil</th>
                    <th><span className="sr-only">Acciones</span></th>
                  </tr>
                </thead>
                <tbody>
                  {d.items.map((u) => {
                    const soyYo = u.id === yo?.id
                    return (
                      <tr key={u.id}>
                        <td className="principal" data-etiqueta="Nombre">
                          <span className="bandeja-titulo">
                            {u.nombre}
                            {soyYo && <Insignia tono="neutro">Tú</Insignia>}
                          </span>
                          <div className="bandeja-detalle">
                            {u.email && <span>{u.email}</span>}
                            {u.telefono && <span className="numero">{telefono(u.telefono)}</span>}
                          </div>
                        </td>
                        <td data-etiqueta="Perfil">
                          {/* El perfil propio no se cambia (quedaría sin administración), ni el de una familia o
                              una clínica aliada. Cambiarlo cierra sus sesiones: se confirma antes. */}
                          {!ROLES_INTERNOS.includes(u.rol) || soyYo || !u.activo ? (
                            NOMBRE_ROL[u.rol]
                          ) : (
                            <select
                              className="input usuarios-perfil"
                              value={u.rol}
                              aria-label={`Perfil de ${u.nombre}`}
                              onChange={(e) => setCambiando({ usuario: u, rol: e.target.value as Rol })}
                            >
                              {ROLES_INTERNOS.map((r) => (
                                <option key={r} value={r}>{NOMBRE_ROL[r]}</option>
                              ))}
                            </select>
                          )}
                        </td>
                        <td className="tabla-acciones">
                          {!soyYo &&
                            (u.activo ? (
                              <button className="btn btn-plano btn-plano-peligro" type="button" onClick={() => setDesactivando(u)} aria-label={`Desactivar a ${u.nombre}`}>
                                Desactivar
                              </button>
                            ) : (
                              <button
                                className="btn btn-suave"
                                type="button"
                                disabled={actualizar.isPending}
                                onClick={() => actualizar.mutate({ id: u.id, activo: true })}
                                aria-label={`Activar a ${u.nombre}`}
                              >
                                Activar
                              </button>
                            ))}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            <Paginacion total={d.total} limit={d.limit} offset={d.offset} onCambio={setOffset} />
          </>
        )}
      </Consulta>
      <NuevoUsuario abierto={nuevo} onCerrar={() => setNuevo(false)} />
      <Desactivar usuario={desactivando} onCerrar={() => setDesactivando(null)} />
      {cambiando && <CambiarPerfil {...cambiando} onCerrar={() => setCambiando(null)} />}
    </section>
  )
}

function CambiarPerfil({ usuario, rol, onCerrar }: { usuario: UsuarioRead; rol: Rol; onCerrar: () => void }) {
  const actualizar = useActualizarUsuario()
  return (
    <Modal
      abierto
      onCambio={(v) => !v && onCerrar()}
      titulo={`¿${usuario.nombre} pasa a ${NOMBRE_ROL[rol]}?`}
      descripcion={`Sus sesiones se cierran al instante; al volver a entrar, tendrá los permisos de ${NOMBRE_ROL[rol]}.`}
      pie={
        <>
          <button className="btn btn-secundario" type="button" onClick={onCerrar}>
            Dejar en {NOMBRE_ROL[usuario.rol]}
          </button>
          <button className="btn btn-primario" type="button" disabled={actualizar.isPending} onClick={() => actualizar.mutate({ id: usuario.id, rol }, { onSuccess: onCerrar })}>
            {actualizar.isPending ? 'Cambiando…' : 'Cambiar el perfil'}
          </button>
        </>
      }
    >
      {actualizar.isError && (
        <p className="error" role="alert">
          {mensajeError(actualizar.error, 'No fue posible cambiar el perfil.')}
        </p>
      )}
    </Modal>
  )
}

function Desactivar({ usuario, onCerrar }: { usuario: UsuarioRead | null; onCerrar: () => void }) {
  const actualizar = useActualizarUsuario()
  function cerrar() {
    actualizar.reset()
    onCerrar()
  }
  return (
    <Modal
      abierto={usuario !== null}
      onCambio={(v) => !v && cerrar()}
      titulo={`Desactivar a ${usuario?.nombre ?? ''}`}
      descripcion="Sus sesiones se cierran al instante y ya no puede entrar. Se puede volver a activar desde «Inactivos»."
      pie={
        <>
          <button className="btn btn-secundario" type="button" onClick={cerrar}>
            Mantener el acceso
          </button>
          <button
            className="btn btn-peligro"
            type="button"
            disabled={actualizar.isPending}
            onClick={() => usuario && actualizar.mutate({ id: usuario.id, activo: false }, { onSuccess: cerrar })}
          >
            {actualizar.isPending ? 'Desactivando…' : 'Desactivar'}
          </button>
        </>
      }
    >
      {actualizar.isError && (
        <p className="error" role="alert">
          {mensajeError(actualizar.error, 'No fue posible desactivar el usuario.')}
        </p>
      )}
    </Modal>
  )
}

function NuevoUsuario({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const crear = useCrearUsuario()
  const [rol, setRol] = useState<Rol>('operaciones')
  const clinicas = useClinicas()

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          crear.reset()
          onCerrar()
        }
      }}
      titulo="Nuevo usuario"
      descripcion="Comparte la contraseña inicial por un canal seguro; la persona puede cambiarla con «¿Olvidaste tu contraseña?»."
      pie={
        <button className="btn btn-primario" type="submit" form="nuevo-usuario" disabled={crear.isPending}>
          Crear usuario
        </button>
      }
    >
      <form
        id="nuevo-usuario"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const d = new FormData(e.currentTarget)
          const t = (c: string) => String(d.get(c) ?? '').trim() || undefined
          crear.mutate(
            {
              nombre: t('nombre') ?? '',
              email: t('email'),
              telefono: t('telefono'),
              rol,
              password: String(d.get('password')),
              clinica_aliada_id: rol === 'aliada' ? t('clinica') : undefined,
            },
            { onSuccess: onCerrar },
          )
        }}
      >
        <label className="campo ancho">
          <span>Nombre</span>
          <input className="input" name="nombre" required />
        </label>
        <label className="campo">
          <span>Correo</span>
          <input className="input" name="email" type="email" />
        </label>
        <label className="campo">
          <span>Celular</span>
          <input className="input" name="telefono" inputMode="tel" />
        </label>
        <label className="campo">
          <span>Perfil</span>
          <select className="input" value={rol} onChange={(e) => setRol(e.target.value as Rol)}>
            {ROLES_EQUIPO.map((r) => (
              <option key={r} value={r}>{NOMBRE_ROL[r]}</option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Contraseña inicial</span>
          <input className="input" name="password" type="password" minLength={8} required autoComplete="new-password" />
        </label>
        {rol === 'aliada' && (
          <label className="campo ancho">
            <span>Clínica aliada</span>
            <select className="input" name="clinica" required defaultValue="">
              <option value="" disabled>Selecciona la clínica</option>
              {clinicas.data?.map((c) => (
                <option key={c.id} value={c.id}>{c.nombre}</option>
              ))}
            </select>
          </label>
        )}
        {crear.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(crear.error, 'No fue posible crear el usuario.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
