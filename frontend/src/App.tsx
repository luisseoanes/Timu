import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AdminPage } from '@/features/admin/AdminPage'
import { AliadasPage } from '@/features/aliadas/AliadasPage'
import { MiClinicaPage } from '@/features/aliadas/MiClinicaPage'
import { AuthProvider } from '@/features/auth/AuthContext'
import { LoginPage } from '@/features/auth/LoginPage'
import { RecuperarPage, RestablecerPage } from '@/features/auth/RecuperarPage'
import { CampanasPage } from '@/features/campanas/CampanasPage'
import { CarteraPage } from '@/features/cartera/CarteraPage'
import { ClinicaPage } from '@/features/clinica/ClinicaPage'
import { EntradaPage } from '@/features/clinica/EntradaPage'
import { HistoriaMascotaPage } from '@/features/clinica/HistoriaMascotaPage'
import { ComercialPage } from '@/features/comercial/ComercialPage'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { FamiliaDetallePage } from '@/features/familias/FamiliaDetallePage'
import { FamiliasPage } from '@/features/familias/FamiliasPage'
import { PortalLayout } from '@/features/portal/PortalLayout'
import { PortalCitas, PortalDatos, PortalInicio, PortalMascota, PortalMascotas, PortalPagos } from '@/features/portal/PortalPages'
import { PreventivosPage } from '@/features/preventivos/PreventivosPage'
import { AfiliacionPage, AfiliacionResultadoPage } from '@/features/publico/AfiliacionPage'
import { EncuestaPage } from '@/features/publico/EncuestaPage'
import { VerificarCarnetPage } from '@/features/publico/VerificarCarnetPage'
import { RutasPage } from '@/features/rutas/RutasPage'
import { ServicioDetallePage } from '@/features/servicios/ServicioDetallePage'
import { ServiciosPage } from '@/features/servicios/ServiciosPage'
import { TareasPage } from '@/features/tareas/TareasPage'
import { AppLayout } from '@/layouts/AppLayout'
import { PERMISOS } from '@/lib/permisos'
import { ProtectedRoute } from '@/routes/ProtectedRoute'
import type { Rol } from '@/types'

// El panel es del equipo interno; las familias y las aliadas tienen su propio espacio.
const EQUIPO: Rol[] = ['admin', 'comercial', 'operaciones', 'medico']

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/recuperar" element={<RecuperarPage />} />
            <Route path="/restablecer" element={<RestablecerPage modo="restablecer" />} />
            <Route path="/activar" element={<RestablecerPage modo="activar" />} />
            <Route path="/encuesta/:token" element={<EncuestaPage />} />
            <Route path="/verificar/:codigo" element={<VerificarCarnetPage />} />
            <Route path="/afiliacion" element={<AfiliacionPage />} />
            <Route path="/afiliacion/resultado" element={<AfiliacionResultadoPage />} />

            <Route element={<ProtectedRoute roles={EQUIPO} />}>
              <Route element={<AppLayout />}>
                <Route index element={<DashboardPage />} />
                <Route path="familias" element={<FamiliasPage />} />
                <Route path="familias/:id" element={<FamiliaDetallePage />} />
                <Route path="cartera" element={<CarteraPage />} />
                <Route path="servicios" element={<ServiciosPage />} />
                <Route path="servicios/:id" element={<ServicioDetallePage />} />
                <Route path="tareas" element={<TareasPage />} />
                <Route path="preventivos" element={<PreventivosPage />} />
                <Route path="clinica" element={<ClinicaPage />} />
                <Route path="clinica/mascotas/:mascotaId" element={<HistoriaMascotaPage />} />
                <Route path="clinica/historias/:id" element={<EntradaPage />} />
                <Route path="rutas" element={<RutasPage />} />
                <Route path="campanas" element={<CampanasPage />} />
                <Route path="aliadas" element={<AliadasPage />} />
                <Route element={<ProtectedRoute roles={[...PERMISOS.mercadeo]} />}>
                  <Route path="comercial" element={<ComercialPage />} />
                </Route>
                <Route element={<ProtectedRoute roles={[...PERMISOS.administrar]} />}>
                  <Route path="admin" element={<AdminPage />} />
                </Route>
              </Route>
            </Route>

            <Route element={<ProtectedRoute roles={['familia']} />}>
              <Route path="portal" element={<PortalLayout />}>
                <Route index element={<PortalInicio />} />
                <Route path="mascotas" element={<PortalMascotas />} />
                <Route path="mascotas/:mascotaId" element={<PortalMascota />} />
                <Route path="citas" element={<PortalCitas />} />
                <Route path="pagos" element={<PortalPagos />} />
                {/* Regreso desde la pasarela: el estado real llega por webhook. */}
                <Route path="pagos/:pagoId" element={<PortalPagos />} />
                <Route path="datos" element={<PortalDatos />} />
              </Route>
            </Route>

            <Route element={<ProtectedRoute roles={['aliada']} />}>
              <Route path="aliada" element={<MiClinicaPage />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
