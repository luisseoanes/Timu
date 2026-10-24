import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useAuth } from '@/features/auth/AuthContext'
import { useClinicas } from '@/features/aliadas/api'
import { mensajeError } from '@/lib/errores'
import { NOMBRE_ROL } from '@/lib/permisos'
import type { Rol } from '@/types'

import { useActualizarUsuario, useCrearUsuario, useUsuarios } from './api'

const ROLES_EQUIPO: Rol[] = ['admin', 'comercial', 'operaciones', 'medico', 'aliada']

export function Usuarios() {
  const { usuario: yo } = useAuth()
  const [rol, setRol] = useState('')
  const usuarios = useUsuarios(rol || undefined)
  const actualizar = useActualizarUsuario()
  const [nuevo, setNuevo] = useState(false)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Usuarios</h3>
        <div className="acciones">
          <select className="input" style={{ width: 'auto' }} value={rol} onChange={(e) => setRol(e.target.value)} aria-label="Perfil">
            <option value="">Todos los perfiles</option>
            {[...ROLES_EQUIPO, 'familia' as Rol].map((r) => (
              <option key={r} value={r}>{NOMBRE_ROL[r]}</option>
            ))}
          </select>
          <button className="btn btn-primario" type="button" onClick={() => setNuevo(true)}>
            <Icono nombre="mas" size={16} /> Nuevo usuario
          </button>
        </div>
      </div>
      <p className="apagado" style={{ marginBottom: 'var(--e4)' }}>
        Cambiar el perfil o desactivar a alguien cierra todas sus sesiones al instante.
      </p>
      {actualizar.isError && (
        <p className="error" role="alert">
          {mensajeError(actualizar.error, 'No fue posible actualizar el usuario.')}
        </p>
      )}
      <Consulta
        consulta={usuarios}
        cargando="Cargando usuarios…"
        error="No fue posible cargar los usuarios."
        vacio="No hay usuarios con este perfil."
        estaVacio={(d) => d.items.length === 0}
      >
        {(d) => (
          <div className="scroll-x">
            <table className="tabla">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Acceso</th>
                  <th>Perfil</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {d.items.map((u) => {
                  const soyYo = u.id === yo?.id
                  return (
                    <tr key={u.id}>
                      <td className="principal">{u.nombre}</td>
                      <td className="numero">{u.email ?? u.telefono ?? '—'}</td>
                      <td>
                        {u.rol === 'familia' || soyYo ? (
                          NOMBRE_ROL[u.rol]
                        ) : (
                          <select
                            className="input"
                            value={u.rol}
                            aria-label={`Perfil de ${u.nombre}`}
                            onChange={(e) => actualizar.mutate({ id: u.id, rol: e.target.value as Rol })}
                          >
                            {ROLES_EQUIPO.map((r) => (
                              <option key={r} value={r}>{NOMBRE_ROL[r]}</option>
                            ))}
                          </select>
                        )}
                      </td>
                      <td>
                        <label className="acciones">
                          <input
                            type="checkbox"
                            checked={u.activo}
                            disabled={soyYo}
                            aria-label={`${u.nombre} activo`}
                            onChange={(e) => actualizar.mutate({ id: u.id, activo: e.target.checked })}
                          />
                          {u.activo ? 'Activo' : 'Inactivo'}
                        </label>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Consulta>
      <NuevoUsuario abierto={nuevo} onCerrar={() => setNuevo(false)} />
    </section>
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
