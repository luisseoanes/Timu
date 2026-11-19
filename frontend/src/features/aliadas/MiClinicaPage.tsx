import { MarcaTimu } from '@/components/MarcaTimu'
import { MenuCuenta } from '@/components/MenuCuenta'
import { useAuth } from '@/features/auth'

import { useMiClinica } from './api'
import { Atendidas } from './Atendidas'
import { ValidarRemision } from './ValidarRemision'

/**
 * Espacio de la clínica aliada (6.22, R3-ALI-01): un mostrador. A la izquierda se valida
 * el código que trae la familia y se reporta la atención; a la derecha, lo que la clínica ya
 * atendió en el mes y lo que cubrió TIMU. Solo ve de la familia lo necesario para atender:
 * titular, últimos dígitos del documento y la mascota. Las remisiones por usar no se listan:
 * el código es la prueba de que la familia se presentó.
 */
export function MiClinicaPage() {
  const { usuario, logout } = useAuth()
  const clinica = useMiClinica()

  return (
    <div className="shell aliada">
      <header className="barra-marca">
        <MarcaTimu claro compacta />
        {/* En un computador compartido de recepción, en qué clínica se está. */}
        <p className="aliada-barra-clinica">{clinica.data?.nombre}</p>
        <MenuCuenta
          nombre={usuario?.nombre}
          detalle={clinica.data ? `${clinica.data.nombre} · ${clinica.data.ciudad}` : 'Clínica aliada'}
          alSalir={logout}
        />
      </header>
      <main className="contenido aliada-contenido">
        <div className="aliada-mostrador">
          <ValidarRemision />
          <Atendidas />
        </div>
      </main>
    </div>
  )
}
