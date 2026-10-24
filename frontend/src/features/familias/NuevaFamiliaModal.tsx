import { useNavigate } from 'react-router-dom'

import { Modal } from '@/components/Modal'
import { useCiudades, useEspecies } from '@/features/catalogos/api'
import { mensajeError } from '@/lib/errores'
import type { TipoDocumento } from '@/types'

import { useCrearFamilia, type NuevaFamilia } from './api'

const TIPOS_DOCUMENTO: { valor: TipoDocumento; label: string }[] = [
  { valor: 'CC', label: 'Cédula de ciudadanía' },
  { valor: 'CE', label: 'Cédula de extranjería' },
  { valor: 'PA', label: 'Pasaporte' },
  { valor: 'PPT', label: 'Permiso de protección temporal' },
  { valor: 'TI', label: 'Tarjeta de identidad' },
  { valor: 'NIT', label: 'NIT' },
]

/** Lo vacío no viaja: el backend distingue «sin dato» de «dato en blanco». */
function texto(datos: FormData, campo: string): string | undefined {
  const valor = String(datos.get(campo) ?? '').trim()
  return valor || undefined
}

/**
 * Alta de una familia con su primera mascota. Al guardar abre la ficha, donde se
 * agregan las demás mascotas y se gestiona la afiliación.
 */
export function NuevaFamiliaModal({ abierto, onCambio }: { abierto: boolean; onCambio: (v: boolean) => void }) {
  const navegar = useNavigate()
  const crear = useCrearFamilia()
  const ciudades = useCiudades()
  const especies = useEspecies()

  function cerrar(valor: boolean) {
    if (!valor) crear.reset()
    onCambio(valor)
  }

  function guardar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    const familia: NuevaFamilia = {
      titular_nombre: texto(d, 'titular_nombre') ?? '',
      tipo_documento: texto(d, 'tipo_documento') ?? 'CC',
      documento: texto(d, 'documento') ?? '',
      telefono: texto(d, 'telefono') ?? '',
      email: texto(d, 'email'),
      ciudad: texto(d, 'ciudad') ?? '',
      direccion: texto(d, 'direccion'),
      mascotas: [
        {
          nombre: texto(d, 'mascota_nombre') ?? '',
          especie: texto(d, 'mascota_especie') ?? '',
          sexo: texto(d, 'mascota_sexo') as 'macho' | 'hembra' | undefined,
        },
      ],
    }
    crear.mutate(familia, { onSuccess: (creada) => navegar(`/familias/${creada.id}`) })
  }

  return (
    <Modal
      abierto={abierto}
      onCambio={cerrar}
      titulo="Nueva familia"
      descripcion="Datos del titular y de la primera mascota. Las demás se agregan desde la ficha."
      pie={
        <>
          <button className="btn btn-plano" type="button" onClick={() => cerrar(false)}>
            Cancelar
          </button>
          <button className="btn btn-primario" type="submit" form="nueva-familia" disabled={crear.isPending}>
            {crear.isPending ? 'Guardando…' : 'Guardar familia'}
          </button>
        </>
      }
    >
      <form id="nueva-familia" className="formulario" onSubmit={guardar}>
        <label className="campo ancho">
          <span>Nombre del titular</span>
          <input className="input" name="titular_nombre" required minLength={2} autoComplete="name" />
        </label>
        <label className="campo">
          <span>Tipo de documento</span>
          <select className="input" name="tipo_documento" defaultValue="CC">
            {TIPOS_DOCUMENTO.map((t) => (
              <option key={t.valor} value={t.valor}>{t.label}</option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Número de documento</span>
          <input className="input" name="documento" required inputMode="numeric" />
        </label>
        <label className="campo">
          <span>Celular</span>
          <input className="input" name="telefono" required inputMode="tel" placeholder="3001234567" />
        </label>
        <label className="campo">
          <span>Correo (opcional)</span>
          <input className="input" name="email" type="email" autoComplete="email" />
        </label>
        <label className="campo">
          <span>Ciudad</span>
          <select className="input" name="ciudad" required defaultValue="" disabled={ciudades.isPending}>
            <option value="" disabled>
              {ciudades.isPending ? 'Cargando ciudades…' : 'Selecciona la ciudad'}
            </option>
            {ciudades.data
              ?.filter((c) => c.activa)
              .map((c) => (
                <option key={c.codigo} value={c.nombre}>{c.nombre}</option>
              ))}
          </select>
        </label>
        <label className="campo">
          <span>Dirección (opcional)</span>
          <input className="input" name="direccion" autoComplete="street-address" />
        </label>

        <fieldset className="ancho formulario">
          <legend className="ancho">Primera mascota</legend>
          <label className="campo">
            <span>Nombre de la mascota</span>
            <input className="input" name="mascota_nombre" required />
          </label>
          <label className="campo">
            <span>Especie</span>
            <select className="input" name="mascota_especie" required defaultValue="" disabled={especies.isPending}>
              <option value="" disabled>
                {especies.isPending ? 'Cargando especies…' : 'Selecciona la especie'}
              </option>
              {especies.data
                ?.filter((e) => e.activa)
                .map((e) => (
                  <option key={e.codigo} value={e.codigo}>{e.nombre}</option>
                ))}
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

        {(ciudades.isError || especies.isError) && (
          <p className="error ancho" role="alert">
            No fue posible cargar los catálogos. Cierra y vuelve a abrir el formulario.
          </p>
        )}
        {crear.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(crear.error, 'No fue posible guardar la familia.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
