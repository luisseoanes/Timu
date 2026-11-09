import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AdminPage } from '@/features/admin'
import { AliadasPage, MiClinicaPage } from '@/features/aliadas'
import { AuthProvider, LoginPage, RecuperarPage, RestablecerPage } from '@/features/auth'
import { CampanasPage } from '@/features/campanas'
import { CarteraPage } from '@/features/cartera'
import { ClinicaPage, EntradaPage, HistoriaMascotaPage } from '@/features/clinica'
import { ComercialPage } from '@/features/comercial'
import { DashboardPage } from '@/features/dashboard'
import { FamiliaDetallePage, FamiliasPage } from '@/features/familias'
import { PortalCitas, PortalDatos, PortalInicio, PortalLayout, PortalMascota, PortalMascotas, PortalPagos } from '@/features/portal'
import { PreventivosPage } from '@/features/preventivos'
import { AfiliacionPage, AfiliacionResultadoPage, EncuestaPage, VerificarCarnetPage } from '@/features/publico'
import { RutasPage } from '@/features/rutas'
import { ServicioDetallePage, ServiciosPage } from '@/features/servicios'
import { TareasPage } from '@/features/tareas'
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
